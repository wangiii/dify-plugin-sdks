from binascii import hexlify, unhexlify
from collections.abc import Generator
from typing import IO, Any, Literal, Optional, Type, overload
import uuid

from pydantic import BaseModel

from dify_plugin.core.runtime.abstract.request import AbstractRequestInterface
from dify_plugin.core.runtime.entities.backwards_invocation.response_event import (
    BackwardsInvocationResponseEvent,
)
from dify_plugin.core.runtime.entities.model_runtime.llm import (
    LLMResult,
    LLMResultChunk,
)
from dify_plugin.core.runtime.entities.model_runtime.message import (
    PromptMessage,
    PromptMessageTool,
)
from dify_plugin.core.runtime.entities.model_runtime.model_config import (
    LLMModelConfig,
    ModerationModelConfig,
    RerankModelConfig,
    Speech2TextModelConfig,
    TTSModelConfig,
)
from dify_plugin.core.runtime.entities.model_runtime.moderation import ModerationResult
from dify_plugin.core.runtime.entities.model_runtime.rerank import RerankResult
from dify_plugin.core.runtime.entities.model_runtime.speech2text import (
    Speech2TextResult,
)
from dify_plugin.core.runtime.entities.model_runtime.text_embedding import (
    TextEmbeddingResult,
)
from dify_plugin.core.runtime.entities.model_runtime.tts import TTSResult
from dify_plugin.core.runtime.entities.plugin.dify import ToolProviderType
from dify_plugin.core.runtime.entities.plugin.invocation import InvokeType
from dify_plugin.core.runtime.entities.plugin.io import PluginInStream
from dify_plugin.core.runtime.entities.plugin.workflow import (
    KnowledgeRetrievalNodeData,
    NodeResponse,
    ParameterExtractorNodeData,
    QuestionClassifierNodeData,
)
from dify_plugin.stream.io_stream import PluginIOStream
from dify_plugin.tool.entities import ToolInvokeMessage


class RequestInterface(AbstractRequestInterface):
    session_id: Optional[str]
    io_stream: PluginIOStream

    def __init__(self, io_stream: PluginIOStream, session_id: Optional[str] = None) -> None:
        self.session_id = session_id
        self.io_stream = io_stream

    def _generate_backwards_request_id(self):
        return uuid.uuid4().hex

    def _backwards_invoke(
        self, backwards_request_id: str, type: InvokeType, data: dict
    ):
        self.io_stream.session_message(
            session_id=self.session_id,
            data=self.io_stream.stream_invoke_object(
                data={
                    "type": type.value,
                    "backwards_request_id": backwards_request_id,
                    "request": data,
                }
            ),
        )

    def _wrapper_stream_invoke[T: BaseModel](
        self, request_id: str, data_type: Type[T]
    ) -> Generator[T, None, None]:
        """
        Wrapper for stream invoke
        """

        def filter(data: PluginInStream) -> bool:
            return (
                data.event == PluginInStream.Event.BackwardInvocationResponse
                and data.data.get("backwards_request_id") == request_id
            )

        empty_response_count = 0
        with self.io_stream.read(filter) as reader:
            for data in reader.read(timeout_for_round=1):
                """
                accept response from input stream and wait for at most 60 seconds
                """
                if data is None:
                    empty_response_count += 1
                    # if no response for 60 seconds, break
                    if empty_response_count >= 60:
                        raise Exception("invocation exited without response")
                    continue

                event = BackwardsInvocationResponseEvent(**data.data)
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
        backwards_request_id = self._generate_backwards_request_id()

        self._backwards_invoke(
            backwards_request_id,
            InvokeType.Tool,
            {
                "provider_type": provider_type.value,
                "provider": provider,
                "tool": tool_name,
                "tool_parameters": parameters,
            },
        )

        return self._wrapper_stream_invoke(backwards_request_id, ToolInvokeMessage)

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
        backwards_request_id = self._generate_backwards_request_id()

        self._backwards_invoke(
            backwards_request_id,
            InvokeType.LLM,
            {
                **model_config.model_dump(),
                "prompt_messages": [
                    message.model_dump() for message in prompt_messages
                ],
                "tools": [tool.model_dump() for tool in tools] if tools else None,
                "stop": stop,
                "stream": stream,
            },
        )

        return self._wrapper_stream_invoke(backwards_request_id, LLMResultChunk)

    def invoke_text_embedding(
        self, model_config: TextEmbeddingResult, texts: list[str]
    ) -> TextEmbeddingResult:
        """
        Invoke text embedding
        """
        backwards_request_id = self._generate_backwards_request_id()

        self._backwards_invoke(
            backwards_request_id,
            InvokeType.TextEmbedding,
            {
                **model_config.model_dump(),
                "texts": texts,
            },
        )

        for data in self._wrapper_stream_invoke(
            backwards_request_id, TextEmbeddingResult
        ):
            return data

        raise Exception("No response from text embedding")

    def invoke_rerank(
        self, model_config: RerankModelConfig, docs: list[str], query: str
    ) -> RerankResult:
        """
        Invoke rerank
        """
        backwards_request_id = self._generate_backwards_request_id()

        self._backwards_invoke(
            backwards_request_id,
            InvokeType.Rerank,
            {
                **model_config.model_dump(),
                "docs": docs,
                "query": query,
            },
        )

        for data in self._wrapper_stream_invoke(backwards_request_id, RerankResult):
            return data

        raise Exception("No response from rerank")

    def invoke_speech2text(
        self, model_config: Speech2TextModelConfig, file: IO[bytes]
    ) -> str:
        """
        Invoke speech2text
        """
        backwards_request_id = self._generate_backwards_request_id()

        self._backwards_invoke(
            backwards_request_id,
            InvokeType.Speech2Text,
            {
                **model_config.model_dump(),
                "file": hexlify(file.read()),
            },
        )

        for data in self._wrapper_stream_invoke(
            backwards_request_id, Speech2TextResult
        ):
            return data.result

        raise Exception("No response from speech2text")

    def invoke_moderation(self, model_config: ModerationModelConfig, text: str) -> bool:
        """
        Invoke moderation
        """
        backwards_request_id = self._generate_backwards_request_id()

        self._backwards_invoke(
            backwards_request_id,
            InvokeType.Moderation,
            {
                **model_config.model_dump(),
                "text": text,
            },
        )

        for data in self._wrapper_stream_invoke(backwards_request_id, ModerationResult):
            return data.result

        raise Exception("No response from moderation")

    def invoke_tts(
        self, model_config: TTSModelConfig, content_text: str
    ) -> Generator[bytes, None, None]:
        """
        Invoke tts
        """
        backwards_request_id = self._generate_backwards_request_id()

        self._backwards_invoke(
            backwards_request_id,
            InvokeType.TTS,
            {
                **model_config.model_dump(),
                "content_text": content_text,
            },
        )

        for data in self._wrapper_stream_invoke(backwards_request_id, TTSResult):
            yield unhexlify(data.result)

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
