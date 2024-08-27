from enum import Enum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dify_plugin.core.server.__base.request_reader import RequestReader

from dify_plugin.core.server.__base.response_writer import ResponseWriter


class PluginInStreamEvent(Enum):
    Request = "request"
    BackwardInvocationResponse = "backwards_response"

    @classmethod
    def value_of(cls, v: str):
        for e in cls:
            if e.value == v:
                return e
        raise ValueError(f"Invalid value for PluginInStream.Event: {v}")


class PluginInStreamBase:
    def __init__(
        self,
        session_id: str,
        event: PluginInStreamEvent,
        data: dict,
    ) -> None:
        self.session_id = session_id
        self.event = event
        self.data = data


class PluginInStream(PluginInStreamBase):
    def __init__(
        self,
        session_id: str,
        event: PluginInStreamEvent,
        data: dict,
        reader: "RequestReader",
        writer: "ResponseWriter",
    ):
        self.reader = reader
        self.writer = writer
        super().__init__(session_id, event, data)
