import binascii
import io
import tempfile
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


class PluginExecutor:
    def __init__(self, registration: PluginRegistration) -> None:
        self.registration = registration

    def validate_tool_provider_credentials(
        self, session: Session, data: ToolValidateCredentialsRequest
    ):
        pass

    def invoke_tool(self, session: Session, request: ToolInvokeRequest):
        provider_cls = self.registration.get_tool_provider_cls(request.provider)
        if provider_cls is None:
            raise ValueError(f"Provider `{request.provider}` not found")

        tool_cls = self.registration.get_tool_cls(request.provider, request.tool)
        if tool_cls is None:
            raise ValueError(
                f"Tool `{request.tool}` not found for provider `{request.provider}`"
            )

        # instantiate provider and tool
        provider = provider_cls()
        tool = tool_cls(
            runtime=ToolRuntime(
                credentials=request.credentials, user_id=request.user_id
            )
        )

        # invoke tool
        try:
            return session.run_tool(
                action=request.action,
                provider=provider,
                tool=tool,
                parameters=request.tool_parameters,
            )
        except Exception as e:
            raise ValueError(f"Failed to invoke tool: {type(e).__name__}: {str(e)}")

    def validate_model_provider_credentials(
        self, session: Session, data: ModelValidateProviderCredentialsRequest
    ):
        pass

    def validate_model_credentials(
        self, session: Session, data: ModelValidateModelCredentialsRequest
    ):
        pass

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

    def invoke_text_embedding(self, session: Session, data: ModelInvokeTextEmbeddingRequest):
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
                data.user_id
            )
            if isinstance(b, bytes):
                return {"result": binascii.hexlify(b).decode()}
            
            for chunk in b:
                yield {"result": binascii.hexlify(bytes(chunk)).decode()}

    def invoke_speech_to_text(self, session: Session, data: ModelInvokeSpeech2TextRequest):
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