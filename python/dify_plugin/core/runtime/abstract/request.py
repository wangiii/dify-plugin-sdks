from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any

from dify_plugin.core.runtime.entities.dify import ToolProviderType
from dify_plugin.core.runtime.entities.model import LLMResultChunk, RerankResult, TextEmbeddingResult
from dify_plugin.core.runtime.entities.workflow import KnowledgeRetrievalNodeData, NodeResponse, ParameterExtractorNodeData, QuestionClassifierNodeData
from dify_plugin.tool.entities import ToolInvokeMessage

class AbstractRequestInterface(ABC):
    @abstractmethod
    def invoke_tool(self, provider_type: ToolProviderType, provider: str, tool_name: str,
                    parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke tool
        """

    @abstractmethod
    def invoke_builtin_tool(self, provider: str, tool_name: str, parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke builtin tool
        """

    @abstractmethod
    def invoke_workflow_tool(self, provider: str, tool_name: str, parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke workflow tool
        """

    @abstractmethod
    def invoke_api_tool(self, provider: str, tool_name: str, parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke api tool
        """

    @abstractmethod
    def invoke_llm(self, provider: str, model_name: str, parameters: dict[str, Any]) -> Generator[LLMResultChunk, None, None]:
        """
        Invoke llm
        """

    @abstractmethod
    def invoke_text_embedding(self, provider: str, model_name: str, parameters: dict[str, Any]) -> TextEmbeddingResult:
        """
        Invoke text embedding
        """

    @abstractmethod
    def invoke_rerank(self, provider: str, model_name: str, parameters: dict[str, Any]) -> RerankResult:
        """
        Invoke rerank
        """

    @abstractmethod
    def invoke_question_classifier(self, node_data: QuestionClassifierNodeData, inputs: dict) -> NodeResponse:
        """
        Invoke question classifier
        """

    @abstractmethod
    def invoke_parameter_extractor(self, node_data: ParameterExtractorNodeData, inputs: dict) -> NodeResponse:
        """
        Invoke parameter extractor
        """

    @abstractmethod
    def invoke_knowledge_retrieval(self, node_data: KnowledgeRetrievalNodeData, inputs: dict) -> NodeResponse:
        """
        Invoke knowledge retrieval
        """