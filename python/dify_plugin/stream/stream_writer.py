from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Event(Enum):
    LOG = 'log'
    ERROR = 'error'
    SESSION = 'session'
    HEARTBEAT = 'heartbeat'

class StreamOutputMessage(BaseModel):
    event: Event
    session_id: Optional[str]
    data: Optional[dict | BaseModel]

class PluginOutputStreamWriter(ABC):
    @abstractmethod
    def write(self, data: str):
        """
        write data to the output stream
        """
