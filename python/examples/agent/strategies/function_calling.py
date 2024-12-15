from collections.abc import Generator
from typing import Any


from dify_plugin.entities.agent import AgentInvokeMessage
from dify_plugin.interfaces.agent import AgentStrategy


class FunctionCallingAgentStrategy(AgentStrategy):
    def _invoke(self, parameters: dict[str, Any]) -> Generator[AgentInvokeMessage]:
        root = self.create_log_message(data={"Thought": "aaa", "sss": "xxx"}, label="root")
        yield root

        child1 = self.create_log_message(
            data={
                "tool-response": "111",
            },
            label="child1",
            parent=root,
        )

        yield child1

        child2 = self.create_log_message(
            data={
                "tool-response": "111",
            },
            label="child2",
            parent=root,
        )
        yield child2

        child3 = self.create_log_message(
            data={
                "tool-response": "111",
            },
            label="child3",
            parent=root,
        )
        yield child3

        # finish log
        yield self.finish_log_message(child3)
        yield self.finish_log_message(child2)
        yield self.finish_log_message(child1)
        yield self.finish_log_message(root)

        yield self.create_json_message(parameters)
