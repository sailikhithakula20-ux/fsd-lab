"""
AI Assistant Routes: Endpoints for the Grounded Generative AI Healthcare Assistant.
Handles chat interface rendering, message submission, history retrieval, and session management.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from services.ai_service import AIService

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/ai-assistant')
@login_required
def index():
    """Render the AI Assistant chat interface with existing conversation history."""
    messages = AIService.get_chat_history_for_display(current_user.id, limit=50)
    return render_template('ai_assistant.html', messages=messages)


@ai_bp.route('/api/v1/ai/chat', methods=['POST'])
@login_required
def api_chat():
    """
    Process a user message through the RAG-grounded GenAI pipeline.
    Returns the assistant reply, citations, and message metadata.
    """
    data = request.get_json(silent=True) or {}
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({'success': False, 'error': 'Message cannot be empty.'}), 400

    if len(user_message) > 2000:
        return jsonify({'success': False, 'error': 'Message exceeds 2000 character limit.'}), 400

    try:
        result = AIService.generate_response(
            user_id=current_user.id,
            user_message=user_message
        )

        return jsonify({
            'success': True,
            'reply': result['reply'],
            'citations': result['citations'],
            'message_id': result['message_id']
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'AI service error: {str(e)[:200]}'
        }), 500


@ai_bp.route('/api/v1/ai/history', methods=['GET'])
@login_required
def api_history():
    """Retrieve full chat history for the current user."""
    messages = AIService.get_chat_history_for_display(current_user.id, limit=50)
    return jsonify({'success': True, 'messages': messages})


@ai_bp.route('/api/v1/ai/clear', methods=['POST'])
@login_required
def api_clear():
    """Clear all conversation history for the current user."""
    AIService.clear_chat_history(current_user.id)
    return jsonify({
        'success': True,
        'message': 'Conversation history cleared successfully.'
    })
