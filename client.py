import asyncio
import logging
import sys
from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d [%(name)s]: %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
)
logger = logging.getLogger("client")
# stop_event = asyncio.Event()


@dataclass
class Client:
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    _reader: StreamReader = None
    _writer: StreamWriter = None
    _client_is_work: bool = False

    async def _send(self, message: str = "") -> None:
        if not self._client_is_work:
            await self._close()
            return
        logger.debug(f"Send: {message}")
        # message += "\n"
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

    # async def _read_starter(self):
    #     while self._client_is_work:
    #         await asyncio.wait([self._read_stdin2()], timeout=5.0)
    #
    # async def _read_stdin2(self):
    #     rand_delay = 1.5
    #     print(f"Generated rand {rand_delay}...")
    #     await asyncio.sleep(rand_delay)
    #     print(f"Coro finished {rand_delay}...")
    #     return rand_delay

    async def _read_stdin(self) -> None:
        loop = asyncio.get_event_loop()
        while self._client_is_work:
            # try:
            #     future = loop.run_in_executor(None, sys.stdin.readline)
            #     line = await asyncio.wait_for(future, 5, loop=loop)
            # except asyncio.futures.TimeoutError:
            #     logger.debug("Timeout")
            #     continue

            line = await loop.run_in_executor(None, sys.stdin.readline)
            await self._send(line)

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
            # self._read_starter()
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
