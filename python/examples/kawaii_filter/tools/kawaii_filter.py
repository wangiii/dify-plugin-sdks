from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.file.file import File

class KawaiiFilterTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        file: File | None = tool_parameters.get("image")
        if file is None:
            raise ValueError("image is required")
        
        blob = file.blob
        
        yield self.create_blob_message(blob, {
            "mime_type": "image/png"
        })
