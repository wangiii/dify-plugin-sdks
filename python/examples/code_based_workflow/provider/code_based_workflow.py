from typing import Any

from dify_plugin.tool.tool import ToolProvider

class CodeBasedWorkflowProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        pass
