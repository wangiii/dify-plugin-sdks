from typing import Any

from pydantic import BaseModel

from dify_plugin.entities.tool import ToolProviderType
from dify_plugin.interfaces.agent import (
    AgentModelConfig,
    AgentStrategy,
    ToolEntity,
)


class FunctionCallingParams(BaseModel):
    query: str
    instruction: str | None
    model: AgentModelConfig
    tools: list[ToolEntity] | None
    maximum_iterations: int = 3


class FunctionCallingAgentStrategy(AgentStrategy):
    def __init__(self, runtime, session):
        super().__init__(runtime, session)
        self.query = ""
        self.instruction = ""

    def invoke(self, tool_instance: ToolEntity, tool_call_args: dict[str, Any]):
        tool_invoke_responses = self.session.tool.invoke(
            provider_type=ToolProviderType(tool_instance.provider_type),
            provider=tool_instance.identity.provider,
            tool_name=tool_instance.identity.name,
            parameters={
                **tool_instance.runtime_parameters,
                **tool_call_args,
            },
        )


if __name__ == "__main__":
    FunctionCallingAgentStrategy(runtime, session)
