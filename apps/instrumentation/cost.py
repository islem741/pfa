# cost.py
# Calcule le coût en dollars de chaque appel LLM.
# Chaque token (≈ 1 mot) coûte une fraction de centime.

import logging

logger = logging.getLogger(__name__)

# Prix en USD pour 1000 tokens
PRICING = {
    "openai": {
        "gpt-4o":      {"input": 0.0025,   "output": 0.010},
        "gpt-4o-mini": {"input": 0.000150, "output": 0.000600},
    },
    "anthropic": {
        "claude-3-haiku-20240307":  {"input": 0.00025, "output": 0.00125},
        "claude-3-5-sonnet-latest": {"input": 0.003,   "output": 0.015},
    },
}


class CostCalculator:
    """
    Utilisation :
        calc = CostCalculator()
        cost = calc.calculate("openai", "gpt-4o-mini", 500, 200)
        # → 0.000195 dollars
    """

    def calculate(self, provider: str, model: str,
                  input_tokens: int, output_tokens: int) -> float:
        """Retourne le coût en USD. Retourne 0.0 si modèle inconnu."""
        prices = PRICING.get(provider, {}).get(model)
        if not prices:
            logger.warning("unknown_model provider=%s model=%s", provider, model)
            return 0.0
        cost = (
            (input_tokens  / 1000) * prices["input"] +
            (output_tokens / 1000) * prices["output"]
        )
        return round(cost, 6)

    def format_usd(self, cost: float) -> str:
        return f"${cost:.6f}"