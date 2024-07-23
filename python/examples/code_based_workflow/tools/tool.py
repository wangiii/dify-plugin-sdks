from collections.abc import Generator
from dify_plugin.tool.entities import ToolInvokeMessage
from dify_plugin.tool.tool import Tool


class ToolTool(Tool):
    def _invoke(self, tool_parameters: dict) -> Generator[ToolInvokeMessage, None, None]:
        return super()._invoke(tool_parameters)