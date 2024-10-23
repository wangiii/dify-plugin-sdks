from collections.abc import Generator
import io
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.file.file import File
from PIL import Image
from rembg import remove

class KawaiiFilterTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        file: File | None = tool_parameters.get("image")
        if file is None:
            raise ValueError("image is required")
        
        blob = file.blob

        img = Image.open(io.BytesIO(blob))
        img = remove(img)

        # get the bytes of the image
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes = img_bytes.getvalue()
        
        yield self.create_blob_message(img_bytes, {
            "mime_type": "image/png"
        })
