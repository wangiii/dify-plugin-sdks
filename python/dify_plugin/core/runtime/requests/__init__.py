from abc import ABC
from collections.abc import Generator
import json
from typing import TYPE_CHECKING, Generic, Optional, Type, TypeVar, Union
import uuid

import httpx
from pydantic import BaseModel
from yarl import URL

from dify_plugin.config.config import InstallMethod
from dify_plugin.core.entities.backwards_invocation.response_event import (
    BackwardsInvocationResponseEvent,
)
from dify_plugin.core.entities.plugin.invocation import InvokeType
from dify_plugin.core.entities.plugin.io import (
    PluginInStream,
    PluginInStreamBase,
    PluginInStreamEvent,
)

if TYPE_CHECKING:
    from dify_plugin.core.runtime import Session


T = TypeVar('T', bound=Union[BaseModel, dict, str])

class DifyRequest(Generic[T], ABC):
    def __init__(
        self,
        session: Optional["Session"] = None,
    ) -> None:
        self.session = session

    def _generate_backwards_request_id(self):
        return uuid.uuid4().hex

    def _backwards_invoke(
        self,
        type: InvokeType,
        data_type: Type[T],
        data: dict,
    ) -> Generator[T, None, None]:
        """
        backwards invoke dify depends on current runtime type
        """
        backwards_request_id = self._generate_backwards_request_id()

        if not self.session:
            raise Exception("current tool runtime does not support backwards invoke")
        if self.session.install_method in [InstallMethod.Local, InstallMethod.Remote]:
            return self._full_duplex_backwards_invoke(
                backwards_request_id, type, data_type, data
            )
        return self._http_backwards_invoke(backwards_request_id, type, data_type, data)

    def _line_converter_wrapper(
        self,
        generator: Generator[PluginInStreamBase | None, None, None],
        data_type: Type[T],
    ) -> Generator[T, None, None]:
        """
        convert string into type T
        """
        empty_response_count = 0

        for chunk in generator:
            """
            accept response from input stream and wait for at most 60 seconds
            """
            if chunk is None:
                empty_response_count += 1
                # if no response for 250 seconds, break
                if empty_response_count >= 250:
                    raise Exception("invocation exited without response")
                continue

            event = BackwardsInvocationResponseEvent(**chunk.data)
            if event.event == BackwardsInvocationResponseEvent.Event.End:
                break

            if event.event == BackwardsInvocationResponseEvent.Event.Error:
                raise Exception(event.message)

            if event.data is None:
                break

            empty_response_count = 0
            try:
                if data_type is dict:
                    event.data
                else:
                    yield data_type(**event.data)
            except Exception as e:
                raise Exception(f"Failed to parse response: {str(e)}")

    def _http_backwards_invoke(
        self,
        backwards_request_id: str,
        type: InvokeType,
        data_type: Type[T],
        data: dict,
    ) -> Generator[T, None, None]:
        """
        http backwards invoke
        """
        if not self.session or not self.session.dify_plugin_daemon_url:
            raise Exception("current tool runtime does not support backwards invoke")

        url = (
            URL(self.session.dify_plugin_daemon_url)
            / "backwards-invocation"
            / "transaction"
        )
        headers = {
            "Dify-Plugin-Session-ID": self.session.session_id,
        }

        payload = self.session.writer.session_message_text(
            session_id=self.session.session_id,
            data=self.session.writer.stream_invoke_object(
                data={
                    "type": type.value,
                    "backwards_request_id": backwards_request_id,
                    "request": data,
                }
            ),
        )

        with httpx.Client() as client:
            with client.stream(
                method="POST",
                url=str(url),
                headers=headers,
                content=payload,
            ) as response:

                def generator():
                    for line in response.iter_lines():
                        data = json.loads(line)
                        yield PluginInStreamBase(
                            session_id=data["session_id"],
                            event=PluginInStreamEvent.value_of(data["event"]),
                            data=data["data"],
                        )

                return self._line_converter_wrapper(generator(), data_type)

    def _full_duplex_backwards_invoke(
        self,
        backwards_request_id: str,
        type: InvokeType,
        data_type: Type[T],
        data: dict,
    ) -> Generator[T, None, None]:
        if not self.session:
            raise Exception("current tool runtime does not support backwards invoke")

        self.session.writer.session_message(
            session_id=self.session.session_id,
            data=self.session.writer.stream_invoke_object(
                data={
                    "type": type.value,
                    "backwards_request_id": backwards_request_id,
                    "request": data,
                }
            ),
        )

        def filter(data: PluginInStream) -> bool:
            return (
                data.event == PluginInStreamEvent.BackwardInvocationResponse
                and data.data.get("backwards_request_id") == backwards_request_id
            )

        with self.session.reader.read(filter) as reader:
            return self._line_converter_wrapper(
                reader.read(timeout_for_round=1), data_type
            )
