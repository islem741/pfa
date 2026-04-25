# output_guards.py
# Valide la RÉPONSE du LLM avant de la renvoyer à l'utilisateur.
# Le LLM doit répondre en JSON. Parfois il ajoute du texte autour.
# Ce fichier extrait le JSON et vérifie qu'il est valide.

import json
import logging
import re
from pydantic import ValidationError
from apps.guardrails.schemas import KnowledgeAnswer

logger = logging.getLogger(__name__)


class OutputParseError(Exception):
    """Levée quand on ne peut pas parser la réponse du LLM."""


class OutputGuard:
    """
    Étapes :
    1. Trouver le JSON dans le texte brut
    2. Parser le JSON
    3. Valider avec Pydantic (KnowledgeAnswer)
    4. Ajouter disclaimer si confiance < 30%
    5. Retourner KnowledgeAnswer OU lever OutputParseError
    """

    CONFIDENCE_THRESHOLD = 0.3

    def validate(self, raw_text: str) -> KnowledgeAnswer:
        json_str = self._extract_json(raw_text)
        if not json_str:
            raise OutputParseError(f"Aucun JSON trouvé : {raw_text[:200]}")

        try:
            data   = json.loads(json_str)
            answer = KnowledgeAnswer(**data)
        except json.JSONDecodeError as e:
            logger.warning("json_error=%s", str(e))
            raise OutputParseError(f"JSON invalide : {e}") from e
        except ValidationError as e:
            logger.warning("schema_error=%s", str(e))
            raise OutputParseError(f"Schéma invalide : {e}") from e

        if answer.confidence < self.CONFIDENCE_THRESHOLD:
            answer.disclaimer = (
                "Avertissement : faible confiance dans cette réponse. "
                "Veuillez vérifier avec d'autres sources."
            )
            logger.info("low_confidence=%.2f disclaimer_added", answer.confidence)

        return answer

    def _extract_json(self, text: str) -> str | None:
        """
        Trouve le JSON dans le texte.
        Gère 3 cas :
        - texte = directement du JSON
        - texte contient ```json ... ```
        - texte contient {...} quelque part
        """
        # Cas 1 : le texte EST du JSON
        try:
            json.loads(text.strip())
            return text.strip()
        except json.JSONDecodeError:
            pass

        # Cas 2 : bloc ```json ... ```
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            return match.group(1)

        # Cas 3 : premier { ... } trouvé
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)

        return None