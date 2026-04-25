"""
apps/orchestration/tools/fetch.py
External data fetcher — uses mock data for academic demo.
"""
from apps.orchestration.tools.base import BaseTool, ToolResult
from apps.orchestration.tools.registry import register


class FetchExternalDataTool(BaseTool):
    name = "fetch_external_data"
    description = (
        "Fetch external data for a given topic (weather, news headlines, etc.). "
        "Use when the user asks about current events or real-world data."
    )
    parameters = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Topic to fetch data about",
            },
            "source": {
                "type": "string",
                "enum": ["weather", "news"],
                "default": "news",
            },
        },
        "required": ["topic"],
    }

    MOCK_DATA = {
        "weather": lambda topic: {
            "location": topic,
            "temp_c": 22,
            "condition": "Sunny",
            "humidity": "45%",
        },
        "news": lambda topic: {
            "headlines": [
                f"Breaking: {topic} — major update today",
                f"Analysis: what {topic} means for the industry",
            ]
        },
    }

    def execute(self, topic: str, source: str = "news", **kwargs) -> ToolResult:
        generator = self.MOCK_DATA.get(source)
        if not generator:
            return ToolResult(success=False, error=f"Unknown source: {source}")
        return ToolResult(success=True, data=generator(topic))


# Auto-register on import
register(FetchExternalDataTool())
