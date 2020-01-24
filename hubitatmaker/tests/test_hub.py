import asyncio
import json
import sys
from os.path import dirname, join
from typing import Any, Coroutine, Dict, List
from unittest import TestCase
from unittest.mock import patch

from hubitatmaker.hub import Hub, InvalidConfig, NotReady

with open(join(dirname(__file__), "hub_edit.html")) as f:
    hub_edit_page = f.read()

with open(join(dirname(__file__), "devices.json")) as f:
    devices = f.read()


def run(cr: Coroutine) -> Any:
    return asyncio.get_event_loop().run_until_complete(cr)


class FakeResponse:
    def __init__(self, status=200, text: str = ""):
        self.status = status
        self._text = text

    async def json(self):
        return json.loads(self._text)

    async def text(self):
        return self._text


requests: List[Dict[str, Any]] = []


class fake_request:
    def __init__(self, method: str, url: str, **kwargs: Any):
        data = kwargs

        if url.endswith("/hub/edit"):
            self.response = FakeResponse(text=hub_edit_page)
        elif url.endswith("/devices"):
            self.response = FakeResponse(text=devices)
        else:
            self.response = FakeResponse(text="{}")

        requests.append({"method": method, "url": url, "data": kwargs})

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc, tb):
        pass


class TestHub(TestCase):
    def setUp(self):
        requests = []

    def test_hub_checks_arguments(self) -> None:
        """The hub should check for its required inputs."""
        self.assertRaises(InvalidConfig, Hub, "", "1234", "token")
        self.assertRaises(InvalidConfig, Hub, "1.2.3.4", "", "token")
        self.assertRaises(InvalidConfig, Hub, "1.2.3.4", "1234", "")
        Hub("1.2.3.4", "1234", "token")

    def test_connection_required(self) -> None:
        """Some property and method accesses should fail without a connection."""
        hub = Hub("1.2.3.4", "1234", "token")
        self.assertRaises(NotReady, getattr, hub, "devices")
        self.assertRaises(NotReady, getattr, hub, "hw_version")
        self.assertRaises(NotReady, getattr, hub, "id")
        self.assertRaises(NotReady, getattr, hub, "mac")
        self.assertRaises(NotReady, getattr, hub, "sw_version")
        self.assertRaises(NotReady, hub.get_device_attribute, "foo", "bar")

    def test_hub_name(self) -> None:
        """A hub should return its name."""
        hub = Hub("1.2.3.4", "1234", "token")
        self.assertEqual(hub.name, "Hubitat Elevation")

    @patch("aiohttp.request", new=fake_request)
    def test_connect(self):
        """connect() should request data from the Hubitat hub."""
        hub = Hub("1.2.3.4", "1234", "token")
        run(hub.connect())
        self.assertGreaterEqual(len(requests), 2)
        self.assertRegex(requests[0]["url"], "/hub/edit$")
        self.assertRegex(requests[1]["url"], "devices$")

    @patch("aiohttp.request", new=fake_request)
    def test_info_parsed(self):
        """Connected hub should have parsed Hubitat info."""
        hub = Hub("1.2.3.4", "1234", "token")
        run(hub.connect())
        self.assertEqual(hub.id, "1234abcd-1234-abcd-1234-abcd1234abcd")
        self.assertEqual(hub.mac, "12:34:56:78:9A:BC")

    @patch("aiohttp.request", new=fake_request)
    def test_devices_loaded(self):
        """Connected hub should have parsed device info."""
        hub = Hub("1.2.3.4", "1234", "token")
        run(hub.connect())
        self.assertEqual(len(hub.devices), 9)
