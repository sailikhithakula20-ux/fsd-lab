"""
RAG Retrieval Service: BM25-based sparse retrieval engine for grounding
Generative AI responses in verified clinical and nutritional knowledge.
Indexes curated ICMR-NIN, IFCT, and preventive healthcare markdown documents.
"""

import os
import re
import math
from collections import Counter


class RAGService:
    """BM25 sparse retrieval over segmented medical knowledge documents."""

    _instance = None
    _corpus = []
    _doc_metadata = []
    _loaded = False

    # BM25 tuning parameters
    K1 = 1.5
    B = 0.75

    @classmethod
    def _ensure_loaded(cls, rag_dir=None):
        """Lazy-load and segment all markdown knowledge documents."""
        if cls._loaded:
            return

        if rag_dir is None:
            rag_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'rag', 'documents'
            )

        cls._corpus = []
        cls._doc_metadata = []

        if not os.path.isdir(rag_dir):
            cls._loaded = True
            return

        for filename in sorted(os.listdir(rag_dir)):
            if not filename.endswith('.md'):
                continue

            filepath = os.path.join(rag_dir, filename)
            source_name = filename.replace('.md', '').replace('_', ' ').title()

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            chunks = cls._segment_markdown(content, source_name)
            cls._corpus.extend(chunks)

        cls._loaded = True

    @staticmethod
    def _segment_markdown(text, source_name, max_chunk_tokens=350):
        """
        Split markdown into semantically coherent chunks using heading boundaries.
        Each chunk retains its section heading hierarchy for context.
        """
        lines = text.split('\n')
        chunks = []
        current_heading = source_name
        current_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                # Flush current
                if current_lines:
                    body = '\n'.join(current_lines).strip()
                    if len(body) > 30:
                        chunks.append({
                            'heading': current_heading,
                            'text': body,
                            'source': source_name,
                            'tokens': cls_tokenize(body)
                        })
                heading_text = stripped.lstrip('#').strip()
                current_heading = heading_text
                current_lines = []
            else:
                current_lines.append(line)

        # Flush remainder
        if current_lines:
            body = '\n'.join(current_lines).strip()
            if len(body) > 30:
                chunks.append({
                    'heading': current_heading,
                    'text': body,
                    'source': source_name,
                    'tokens': cls_tokenize(body)
                })

        return chunks

    @classmethod
    def retrieve(cls, query, top_k=5):
        """
        BM25 retrieval: rank knowledge chunks by relevance to the user query.
        Returns list of dicts: [{heading, text, source, score}, ...]
        """
        cls._ensure_loaded()

        if not cls._corpus:
            return []

        query_tokens = cls_tokenize(query)
        if not query_tokens:
            return []

        # Compute IDF for query terms
        N = len(cls._corpus)
        avg_dl = sum(len(c['tokens']) for c in cls._corpus) / max(N, 1)

        # Document frequency for each query token
        df = Counter()
        for token in set(query_tokens):
            for doc in cls._corpus:
                if token in doc['tokens']:
                    df[token] += 1

        idf = {}
        for token in set(query_tokens):
            n_t = df.get(token, 0)
            idf[token] = math.log((N - n_t + 0.5) / (n_t + 0.5) + 1.0)

        # Score each document
        scored = []
        for idx, doc in enumerate(cls._corpus):
            score = 0.0
            dl = len(doc['tokens'])
            tf_counter = Counter(doc['tokens'])

            for token in query_tokens:
                tf = tf_counter.get(token, 0)
                if tf == 0:
                    continue
                numerator = tf * (cls.K1 + 1)
                denominator = tf + cls.K1 * (1 - cls.B + cls.B * (dl / avg_dl))
                score += idf.get(token, 0) * (numerator / denominator)

            if score > 0:
                scored.append((score, idx))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, idx in scored[:top_k]:
            doc = cls._corpus[idx]
            results.append({
                'heading': doc['heading'],
                'text': doc['text'],
                'source': doc['source'],
                'score': round(score, 3)
            })

        return results

    @classmethod
    def build_grounding_context(cls, query, top_k=4, max_chars=3000):
        """
        Build a formatted grounding context string suitable for LLM prompt injection.
        Truncates total context to max_chars to stay within token budgets.
        """
        results = cls.retrieve(query, top_k=top_k)
        if not results:
            return "", []

        context_parts = []
        citations = []
        total_len = 0

        for i, doc in enumerate(results, 1):
            citation_tag = f"[Source {i}: {doc['source']} - {doc['heading']}]"
            text_block = doc['text']

            # Truncate if approaching limit
            remaining = max_chars - total_len
            if remaining < 100:
                break
            if len(text_block) > remaining:
                text_block = text_block[:remaining] + "..."

            context_parts.append(f"{citation_tag}\n{text_block}")
            citations.append({
                'index': i,
                'source': doc['source'],
                'heading': doc['heading'],
                'relevance_score': doc['score']
            })
            total_len += len(text_block) + len(citation_tag) + 2

        grounding_text = "\n\n".join(context_parts)
        return grounding_text, citations

    @classmethod
    def reset(cls):
        """Reset cached corpus (useful for testing)."""
        cls._corpus = []
        cls._doc_metadata = []
        cls._loaded = False


def cls_tokenize(text):
    """Simple whitespace + punctuation tokenizer with lowercasing and stopword removal."""
    STOPWORDS = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
        'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'between', 'out', 'off', 'over', 'under', 'again', 'further',
        'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'and', 'but', 'or', 'if', 'while', 'because',
        'this', 'that', 'these', 'those', 'i', 'me', 'my', 'we', 'our',
        'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it', 'its',
        'they', 'them', 'their', 'what', 'which', 'who', 'whom'
    }
    text_lower = text.lower()
    words = re.findall(r'[a-z0-9]+', text_lower)
    return [w for w in words if w not in STOPWORDS and len(w) > 1]
