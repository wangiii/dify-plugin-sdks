from collections.abc import Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class ToolTool(Tool):
    def _invoke(
        self, tool_parameters: dict
    ) -> Generator[ToolInvokeMessage, None, None]:
        return super()._invoke(tool_parameters)
