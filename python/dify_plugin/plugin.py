from gevent import monkey

from dify_plugin.core.server.stdio_stream import StdioStream
from dify_plugin.core.server.tcp_stream import TCPStream
from dify_plugin.stream.input_stream import PluginInputStream
from dify_plugin.stream.output_stream import PluginOutputStream

# patch all the blocking calls
monkey.patch_all(sys=True)

from collections.abc import Generator  # noqa: E402
import logging  # noqa: E402

from dify_plugin.config.config import DifyPluginEnv, InstallMethod  # noqa: E402

from dify_plugin.core.runtime.entities.plugin.request import (  # noqa: E402
    ModelActions,
    PluginInvokeType,
    ToolActions,
)
from dify_plugin.core.runtime.session import Session  # noqa: E402
from dify_plugin.core.server.io_server import IOServer  # noqa: E402
from dify_plugin.core.server.router import Router  # noqa: E402
from dify_plugin.logger_format import plugin_logger_handler  # noqa: E402

from dify_plugin.plugin_executor import PluginExecutor  # noqa: E402
from dify_plugin.plugin_registration import PluginRegistration  # noqa: E402


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

        if config.INSTALL_METHOD == InstallMethod.Local:
            stdio_stream = StdioStream()
            PluginInputStream.reset(stdio_stream)
            PluginOutputStream.init(stdio_stream)
        elif config.INSTALL_METHOD == InstallMethod.Remote:
            if not config.REMOTE_INSTALL_KEY:
                raise ValueError("Missing remote install key")

            tcp_stream = TCPStream(
                config.REMOTE_INSTALL_HOST,
                config.REMOTE_INSTALL_PORT,
                config.REMOTE_INSTALL_KEY,
                on_connected=lambda: PluginOutputStream.write(
                    self.registration.configuration.model_dump_json() + "\n\n"
                )
                and self._log_configuration(),
            )
            PluginInputStream.reset(tcp_stream)
            PluginOutputStream.init(tcp_stream)
            tcp_stream.launch()
        else:
            raise ValueError("Invalid install method")

        if config.INSTALL_METHOD == InstallMethod.Local:
            PluginOutputStream.write(
                self.registration.configuration.model_dump_json() + "\n\n"
            )
            self._log_configuration()

        # initialize plugin executor
        self.plugin_executer = PluginExecutor(self.registration)

        IOServer.__init__(self, config)
        Router.__init__(self)

        # register io routes
        self._register_request_routes()

    def _log_configuration(self):
        """
        Log plugin configuration
        """
        for tool in self.registration.tools_configuration:
            logger.info(f"Installed tool: {tool.identity.name}")
        for model in self.registration.models_configuration:
            logger.info(f"Installed model: {model.provider}")

    def _register_request_routes(self):
        """
        Register routes
        """
        self.register_route(
            self.plugin_executer.invoke_tool,
            lambda data: data.get("type") == PluginInvokeType.Tool.value
            and data.get("action") == ToolActions.InvokeTool.value,
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
            self.plugin_executer.invoke_text_embedding,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.InvokeTextEmbedding.value,
        )

        self.register_route(
            self.plugin_executer.invoke_rerank,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.InvokeRerank.value,
        )

        self.register_route(
            self.plugin_executer.invoke_tts,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.InvokeTTS.value,
        )

        self.register_route(
            self.plugin_executer.invoke_speech_to_text,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.InvokeSpeech2Text.value,
        )

        self.register_route(
            self.plugin_executer.invoke_moderation,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.InvokeModeration.value,
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
