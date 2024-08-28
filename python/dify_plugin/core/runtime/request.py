from binascii import hexlify, unhexlify
from collections.abc import Generator
import json
from typing import IO, Any, Literal, Optional, Type, overload
import uuid

import httpx
from pydantic import BaseModel
from yarl import URL

from dify_plugin.config.config import InstallMethod
from dify_plugin.core.entities.backwards_invocation.response_event import (
    BackwardsInvocationResponseEvent,
)
from dify_plugin.core.entities.model_runtime.llm import (
    LLMResult,
    LLMResultChunk,
)
from dify_plugin.core.entities.model_runtime.message import (
    PromptMessage,
    PromptMessageTool,
)
from dify_plugin.core.entities.model_runtime.model_config import (
    LLMModelConfig,
    ModerationModelConfig,
    RerankModelConfig,
    Speech2TextModelConfig,
    TTSModelConfig,
)
from dify_plugin.core.entities.model_runtime.moderation import ModerationResult
from dify_plugin.core.entities.model_runtime.rerank import RerankResult
from dify_plugin.core.entities.model_runtime.speech2text import (
    Speech2TextResult,
)
from dify_plugin.core.entities.model_runtime.text_embedding import (
    TextEmbeddingResult,
)
from dify_plugin.core.entities.model_runtime.tts import TTSResult
from dify_plugin.core.entities.plugin.dify import ToolProviderType
from dify_plugin.core.entities.plugin.invocation import InvokeType
from dify_plugin.core.entities.plugin.io import (
    PluginInStream,
    PluginInStreamBase,
    PluginInStreamEvent,
)
from dify_plugin.core.entities.plugin.workflow import (
    KnowledgeRetrievalNodeData,
    NodeResponse,
    ParameterExtractorNodeData,
    QuestionClassifierNodeData,
)
from dify_plugin.core.runtime.abstract.request import AbstractRequestInterface
from dify_plugin.core.runtime.session import Session
from dify_plugin.tool.entities import ToolInvokeMessage


class RequestInterface(AbstractRequestInterface):
    def __init__(
        self,
        session: Optional[Session] = None,
    ) -> None:
        self.session = session

    def _generate_backwards_request_id(self):
        return uuid.uuid4().hex

    def _backwards_invoke[T: BaseModel | dict](
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

    def _line_converter_wrapper[T: BaseModel | dict](
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

    def _http_backwards_invoke[T: BaseModel | dict](
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

    def _full_duplex_backwards_invoke[T: BaseModel | dict](
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

    def invoke_tool(
        self,
        provider_type: ToolProviderType,
        provider: str,
        tool_name: str,
        parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke tool
        """
        return self._backwards_invoke(
            InvokeType.Tool,
            ToolInvokeMessage,
            {
                "provider_type": provider_type.value,
                "provider": provider,
                "tool": tool_name,
                "tool_parameters": parameters,
            },
        )

    def invoke_builtin_tool(
        self, provider: str, tool_name: str, parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke builtin tool
        """
        return self.invoke_tool(
            ToolProviderType.BUILT_IN, provider, tool_name, parameters
        )

    def invoke_workflow_tool(
        self, provider: str, tool_name: str, parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke workflow tool
        """
        return self.invoke_tool(
            ToolProviderType.WORKFLOW, provider, tool_name, parameters
        )

    def invoke_api_tool(
        self, provider: str, tool_name: str, parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke api tool
        """
        return self.invoke_tool(ToolProviderType.API, provider, tool_name, parameters)

    @overload
    def invoke_llm(
        self,
        model_config: LLMModelConfig,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: Literal[True] = True,
    ) -> Generator[LLMResultChunk, None, None]: ...

    @overload
    def invoke_llm(
        self,
        model_config: LLMModelConfig,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: Literal[False] = False,
    ) -> LLMResult: ...

    def invoke_llm(
        self,
        model_config: LLMModelConfig,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: bool = True,
    ) -> Generator[LLMResultChunk, None, None] | LLMResult:
        """
        Invoke llm
        """
        data = {
            **model_config.model_dump(),
            "prompt_messages": [message.model_dump() for message in prompt_messages],
            "tools": [tool.model_dump() for tool in tools] if tools else None,
            "stop": stop,
            "stream": stream,
        }
        if stream:
            return self._backwards_invoke(
                InvokeType.LLM,
                LLMResultChunk,
                data,
            )

        for data in self._backwards_invoke(
            InvokeType.LLM,
            LLMResult,
            data,
        ):
            return data

        raise Exception("No response from llm")

    def invoke_text_embedding(
        self, model_config: TextEmbeddingResult, texts: list[str]
    ) -> TextEmbeddingResult:
        """
        Invoke text embedding
        """
        for data in self._backwards_invoke(
            InvokeType.TextEmbedding,
            TextEmbeddingResult,
            {
                **model_config.model_dump(),
                "texts": texts,
            },
        ):
            return data

        raise Exception("No response from text embedding")

    def invoke_rerank(
        self, model_config: RerankModelConfig, docs: list[str], query: str
    ) -> RerankResult:
        """
        Invoke rerank
        """
        for data in self._backwards_invoke(
            InvokeType.Rerank,
            RerankResult,
            {
                **model_config.model_dump(),
                "docs": docs,
                "query": query,
            },
        ):
            return data

        raise Exception("No response from rerank")

    def invoke_speech2text(
        self, model_config: Speech2TextModelConfig, file: IO[bytes]
    ) -> str:
        """
        Invoke speech2text
        """
        for data in self._backwards_invoke(
            InvokeType.Speech2Text,
            Speech2TextResult,
            {
                **model_config.model_dump(),
                "file": hexlify(file.read()),
            },
        ):
            return data.result

        raise Exception("No response from speech2text")

    def invoke_moderation(self, model_config: ModerationModelConfig, text: str) -> bool:
        """
        Invoke moderation
        """
        for data in self._backwards_invoke(
            InvokeType.Moderation,
            ModerationResult,
            {
                **model_config.model_dump(),
                "text": text,
            },
        ):
            return data.result

        raise Exception("No response from moderation")

    def invoke_tts(
        self, model_config: TTSModelConfig, content_text: str
    ) -> Generator[bytes, None, None]:
        """
        Invoke tts
        """
        for data in self._backwards_invoke(
            InvokeType.TTS,
            TTSResult,
            {
                **model_config.model_dump(),
                "content_text": content_text,
            },
        ):
            yield unhexlify(data.result)

    @overload
    def invoke_chat(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["streaming"],
        conversation_id: str,
        files: list,
    ) -> Generator[dict, None, None]: ...

    @overload
    def invoke_chat(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["blocking"],
        conversation_id: str,
        files: list,
    ) -> dict: ...

    def invoke_chat(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["streaming", "blocking"],
        conversation_id: str,
        files: list,
    ) -> Generator[dict, None, None] | dict:
        """
        Invoke chat app
        """
        response = self._backwards_invoke(
            InvokeType.App,
            dict,
            {
                "app_id": app_id,
                "inputs": inputs,
                "response_mode": response_mode,
                "conversation_id": conversation_id,
                "files": files,
            },
        )

        if response_mode == "streaming":
            return response

        for data in response:
            return data

        raise Exception("No response from chat")

    @overload
    def invoke_completion(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["streaming"],
        files: list,
    ) -> Generator[dict, None, None]: ...

    @overload
    def invoke_completion(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["blocking"],
        files: list,
    ) -> dict: ...

    def invoke_completion(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["streaming", "blocking"],
        files: list,
    ) -> Generator[dict, None, None] | dict:
        """
        Invoke completion app
        """
        response = self._backwards_invoke(
            InvokeType.App,
            dict,
            {
                "app_id": app_id,
                "inputs": inputs,
                "response_mode": response_mode,
                "files": files,
            },
        )

        if response_mode == "streaming":
            return response

        for data in response:
            return data

        raise Exception("No response from completion")

    @overload
    def invoke_workflow(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["streaming"],
        files: list,
    ) -> Generator[dict, None, None]: ...

    @overload
    def invoke_workflow(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["blocking"],
        files: list,
    ) -> dict: ...

    def invoke_workflow(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["streaming", "blocking"],
        files: list,
    ) -> Generator[dict, None, None] | dict:
        """
        Invoke workflow app
        """
        response = self._backwards_invoke(
            InvokeType.App,
            dict,
            {
                "app_id": app_id,
                "inputs": inputs,
                "response_mode": response_mode,
                "files": files,
            },
        )

        if response_mode == "streaming":
            return response

        for data in response:
            return data

        raise Exception("No response from workflow")

    def invoke_question_classifier(
        self, node_data: QuestionClassifierNodeData, inputs: dict
    ) -> NodeResponse:
        """
        Invoke question classifier
        """
        return super().invoke_question_classifier(node_data, inputs)

    def invoke_parameter_extractor(
        self, node_data: ParameterExtractorNodeData, inputs: dict
    ) -> NodeResponse:
        """
        Invoke parameter extractor
        """
        return super().invoke_parameter_extractor(node_data, inputs)

    def invoke_knowledge_retrieval(
        self, node_data: KnowledgeRetrievalNodeData, inputs: dict
    ) -> NodeResponse:
        """
        Invoke knowledge retrieval
        """
        return super().invoke_knowledge_retrieval(node_data, inputs)

    def storage_set(self, key: str, val: bytes):
        """
        set a value into persistence storage.
        """
        for data in self._backwards_invoke(
            InvokeType.STORAGE,
            dict,
            {"opt": "set", "key": key, "value": hexlify(val).decode()},
        ):
            if data["data"] == "ok":
                return

            raise Exception("unexpected data")

        Exception("no data found")

    def storage_get(self, key: str):
        for data in self._backwards_invoke(
            InvokeType.STORAGE,
            dict,
            {
                "opt": "get",
                "key": key,
            },
        ):
            return unhexlify(data["data"])

        raise Exception("no data found")

    def storage_del(self, key: str):
        for data in self._backwards_invoke(
            InvokeType.STORAGE,
            dict,
            {
                "opt": "del",
                "key": key,
            },
        ):
            if data["data"] == "ok":
                return

            raise Exception("unexpected data")

        raise Exception("no data found")
