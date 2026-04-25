"""
apps/api/views.py
REST API endpoints — entry point for all user queries.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.api.serializers import QueryRequestSerializer, QueryResponseSerializer
from apps.orchestration.runner import WorkflowRunner, InputBlockedError

logger = logging.getLogger(__name__)


class QueryView(APIView):
    """
    POST /api/v1/query/
    Main query endpoint. Runs the full LLM pipeline and returns a structured answer.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = QueryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        query      = serializer.validated_data["query"]
        session_id = str(serializer.validated_data.get("session_id", ""))
        workflow   = serializer.validated_data.get("workflow", "default")

        try:
            runner = WorkflowRunner(workflow_name=workflow)
            result = runner.run(query=query, user=request.user, session_id=session_id)
        except InputBlockedError as e:
            return Response(
                {"detail": e.reason, "blocked_by": e.guard_name},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:
            logger.error("query_view_error: %s", e, exc_info=True)
            return Response(
                {"detail": "Internal server error. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        response_data = QueryResponseSerializer(result).data
        return Response(response_data, status=status.HTTP_200_OK)


class SessionListView(APIView):
    """
    GET /api/v1/sessions/
    List recent LLM requests for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.instrumentation.models import LLMRequestLog
        logs = (
            LLMRequestLog.objects
            .filter(user=request.user)
            .order_by("-created_at")
            .values("id", "status", "raw_query", "provider",
                    "cost_usd", "latency_ms", "created_at")[:20]
        )
        return Response(list(logs))
