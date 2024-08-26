from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from dify_plugin.config.config import InstallMethod
from dify_plugin.core.server.__base.request_reader import RequestReader
from dify_plugin.core.server.__base.response_writer import ResponseWriter


class Session:
    # class variable to store all sessions
    _session_pool = set["Session"]()
    _executor: ThreadPoolExecutor
    # current session id
    session_id: str
    # reader and writer
    reader: RequestReader
    writer: ResponseWriter
    # install method
    install_method: Optional[InstallMethod] = None
    # dify plugin daemon url
    dify_plugin_daemon_url: Optional[str] = None

    def __init__(
        self,
        session_id: str,
        executor: ThreadPoolExecutor,
        reader: RequestReader,
        writer: ResponseWriter,
        install_method: Optional[InstallMethod] = None,
        dify_plugin_daemon_url: Optional[str] = None,
    ):
        self.session_id = session_id
        self._session_pool.add(self)
        self._executor = executor
        self.reader = reader
        self.writer = writer
        self.install_method = install_method
        self.dify_plugin_daemon_url = dify_plugin_daemon_url

    def __del__(self):
        self._session_pool.remove(self)

    def close(self):
        self._session_pool.remove(self)

    @classmethod
    def get_session(cls, session_id: str):
        for session in cls._session_pool:
            if session.session_id == session_id:
                return session
        return None
