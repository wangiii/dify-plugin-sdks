import httpx
from pydantic import BaseModel

from dify_plugin.file.constants import DIFY_FILE_IDENTITY


class File(BaseModel):
    dify_model_identity: str = DIFY_FILE_IDENTITY
    url: str

    _blob: bytes | None = None

    @property
    def blob(self) -> bytes:
        """
        Get the file content as a bytes object.

        If the file content is not loaded yet, it will be loaded from the URL and stored in the `_blob` attribute.
        """
        if self._blob is None:
            response = httpx.get(self.url)
            response.raise_for_status()
            self._blob = response.content

        assert self._blob is not None
        return self._blob
