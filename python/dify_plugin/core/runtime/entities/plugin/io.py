from enum import Enum
from pydantic import BaseModel


class PluginInStream(BaseModel):
    class Event(Enum):
        Request = 'request'
        BackwardInvocationResponse = 'backwards_response'

    session_id: str
    event: Event
    data: dict
