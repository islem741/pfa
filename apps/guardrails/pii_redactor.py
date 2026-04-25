# pii_redactor.py
# EFFACE les données personnelles des textes (documents de la base de connaissance).
# Différence avec PIIGuard :
#   - PIIGuard BLOQUE une question utilisateur
#   - PIIRedactor NETTOIE un document avant qu'il entre dans le contexte du LLM

import re
import logging

logger = logging.getLogger(__name__)


class PIIRedactor:
    """
    Remplace les données personnelles par des tokens.
    
    Exemple :
    "Email: alice@test.com, Tél: 555-123-4567"
    → "Email: [EMAIL], Tél: [PHONE]"
    """

    REDACTION_RULES = {
        "email":       (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  "[EMAIL]"),
        "phone":       (r"\b(\+\d{1,3}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b", "[PHONE]"),
        "ssn":         (r"\b\d{3}-\d{2}-\d{4}\b",                                  "[SSN]"),
        "credit_card": (r"\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}\b",               "[CARD]"),
    }

    def redact(self, text: str) -> str:
        """Retourne le texte avec toutes les PII remplacées."""
        result = text
        for pii_type, (pattern, token) in self.REDACTION_RULES.items():
            found = re.findall(pattern, result)
            if found:
                result = re.sub(pattern, token, result)
                logger.info("redacted type=%s count=%d", pii_type, len(found))
        return result

    def has_pii(self, text: str) -> bool:
        """Retourne True si le texte contient des PII."""
        for _, (pattern, _) in self.REDACTION_RULES.items():
            if re.search(pattern, text):
                return True
        return False