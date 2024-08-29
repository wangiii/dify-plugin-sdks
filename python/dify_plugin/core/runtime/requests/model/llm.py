from collections.abc import Generator
from typing import Literal, cast, overload

from dify_plugin.core.entities.model.llm import LLMResult, LLMResultChunk
from dify_plugin.core.entities.model.message import PromptMessage, PromptMessageTool
from dify_plugin.core.entities.plugin.invocation import InvokeType
from dify_plugin.core.runtime.requests import DifyRequest
from dify_plugin.core.runtime.requests.model import BaseModelConfig, ModelType


class LLMModelConfig(BaseModelConfig):
    """
    Model class for llm model config.
    """

    model_type: ModelType = ModelType.LLM
    mode: str
    model_parameters: dict | None = None
    

class LLMRequest(DifyRequest[LLMResult | LLMResultChunk]):
    @overload
    def invoke(
        self,
        model_config: LLMModelConfig,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: Literal[True] = True,
    ) -> Generator[LLMResultChunk, None, None]: ...

    @overload
    def invoke(
        self,
        model_config: LLMModelConfig,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: Literal[False] = False,
    ) -> LLMResult: ...

    def invoke(
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
            response = self._backwards_invoke(
                InvokeType.LLM,
                LLMResultChunk,
                data,
            )
            response = cast(Generator[LLMResultChunk, None, None], response)
            return response

        for data in self._backwards_invoke(
            InvokeType.LLM,
            LLMResult,
            data,
        ):
            data = cast(LLMResult, data)
            return data

        raise Exception("No response from llm")
