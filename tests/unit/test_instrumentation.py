# test_instrumentation.py
# Tests pour cost.py, tracker.py et models.py
# Lancer avec : pytest tests/unit/test_instrumentation.py -v

import time
import pytest
from apps.instrumentation.cost import CostCalculator
from apps.instrumentation.tracker import track_latency
from apps.instrumentation.eval.metrics import exact_match, contains_match, schema_valid


class TestCostCalculator:
    def setup_method(self):
        self.calc = CostCalculator()

    def test_gpt4o_mini(self):
        # (500/1000 * 0.000150) + (200/1000 * 0.000600) = 0.000075 + 0.000120 = 0.000195
        cost = self.calc.calculate("openai", "gpt-4o-mini", 500, 200)
        assert abs(cost - 0.000195) < 0.000001

    def test_unknown_provider_returns_zero(self):
        assert self.calc.calculate("unknown", "model-x", 1000, 1000) == 0.0

    def test_unknown_model_returns_zero(self):
        assert self.calc.calculate("openai", "gpt-99-ultra", 1000, 1000) == 0.0

    def test_zero_tokens(self):
        assert self.calc.calculate("openai", "gpt-4o-mini", 0, 0) == 0.0

    def test_format_usd(self):
        assert self.calc.format_usd(0.000195).startswith("$")


class TestLatencyTracker:
    def test_measures_time(self):
        with track_latency("test") as t:
            time.sleep(0.05)
        assert t.latency_ms >= 40

    def test_label_preserved(self):
        with track_latency("mon_label") as t:
            pass
        assert t.label == "mon_label"

    def test_returns_integer(self):
        with track_latency("test") as t:
            pass
        assert isinstance(t.latency_ms, int)

    def test_works_with_exception(self):
        with pytest.raises(ValueError):
            with track_latency("test") as t:
                raise ValueError("erreur test")
        assert t.latency_ms >= 0


class TestMetrics:
    def test_exact_match_true(self):
        assert exact_match("105", "105") is True

    def test_exact_match_ignores_spaces(self):
        assert exact_match("  105  ", "105") is True

    def test_exact_match_ignores_case(self):
        assert exact_match("PARIS", "paris") is True

    def test_exact_match_false(self):
        assert exact_match("106", "105") is False

    def test_contains_match_true(self):
        assert contains_match("The answer is 105 exactly.", "105") is True

    def test_contains_match_false(self):
        assert contains_match("The answer is 106.", "105") is False

    def test_schema_valid_all_keys(self):
        assert schema_valid('{"answer": "yes", "confidence": 0.9}',
                            {"required_keys": ["answer", "confidence"]}) is True

    def test_schema_valid_missing_key(self):
        assert schema_valid('{"answer": "yes"}',
                            {"required_keys": ["answer", "confidence"]}) is False

    def test_schema_valid_bad_json(self):
        assert schema_valid("not json", {"required_keys": ["answer"]}) is False


@pytest.mark.django_db
class TestLLMRequestLog:
    def test_create_log(self):
        from apps.instrumentation.models import LLMRequestLog
        log = LLMRequestLog.objects.create(raw_query="What is Django?", user=None)
        assert log.pk is not None
        assert log.status == "PENDING"
        assert log.cost_usd == 0

    def test_log_str(self):
        from apps.instrumentation.models import LLMRequestLog
        log = LLMRequestLog.objects.create(raw_query="test", user=None)
        assert "PENDING" in str(log)

    def test_failed_cases_property(self):
        from apps.instrumentation.models import EvalRun
        run = EvalRun(total_cases=10, passed_cases=7, pass_rate=0.7,
                      avg_latency_ms=200, total_cost_usd=0.001,
                      prompt_template_name="test", prompt_version_number=1)
        assert run.failed_cases == 3