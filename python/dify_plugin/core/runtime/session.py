from concurrent.futures import ThreadPoolExecutor


class Session:
    _session_pool = set["Session"]()
    session_id: str
    executor: ThreadPoolExecutor

    def __init__(self, session_id: str, executor: ThreadPoolExecutor) -> None:
        self.session_id = session_id
        self._session_pool.add(self)
        self.executor = executor

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
