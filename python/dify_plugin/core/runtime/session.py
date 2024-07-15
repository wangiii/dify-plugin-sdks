from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional, cast

from dify_plugin.core.runtime.entities.model_runtime.message import (
    PromptMessage,
    PromptMessageTool,
)
from dify_plugin.core.runtime.entities.plugin.request import ModelActions, ToolActions
from dify_plugin.model.ai_model import AIModel
from dify_plugin.model.large_language_model import LargeLanguageModel
from dify_plugin.model.model import ModelProvider
from dify_plugin.model.model_entities import ModelType
from dify_plugin.tool.tool import Tool, ToolProvider


class Session:
    _session_pool = set["Session"]()
    session_id: str
    executor: ThreadPoolExecutor

    def __init__(self, session_id: str, executor: ThreadPoolExecutor) -> None:
        self.session_id = session_id
        self._session_pool.add(self)
        self.executor = executor

    def run_tool(
        self, action: ToolActions, provider: ToolProvider, tool: Tool, parameters: dict
    ):
        """
        Run tool
        """
        if action == ToolActions.Invoke:
            yield from tool.invoke(parameters)

    def run_model(
        self,
        action: ModelActions,
        provider: ModelProvider,
        model: AIModel,
        model_type: ModelType,
        model_name: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        parameters: dict,
        tools: list[PromptMessageTool],
        stop: list[str],
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Generator[Any, None, None]:
        """
        Run model
        """
        if action == ModelActions.Invoke:
            yield from self._run_model_invocation(
                model,
                model_type,
                model_name,
                credentials,
                prompt_messages,
                parameters,
                tools,
                stop,
                stream,
                user,
            )
        elif action == ModelActions.ValidateProviderCredentials:
            yield self._run_model_provider_validate_credentials(provider, credentials)

    def _run_model_invocation(
        self,
        model: AIModel,
        model_type: ModelType,
        model_name: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        parameters: dict,
        tools: list[PromptMessageTool],
        stop: list[str],
        stream: bool,
        user: Optional[str] = None,
    ) -> Generator[Any, None, None]:
        """
        Invoke model
        """
        match model_type:
            case ModelType.LLM:
                llm = cast(LargeLanguageModel, model)
                result = llm._invoke(
                    model_name,
                    credentials,
                    prompt_messages,
                    parameters,
                    tools,
                    stop,
                    stream,
                    user,
                )
                if isinstance(result, Generator):
                    yield from result
                else:
                    yield result.to_llm_result_chunk()
            case _:
                raise NotImplementedError

    def _run_model_provider_validate_credentials(
        self, provider: ModelProvider, credentials: dict
    ):
        """
        Validate model provider credentials

        TODO: handle exceptions
        """
        try:
            return provider.validate_provider_credentials(credentials)
        except Exception as e:
            raise e

    def __del__(self):
        self._session_pool.remove(self)

    def close(self):
        self._session_pool.remove(self)

    @classmethod
    def get_session(cls, session_id: str):
        for session in cls._session_pool:
            if session.session_id == session_id:
                return session
        return None
