from collections.abc import Generator
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin import Tool


class ToolTool(Tool):
    def invoke(self, tool_parameters: dict) -> Generator[ToolInvokeMessage, None, None]:
        return super().invoke(tool_parameters)