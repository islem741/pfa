# hallucination.py
# Vérifie si la réponse du LLM est basée sur les sources fournies.
# Une hallucination = le LLM invente des faits qui ne viennent pas des sources.

import re
import logging

logger = logging.getLogger(__name__)


class HallucinationChecker:
    """
    Stratégie simple (pour le projet académique) :
    - On extrait les mots importants de la réponse
    - On vérifie combien sont présents dans les documents sources
    - Peu de mots en commun → probable hallucination → confiance réduite
    """

    GROUNDING_THRESHOLD = 0.3
    CONFIDENCE_PENALTY  = 0.2

    def check(self, answer: str, source_documents: list[str]) -> float:
        """
        Retourne un score de confiance (0.0 à 1.0).
        Si pas de sources → 0.5 (on ne peut pas juger).
        """
        if not source_documents:
            return 0.5

        keywords = self._extract_keywords(answer)
        if not keywords:
            return 0.5

        sources_text    = " ".join(source_documents).lower()
        matched         = sum(1 for kw in keywords if kw in sources_text)
        grounding_score = matched / len(keywords)

        logger.debug("grounding keywords=%d matched=%d score=%.2f",
                     len(keywords), matched, grounding_score)

        if grounding_score < self.GROUNDING_THRESHOLD:
            confidence = max(0.0, 1.0 - self.CONFIDENCE_PENALTY)
            logger.warning("possible_hallucination grounding=%.2f", grounding_score)
            return confidence

        return min(1.0, 0.5 + grounding_score * 0.5)

    def _extract_keywords(self, text: str) -> list[str]:
        """Mots de plus de 4 lettres, en minuscules, sans mots vides."""
        STOP_WORDS = {"that", "this", "with", "from", "have", "will", "been",
                      "they", "their", "what", "when", "where", "about", "would"}
        words = re.findall(r"\b[a-zA-Z]{5,}\b", text.lower())
        return [w for w in words if w not in STOP_WORDS]