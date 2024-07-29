from collections.abc import Generator
from typing import Any

from dify_plugin.core.runtime.entities.model_runtime.message import SystemPromptMessage, UserPromptMessage
from dify_plugin.core.runtime.entities.model_runtime.model_config import LLMModelConfig
from dify_plugin.tool.entities import ToolInvokeMessage
from dify_plugin.tool.tool import Tool

class LLMTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        response = self.invoke_llm(
            model_config=LLMModelConfig(
                provider='openai',
                model='gpt-4o-mini',
                mode='chat',
                model_parameters={}
            ),
            prompt_messages=[
                SystemPromptMessage(
                    content='you are a helpful assistant'
                ),
                UserPromptMessage(
                    content=tool_parameters.get('query')
                )
            ],
            stream=True
        )

        for chunk in response:
            if chunk.delta.message:
                assert isinstance(chunk.delta.message.content, str)
                yield self.create_text_message(text=chunk.delta.message.content)