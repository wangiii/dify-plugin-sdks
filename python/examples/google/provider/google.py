from typing import Any

from dify_plugin.tool.errors import ToolProviderCredentialValidationError
from dify_plugin.tool.tool import ToolProvider
from tools.google_search import GoogleSearchTool

class GoogleProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            for _ in GoogleSearchTool.from_credentials(credentials).invoke(
                tool_parameters={"query": "test", "result_type": "link"},
            ):
                pass
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
