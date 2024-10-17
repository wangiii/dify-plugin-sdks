from enum import Enum
from typing import Optional

from pydantic import BaseModel

from ..config.config import InstallMethod
from concurrent.futures import ThreadPoolExecutor

from abc import ABC
from collections.abc import Generator
import json
from typing import Generic, Type, TypeVar, Union
import uuid

import httpx
from yarl import URL

from ..core.server.__base.request_reader import RequestReader
from ..core.server.__base.response_writer import ResponseWriter
from ..core.server.tcp.request_reader import TCPReaderWriter
from ..core.entities.invocation import InvokeType
from ..core.entities.plugin.io import (
    PluginInStream,
    PluginInStreamBase,
    PluginInStreamEvent,
)


#################################################
# Session
#################################################


class ModelInvocations:
    def __init__(self, session: "Session") -> None:
        from ..invocations.model.llm import LLMInvocation, SummaryInvocation
        from ..invocations.model.moderation import ModerationInvocation
        from ..invocations.model.rerank import RerankInvocation
        from ..invocations.model.speech2text import Speech2TextInvocation
        from ..invocations.model.text_embedding import TextEmbeddingInvocation
        from ..invocations.model.tts import TTSInvocation

        self.llm = LLMInvocation(session)
        self.text_embedding = TextEmbeddingInvocation(session)
        self.rerank = RerankInvocation(session)
        self.speech2text = Speech2TextInvocation(session)
        self.tts = TTSInvocation(session)
        self.moderation = ModerationInvocation(session)
        self.summary = SummaryInvocation(session)


class AppInvocations:
    def __init__(self, session: "Session"):
        from ..invocations.app.chat import ChatAppInvocation
        from ..invocations.app.completion import CompletionAppInvocation
        from ..invocations.app.workflow import WorkflowAppInvocation

        self.chat = ChatAppInvocation(session)
        self.completion = CompletionAppInvocation(session)
        self.workflow = WorkflowAppInvocation(session)


class WorkflowNodeInvocations:
    def __init__(self, session: "Session"):
        from ..invocations.workflow_node.parameter_extractor import (
            ParameterExtractorNodeInvocation,
        )
        from ..invocations.workflow_node.question_classifier import (
            QuestionClassifierNodeInvocation,
        )

        self.question_classifier = QuestionClassifierNodeInvocation(session)
        self.parameter_extractor = ParameterExtractorNodeInvocation(session)


class Session:
    # class variable to store all sessions
    _session_pool: set["Session"] = set()

    def __init__(
        self,
        session_id: str,
        executor: ThreadPoolExecutor,
        reader: RequestReader,
        writer: ResponseWriter,
        install_method: Optional[InstallMethod] = None,
        dify_plugin_daemon_url: Optional[str] = None,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None,
        app_id: Optional[str] = None,
        endpoint_id: Optional[str] = None,
    ) -> None:
        # current session id
        self.session_id: str = session_id

        # add current session to session pool
        self._session_pool.add(self)

        # thread pool executor
        self._executor: ThreadPoolExecutor = executor

        # reader and writer
        self.reader: RequestReader = reader
        self.writer: ResponseWriter = writer

        # conversation id
        self.conversation_id: Optional[str] = conversation_id

        # message id
        self.message_id: Optional[str] = message_id

        # app id
        self.app_id: Optional[str] = app_id

        # endpoint id
        self.endpoint_id: Optional[str] = endpoint_id

        # install method
        self.install_method: Optional[InstallMethod] = install_method

        # dify plugin daemon url
        self.dify_plugin_daemon_url: Optional[str] = dify_plugin_daemon_url

        # register invocations
        self._register_invocations()

    def _register_invocations(self) -> None:
        from ..invocations.tool import ToolInvocation
        from ..invocations.storage import StorageInvocation

        self.model = ModelInvocations(self)
        self.tool = ToolInvocation(self)
        self.app = AppInvocations(self)
        self.workflow_node = WorkflowNodeInvocations(self)
        self.storage = StorageInvocation(self)

    @classmethod
    def empty_session(cls) -> "Session":
        return cls(
            session_id="",
            executor=ThreadPoolExecutor(),
            reader=TCPReaderWriter(host="", port=0, key=""),
            writer=TCPReaderWriter(host="", port=0, key=""),
            install_method=None,
            dify_plugin_daemon_url=None,
        )

    def __del__(self) -> None:
        self._session_pool.remove(self)

    def close(self) -> None:
        self._session_pool.remove(self)

    @classmethod
    def get_session(cls, session_id: str) -> "Session | None":
        for session in cls._session_pool:
            if session.session_id == session_id:
                return session
        return None


#################################################
# Backwards Invocation Request
#################################################


class BackwardsInvocationResponseEvent(BaseModel):
    class Event(Enum):
        response = "response"
        Error = "error"
        End = "end"

    backwards_request_id: str
    event: Event
    message: str
    data: Optional[dict]


T = TypeVar("T", bound=Union[BaseModel, dict, str])


class BackwardsInvocation(Generic[T], ABC):
    def __init__(
        self,
        session: Optional[Session] = None,
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
                        if not line:
                            continue

                        data = json.loads(line)
                        yield PluginInStreamBase(
                            session_id=data["session_id"],
                            event=PluginInStreamEvent.value_of(data["event"]),
                            data=data["data"],
                        )

                yield from self._line_converter_wrapper(generator(), data_type)

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
            yield from self._line_converter_wrapper(
                reader.read(timeout_for_round=1), data_type
            )
