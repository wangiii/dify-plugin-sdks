from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor

from dify_plugin.core.runtime.entities.model_runtime.llm import LLMResultChunk
from dify_plugin.core.runtime.entities.plugin.request import ToolActions
from dify_plugin.model.model import Model, ModelProvider
from dify_plugin.tool.tool import Tool, ToolProvider

class Session:
    _session_pool = set['Session']()
    session_id: str
    executor: ThreadPoolExecutor

    def __init__(self, session_id: str, executor: ThreadPoolExecutor) -> None:
        self.session_id = session_id
        self._session_pool.add(self)
        self.executor = executor

    def run_tool(self, action: ToolActions, provider: ToolProvider, tool: Tool, parameters: dict):
        if action == ToolActions.Invoke:
            yield from tool.invoke(parameters)
        
    def run_model(self, provider: ModelProvider, model: Model, parameters: dict) -> Generator[LLMResultChunk, None, None]:
        return self.run_model(provider, model, parameters)
        
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