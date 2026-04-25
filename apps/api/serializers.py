"""
apps/api/serializers.py
Request and response serializers for the API layer.
"""
from rest_framework import serializers


class QueryRequestSerializer(serializers.Serializer):
    query      = serializers.CharField(
        min_length=1, max_length=4000,
        error_messages={"blank": "Query cannot be empty."},
    )
    session_id = serializers.UUIDField(required=False)
    workflow   = serializers.ChoiceField(
        choices=["default", "safe", "math"],
        default="default",
        required=False,
    )


class QueryResponseSerializer(serializers.Serializer):
    answer             = serializers.CharField()
    request_id         = serializers.CharField()
    session_id         = serializers.CharField()
    fallback_used      = serializers.BooleanField()
    truncation_applied = serializers.BooleanField()
    tool_calls_made    = serializers.ListField(child=serializers.CharField())
    cost_usd           = serializers.FloatField()
    latency_ms         = serializers.IntegerField()
    confidence         = serializers.FloatField(allow_null=True)
    provider_used      = serializers.CharField()
