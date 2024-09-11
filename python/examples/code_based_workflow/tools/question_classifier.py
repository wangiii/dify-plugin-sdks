from collections.abc import Generator
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin import Tool


class QuestionClassifierTool(Tool):
    def invoke(self, tool_parameters: dict) -> Generator[ToolInvokeMessage, None, None]:
        return super()._invoke(tool_parameters)