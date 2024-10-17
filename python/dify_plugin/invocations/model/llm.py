from collections.abc import Generator
from typing import Literal, cast, overload

from ...entities.model.llm import LLMModelConfig, LLMResult, LLMResultChunk, SummaryResult
from ...entities.model.message import PromptMessage, PromptMessageTool
from ...core.entities.invocation import InvokeType
from ...core.runtime import BackwardsInvocation
    

class LLMInvocation(BackwardsInvocation[LLMResult | LLMResultChunk]):
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

class SummaryInvocation(BackwardsInvocation[SummaryResult]):
    def invoke(
        self,
        text: str,
        instruction: str,
    ) -> str:
        """
        Invoke summary
        """
        data = {
            "text": text,
            "instruction": instruction,
        }

        for data in self._backwards_invoke(
            InvokeType.LLM,
            SummaryResult,
            data,
        ):
            data = cast(SummaryResult, data)
            return data.summary

        raise Exception("No response from summary")