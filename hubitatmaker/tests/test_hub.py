import asyncio
import json
import re
import sys
from os.path import dirname, join
from typing import Any, Coroutine, Dict, List, cast
from unittest import TestCase
from unittest.mock import patch

from hubitatmaker.hub import Hub, InvalidConfig

with open(join(dirname(__file__), "hub_edit.html")) as f:
    hub_edit_page = f.read()

with open(join(dirname(__file__), "devices.json")) as f:
    devices = f.read()

with open(join(dirname(__file__), "device_details.json")) as f:
    device_details = json.loads(f.read())

with open(join(dirname(__file__), "events.json")) as f:
    events = json.loads(f.read())


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


class FakeServer:
    url = "http://localhost:9999"


requests: List[Dict[str, Any]] = []


class fake_request:
    def __init__(self, method: str, url: str, **kwargs: Any):
        data = kwargs

        if url.endswith("/hub/edit"):
            self.response = FakeResponse(text=hub_edit_page)
        elif url.endswith("/devices"):
            self.response = FakeResponse(text=devices)
        else:
            dev_match = re.match(".*/devices/(\\d+)$", url)
            if dev_match:
                dev_id = dev_match.group(1)
                self.response = FakeResponse(
                    text=json.dumps(device_details.get(dev_id, {}))
                )
            else:
                self.response = FakeResponse(text="{}")

        requests.append({"method": method, "url": url, "data": kwargs})

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc, tb):
        pass


def fake_get_mac_address(**kwargs: str):
    return "aa:bb:cc:dd:ee:ff"


class TestHub(TestCase):
    def setUp(self):
        requests = []

    def test_hub_checks_arguments(self) -> None:
        """The hub should check for its required inputs."""
        self.assertRaises(InvalidConfig, Hub, "", "1234", "token")
        self.assertRaises(InvalidConfig, Hub, "1.2.3.4", "", "token")
        self.assertRaises(InvalidConfig, Hub, "1.2.3.4", "1234", "")
        Hub("1.2.3.4", "1234", "token")

    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    def test_initial_values(self) -> None:
        """Hub properties should have expected initial values."""
        hub = Hub("1.2.3.4", "1234", "token")
        self.assertEqual(list(hub.devices), [])
        self.assertEqual(hub.mac, "aa:bb:cc:dd:ee:ff")

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_start_server(self, MockServer) -> None:
        """Hub should start a server when asked to."""
        hub = Hub("1.2.3.4", "1234", "token", True)
        run(hub.start())
        self.assertTrue(MockServer.called)

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_start(self, MockServer) -> None:
        """start() should request data from the Hubitat hub."""
        hub = Hub("1.2.3.4", "1234", "token")
        run(hub.start())
        # 33 requests - 1 to get device list, 32 to update devices
        self.assertEqual(len(requests), 33)
        self.assertRegex(requests[1]["url"], "devices$")
        self.assertRegex(requests[2]["url"], "devices/\d+$")
        self.assertRegex(requests[-1]["url"], "devices/\d+$")

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_stop_server(self, MockServer) -> None:
        """Hub should stop a server when stopped."""
        hub = Hub("1.2.3.4", "1234", "token", True)
        run(hub.start())
        self.assertTrue(MockServer.return_value.start.called)
        hub.stop()
        self.assertTrue(MockServer.return_value.stop.called)

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_devices_loaded(self, MockServer) -> None:
        """Started hub should have parsed device info."""
        hub = Hub("1.2.3.4", "1234", "token")
        run(hub.start())
        self.assertEqual(len(hub.devices), 9)

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_process_event(self, MockServer) -> None:
        """Started hub should process a device event."""
        hub = Hub("1.2.3.4", "1234", "token")
        run(hub.start())
        device = hub.devices["176"]
        attr = device.attributes["switch"]
        self.assertEqual(attr.value, "off")

        hub.process_event(events[0])

        attr = device.attributes["switch"]
        self.assertEqual(attr.value, "on")
