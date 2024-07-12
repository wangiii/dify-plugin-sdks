from enum import Enum
import sys
from typing import Optional

from pydantic import BaseModel

from ..core.runtime.entities.message import SessionMessage

class Event(Enum):
        LOG = 'log'
        ERROR = 'error'
        SESSION = 'session'

class StreamOutputMessage(BaseModel):
    event: Event
    session_id: Optional[str]
    data: Optional[dict | BaseModel]

class PluginOutputStream:
    @classmethod
    def put(cls, event: Event, session_id: Optional[str] = None, data: Optional[dict | BaseModel] = None):
        """
        serialize the output to the daemon
        """
        if isinstance(data, BaseModel):
            data = data.model_dump()
        
        sys.stdout.write(StreamOutputMessage(
            event=event,
            session_id=session_id,
            data=data
        ).model_dump_json())
        
        sys.stdout.write('\n\n')
        sys.stdout.flush()

    @classmethod
    def error(cls, session_id: Optional[str] = None, data: Optional[dict | BaseModel] = None):
        return cls.put(Event.ERROR, session_id, data)
    
    @classmethod
    def log(cls, data: Optional[dict] = None):
        return cls.put(Event.LOG, None, data)
    
    @classmethod
    def session_message(cls, session_id: Optional[str] = None, data: Optional[dict | BaseModel] = None):
        return cls.put(Event.SESSION, 
                       session_id, 
                       data)
    
    @classmethod
    def stream_object(cls, data: dict | BaseModel) -> SessionMessage:
        if isinstance(data, BaseModel):
            data = data.model_dump()

        return SessionMessage(
            type=SessionMessage.Type.STREAM,
            data=data
        )
    
    @classmethod
    def stream_end_object(cls) -> SessionMessage:
        return SessionMessage(
            type=SessionMessage.Type.END,
            data={}
        )
    
    @classmethod
    def stream_invoke_object(cls, data: dict | BaseModel) -> SessionMessage:
        if isinstance(data, BaseModel):
            data = data.model_dump()

        return SessionMessage(
            type=SessionMessage.Type.INVOKE,
            data=data
        ) 
