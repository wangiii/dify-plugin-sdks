from collections.abc import Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.file.file import File


class TransformImageTool(Tool):
    def _invoke(self, tool_parameters: dict) -> Generator[ToolInvokeMessage, None, None]:
        for image in tool_parameters["image"]:
            assert isinstance(image, File)
            yield self.create_json_message(
                {
                    "mime_type": image.mime_type,
                    "type": image.type,
                    "length": len(image.blob),
                }
            )
            yield self.create_blob_message(image.blob, {"mime_type": image.mime_type})
