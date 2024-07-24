from typing import Optional

from pydantic import BaseModel

from dify_plugin.core.runtime.entities.plugin.message import SessionMessage
from dify_plugin.stream.stream_writer import Event, PluginOutputStreamWriter, StreamOutputMessage


class PluginOutputStream:
    writer: Optional[PluginOutputStreamWriter] = None

    @classmethod
    def init(cls, writer: PluginOutputStreamWriter):
        cls.writer = writer

    @classmethod
    def write(cls, data: str):
        if cls.writer:
            cls.writer.write(data)
        else:
            raise Exception('Output stream writer not initialized')

    @classmethod
    def put(cls, event: Event, session_id: Optional[str] = None, data: Optional[dict | BaseModel] = None):
        """
        serialize the output to the daemon
        """
        if isinstance(data, BaseModel):
            data = data.model_dump()
        
        cls.write(StreamOutputMessage(
            event=event,
            session_id=session_id,
            data=data
        ).model_dump_json())
        cls.write('\n\n')

    @classmethod
    def error(cls, session_id: Optional[str] = None, data: Optional[dict | BaseModel] = None):
        return cls.put(Event.ERROR, session_id, data)
    
    @classmethod
    def log(cls, data: Optional[dict] = None):
        return cls.put(Event.LOG, None, data)
    
    @classmethod
    def heartbeat(cls):
        return cls.put(Event.HEARTBEAT, None, {})
    
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
    def stream_error_object(cls, data: dict | BaseModel) -> SessionMessage:
        if isinstance(data, BaseModel):
            data = data.model_dump()

        return SessionMessage(
            type=SessionMessage.Type.ERROR,
            data=data
        )
    
    @classmethod
    def stream_invoke_object(cls, data: dict | BaseModel) -> SessionMessage:
        if isinstance(data, BaseModel):
            data = data.model_dump()

        return SessionMessage(
            type=SessionMessage.Type.INVOKE,
            data=data
        ) 
