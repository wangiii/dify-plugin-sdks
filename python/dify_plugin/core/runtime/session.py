import asyncio
from collections.abc import AsyncGenerator, Generator
from concurrent.futures import ThreadPoolExecutor

from dify_plugin.core.runtime.entities.model import LLMResultChunk
from dify_plugin.core.runtime.entities.request import ToolActions
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

    async def to_async_generator[T](self, generator: Generator[T, None, None]):
        loop = asyncio.get_event_loop()

        def _next(iterator):
            try:
                return next(iterator)
            except StopIteration:
                return None
            except Exception as e:
                return e

        iterator = iter(generator)
        
        while True:
            result = await loop.run_in_executor(self.executor, _next, iterator)
            if isinstance(result, Exception):
                raise result
            if result is not None:
                yield result
            else:
                break

    async def run_tool(self, action: ToolActions, provider: ToolProvider, tool: Tool, parameters: dict):
        if action == ToolActions.Invoke:
            async for message in self.to_async_generator(tool._invoke(tool.runtime.user_id, parameters)):
                yield message

    async def run_model(self, provider: ModelProvider, model: Model, parameters: dict) -> AsyncGenerator[LLMResultChunk, None]:
        return await self.run_model(provider, model, parameters)
        
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