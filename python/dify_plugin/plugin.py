from collections.abc import Generator
import logging

from dify_plugin.config.config import DifyPluginEnv

from dify_plugin.core.runtime.entities.plugin.request import (
    ModelActions,
    PluginInvokeType,
    ToolActions,
)
from dify_plugin.core.runtime.session import Session
from dify_plugin.core.server.io_server import IOServer
from dify_plugin.core.server.router import Router
from dify_plugin.logger_format import plugin_logger_handler

from dify_plugin.plugin_executor import PluginExecutor
from dify_plugin.plugin_registration import PluginRegistration


from dify_plugin.utils.io_writer import PluginOutputStream

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class Plugin(IOServer, Router):
    def __init__(self, config: DifyPluginEnv) -> None:
        """
        Initialize plugin
        """

        # load plugin configuration
        self.registration = PluginRegistration(config)

        # initialize plugin executor
        self.plugin_executer = PluginExecutor(self.registration)

        IOServer.__init__(self, config)
        Router.__init__(self)

        # register io routes
        self._register_request_routes()

    def _register_request_routes(self):
        """
        Register routes
        """
        self.register_route(
            self.plugin_executer.invoke_tool,
            lambda data: data.get("type") == PluginInvokeType.Tool.value
            and data.get("action") == ToolActions.Invoke.value,
        )

        self.register_route(
            self.plugin_executer.validate_tool_provider_credentials,
            lambda data: data.get("type") == PluginInvokeType.Tool.value
            and data.get("action") == ToolActions.ValidateCredentials.value,
        )

        self.register_route(
            self.plugin_executer.invoke_llm,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.InvokeLLM.value,
        )

        self.register_route(
            self.plugin_executer.validate_model_provider_credentials,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.ValidateProviderCredentials.value,
        )

        self.register_route(
            self.plugin_executer.validate_model_credentials,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.ValidateModelCredentials.value,
        )


    def _execute_request(self, session_id: str, data: dict):
        """
        accept requests and execute
        :param session_id: session id, unique for each request
        :param data: request data
        """

        session = Session(session_id=session_id, executor=self.executer)
        response = self.dispatch(session, data)
        if response:
            if isinstance(response, Generator):
                for message in response:
                    PluginOutputStream.session_message(
                        session_id=session_id,
                        data=PluginOutputStream.stream_object(data=message),
                    )
            else:
                PluginOutputStream.session_message(
                    session_id=session_id,
                    data=PluginOutputStream.stream_object(data=response),
                )
