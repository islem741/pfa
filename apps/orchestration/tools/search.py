"""
apps/orchestration/tools/search.py
Knowledge base search tool — simple text search using Django ORM.
"""
import logging
from apps.orchestration.tools.base import BaseTool, ToolResult
from apps.orchestration.tools.registry import register

logger = logging.getLogger(__name__)


class SearchKnowledgeBaseTool(BaseTool):
    name = "search_knowledge_base"
    description = (
        "Search the knowledge base for information relevant to the user's question. "
        "Use this when the question is factual and may have an answer in our documents."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up in the knowledge base.",
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (default: 3)",
                "default": 3,
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str, top_k: int = 3, **kwargs) -> ToolResult:
        try:
            from apps.orchestration.models import KnowledgeItem
            results = list(
                KnowledgeItem.objects
                .filter(content__icontains=query)
                .values("title", "content", "source")[:top_k]
            )
            logger.info("knowledge_search query=%s results=%d", query[:50], len(results))
            return ToolResult(success=True, data=results)
        except Exception as e:
            logger.error("knowledge_search_error: %s", e, exc_info=True)
            return ToolResult(success=False, error=str(e))


# Auto-register on import
register(SearchKnowledgeBaseTool())
