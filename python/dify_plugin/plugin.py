from typing import Optional

from dify_plugin.core.server.__base.request_reader import RequestReader
from dify_plugin.core.server.__base.response_writer import ResponseWriter
from dify_plugin.core.server.aws.request_reader import AWSLambdaRequestReader
from dify_plugin.core.server.stdio.request_reader import StdioRequestReader
from dify_plugin.core.server.stdio.response_writer import StdioResponseWriter
from dify_plugin.core.server.tcp.request_reader import TCPReaderWriter
from collections.abc import Generator  # noqa: E402
import logging  # noqa: E402
from dify_plugin.config.config import DifyPluginEnv, InstallMethod  # noqa: E402
from dify_plugin.core.entities.plugin.request import (  # noqa: E402
    ModelActions,
    PluginInvokeType,
    ToolActions,
    EndpointActions,
)
from dify_plugin.core.server.io_server import IOServer  # noqa: E402
from dify_plugin.core.server.router import Router  # noqa: E402
from dify_plugin.logger_format import plugin_logger_handler  # noqa: E402

from dify_plugin.plugin_executor import PluginExecutor  # noqa: E402
from dify_plugin.plugin_registration import PluginRegistration
from dify_plugin.core.runtime import Session  # noqa: E402


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
            request_reader, response_writer = self._launch_local_stream(config)
        elif config.INSTALL_METHOD == InstallMethod.Remote:
            request_reader, response_writer = self._launch_remote_stream(config)
        elif config.INSTALL_METHOD == InstallMethod.AWSLambda:
            request_reader, response_writer = self._launch_aws_stream(config)
        else:
            raise ValueError("Invalid install method")

        # set default response writer
        self.default_response_writer = response_writer

        # initialize plugin executor
        self.plugin_executer = PluginExecutor(config, self.registration)

        IOServer.__init__(self, config, request_reader, response_writer)
        Router.__init__(self, request_reader, response_writer)

        # register io routes
        self._register_request_routes()

    def _launch_local_stream(
        self, config: DifyPluginEnv
    ) -> tuple[RequestReader, Optional[ResponseWriter]]:
        """
        Launch local stream
        """
        reader = StdioRequestReader()
        writer = StdioResponseWriter()
        writer.write(self.registration.configuration.model_dump_json() + "\n\n")

        self._log_configuration()
        return reader, writer

    def _launch_remote_stream(
        self, config: DifyPluginEnv
    ) -> tuple[RequestReader, Optional[ResponseWriter]]:
        """
        Launch remote stream
        """
        if not config.REMOTE_INSTALL_KEY:
            raise ValueError("Missing remote install key")

        tcp_stream = TCPReaderWriter(
            config.REMOTE_INSTALL_HOST,
            config.REMOTE_INSTALL_PORT,
            config.REMOTE_INSTALL_KEY,
            on_connected=lambda: tcp_stream.write(
                self.registration.configuration.model_dump_json() + "\n\n"
            )
            and self._log_configuration(),
        )

        tcp_stream.launch()

        return tcp_stream, tcp_stream

    def _launch_aws_stream(
        self, config: DifyPluginEnv
    ) -> tuple[RequestReader, Optional[ResponseWriter]]:
        """
        Launch AWS stream
        """
        aws_stream = AWSLambdaRequestReader(
            config.AWS_LAMBDA_PORT, config.MAX_REQUEST_TIMEOUT
        )
        aws_stream.launch()

        return aws_stream, None

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

        self.register_route(
            self.plugin_executer.invoke_endpoint,
            lambda data: data.get("type") == PluginInvokeType.Endpoint.value
            and data.get("action") == EndpointActions.InvokeEndpoint.value,
        )

    def _execute_request(
        self, session_id: str, data: dict, reader: RequestReader, writer: ResponseWriter
    ):
        """
        accept requests and execute
        :param session_id: session id, unique for each request
        :param data: request data
        """

        session = Session(
            session_id=session_id,
            executor=self.executer,
            reader=reader,
            writer=writer,
            install_method=self.config.INSTALL_METHOD,
            dify_plugin_daemon_url=self.config.DIFY_PLUGIN_DAEMON_URL,
        )
        response = self.dispatch(session, data)
        if response:
            if isinstance(response, Generator):
                for message in response:
                    if self.response_writer:
                        self.response_writer.session_message(
                            session_id=session_id,
                            data=self.response_writer.stream_object(data=message),
                        )
            else:
                if self.response_writer:
                    self.response_writer.session_message(
                        session_id=session_id,
                        data=self.response_writer.stream_object(data=response),
                    )
