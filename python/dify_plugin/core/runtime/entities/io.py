from enum import Enum
from pydantic import BaseModel


class PluginInStream(BaseModel):
    """
    testcase:
    - input: {"session_id": "session_id", "event": "request", "data": {"key": "value"}}
    - input: {"session_id": "session_id", "event": "invoke_response", "data": {"key": "value"}}
    """

    class Event(Enum):
        Request = 'request'
        InvokeResponse = 'invoke_response'

    session_id: str
    event: Event
    data: dict
