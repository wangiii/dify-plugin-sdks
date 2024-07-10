from enum import Enum
from pydantic import BaseModel


class ToolInvokeMessage(BaseModel):
    class TextMessage(BaseModel):
        text: str

        def to_dict(self):
            return {
                'text': self.text
            }

    class MessageType(Enum):
        TEXT = "text"
        FILE = "file"
        BLOB = "blob"
        JSON = "json"

    type: MessageType
    message: TextMessage

    def to_dict(self):
        return {
            'type': self.type.value,
            'message': self.message.to_dict()
        }

class ToolInvokeTextMessage(ToolInvokeMessage):
    type: ToolInvokeMessage.MessageType = ToolInvokeMessage.MessageType.TEXT


