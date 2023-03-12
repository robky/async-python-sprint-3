import asyncio

import pytest

from client import Client
from server import Server


@pytest.fixture()
def server(event_loop, unused_tcp_port):
    server = Server(port=unused_tcp_port)
    cancel_handle = asyncio.ensure_future(
        server.listen(), loop=event_loop)
    event_loop.run_until_complete(asyncio.sleep(0.01))

    try:
        yield unused_tcp_port
    finally:
        cancel_handle.cancel()


@pytest.mark.asyncio
async def test_client(server, monkeypatch, capsys):
    async def fake_read_stdin(*args, **kwargs):
        await asyncio.sleep(0)

    client_one = Client(server_port=server)
    monkeypatch.setattr(client_one, "_read_stdin", fake_read_stdin)

    asyncio.create_task(client_one.start())
    await asyncio.sleep(0.1)
    captured = capsys.readouterr()
    assert captured.out == "Welcome. Enter your name:\n"
    name_one = "test_one"
    await client_one._send(name_one + "\n")
    await asyncio.sleep(0.1)
    captured = capsys.readouterr()
    assert captured.out == (f"Hello [{name_one}]. Enter /q to exit or enter /h"
                            f" if you need help.\n")

    client_two = Client(server_port=server)
    monkeypatch.setattr(client_two, "_read_stdin", fake_read_stdin)

    asyncio.create_task(client_two.start())
    await asyncio.sleep(0.1)
    captured = capsys.readouterr()
    assert captured.out == "Welcome. Enter your name:\n"
    name_two = "test_two"
    await client_two._send(name_two + "\n")
    await asyncio.sleep(0.1)
    captured = capsys.readouterr()
    assert captured.out == (
        f"Hello [{name_two}]. Enter /q to exit or enter /h if you need help.\n"
        f"[server] The new user [{name_two}] has just connected\n")

    message = "Hello my friend!\n"
    private_message = f"{name_two} {message}"
    await client_one._send("/p " + private_message)
    await asyncio.sleep(0.1)
    captured = capsys.readouterr()
    assert captured.out == f"[{name_one}] -> [{name_two}] {message}"

    await client_one._close()
    await client_two._close()
