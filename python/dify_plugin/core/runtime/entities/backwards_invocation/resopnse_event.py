from enum import Enum
from typing import Optional
from pydantic import BaseModel

class BackwardsInvocationResponseEvent(BaseModel):
    class Event(Enum):
        response = "response"
        Error = "error"
        End = "end"

    backwards_request_id: str
    event: Event
    message: str
    data: Optional[dict]