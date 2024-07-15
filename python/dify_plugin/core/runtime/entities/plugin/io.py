from enum import Enum
from pydantic import BaseModel


class PluginInStream(BaseModel):
    """
    testcase:
    - input: {"session_id": "session_id", "event": "request", "data": {"key": "value"}}
    - input: {"session_id": "session_id", "event": "invoke_response", "data": {"key": "value"}}

    - invoke_tool: {"session_id": "session_id", "event": "request", "data": {"type": "tool", "user_id": "user_id", "action": "invoke", "provider": "basic_math", "tool": "add", "credentials": {"key": "value"}, "parameters": {"a": 1, "b":2}}}
    """

    class Event(Enum):
        Request = 'request'
        InvokeResponse = 'invoke_response'

    session_id: str
    event: Event
    data: dict
