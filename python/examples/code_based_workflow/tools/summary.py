from collections.abc import Generator

from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.interfaces.tool import Tool


class Summary(Tool):
    def _invoke(self, tool_parameters: dict) -> Generator[ToolInvokeMessage, None, None]:
        response = self.session.model.summary.invoke(
            text="Hello, world!",
            instruction="Summarize the text",
            min_summarize_length=1,
        )

        yield self.create_json_message(
            {
                "data": response,
            }
        )
