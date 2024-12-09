from abc import abstractmethod
from typing import Generator
from dify_plugin.core.runtime import Session
from dify_plugin.entities.agent import AgentInvokeMessage
from dify_plugin.interfaces.tool import ToolLike, ToolProvider


class AgentProvider(ToolProvider):
    def validate_credentials(self):
        """
        Always permit the agent to run
        """
        return True

    def _validate_credentials(self):
        pass


class AgentStrategy(ToolLike[AgentInvokeMessage]):
    def __init__(
        self,
        session: Session,
    ):
        self.session = session
        self.response_type = AgentInvokeMessage

    ############################################################
    #        Methods that can be implemented by plugin         #
    ############################################################

    @abstractmethod
    def _invoke(self, parameters: dict) -> Generator[AgentInvokeMessage, None, None]:
        pass

    ############################################################
    #                 For executor use only                    #
    ############################################################

    def invoke(self, parameters: dict) -> Generator[AgentInvokeMessage, None, None]:
        # convert parameters into correct types
        parameters = self._convert_parameters(parameters)
        return self._invoke(parameters)
