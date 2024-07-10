from enum import Enum
import json
from typing import Optional

from ..core.runtime.entities.message import InvokeMessage, SessionMessage

class PluginOutputStream:
    class Event(Enum):
        LOG = 'log'
        ERROR = 'error'
        SESSION = 'session'

    @classmethod
    def put(cls, event: Event, session_id: Optional[str] = None, data: Optional[dict] = None) -> str:
        """
        serialize the output to the daemon
        """
        print(json.dumps({
            'event': event.value,
            'session_id': session_id,
            'data': data
        }))
    
    @classmethod
    def error(cls, session_id: Optional[str] = None, data: Optional[dict] = None) -> str:
        return cls.put(cls.Event.ERROR, session_id, data)
    
    @classmethod
    def log(cls, data: Optional[dict] = None) -> str:
        return cls.put(cls.Event.LOG, None, data)
    
    @classmethod
    def session_message(cls, session_id: Optional[str] = None, data: Optional[dict] = None) -> str:
        return cls.put(cls.Event.SESSION, 
                       session_id, 
                       data)
    
    @classmethod
    def stream_object(cls, data: dict) -> SessionMessage:
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
    def stream_invoke_object(cls, data: dict) -> InvokeMessage:
        return SessionMessage(
            type=SessionMessage.Type.INVOKE,
            data=data
        ) 
