# pipeline.py
# Lance les gardes UN PAR UN dans l'ordre.
# S'arrête au PREMIER échec (pas besoin de continuer si c'est déjà bloqué).
# Pattern : "Chain of Responsibility"

import logging
from apps.guardrails.input_guards import (
    GuardResult, LengthGuard, PromptInjectionGuard, PIIGuard,
)

logger = logging.getLogger(__name__)


class GuardrailPipeline:
    """
    INPUT ──▶ LengthGuard ──▶ InjectionGuard ──▶ PIIGuard ──▶ [PASS]
                  │                  │                │
               [FAIL]             [FAIL]           [FAIL]
    
    Pour ajouter un nouveau garde : une seule ligne dans __init__ !
    """

    def __init__(self):
        self._input_guards = [
            LengthGuard(),
            PromptInjectionGuard(),
            PIIGuard(),
        ]

    def check_input(self, query: str) -> GuardResult:
        for guard in self._input_guards:
            result = guard.check(query)
            if not result.passed:
                logger.warning("input_blocked guard=%s reason=%s", result.guard_name, result.reason)
                return result
        logger.debug("input_passed all_guards len=%d", len(query))
        return GuardResult(passed=True)