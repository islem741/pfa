# harness.py
# Le "professeur" du système.
# Lance tous les cas de test, compare les résultats, calcule la note.

import json
import logging
import time
from apps.instrumentation.models import EvalCase, EvalRun
from apps.instrumentation.eval.metrics import exact_match, schema_valid

logger = logging.getLogger(__name__)


class EvalHarness:
    """
    Utilisation :
        python manage.py run_eval
    Ou depuis Python :
        EvalHarness().run("knowledge_assistant", version=1)
    """

    def run(self, prompt_name: str, version: int) -> EvalRun:
        cases = list(EvalCase.objects.all())
        if not cases:
            logger.warning("Aucun cas de test — lancez seed_demo d'abord")
            return None

        passed        = 0
        total_latency = 0
        total_cost    = 0.0

        for case in cases:
            try:
                result = self._run_case(case)
                if result["passed"]:
                    passed += 1
                total_latency += result.get("latency_ms", 0)
                total_cost    += result.get("cost_usd",   0)
                logger.info("case=%s passed=%s", case.name, result["passed"])
            except Exception as e:
                logger.error("case_error=%s error=%s", case.name, e)

        pass_rate = passed / len(cases)

        eval_run = EvalRun.objects.create(
            prompt_template_name  = prompt_name,
            prompt_version_number = version,
            total_cases           = len(cases),
            passed_cases          = passed,
            pass_rate             = pass_rate,
            avg_latency_ms        = total_latency / len(cases),
            total_cost_usd        = total_cost,
        )
        logger.info("eval_done pass_rate=%.0f%%  %d/%d", pass_rate * 100, passed, len(cases))
        return eval_run

    def _run_case(self, case: EvalCase) -> dict:
        from apps.orchestration.runner import WorkflowRunner
        start  = time.monotonic()
        result = WorkflowRunner().run(query=case.input_query, user=None)
        latency = int((time.monotonic() - start) * 1000)

        passed = False
        if case.expected_answer:
            passed = exact_match(result.answer, case.expected_answer)
        elif case.expected_schema:
            output_str = (json.dumps(result.structured_output)
                          if result.structured_output else result.answer)
            passed = schema_valid(output_str, case.expected_schema)

        return {"passed": passed, "latency_ms": latency,
                "cost_usd": float(result.cost_usd) if result.cost_usd else 0.0}