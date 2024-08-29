from binascii import hexlify, unhexlify

from dify_plugin.core.entities.plugin.invocation import InvokeType
from dify_plugin.core.runtime.requests import DifyRequest


class StorageRequest(DifyRequest[dict]):
    def set(self, key: str, val: bytes) -> None:
        """
        set a value into persistence storage.
        """
        for data in self._backwards_invoke(
            InvokeType.STORAGE,
            dict,
            {"opt": "set", "key": key, "value": hexlify(val).decode()},
        ):
            if data["data"] == "ok":
                return

            raise Exception("unexpected data")

        Exception("no data found")

    def get(self, key: str) -> bytes:
        for data in self._backwards_invoke(
            InvokeType.STORAGE,
            dict,
            {
                "opt": "get",
                "key": key,
            },
        ):
            return unhexlify(data["data"])

        raise Exception("no data found")

    def delete(self, key: str) -> None:
        for data in self._backwards_invoke(
            InvokeType.STORAGE,
            dict,
            {
                "opt": "del",
                "key": key,
            },
        ):
            if data["data"] == "ok":
                return

            raise Exception("unexpected data")

        raise Exception("no data found")
