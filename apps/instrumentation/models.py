# models.py
# Les "tables" de la base de données.
# Tout ce qui se passe dans le système est enregistré ici.
# IMPORTANT : on n'efface JAMAIS ces données (journal immuable).

import uuid
from django.db import models
from django.contrib.auth.models import User


class LLMRequestLog(models.Model):
    """
    Une ligne = une requête LLM.
    Statut : PENDING → IN_FLIGHT → COMPLETED / FAILED / BLOCKED
    """
    STATUS_CHOICES = [
        ("PENDING",   "Pending"),
        ("IN_FLIGHT", "In Flight"),
        ("COMPLETED", "Completed"),
        ("FAILED",    "Failed"),
        ("BLOCKED",   "Blocked by Guardrail"),
    ]

    id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default="PENDING", db_index=True)

    prompt_template_name  = models.CharField(max_length=100, blank=True)
    prompt_version_number = models.PositiveIntegerField(null=True)

    raw_query         = models.TextField()
    rendered_prompt   = models.TextField(blank=True)
    raw_response      = models.TextField(blank=True)
    structured_output = models.JSONField(null=True, blank=True)

    provider      = models.CharField(max_length=50, blank=True)
    model         = models.CharField(max_length=100, blank=True)
    fallback_used = models.BooleanField(default=False)

    input_tokens  = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    cost_usd      = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    latency_ms    = models.PositiveIntegerField(null=True)

    input_blocked      = models.BooleanField(default=False)
    input_block_reason = models.CharField(max_length=200, blank=True)
    output_blocked     = models.BooleanField(default=False)
    truncation_applied = models.BooleanField(default=False)
    turns_removed      = models.PositiveSmallIntegerField(default=0)

    retry_count = models.PositiveSmallIntegerField(default=0)
    error_class = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering     = ["-created_at"]
        verbose_name = "LLM Request Log"

    def __str__(self):
        return f"[{self.status}] {self.user} — {str(self.id)[:8]}"


class ToolCallLog(models.Model):
    """Une ligne = un appel d'outil (calculatrice, recherche...) fait par le LLM."""
    request    = models.ForeignKey(LLMRequestLog, on_delete=models.CASCADE,
                                   related_name="tool_calls")
    tool_name  = models.CharField(max_length=100)
    arguments  = models.JSONField()
    result     = models.JSONField(null=True)
    success    = models.BooleanField(default=True)
    error      = models.TextField(blank=True)
    latency_ms = models.PositiveIntegerField(null=True)
    iteration  = models.PositiveSmallIntegerField(default=1)
    called_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tool_name} — {'OK' if self.success else 'FAIL'}"


class EvalCase(models.Model):
    """Un cas de test : question + réponse attendue."""
    name            = models.CharField(max_length=200, unique=True)
    input_query     = models.TextField()
    expected_answer = models.TextField(blank=True)
    expected_schema = models.JSONField(null=True)
    rubric          = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class EvalRun(models.Model):
    """Résultat d'une session d'évaluation complète."""
    prompt_template_name  = models.CharField(max_length=100)
    prompt_version_number = models.PositiveIntegerField()
    total_cases           = models.PositiveIntegerField()
    passed_cases          = models.PositiveIntegerField()
    pass_rate             = models.FloatField()
    avg_latency_ms        = models.FloatField()
    total_cost_usd        = models.DecimalField(max_digits=8, decimal_places=4)
    run_at                = models.DateTimeField(auto_now_add=True)
    notes                 = models.TextField(blank=True)

    @property
    def failed_cases(self):
        return self.total_cases - self.passed_cases

    def __str__(self):
        return f"{self.prompt_template_name} v{self.prompt_version_number} — {self.pass_rate:.0%}"