from pydantic import BaseModel
import requests
from dify_plugin.core.entities.invocation import InvokeType
from dify_plugin.core.runtime import BackwardsInvocation


class UploadFileResponse(BaseModel):
    id: str
    name: str
    size: int
    extension: str
    mime_type: str


class File(BackwardsInvocation[dict]):
    def upload(
        self, filename: str, content: bytes, mimetype: str
    ) -> UploadFileResponse:
        """
        Upload a file

        :param filename: file name
        :param content: file content
        :param mimetype: file mime type

        :return: file id
        """
        for response in self._backwards_invoke(
            InvokeType.UploadFile,
            dict,
            {
                "filename": filename,
                "mimetype": mimetype,
            },
        ):
            url = response.get("url")
            if not url:
                raise Exception("upload file failed, could not get signed url")

            response = requests.post(url, files={"file": (filename, content, mimetype)})
            if response.status_code != 201:
                raise Exception(
                    f"upload file failed, status code: {response.status_code}, response: {response.text}"
                )

            return UploadFileResponse(**response.json())

        raise Exception("upload file failed, empty response from server")
