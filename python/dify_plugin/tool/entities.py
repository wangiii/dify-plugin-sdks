from pydantic import BaseModel
from enum import Enum


class ToolConfiguration(BaseModel):
    name: str


class ToolProviderConfiguration(BaseModel):
    name: str


class ToolRuntime(BaseModel):
    credentials: dict[str, str]
    user_id: str


class ToolInvokeMessage(BaseModel):
    class TextMessage(BaseModel):
        text: str

        def to_dict(self):
            return {"text": self.text}

    class JsonMessage(BaseModel):
        json_object: dict

        def to_dict(self):
            return {"json_object": self.json_object}

    class MessageType(Enum):
        TEXT = "text"
        FILE = "file"
        BLOB = "blob"
        JSON = "json"

    type: MessageType
    message: TextMessage | JsonMessage

    def to_dict(self):
        return {"type": self.type.value, "message": self.message.to_dict()}
