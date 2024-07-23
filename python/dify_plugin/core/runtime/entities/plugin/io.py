from enum import Enum
from pydantic import BaseModel


class PluginInStream(BaseModel):
    class Event(Enum):
        Request = 'request'
        BackwardInvocationResponse = 'backward_invocation_response'
        BackwardInvocationEnd = 'backward_invocation_end'
        BackwardInvocationError = 'backward_invocation_error'

    session_id: str
    event: Event
    data: dict
