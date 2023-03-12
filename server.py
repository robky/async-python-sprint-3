import os
from asyncio import StreamReader, StreamWriter, run, start_server
from collections import namedtuple
from dataclasses import dataclass, field

from dotenv import load_dotenv

from logger_set import get_logger

load_dotenv()
SERVER_HOST = os.getenv('SERVER_HOST', "127.0.0.1")
SERVER_PORT = int(os.getenv('SERVER_PORT', 8000))
SERVER_NAME = os.getenv('SERVER_NAME', "server")

CIRCLE_LIST_SIZE = 20

logger = get_logger(SERVER_NAME)

User = namedtuple("User", ["name", "address", "writer"])


@dataclass
class CircleList:
    size: int = CIRCLE_LIST_SIZE
    _head: int = 0
    _tail: int = -1
    _circle = []

    def add(self, value):
        if len(self._circle) < self.size:
            self._circle.append(value)
            self._tail += 1
            return
        self._tail = (self._tail + 1) % self.size
        self._circle[self._tail] = value
        if self._head == self._tail:
            self._head = (self._head + 1) % self.size

    def get(self):
        if self._tail < 0:
            return []
        index = self._head
        result = []
        while index != self._tail:
            result.append(self._circle[index])
            index = (index + 1) % self.size
        result.append(self._circle[self._tail])
        return result


@dataclass
class Server:
    host: str = SERVER_HOST
    port: int = SERVER_PORT
    _passport: dict[str, dict[int, StreamWriter]] = field(default_factory=dict)
    _last_messages: CircleList = CircleList()

    async def client_connected(
        self, reader: StreamReader, writer: StreamWriter
    ):
        _, address = writer.get_extra_info("peername")
        user = User(None, address, writer)
        logger.info(f"The new Client {user.address} is connected")
        encoding_err_msg = "Only utf-8 encoding is supported."
        not_send_msg = "The message has not been sent."

        while True:
            message = "Welcome. Enter your name:"
            await self._write(user, message)

            try:
                input_date = await reader.readline()
                user = user._replace(name=input_date.decode().strip())
                logger.info(
                    f"The Client {user.address} called himself [{user.name}]"
                )
                break
            except ConnectionResetError:
                await self._user_out(user)
                return
            except UnicodeDecodeError:
                await self._write(user, encoding_err_msg)

        message = (
            f"Hello [{user.name}]. Enter /q to exit or enter /h if you "
            f"need help."
        )
        await self._write(user, message)

        if user.name in self._passport:
            self._passport.get(user.name).update({user.address: user.writer})
        else:
            self._passport[user.name] = {user.address: user.writer}
            message = f"The new user [{user.name}] has just connected"
            await self._write_all(message, user)

        await self._write_last_messages(user)

        while True:
            try:
                input_date = await reader.readline()
            except ConnectionResetError:
                break
            if not input_date:
                break
            try:
                input_msg = input_date.decode().strip()
            except UnicodeDecodeError:
                await self._write(user, encoding_err_msg + not_send_msg)
                continue
            logger.debug(
                f"User [{user.name}]:{user.address} received: {input_msg}"
            )
            if "/" in input_msg:
                await self._command(user, input_msg)
            else:
                await self._write_all(input_msg, user, from_server=False)

        await self._user_out(user)

    async def _write(self, user: User, message: str) -> bool:
        message = message.strip() + "\r\n"
        try:
            user.writer.write(message.encode())
            await user.writer.drain()
        except ConnectionResetError:
            await self._user_out(user)
            return False
        return True

    async def _write_last_messages(self, user: User) -> None:
        messages = self._last_messages.get()
        for message in messages:
            await self._write(user, message)

    async def _write_from_server(self, user: User, message: str) -> None:
        message = f"[{SERVER_NAME}] {message}"
        await self._write(user, message)

    async def _write_all(
        self, message: str, except_for: User = None, from_server: bool = True
    ):
        if from_server:
            name = SERVER_NAME
        else:
            name = except_for.name
        message = f"[{name}] {message.strip()}"
        if from_server is False:
            self._last_messages.add(message)
        for user_name, client_writers in self._passport.items():
            for address, writer in client_writers.items():
                if except_for and except_for.address == address:
                    continue
                await self._write(User(user_name, address, writer), message)

    async def _write_private(
        self, user_from: User, user_to: str, message: str
    ) -> bool:
        if user_to not in self._passport:
            message_error = f"User {user_to} not found"
            await self._write(user_from, message_error)
            return False
        user_to_writers = self._passport[user_to]
        user_to_writers.update(self._passport.get(user_from.name, {}))
        number_of_sent = 0
        message = f"[{user_from.name}] -> [{user_to}] {message}"
        for address, writer in user_to_writers.items():
            if address == user_from.address:
                continue
            result = await self._write(User(user_to, address, writer), message)
            if result:
                number_of_sent += 1
        return True if number_of_sent else False

    async def _command(self, user: User, message: str) -> None:
        index = message.find("/") + 1
        command = message[index: index + 1].lower()
        message = message[index + 1:]
        error_message = "Input error"
        if not command:
            await self._write_from_server(user, error_message)
            return
        match command:
            case "q":
                await self._user_out(user)
            case "h":
                mes = [
                    "Possible actions are described below:",
                    "/h - The help (this messages).",
                    "/q - To exit.",
                    "/p <user> <message> - Private message for the <user>",
                ]
                for send_message in mes:
                    await self._write_from_server(user, send_message)
            case "p":
                parts_messages = message.split()
                if len(parts_messages) < 2:
                    await self._write_from_server(user, error_message)
                    return
                user_to = parts_messages[0]
                if user_to == user.name:
                    msg_err_yourself = "You can't send a message to yourself!"
                    await self._write(user, msg_err_yourself)
                    return
                send_message = " ".join(parts_messages[1:])
                result = await self._write_private(user, user_to, send_message)
                if result:
                    logger.debug(
                        f"User [{user.name}]:{user.address} received to "
                        f"[{user_to}]: {send_message}"
                    )
                else:
                    error_message = (
                        f"The message for the [{user_to}] was " f"not sent"
                    )
                    await self._write_from_server(user, error_message)
                    logger.debug(
                        f"User [{user.name}]:{user.address} do not received "
                        f"to [{user_to}]: {send_message}"
                    )
            case _:
                error_message = "Unknown command or input error"
                await self._write_from_server(user, error_message)

    async def _user_out(self, user: User) -> None:
        user.writer.close()
        user_clients = self._passport.get(user.name)
        if user_clients is None:
            return
        if user.address in user_clients:
            del self._passport[user.name][user.address]
            logger.info(
                f"Stop serving [{user.name}] for address: {user.address}"
            )
        if len(self._passport.get(user.name)) == 0:
            del self._passport[user.name]
            message = f"The user [{user.name}] has left"
            logger.info(f"The user: [{user.name}] quit")
            await self._write_all(message, user)

    async def listen(self):
        srv = await start_server(self.client_connected, self.host, self.port)
        logger.info(
            f"The server is running and waiting for connection on "
            f"{self.host}:{self.port}"
        )

        async with srv:
            await srv.serve_forever()


if __name__ == "__main__":
    logger.info("Start program server")
    run(Server().listen())
