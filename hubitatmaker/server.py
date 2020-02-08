import asyncio
import threading
from typing import Any, Callable, Dict

from aiohttp import web

EventCallback = Callable[[Dict[str, Any]], None]


class Server:
    """A handle to a running server."""

    def __init__(self, handle_event: EventCallback, host: str, port: int):
        """Initialize a Server."""
        self.host = host
        self.port = port
        self.handle_event = handle_event
        self._main_loop = asyncio.get_running_loop()

    def start(self) -> None:
        """Start a new server running in a background thread."""
        app = web.Application()
        app.add_routes([web.post("/", self._handle_request)])
        self._runner = web.AppRunner(app)

        self._server_loop = asyncio.new_event_loop()
        t = threading.Thread(target=self._run)
        t.start()

    def stop(self) -> None:
        """Gracefully stop a running server."""
        # Call the server shutdown functions and wait for them to finish. These
        # must be called on the server thread's event loop.
        future = asyncio.run_coroutine_threadsafe(self._stop(), self._server_loop)
        future.result(5)

        # Stop the server thread's event loop
        self._server_loop.call_soon_threadsafe(self._server_loop.stop)

    async def _handle_request(self, request: web.Request) -> web.Response:
        """Handle an incoming request."""
        event = await request.json()
        # This handler will be called on the server thread. Call the external
        # handler on the app thread.
        self._main_loop.call_soon_threadsafe(self.handle_event, event)
        return web.Response(text="OK")

    def _run(self) -> None:
        """Execute the server in its own thread with its own event loop."""
        asyncio.set_event_loop(self._server_loop)
        self._server_loop.run_until_complete(self._runner.setup())
        site = web.TCPSite(self._runner, self.host, self.port)
        self._server_loop.run_until_complete(site.start())
        self._server_loop.run_forever()

    async def _stop(self) -> None:
        """Stop the server."""
        await self._runner.shutdown()
        await self._runner.cleanup()


def create_server(
    handle_event: EventCallback, host: str = "0.0.0.0", port: int = 0
) -> Server:
    """Create a new server."""
    return Server(handle_event, host, port)
