# metrics.py
# Fonctions pour mesurer si une réponse LLM est correcte.

import json


def exact_match(actual: str, expected: str) -> bool:
    """La réponse est-elle exactement ce qu'on attendait ? (ignore majuscules et espaces)"""
    return actual.strip().lower() == expected.strip().lower()


def contains_match(actual: str, expected: str) -> bool:
    """La réponse contient-elle la valeur attendue quelque part ?"""
    return expected.strip().lower() in actual.strip().lower()


def schema_valid(actual: str, schema: dict) -> bool:
    """La réponse est-elle un JSON valide avec toutes les clés requises ?"""
    try:
        data = json.loads(actual)
        return all(key in data for key in schema.get("required_keys", []))
    except (json.JSONDecodeError, TypeError):
        return False
