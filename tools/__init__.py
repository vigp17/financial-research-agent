from .market_tools import TOOL_SCHEMAS as MARKET_SCHEMAS, TOOL_HANDLERS as MARKET_HANDLERS
from .regime_tool import REGIME_TOOL_SCHEMA, detect_market_regime
from .news_tool import NEWS_TOOL_SCHEMA, get_stock_news

import json

# Combine all tool schemas
TOOL_SCHEMAS = MARKET_SCHEMAS + [REGIME_TOOL_SCHEMA, NEWS_TOOL_SCHEMA]

# Combine all tool handlers
TOOL_HANDLERS = {
    **MARKET_HANDLERS,
    "detect_market_regime": detect_market_regime,
    "get_stock_news": get_stock_news,
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name with the given inputs."""
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    result = handler(**tool_input)
    return json.dumps(result, indent=2, default=str)