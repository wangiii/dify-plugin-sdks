import base64
from typing import Any, Optional
import uuid
from pydantic import RootModel

from dify_plugin.core.entities.message import InitializeMessage
from dify_plugin.entities.tool import ToolInvokeMessage

from .core.server.__base.request_reader import RequestReader
from .core.server.__base.response_writer import ResponseWriter
from .core.server.aws.request_reader import AWSLambdaRequestReader
from .core.server.stdio.request_reader import StdioRequestReader
from .core.server.stdio.response_writer import StdioResponseWriter
from .core.server.tcp.request_reader import TCPReaderWriter
from collections.abc import Generator
import logging
from .config.config import DifyPluginEnv, InstallMethod
from .core.entities.plugin.request import (
    ModelActions,
    PluginInvokeType,
    ToolActions,
    EndpointActions,
)
from .core.runtime import Session
from .core.server.io_server import IOServer
from .core.server.router import Router
from .config.logger_format import plugin_logger_handler

from .core.plugin_executor import PluginExecutor
from .core.plugin_registration import PluginRegistration


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
            on_connected=lambda: self._initialize_tcp_stream(tcp_stream),
        )

        tcp_stream.launch()

        return tcp_stream, tcp_stream

    def _initialize_tcp_stream(
        self,
        tcp_stream: TCPReaderWriter,
    ):
        class List(RootModel):
            root: list[Any]

        tcp_stream.write(
            InitializeMessage(
                type=InitializeMessage.Type.MANIFEST_DECLARATION,
                data=self.registration.configuration.model_dump(),
            ).model_dump_json()
            + "\n\n"
        )

        if self.registration.tools_configuration:
            tcp_stream.write(
                InitializeMessage(
                    type=InitializeMessage.Type.TOOL_DECLARATION,
                    data=List(root=self.registration.tools_configuration).model_dump(),
                ).model_dump_json()
                + "\n\n"
            )

        if self.registration.models_configuration:
            tcp_stream.write(
                InitializeMessage(
                    type=InitializeMessage.Type.MODEL_DECLARATION,
                    data=List(root=self.registration.models_configuration).model_dump(),
                ).model_dump_json()
                + "\n\n"
            )

        if self.registration.endpoints_configuration:
            tcp_stream.write(
                InitializeMessage(
                    type=InitializeMessage.Type.ENDPOINT_DECLARATION,
                    data=List(root=self.registration.endpoints_configuration).model_dump(),
                ).model_dump_json()
                + "\n\n"
            )

        for file in self.registration.files:
            # divide the file into chunks
            chunks = [file.data[i : i + 8192] for i in range(0, len(file.data), 8192)]
            for sequence, chunk in enumerate(chunks):
                tcp_stream.write(
                    InitializeMessage(
                        type=InitializeMessage.Type.ASSET_CHUNK,
                        data=InitializeMessage.AssetChunk(
                            filename=file.filename,
                            data=base64.b64encode(chunk).decode(),
                            end=sequence == len(chunks) - 1,
                        ).model_dump(),
                    ).model_dump_json()
                    + "\n\n"
                )

        tcp_stream.write(
            InitializeMessage(
                type=InitializeMessage.Type.END,
                data={},
            ).model_dump_json()
            + "\n\n"
        )

        self._log_configuration()

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
        for endpoint in self.registration.endpoints_configuration:
            logger.info(f"Installed endpoint: {[e.path for e in endpoint.endpoints]}")

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
            self.plugin_executer.get_llm_num_tokens,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.GetLLMNumTokens.value,
        )

        self.register_route(
            self.plugin_executer.invoke_text_embedding,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.InvokeTextEmbedding.value,
        )

        self.register_route(
            self.plugin_executer.get_text_embedding_num_tokens,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.GetTextEmbeddingNumTokens.value,
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
            self.plugin_executer.get_tts_model_voices,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.GetTTSVoices.value,
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

        self.register_route(
            self.plugin_executer.get_ai_model_schemas,
            lambda data: data.get("type") == PluginInvokeType.Model.value
            and data.get("action") == ModelActions.GetAIModelSchemas.value,
        )

    def _execute_request(
        self,
        session_id: str,
        data: dict,
        reader: RequestReader,
        writer: ResponseWriter,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None,
        app_id: Optional[str] = None,
        endpoint_id: Optional[str] = None,
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
            conversation_id=conversation_id,
            message_id=message_id,
            app_id=app_id,
            endpoint_id=endpoint_id,
        )
        response = self.dispatch(session, data)
        if response:
            if isinstance(response, Generator):
                for message in response:
                    if isinstance(message, ToolInvokeMessage) and isinstance(
                        message.message, ToolInvokeMessage.BlobMessage
                    ):
                        # convert blob to file chunks
                        id = uuid.uuid4().hex
                        blob = message.message.blob
                        message.message.blob = id.encode("utf-8")
                        # split the blob into chunks
                        chunks = [blob[i : i + 8192] for i in range(0, len(blob), 8192)]
                        for sequence, chunk in enumerate(chunks):
                            writer.session_message(
                                session_id=session_id,
                                data=writer.stream_object(
                                    data=ToolInvokeMessage(
                                        type=ToolInvokeMessage.MessageType.BLOB_CHUNK,
                                        message=ToolInvokeMessage.BlobChunkMessage(
                                            id=id,
                                            sequence=sequence,
                                            total_length=len(blob),
                                            blob=chunk,
                                            end=False,
                                        ),
                                        meta=message.meta,
                                    ),
                                ),
                            )

                        # end the file stream
                        writer.session_message(
                            session_id=session_id,
                            data=writer.stream_object(
                                data=ToolInvokeMessage(
                                    type=ToolInvokeMessage.MessageType.BLOB_CHUNK,
                                    message=ToolInvokeMessage.BlobChunkMessage(
                                        id=id,
                                        sequence=len(chunks),
                                        total_length=len(blob),
                                        blob=b"",
                                        end=True,
                                    ),
                                    meta=message.meta,
                                )
                            ),
                        )
                    else:
                        writer.session_message(
                            session_id=session_id,
                            data=writer.stream_object(data=message),
                        )
            else:
                writer.session_message(
                    session_id=session_id,
                    data=writer.stream_object(data=response),
                )
