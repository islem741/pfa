# admin.py
# Configure le panneau d'administration Django.
# URL : http://localhost:8000/admin/
# Le jury peut tout voir ici.

from django.contrib import admin
from django.utils.html import format_html
from apps.instrumentation.models import LLMRequestLog, ToolCallLog, EvalCase, EvalRun


class ToolCallLogInline(admin.TabularInline):
    """Affiche les appels d'outils DANS la page d'une requête."""
    model           = ToolCallLog
    extra           = 0
    readonly_fields = ("tool_name", "success", "latency_ms", "called_at", "error")
    can_delete      = False


@admin.register(LLMRequestLog)
class LLMRequestLogAdmin(admin.ModelAdmin):
    list_display  = ("short_id", "colored_status", "user", "provider",
                     "fallback_used", "cost_usd", "latency_ms", "input_blocked", "created_at")
    list_filter   = ("status", "provider", "fallback_used", "input_blocked")
    search_fields = ("raw_query", "user__username")
    ordering      = ["-created_at"]
    inlines       = [ToolCallLogInline]

    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False

    def short_id(self, obj):
        return str(obj.id)[:8]
    short_id.short_description = "ID"

    def colored_status(self, obj):
        colors = {"COMPLETED": "green", "FAILED": "red",
                  "BLOCKED": "orange", "IN_FLIGHT": "blue", "PENDING": "gray"}
        color = colors.get(obj.status, "black")
        return format_html('<span style="color:{};font-weight:bold">{}</span>',
                           color, obj.status)
    colored_status.short_description = "Statut"


@admin.register(EvalRun)
class EvalRunAdmin(admin.ModelAdmin):
    list_display = ("prompt_template_name", "prompt_version_number",
                    "passed_cases", "total_cases", "pass_rate_display",
                    "avg_latency_ms", "total_cost_usd", "run_at")

    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False

    def pass_rate_display(self, obj):
        pct   = obj.pass_rate * 100
        color = "green" if pct >= 80 else "orange" if pct >= 60 else "red"
        return format_html('<span style="color:{};font-weight:bold">{:.0f}%</span>',
                           color, pct)
    pass_rate_display.short_description = "Taux réussite"


@admin.register(EvalCase)
class EvalCaseAdmin(admin.ModelAdmin):
    list_display  = ("name", "query_preview", "created_at")
    search_fields = ("name", "input_query")

    def query_preview(self, obj):
        return obj.input_query[:80]
    query_preview.short_description = "Question"


@admin.register(ToolCallLog)
class ToolCallLogAdmin(admin.ModelAdmin):
    list_display = ("tool_name", "success", "latency_ms", "iteration", "called_at")
    list_filter  = ("tool_name", "success")

    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False