from dify_plugin.core.runtime.entities.plugin.request import (
    ModelInvokeLLMRequest,
    ModelValidateModelCredentialsRequest,
    ModelValidateProviderCredentialsRequest,
    ToolInvokeRequest,
    ToolValidateCredentialsRequest,
)
from dify_plugin.core.runtime.session import Session
from dify_plugin.model.large_language_model import LargeLanguageModel
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
                parameters=request.parameters,
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
