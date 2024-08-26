import binascii
from collections.abc import Generator, Iterable
import tempfile

from werkzeug import Response

from dify_plugin.config.config import InstallMethod
from dify_plugin.core.runtime.entities.plugin.request import (
    ModelInvokeLLMRequest,
    ModelInvokeModerationRequest,
    ModelInvokeRerankRequest,
    ModelInvokeSpeech2TextRequest,
    ModelInvokeTTSRequest,
    ModelInvokeTextEmbeddingRequest,
    ModelValidateModelCredentialsRequest,
    ModelValidateProviderCredentialsRequest,
    ToolInvokeRequest,
    ToolValidateCredentialsRequest,
    WebhookInvokeRequest,
)
from dify_plugin.core.runtime.session import Session
from dify_plugin.model.large_language_model import LargeLanguageModel
from dify_plugin.model.moderation_model import ModerationModel
from dify_plugin.model.rerank_model import RerankModel
from dify_plugin.model.speech2text_model import Speech2TextModel
from dify_plugin.model.text_embedding_model import TextEmbeddingModel
from dify_plugin.model.tts_model import TTSModel
from dify_plugin.plugin_registration import PluginRegistration
from dify_plugin.tool.entities import ToolRuntime
from dify_plugin.utils.http_parser import parse_raw_request


class PluginExecutor:
    def __init__(self, install_method: InstallMethod, registration: PluginRegistration) -> None:
        self.install_method = install_method
        self.registration = registration

    def validate_tool_provider_credentials(
        self, session: Session, data: ToolValidateCredentialsRequest
    ):
        provider_instance = self.registration.get_tool_provider_cls(data.provider)
        if provider_instance is None:
            raise ValueError(f"Provider `{data.provider}` not found")

        provider_instance = provider_instance()

        try:
            provider_instance.validate_credentials(data.credentials)
        except Exception as e:
            raise ValueError(
                f"Failed to validate provider credentials: {type(e).__name__}: {str(e)}"
            )

        return {"result": True}

    def invoke_tool(self, session: Session, request: ToolInvokeRequest):
        provider_cls = self.registration.get_tool_provider_cls(request.provider)
        if provider_cls is None:
            raise ValueError(f"Provider `{request.provider}` not found")

        tool_cls = self.registration.get_tool_cls(request.provider, request.tool)
        if tool_cls is None:
            raise ValueError(
                f"Tool `{request.tool}` not found for provider `{request.provider}`"
            )

        # instantiate tool
        tool = tool_cls(
            runtime=ToolRuntime(
                credentials=request.credentials,
                user_id=request.user_id,
                session_id=session.session_id,
                install_method=self.install_method
            )
        )

        # invoke tool
        try:
            yield from tool.invoke(request.tool_parameters)
        except Exception as e:
            raise ValueError(f"Failed to invoke tool: {type(e).__name__}: {str(e)}")

    def validate_model_provider_credentials(
        self, session: Session, data: ModelValidateProviderCredentialsRequest
    ):
        provider_instance = self.registration.get_model_provider_instance(data.provider)
        if provider_instance is None:
            raise ValueError(f"Provider `{data.provider}` not found")

        try:
            provider_instance.validate_provider_credentials(data.credentials)
        except Exception as e:
            raise ValueError(
                f"Failed to validate provider credentials: {type(e).__name__}: {str(e)}"
            )

        return {"result": True}

    def validate_model_credentials(
        self, session: Session, data: ModelValidateModelCredentialsRequest
    ):
        provider_instance = self.registration.get_model_provider_instance(data.provider)
        if provider_instance is None:
            raise ValueError(f"Provider `{data.provider}` not found")

        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )
        if model_instance is None:
            raise ValueError(
                f"Model `{data.model_type}` not found for provider `{data.provider}`"
            )

        try:
            model_instance.validate_credentials(data.model, data.credentials)
        except Exception as e:
            raise ValueError(
                f"Failed to validate model credentials: {type(e).__name__}: {str(e)}"
            )

        return {"result": True}

    def invoke_llm(self, session: Session, data: ModelInvokeLLMRequest):
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )
        if isinstance(model_instance, LargeLanguageModel):
            return model_instance.invoke(
                data.model,
                data.credentials,
                data.prompt_messages,
                data.model_parameters,
                data.tools,
                data.stop,
                data.stream,
                data.user_id,
            )

    def invoke_text_embedding(
        self, session: Session, data: ModelInvokeTextEmbeddingRequest
    ):
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )
        if isinstance(model_instance, TextEmbeddingModel):
            return model_instance.invoke(
                data.model,
                data.credentials,
                data.texts,
                data.user_id,
            )

    def invoke_rerank(self, session: Session, data: ModelInvokeRerankRequest):
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )
        if isinstance(model_instance, RerankModel):
            return model_instance.invoke(
                data.model,
                data.credentials,
                data.query,
                data.docs,
                data.score_threshold,
                data.top_n,
                data.user_id,
            )

    def invoke_tts(self, session: Session, data: ModelInvokeTTSRequest):
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )
        if isinstance(model_instance, TTSModel):
            b = model_instance.invoke(
                data.model,
                data.credentials,
                data.content_text,
                data.voice,
                data.user_id,
            )
            if isinstance(b, bytes | bytearray | memoryview):
                return {"result": binascii.hexlify(b).decode()}

            for chunk in b:
                yield {"result": binascii.hexlify(chunk).decode()}

    def invoke_speech_to_text(
        self, session: Session, data: ModelInvokeSpeech2TextRequest
    ):
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )

        with tempfile.NamedTemporaryFile(suffix=".mp3", mode="wb", delete=True) as temp:
            temp.write(binascii.unhexlify(data.file))
            temp.flush()

            with open(temp.name, "rb") as f:
                if isinstance(model_instance, Speech2TextModel):
                    return {
                        "result": model_instance.invoke(
                            data.model,
                            data.credentials,
                            f,
                            data.user_id,
                        )
                    }

    def invoke_moderation(self, session: Session, data: ModelInvokeModerationRequest):
        model_instance = self.registration.get_model_instance(
            data.provider, data.model_type
        )

        if isinstance(model_instance, ModerationModel):
            return {
                "result": model_instance.invoke(
                    data.model,
                    data.credentials,
                    data.text,
                    data.user_id,
                )
            }

    def invoke_webhook(self, session: Session, data: WebhookInvokeRequest):
        bytes_data = binascii.unhexlify(data.raw_http_request)
        request = parse_raw_request(bytes_data)


        try:
            # dispatch request
            webhook, values = self.registration.dispatch_webhook_request(request)
            # construct response
            webhook_instance = webhook()
            response = webhook_instance.invoke(request, values)
        except Exception:
            response = Response('Not Found', status=404)

        # check if response is a generator
        if isinstance(response.response, Generator):
            # return headers
            yield {
                "status": response.status_code,
                "headers": {k: v for k, v in response.headers.items()},
            }

            for chunk in response.response:
                if isinstance(chunk, bytes | bytearray | memoryview):
                    yield {"result": binascii.hexlify(chunk).decode()}
                else:
                    yield {"result": binascii.hexlify(chunk.encode("utf-8")).decode()}
        else:
            result = {
                "status": response.status_code,
                "headers": {k: v for k, v in response.headers.items()},
            }

            if isinstance(response.response, bytes | bytearray | memoryview):
                result["result"] = binascii.hexlify(response.response).decode()
            elif isinstance(response.response, str):
                result["result"] = binascii.hexlify(
                    response.response.encode("utf-8")
                ).decode()
            elif isinstance(response.response, Iterable):
                result["result"] = ""
                for chunk in response.response:
                    if isinstance(chunk, bytes | bytearray | memoryview):
                        result["result"] += binascii.hexlify(chunk).decode()
                    else:
                        result["result"] += binascii.hexlify(
                            chunk.encode("utf-8")
                        ).decode()

            yield result
