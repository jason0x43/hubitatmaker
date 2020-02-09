"""Hubitat API."""
import re
import socket
from contextlib import contextmanager
from functools import wraps
from logging import getLogger
from typing import Any, Callable, Dict, List, Optional, Union, ValuesView, cast
from urllib.parse import quote, urlparse

import aiohttp
import getmac
from bs4 import BeautifulSoup

from . import server
from .error import (
    InvalidAttribute,
    InvalidConfig,
    InvalidInfo,
    InvalidToken,
    RequestError,
)

_LOGGER = getLogger(__name__)

Listener = Callable[[], None]


class Hub:
    """A representation of a Hubitat hub.

    This class downloads initial device data from a Hubitat hub and waits for the 
    hub to push it state updates for devices. This means that the class must be
    able to receive update events. There are two ways to handle this: by relying on external code to pass in update events via this class's 
    """

    api_url: str
    app_id: str
    host: str
    scheme: str
    token: str

    _server: server.Server

    def __init__(self, host: str, app_id: str, access_token: str, port: int = None):
        """Initialize a Hubitat hub interface.

        host:
          The URL of the host to connect to (e.g., http://10.0.1.99), or just
          the host name/address. If only a name or address are provided, http
          is assumed.
        app_id:
          The ID of the Maker API instance this interface should use
        access_token:
          The access token for the Maker API instance
        port:
          The port to listen on for events (optional). Defaults to a random open port.
        """
        if not host or not app_id or not access_token:
            raise InvalidConfig()

        host_url = urlparse(host)

        self.scheme = host_url.scheme or "http"
        self.host = host_url.netloc or host_url.path
        self.port = port
        self.app_id = app_id
        self.token = access_token
        self.base_url = f"{self.scheme}://{self.host}"
        self.api_url = f"{self.base_url}/apps/api/{app_id}"
        self.mac = _get_mac_address(self.host)

        self._devices: Dict[str, Dict[str, Any]] = {}
        self._listeners: Dict[str, List[Listener]] = {}

        _LOGGER.info("Created hub %s", self)

    def __repr__(self) -> str:
        """Return a string representation of this hub."""
        return f"<Hub host={self.host} app_id={self.app_id}>"

    @property
    def devices(self) -> ValuesView[Dict[str, Any]]:
        """Return a list of devices managed by the Hubitat hub."""
        return self._devices.values()

    def add_device_listener(self, device_id: str, listener: Listener):
        """Listen for updates for a particular device."""
        if device_id not in self._listeners:
            self._listeners[device_id] = []
        self._listeners[device_id].append(listener)

    def remove_device_listeners(self, device_id: str):
        """Remove all listeners for a particular device."""
        self._listeners[device_id] = []

    def device_has_attribute(self, device_id: str, attr_name: str):
        """Return True if the given device has the given attribute."""
        state = self._devices[device_id]
        for attr in state["attributes"]:
            if attr["name"] == attr_name:
                return True
        return False

    async def check_config(self) -> None:
        """Verify that the hub is accessible.

        This method will raise a ConnectionError if there was a problem
        communicating with the hub.
        """
        try:
            await self._check_api()
        except aiohttp.ClientError as e:
            raise ConnectionError(str(e))

    async def start(self) -> None:
        """Download initial state data, and start an event server if requested.

        Hub and device data will not be available until this method has
        completed. Methods that rely on that data will raise an error if called
        before this method has completed.
        """

        try:
            await self._start_server()
            await self._load_devices()
            _LOGGER.debug("Connected to Hubitat hub at %s", self.host)
        except aiohttp.ClientError as e:
            raise ConnectionError(str(e))

    def stop(self) -> None:
        """Remove all listeners and stop the event server (if running)."""
        if self._server:
            _LOGGER.debug("stopping event server")
            self._server.stop()
            self._server = None
        self._listeners = {}

    def get_device_attribute(
        self, device_id: str, attr_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get an attribute value for a specific device."""
        state = self._devices.get(device_id)
        if state:
            for attr in state["attributes"]:
                if attr["name"] == attr_name:
                    return attr
        return None

    async def refresh_device(self, device_id: str):
        """Refresh a device's state."""
        await self._load_device(device_id, force_refresh=True)

    async def send_command(
        self, device_id: str, command: str, arg: Optional[Union[str, int]]
    ):
        """Send a device command to the hub."""
        path = f"devices/{device_id}/{command}"
        if arg:
            path += f"/{arg}"
        return await self._api_request(path)

    async def set_event_url(self, event_url: str):
        """Set the URL that Hubitat will POST device events to."""
        _LOGGER.info("setting event update URL to %s", event_url)
        url = quote(str(event_url), safe="")
        await self._api_request(f"postURL/{url}")

    def process_event(self, event: Dict[str, Any]):
        """Process an event received from the hub."""
        try:
            content = event["content"]
            _LOGGER.debug(
                "received event for for %(displayName)s (%(deviceId)s) - %(name)s -> %(value)s",
                content,
            )
        except KeyError:
            _LOGGER.warning("received invalid event: %s", event)
            return

        device_id = content["deviceId"]
        self._update_device_attr(device_id, content["name"], content["value"])
        if device_id in self._listeners:
            for listener in self._listeners[device_id]:
                listener()

    async def set_port(self, port: int) -> None:
        self.port = port
        if self._server:
            self._server.stop()
        await self._start_server()

    async def _check_api(self):
        """Check for api access.

        An error will be raised if a test API request fails.
        """
        await self._api_request("devices")

    def _update_device_attr(
        self, device_id: str, attr_name: str, value: Union[int, str]
    ):
        """Update a device attribute value."""
        _LOGGER.debug("Updating %s of %s to %s", attr_name, device_id, value)
        try:
            state = self._devices[device_id]
        except KeyError:
            _LOGGER.warning("Tried to update unknown device %s", device_id)
            return

        for attr in state["attributes"]:
            if attr["name"] == attr_name:
                attr["currentValue"] = value
                return

        # If we weren't able to set the attribute, this device doesn't
        # understand that attribute
        raise InvalidAttribute(f"Device {device_id} has no attribute {attr_name}")

    async def _load_devices(self, force_refresh=False) -> None:
        """Load the current state of all devices."""
        if force_refresh or len(self._devices) == 0:
            devices = await self._api_request("devices")
            _LOGGER.debug("Loaded device list")

            # load devices sequentially to avoid overloading the hub
            for dev in devices:
                await self._load_device(dev["id"], force_refresh)

    async def _load_device(self, device_id: str, force_refresh=False) -> None:
        """Return full info for a specific device."""
        if force_refresh or device_id not in self._devices:
            _LOGGER.debug("Loading device %s", device_id)
            json = await self._api_request(f"devices/{device_id}")
            try:
                self._devices[device_id] = json
            except Exception as e:
                _LOGGER.error("Invalid device info: %s", json)
                raise e
            _LOGGER.debug("Loaded device %s", device_id)

    async def _api_request(self, path: str, method="GET"):
        """Make a Maker API request."""
        params = {"access_token": self.token}
        async with aiohttp.request(
            method, f"{self.api_url}/{path}", params=params
        ) as resp:
            if resp.status >= 400:
                if resp.status == 401:
                    raise InvalidToken()
                else:
                    raise RequestError(resp)
            json = await resp.json()
            if "error" in json and json["error"]:
                raise RequestError(resp)
            return json

    async def _start_server(self) -> None:
        """Start an event listener server."""
        # First, figure out what address to listen on. Open a connection to
        # the Hubitat hub and see what address it used. This assumes this
        # machine and the Hubitat hub are on the same network.
        with _open_socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect((self.host, 80))
            address = s.getsockname()[0]

        self._server = server.create_server(self.process_event, address, self.port or 0)
        self._server.start()
        _LOGGER.debug("listening on %s:%d", address, self._server.port)

        await self.set_event_url(self._server.url)


@contextmanager
def _open_socket(*args: Any, **kwargs: Any):
    """Open a socket as a context manager."""
    s = socket.socket(*args, **kwargs)
    try:
        yield s
    finally:
        s.close()


def _get_mac_address(host: str) -> str:
    """Return the mac address of a remote host."""
    if re.match("\d+\.\d+\.\d+\.\d+", host):
        return getmac.get_mac_address(ip=host)
    return getmac.get_mac_address(hostname=host)
