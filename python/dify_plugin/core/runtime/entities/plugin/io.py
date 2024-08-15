from enum import Enum
from typing import Callable, Optional
from pydantic import BaseModel, PrivateAttr

class PluginInStream(BaseModel):
    class Event(Enum):
        Request = "request"
        BackwardInvocationResponse = "backwards_response"

    session_id: str
    event: Event
    data: dict

    _executor_hijack: Optional[Callable[[Callable[[], None]], None]] = PrivateAttr()
    """
    when facing http request, we need to bind a flask context to the request
    _executor_hijack is used to wrap the executor to hijack the context
    """

    def set_executor_hijack(self, hijack: Callable[[Callable[[], None]], None]):
        """
        set the hijack function
        """
        self._executor_hijack = hijack

    def get_executor_hijack(self) -> Optional[Callable[[Callable[[], None]], None]]:
        """
        get the hijack function
        """
        return self._executor_hijack
