"""
AIService: Context-Aware Grounded Generative AI Healthcare Assistant.
Integrates RAG retrieval, user health context injection, clinical safety guardrails,
and the Google GenAI SDK for conversational health guidance.
"""

import os
import json
from datetime import date, datetime

from models import (
    db,
    User,
    UserProfile,
    NutritionTarget,
    ChatHistory
)
from services.rag_service import RAGService


# System prompt enforcing clinical safety, grounding, and persona
SYSTEM_PROMPT = """You are AuraHealth AI, a compassionate, evidence-based preventive healthcare and nutrition assistant.

IDENTITY AND ROLE:
- You are part of a research-oriented healthcare platform built for the Indian population.
- You provide personalised dietary, fitness, sleep, and lifestyle guidance grounded in verified clinical literature.
- You reference ICMR-NIN RDA 2020 guidelines, Indian Food Composition Tables (IFCT), and peer-reviewed clinical studies.

CLINICAL SAFETY RULES (MANDATORY):
1. You NEVER diagnose diseases, prescribe medications, or replace a licensed medical professional.
2. Every response must clearly state that your suggestions are educational estimates, not medical prescriptions.
3. If a user describes emergency symptoms (chest pain, severe bleeding, loss of consciousness, difficulty breathing), immediately advise them to call emergency services (108 in India) and do NOT attempt diagnosis.
4. You never recommend extreme caloric restriction below 1200 kcal/day, fasting protocols without medical supervision, or unvalidated supplements.
5. For any clinical laboratory values (blood glucose, cholesterol, blood pressure), advise the user to consult their physician for interpretation.

RESPONSE STYLE:
- Warm, professional, and scientifically precise.
- Use Indian food names naturally (idli, dosa, dal, roti, sambar, ragi, bajra, etc.).
- When recommending foods, include approximate nutritional values per serving.
- Cite your knowledge sources when providing specific nutritional or clinical data.
- Use bullet points and clear structure for actionable advice.
- Keep responses focused and concise (aim for 150-300 words unless the user asks for detail).

GROUNDING INSTRUCTIONS:
- Prioritise information from the provided KNOWLEDGE CONTEXT over your general knowledge.
- If the KNOWLEDGE CONTEXT contains relevant data, cite it explicitly.
- If you are uncertain, say so honestly rather than fabricating clinical data.
"""


class AIService:
    """Orchestrates RAG retrieval, health context, and GenAI conversation."""

    @classmethod
    def get_user_health_context(cls, user_id):
        """Build a summary of the user's current health profile for LLM context injection."""
        user = db.session.get(User, user_id)
        if not user:
            return ""

        profile = UserProfile.query.filter_by(user_id=user_id).first()
        target = NutritionTarget.query.filter_by(user_id=user_id).first()

        parts = [f"USER HEALTH PROFILE: {user.full_name}"]

        if profile:
            if profile.age:
                parts.append(f"- Age: {profile.age} years")
            if profile.gender:
                parts.append(f"- Gender: {profile.gender}")
            if profile.height_cm:
                parts.append(f"- Height: {profile.height_cm} cm")
            if profile.weight_kg:
                parts.append(f"- Weight: {profile.weight_kg} kg")
                if profile.height_cm:
                    h = float(profile.height_cm) / 100.0
                    bmi = round(float(profile.weight_kg) / (h * h), 1)
                    parts.append(f"- BMI: {bmi} kg/m2")
            if profile.dietary_preference:
                parts.append(f"- Dietary Preference: {profile.dietary_preference}")
            if profile.activity_level:
                parts.append(f"- Activity Level: {profile.activity_level}")
            if profile.food_allergies:
                parts.append(f"- Food Allergies: {profile.food_allergies}")
            if profile.health_conditions:
                parts.append(f"- Health Conditions: {profile.health_conditions}")

        if target:
            parts.append(f"- Daily Calorie Target: {target.daily_calories} kcal")
            parts.append(f"- Protein Target: {target.protein_g} g")
            parts.append(f"- Carbohydrate Target: {target.carbs_g} g")
            parts.append(f"- Fat Target: {target.fat_g} g")

        return "\n".join(parts)

    @classmethod
    def get_conversation_history(cls, user_id, last_n=8):
        """Retrieve the most recent chat exchanges for conversational continuity."""
        records = ChatHistory.query.filter_by(user_id=user_id) \
            .order_by(ChatHistory.timestamp.desc()) \
            .limit(last_n).all()

        # Reverse to get chronological order
        records = list(reversed(records))

        history = []
        for rec in records:
            history.append({
                'role': 'user' if rec.sender == 'user' else 'model',
                'parts': [{'text': rec.message}]
            })

        return history

    @classmethod
    def generate_response(cls, user_id, user_message):
        """
        Full pipeline: RAG retrieval -> context construction -> GenAI call -> persist.
        Returns dict with assistant reply, citations, and metadata.
        Falls back to an offline knowledge-only response when no API key is configured.
        """
        # 1. Retrieve grounded clinical knowledge
        RAGService.reset()  # Ensure fresh load in case documents changed
        grounding_context, citations = RAGService.build_grounding_context(
            query=user_message,
            top_k=4,
            max_chars=2800
        )

        # 2. Build user health profile context
        health_context = cls.get_user_health_context(user_id)

        # 3. Persist user message
        user_entry = ChatHistory(
            user_id=user_id,
            sender='user',
            message=user_message,
            context_used=None
        )
        db.session.add(user_entry)
        db.session.commit()

        # 4. Attempt GenAI call
        api_key = os.environ.get('GEMINI_API_KEY', '').strip()

        if api_key:
            assistant_reply = cls._call_gemini(
                user_id=user_id,
                user_message=user_message,
                grounding_context=grounding_context,
                health_context=health_context,
                api_key=api_key
            )
        else:
            # Offline fallback: synthesize response from RAG context
            assistant_reply = cls._offline_fallback(
                user_message=user_message,
                grounding_context=grounding_context,
                health_context=health_context
            )

        # 5. Persist assistant reply
        citation_json = json.dumps(citations) if citations else None
        assistant_entry = ChatHistory(
            user_id=user_id,
            sender='assistant',
            message=assistant_reply,
            context_used=citation_json
        )
        db.session.add(assistant_entry)
        db.session.commit()

        return {
            'reply': assistant_reply,
            'citations': citations,
            'message_id': assistant_entry.id
        }

    @classmethod
    def _call_gemini(cls, user_id, user_message, grounding_context, health_context, api_key):
        """Call Google GenAI SDK (google.genai) with grounded RAG context."""
        try:
            from google import genai

            client = genai.Client(api_key=api_key)

            # Build the augmented prompt
            augmented_prompt = cls._build_augmented_prompt(
                user_message, grounding_context, health_context
            )

            # Retrieve conversation history for multi-turn
            chat_history = cls.get_conversation_history(user_id, last_n=6)

            # Build contents list
            contents = []
            for turn in chat_history:
                contents.append(turn)

            # Add current user message with grounding
            contents.append({
                'role': 'user',
                'parts': [{'text': augmented_prompt}]
            })

            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=contents,
                config={
                    'system_instruction': SYSTEM_PROMPT,
                    'temperature': 0.5,
                    'max_output_tokens': 1200,
                }
            )

            if response and response.text:
                return response.text.strip()
            else:
                return cls._offline_fallback(user_message, grounding_context, health_context)

        except Exception as e:
            error_msg = str(e)
            # Return graceful degradation
            fallback = cls._offline_fallback(user_message, grounding_context, health_context)
            return fallback + f"\n\n---\n*Note: Live AI service encountered an issue ({error_msg[:80]}). Response generated from local clinical knowledge base.*"

    @staticmethod
    def _build_augmented_prompt(user_message, grounding_context, health_context):
        """Construct the final RAG-augmented prompt for the LLM."""
        parts = []

        if health_context:
            parts.append(f"--- PATIENT CONTEXT ---\n{health_context}\n")

        if grounding_context:
            parts.append(f"--- VERIFIED CLINICAL KNOWLEDGE CONTEXT ---\n{grounding_context}\n")

        parts.append(f"--- USER QUESTION ---\n{user_message}")

        parts.append(
            "\nIMPORTANT: Ground your response in the KNOWLEDGE CONTEXT above. "
            "If relevant data exists there, cite the source. If you are unsure, say so. "
            "Include a brief disclaimer that this is educational guidance and not a medical prescription."
        )

        return "\n\n".join(parts)

    @staticmethod
    def _offline_fallback(user_message, grounding_context, health_context):
        """
        Generate a helpful response using only the retrieved RAG knowledge
        when no GenAI API key is available. This ensures the system always works.
        """
        if not grounding_context:
            return (
                "Thank you for your question. I was not able to find specific information "
                "in our clinical knowledge base related to your query. For personalised medical "
                "guidance, please consult a qualified healthcare professional.\n\n"
                "*This response was generated from the local knowledge base. "
                "Configure a Gemini API key in your .env file for AI-powered responses.*"
            )

        response_parts = [
            "Based on our verified clinical knowledge base, here is relevant information:\n"
        ]

        # Extract the most relevant passages
        passages = grounding_context.split('\n\n')
        for passage in passages[:3]:
            if passage.strip():
                response_parts.append(passage.strip())

        response_parts.append(
            "\n---\n**Disclaimer:** This information is educational and sourced from "
            "ICMR-NIN guidelines and peer-reviewed literature. It does not constitute "
            "medical advice. Please consult your healthcare provider for personalised "
            "clinical recommendations."
        )

        response_parts.append(
            "\n*This response was generated from the local clinical knowledge base. "
            "Configure a Gemini API key in your .env file for AI-powered conversational responses.*"
        )

        return "\n\n".join(response_parts)

    @classmethod
    def get_chat_history_for_display(cls, user_id, limit=50):
        """Retrieve formatted chat history for template rendering."""
        records = ChatHistory.query.filter_by(user_id=user_id) \
            .order_by(ChatHistory.timestamp.asc()) \
            .limit(limit).all()

        messages = []
        for rec in records:
            citations = []
            if rec.context_used:
                try:
                    citations = json.loads(rec.context_used)
                except (json.JSONDecodeError, TypeError):
                    pass

            messages.append({
                'id': rec.id,
                'sender': rec.sender,
                'message': rec.message,
                'citations': citations,
                'timestamp': rec.timestamp.strftime('%H:%M - %b %d')
            })

        return messages

    @classmethod
    def clear_chat_history(cls, user_id):
        """Clear all conversation history for a user."""
        ChatHistory.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return True
