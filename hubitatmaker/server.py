import asyncio
import threading
from typing import Any, Callable, Dict

from aiohttp import web

EventCallback = Callable[[Dict[str, Any]], None]


class Server:
    """A handle to a running server."""

    _runner: web.AppRunner
    _loop: asyncio.AbstractEventLoop

    host: str
    port: int
    url: str

    def __init__(
        self,
        runner: web.AppRunner,
        loop: asyncio.AbstractEventLoop,
        host: str,
        port: int,
    ):
        self._runner = runner
        self._loop = loop
        self.host = host
        self.port = port
        self.url = f"http://{host}:{port}"


def create_server(
    handle_event: EventCallback, main_loop: asyncio.AbstractEventLoop
) -> web.AppRunner:
    """Create a new server."""

    async def handle_request(request: web.Request):
        event = await request.json()
        main_loop.call_soon_threadsafe(handle_event, event)
        return web.Response(text="OK")

    app = web.Application()
    app.add_routes([web.post("/", handle_request)])
    runner = web.AppRunner(app)
    return runner


def run_server(
    runner: web.AppRunner, loop: asyncio.AbstractEventLoop, host: str, port: int
) -> None:
    """Execute the server in its own event loop."""
    # create a new event loop for this thread
    asyncio.set_event_loop(loop)

    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, host, port)
    loop.run_until_complete(site.start())
    loop.run_forever()


def start_server(handle_event: EventCallback, host: str, port: int = 10191) -> Server:
    """Start a new server running in a background thread."""
    main_loop = asyncio.get_running_loop()
    server_loop = asyncio.new_event_loop()
    runner = create_server(handle_event, main_loop)
    t = threading.Thread(target=run_server, args=(runner, server_loop, host, port))
    t.start()
    return Server(runner, server_loop, host, port)


def stop_server(server: Server) -> None:
    """Stop a running server."""

    async def stop():
        await server._runner.shutdown()
        await server._runner.cleanup()

    # Call the server shutdown functions and wait for them to finish
    future = asyncio.run_coroutine_threadsafe(stop(), server._loop)
    future.result(5)

    # Stop the server thread's event loop
    server._loop.call_soon_threadsafe(server._loop.stop)
