import time
from abc import abstractmethod
from typing import Optional

from pydantic import ConfigDict

from ...entities.model.text_embedding import TextEmbeddingResult
from .ai_model import AIModel
from ...entities.model import EmbeddingInputType, ModelPropertyKey, ModelType


class TextEmbeddingModel(AIModel):
    """
    Model class for text embedding model.
    """

    model_type: ModelType = ModelType.TEXT_EMBEDDING

    # pydantic configs
    model_config = ConfigDict(protected_namespaces=())

    ############################################################
    #        Methods that can be implemented by plugin         #
    ############################################################

    @abstractmethod
    def _invoke(
        self,
        model: str,
        credentials: dict,
        texts: list[str],
        user: Optional[str] = None,
        input_type: EmbeddingInputType = EmbeddingInputType.DOCUMENT,
    ) -> TextEmbeddingResult:
        """
        Invoke large language model

        :param model: model name
        :param credentials: model credentials
        :param texts: texts to embed
        :param user: unique user id
        :param input_type: embedding input type
        :return: embeddings result
        """
        raise NotImplementedError

    @abstractmethod
    def get_num_tokens(self, model: str, credentials: dict, texts: list[str]) -> int:
        """
        Get number of tokens for given prompt messages

        :param model: model name
        :param credentials: model credentials
        :param texts: texts to embed
        :return:
        """
        raise NotImplementedError

    ############################################################
    #            For plugin implementation use only            #
    ############################################################

    def _get_context_size(self, model: str, credentials: dict) -> int:
        """
        Get context size for given embedding model

        :param model: model name
        :param credentials: model credentials
        :return: context size
        """
        model_schema = self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.CONTEXT_SIZE in model_schema.model_properties
        ):
            return model_schema.model_properties[ModelPropertyKey.CONTEXT_SIZE]

        return 1000

    def _get_max_chunks(self, model: str, credentials: dict) -> int:
        """
        Get max chunks for given embedding model

        :param model: model name
        :param credentials: model credentials
        :return: max chunks
        """
        model_schema = self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.MAX_CHUNKS in model_schema.model_properties
        ):
            return model_schema.model_properties[ModelPropertyKey.MAX_CHUNKS]

        return 1

    ############################################################
    #                 For executor use only                    #
    ############################################################

    def invoke(
        self,
        model: str,
        credentials: dict,
        texts: list[str],
        user: Optional[str] = None,
        input_type: EmbeddingInputType = EmbeddingInputType.DOCUMENT,
    ) -> TextEmbeddingResult:
        """
        Invoke large language model

        :param model: model name
        :param credentials: model credentials
        :param texts: texts to embed
        :param user: unique user id
        :param input_type: embedding input type
        :return: embeddings result
        """
        self.started_at = time.perf_counter()

        try:
            return self._invoke(model, credentials, texts, user, input_type)
        except Exception as e:
            raise self._transform_invoke_error(e)
