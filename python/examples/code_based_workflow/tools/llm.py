from collections.abc import Generator
from typing import Any

from dify_plugin.tool.entities import ToolInvokeMessage
from dify_plugin.tool.tool import Tool

class LLMTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        return self.invoke_builtin_tool(
            provider="dify",
            tool_name="llm",
            parameters=tool_parameters,
        )