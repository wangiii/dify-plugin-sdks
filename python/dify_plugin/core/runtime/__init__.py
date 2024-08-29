from typing import Optional

from dify_plugin.config.config import InstallMethod
from concurrent.futures import ThreadPoolExecutor

from dify_plugin.core.runtime.requests.storage import StorageRequest
from dify_plugin.core.server.__base.request_reader import RequestReader
from dify_plugin.core.server.__base.response_writer import ResponseWriter
from dify_plugin.core.runtime.requests.app.chat import ChatAppRequest
from dify_plugin.core.runtime.requests.app.completion import CompletionAppRequest
from dify_plugin.core.runtime.requests.app.workflow import WorkflowAppRequest
from dify_plugin.core.runtime.requests.model.llm import LLMRequest
from dify_plugin.core.runtime.requests.model.moderation import ModerationRequest
from dify_plugin.core.runtime.requests.model.rerank import RerankRequest
from dify_plugin.core.runtime.requests.model.speech2text import Speech2TextRequest
from dify_plugin.core.runtime.requests.model.text_embedding import TextEmbeddingRequest
from dify_plugin.core.runtime.requests.model.tts import TTSRequest
from dify_plugin.core.runtime.requests.tool import ToolRequest
from dify_plugin.core.runtime.requests.workflow_node.knowledge_retrieval import KnowledgeRetrievalNodeRequest
from dify_plugin.core.runtime.requests.workflow_node.parameter_extractor import ParameterExtractorNodeRequest
from dify_plugin.core.runtime.requests.workflow_node.question_classifier import QuestionClassifierNodeRequest
from dify_plugin.core.server.tcp.request_reader import TCPReaderWriter


class ModelRequests:
    def __init__(self, session: "Session") -> None:
        self.llm = LLMRequest(session)
        self.text_embedding = TextEmbeddingRequest(session)
        self.rerank = RerankRequest(session)
        self.speech2text = Speech2TextRequest(session)
        self.tts = TTSRequest(session)
        self.moderation = ModerationRequest(session)


class AppRequests:
    def __init__(self, session: "Session"):
        self.chat = ChatAppRequest(session)
        self.completion = CompletionAppRequest(session)
        self.workflow = WorkflowAppRequest(session)


class WorkflowNodeRequests:
    def __init__(self, session: "Session"):
        self.question_classifier = QuestionClassifierNodeRequest(session)
        self.parameter_extractor = ParameterExtractorNodeRequest(session)
        self.knowledge_retrieval = KnowledgeRetrievalNodeRequest(session)


class Session:
    # class variable to store all sessions
    _session_pool: set["Session"] = set()

    def __init__(
        self,
        session_id: str,
        executor: ThreadPoolExecutor,
        reader: RequestReader,
        writer: ResponseWriter,
        install_method: Optional[InstallMethod] = None,
        dify_plugin_daemon_url: Optional[str] = None,
    ) -> None:
        # current session id
        self.session_id: str = session_id

        # add current session to session pool
        self._session_pool.add(self)

        # thread pool executor
        self._executor: ThreadPoolExecutor = executor

        # reader and writer
        self.reader: RequestReader = reader
        self.writer: ResponseWriter = writer

        # install method
        self.install_method: Optional[InstallMethod] = install_method

        # dify plugin daemon url
        self.dify_plugin_daemon_url: Optional[str] = dify_plugin_daemon_url

        # register request handlers
        self._register_request_handlers()
    
    def _register_request_handlers(self) -> None:
        self.model = ModelRequests(self)
        self.tool = ToolRequest(self)
        self.app = AppRequests(self)
        self.workflow_node = WorkflowNodeRequests(self)
        self.storage = StorageRequest(self)

    @classmethod
    def empty_session(cls) -> "Session":
        return cls(
            session_id="",
            executor=ThreadPoolExecutor(),
            reader=TCPReaderWriter(host="", port=0, key=""),
            writer=TCPReaderWriter(host="", port=0, key=""),
            install_method=None,
            dify_plugin_daemon_url=None,
        )

    def __del__(self) -> None:
        self._session_pool.remove(self)

    def close(self) -> None:
        self._session_pool.remove(self)

    @classmethod
    def get_session(cls, session_id: str) -> "Session | None":
        for session in cls._session_pool:
            if session.session_id == session_id:
                return session
        return None
