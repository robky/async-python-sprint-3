import asyncio
import os
import sys
from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass

from dotenv import load_dotenv

from logger_set import get_logger

load_dotenv()
SERVER_HOST = os.getenv('SERVER_HOST', "127.0.0.1")
SERVER_PORT = int(os.getenv('SERVER_PORT', 8000))

logger = get_logger("client")


@dataclass
class Client:
    server_host: str = SERVER_HOST
    server_port: int = SERVER_PORT
    _reader: StreamReader = None
    _writer: StreamWriter = None
    _client_is_work: bool = False

    async def _send(self, message: str = "") -> None:
        if not self._client_is_work:
            await self._close()
            return
        logger.debug(f"Send: {message.strip()}")
        try:
            self._writer.write(message.encode())
            await self._writer.drain()
        except Exception as e:
            logger.error(f"Dont sent message: {e}")
            await self._close()

    async def _read(self) -> None:
        while self._client_is_work:
            try:
                data = await self._reader.read(100)
            except ConnectionResetError:
                break
            if not data:
                break
            print(data.decode().strip())
        await self._close()

    async def _read_stdin(self) -> None:
        loop = asyncio.get_event_loop()
        while self._client_is_work:
            try:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                await self._send(line)
                if "/q" in line:
                    await self._close()
            except Exception as e:
                logger.error(f"Error input: {e}")
                raise e

    async def _open(self) -> None:
        self._reader, self._writer = await asyncio.open_connection(
            self.server_host, self.server_port
        )
        self._client_is_work = True

    async def _close(self) -> None:
        if self._client_is_work:
            self._writer.close()
            self._client_is_work = False

    async def start(self) -> None:
        await self._open()
        tasks = [
            self._read(),
            self._read_stdin(),
        ]
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error with the server: {e}")
        finally:
            logger.info("Close the connection")


if __name__ == "__main__":
    logger.info("Start program client")
    try:
        asyncio.run(Client().start())
    except Exception as e:
        logger.error(f"Lost connection with the server: {e}")
    finally:
        logger.info("Stop program client")
