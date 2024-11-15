from json import loads
import socket
import time
from typing import Callable, Generator, Optional

from gevent.select import select

from dify_plugin.core.entities.message import InitializeMessage

from ....core.entities.plugin.io import (
    PluginInStream,
    PluginInStreamEvent,
)
from ....core.server.__base.request_reader import RequestReader
from ....core.server.__base.response_writer import ResponseWriter

import logging

logger = logging.getLogger(__name__)


class TCPReaderWriter(RequestReader, ResponseWriter):
    def __init__(
        self,
        host: str,
        port: int,
        key: str,
        reconnect_attempts: int = 3,
        reconnect_timeout: int = 5,
        on_connected: Optional[Callable] = None,
    ):
        """
        Initialize the TCPStream and connect to the target, raise exception if connection failed
        """
        self.host = host
        self.port = port
        self.key = key
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_timeout = reconnect_timeout
        self.alive = False
        self.on_connected = on_connected

    def launch(self):
        """
        Launch the connection
        """
        self._launch()

    def close(self):
        """
        Close the connection
        """
        if self.alive:
            self.sock.close()
            self.alive = False

    def write(self, data: str):
        if not self.alive:
            raise Exception("connection is dead")

        try:
            self.sock.sendall(data.encode())
        except Exception as e:
            logger.error(f"Failed to write data: {e}")
            self._launch()

    def done(self):
        pass

    def _launch(self):
        """
        Connect to the target, try to reconnect if failed
        """
        attempts = 0
        while attempts < self.reconnect_attempts:
            try:
                self._connect()
                break
            except Exception as e:
                attempts += 1
                if attempts >= self.reconnect_attempts:
                    raise e

                time.sleep(self.reconnect_timeout)

    def _connect(self):
        """
        Connect to the target
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.alive = True
            handshake_message = InitializeMessage(
                type=InitializeMessage.Type.HANDSHAKE,
                data=InitializeMessage.Key(key=self.key).model_dump(),
            )
            self.sock.sendall(handshake_message.model_dump_json().encode() + b"\n")
            logger.info(f"\033[32mConnected to {self.host}:{self.port}\033[0m")
            if self.on_connected:
                self.on_connected()
            logger.info(f"Sent key to {self.host}:{self.port}")
        except socket.error as e:
            logger.error(f"\033[31mFailed to connect to {self.host}:{self.port}, {e}\033[0m")
            raise e

    def _read_stream(self) -> Generator[PluginInStream, None, None]:
        """
        Read data from the target
        """
        buffer = b""
        while self.alive:
            try:
                ready_to_read, _, _ = select([self.sock], [], [], 1)
                if not ready_to_read:
                    continue
                data = self.sock.recv(4096)
                if data == b"":
                    raise Exception("Connection is closed")
            except Exception as e:
                logger.error(f"\033[31mFailed to read data from {self.host}:{self.port}, {e}\033[0m")
                self.alive = False
                time.sleep(self.reconnect_timeout)
                self._launch()
                continue

            if not data:
                continue

            buffer += data

            # process line by line and keep the last line if it is not complete
            lines = buffer.split(b"\n")
            if len(lines) == 0:
                continue

            if lines[-1] != "":
                buffer = lines[-1]
            else:
                buffer = b""

            lines = lines[:-1]
            for line in lines:
                try:
                    data = loads(line)
                    yield PluginInStream(
                        session_id=data["session_id"],
                        event=PluginInStreamEvent.value_of(data["event"]),
                        data=data["data"],
                        reader=self,
                        writer=self,
                    )
                except Exception:
                    logger.error(f"\033[31mAn error occurred while parsing the data: {line}\033[0m")
