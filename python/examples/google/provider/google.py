from typing import Any

from dify_plugin.tool.errors import ToolProviderCredentialValidationError
from dify_plugin.tool.tool import ToolProvider
from tools.google_search import GoogleSearchTool
from plugin import plugin

@plugin.register_tool_provider('google.yaml')
class GoogleProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            GoogleSearchTool.from_credentials(credentials).invoke(
                tool_parameters={"query": "test", "result_type": "link"},
            )
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
