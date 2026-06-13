"""
Text-based evaluation metrics: BLEU, ROUGE, and simple token-overlap similarity.

sentence-transformers is large (~500 MB) and optional. If not installed,
similarity_score falls back to Jaccard overlap on word sets.
"""
from __future__ import annotations

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class TextMetrics:

    @staticmethod
    def bleu_score(reference: str, candidate: str) -> float:
        """BLEU-1 score between reference and candidate strings."""
        from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

        # Simple whitespace tokenisation avoids NLTK corpus download
        ref_tokens = reference.lower().split()
        cand_tokens = candidate.lower().split()
        if not cand_tokens:
            return 0.0
        if ref_tokens == cand_tokens:
            return 1.0
        smoothie = SmoothingFunction().method4
        return float(sentence_bleu([ref_tokens], cand_tokens, smoothing_function=smoothie))

    @staticmethod
    def rouge_score(reference: str, candidate: str) -> Dict[str, float]:
        """ROUGE-1 and ROUGE-L F1 scores."""
        from rouge_score import rouge_scorer

        scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=True)
        scores = scorer.score(reference, candidate)
        return {
            "rouge1": round(scores["rouge1"].fmeasure, 4),
            "rougeL": round(scores["rougeL"].fmeasure, 4),
        }

    @staticmethod
    def similarity_score(text1: str, text2: str) -> float:
        """
        Semantic similarity in [0, 1].

        Uses sentence-transformers when available, otherwise falls back to
        Jaccard word-set overlap (good enough for tests without the large model).
        """
        try:
            from sentence_transformers import SentenceTransformer, util

            model = SentenceTransformer("all-MiniLM-L6-v2")
            emb1 = model.encode(text1, convert_to_tensor=True)
            emb2 = model.encode(text2, convert_to_tensor=True)
            score = float(util.cos_sim(emb1, emb2)[0][0])
            return max(0.0, min(1.0, score))
        except ImportError:
            # Fallback: Jaccard similarity on word sets
            s1 = set(text1.lower().split())
            s2 = set(text2.lower().split())
            if not s1 and not s2:
                return 1.0
            if not s1 or not s2:
                return 0.0
            return len(s1 & s2) / len(s1 | s2)
