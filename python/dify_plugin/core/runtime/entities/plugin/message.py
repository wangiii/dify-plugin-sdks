from enum import Enum

from pydantic import BaseModel


class SessionMessage(BaseModel):
    class Type(Enum):
        STREAM = "stream"
        INVOKE = "invoke"
        END = "end"
        ERROR = "error"

    type: Type
    data: dict

    def to_dict(self):
        return {
            'type': self.type.value,
            'data': self.data
        }
