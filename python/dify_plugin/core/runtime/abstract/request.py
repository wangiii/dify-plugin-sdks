from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import IO, Any, Optional

from dify_plugin.core.entities.model_runtime.llm import (
    LLMResult,
    LLMResultChunk,
)
from dify_plugin.core.entities.model_runtime.message import (
    PromptMessage,
    PromptMessageTool,
)
from dify_plugin.core.entities.model_runtime.model_config import (
    LLMModelConfig,
    ModerationModelConfig,
    RerankModelConfig,
    Speech2TextModelConfig,
    TTSModelConfig,
)
from dify_plugin.core.entities.model_runtime.rerank import RerankResult
from dify_plugin.core.entities.model_runtime.text_embedding import (
    TextEmbeddingResult,
)
from dify_plugin.core.entities.plugin.dify import ToolProviderType
from dify_plugin.core.entities.plugin.workflow import (
    KnowledgeRetrievalNodeData,
    NodeResponse,
    ParameterExtractorNodeData,
    QuestionClassifierNodeData,
)
from dify_plugin.tool.entities import ToolInvokeMessage


class AbstractRequestInterface(ABC):
    @abstractmethod
    def invoke_tool(
        self,
        provider_type: ToolProviderType,
        provider: str,
        tool_name: str,
        parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke tool
        """

    @abstractmethod
    def invoke_builtin_tool(
        self, provider: str, tool_name: str, parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke builtin tool
        """

    @abstractmethod
    def invoke_workflow_tool(
        self, provider: str, tool_name: str, parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke workflow tool
        """

    @abstractmethod
    def invoke_api_tool(
        self, provider: str, tool_name: str, parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke api tool
        """

    @abstractmethod
    def invoke_llm(
        self,
        model_config: LLMModelConfig,
        prompt_messages: list[PromptMessage],
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
    ) -> Generator[LLMResultChunk, None, None] | LLMResult:
        """
        Invoke llm
        """ 

    @abstractmethod
    def invoke_text_embedding(
        self,
        model_config: TextEmbeddingResult,
        texts: list[str],
    ) -> TextEmbeddingResult:
        """
        Invoke text embedding
        """

    @abstractmethod
    def invoke_rerank(
        self, model_config: RerankModelConfig, docs: list[str], query: str
    ) -> RerankResult:
        """
        Invoke rerank
        """

    @abstractmethod
    def invoke_tts(
        self, model_config: TTSModelConfig, content_text: str
    ) -> Generator[bytes, None, None]:
        """
        Invoke tts
        """

    @abstractmethod
    def invoke_speech2text(
        self, model_config: Speech2TextModelConfig, file: IO[bytes]
    ) -> str:
        """
        Invoke speech2text
        """

    @abstractmethod
    def invoke_moderation(self, model_config: ModerationModelConfig, text: str) -> bool:
        """
        Invoke moderation
        """

    @abstractmethod
    def invoke_question_classifier(
        self, node_data: QuestionClassifierNodeData, inputs: dict
    ) -> NodeResponse:
        """
        Invoke question classifier
        """

    @abstractmethod
    def invoke_parameter_extractor(
        self, node_data: ParameterExtractorNodeData, inputs: dict
    ) -> NodeResponse:
        """
        Invoke parameter extractor
        """

    @abstractmethod
    def invoke_knowledge_retrieval(
        self, node_data: KnowledgeRetrievalNodeData, inputs: dict
    ) -> NodeResponse:
        """
        Invoke knowledge retrieval
        """
