from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from dify_plugin.core.runtime.entities.dify import ToolProviderType
from dify_plugin.core.runtime.entities.model import LLMResultChunk, RerankResult, TextEmbeddingResult
from dify_plugin.core.runtime.entities.tool import ToolInvokeMessage
from dify_plugin.core.runtime.entities.workflow import KnowledgeRetrievalNodeData, NodeResponse, ParameterExtractorNodeData, QuestionClassifierNodeData

class AbstractRequestInterface(ABC):
    @abstractmethod
    async def invoke_tool(self, provider_type: ToolProviderType, provider: str, tool_name: str,
                    parameters: dict[str, Any]) -> AsyncGenerator[ToolInvokeMessage, None]:
        """
        Invoke tool
        """

    @abstractmethod
    async def invoke_builtin_tool(self, provider: str, tool_name: str, parameters: dict[str, Any]) -> AsyncGenerator[ToolInvokeMessage, None]:
        """
        Invoke builtin tool
        """

    @abstractmethod
    async def invoke_workflow_tool(self, provider: str, tool_name: str, parameters: dict[str, Any]) -> AsyncGenerator[ToolInvokeMessage, None]:
        """
        Invoke workflow tool
        """

    @abstractmethod
    async def invoke_api_tool(self, provider: str, tool_name: str, parameters: dict[str, Any]) -> AsyncGenerator[ToolInvokeMessage, None]:
        """
        Invoke api tool
        """

    @abstractmethod
    async def invoke_llm(self, provider: str, model_name: str, parameters: dict[str, Any]) -> AsyncGenerator[LLMResultChunk, None]:
        """
        Invoke llm
        """

    @abstractmethod
    async def invoke_text_embedding(self, provider: str, model_name: str, parameters: dict[str, Any]) -> TextEmbeddingResult:
        """
        Invoke text embedding
        """

    @abstractmethod
    async def invoke_rerank(self, provider: str, model_name: str, parameters: dict[str, Any]) -> RerankResult:
        """
        Invoke rerank
        """

    @abstractmethod
    async def invoke_question_classifier(self, node_data: QuestionClassifierNodeData, inputs: dict) -> NodeResponse:
        """
        Invoke question classifier
        """

    @abstractmethod
    async def invoke_parameter_extractor(self, node_data: ParameterExtractorNodeData, inputs: dict) -> NodeResponse:
        """
        Invoke parameter extractor
        """

    @abstractmethod
    async def invoke_knowledge_retrieval(self, node_data: KnowledgeRetrievalNodeData, inputs: dict) -> NodeResponse:
        """
        Invoke knowledge retrieval
        """