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
        """Some property and method accesses return unknown without a connection."""
        hub = Hub("1.2.3.4", "1234", "token")
        self.assertEqual(list(hub.devices), [])
        self.assertEqual(hub.hw_version, "unknown")
        self.assertEqual(hub.mac, "unknown")
        self.assertEqual(hub.sw_version, "unknown")
        hub.get_device_attribute("foo", "bar")

    def test_hub_name(self) -> None:
        """A hub should return its name."""
        hub = Hub("1.2.3.4", "1234", "token")
        self.assertEqual(hub.name, "Hubitat Elevation")

    def test_hub_id(self) -> None:
        """A hub should return its id."""
        hub = Hub("1.2.3.4", "1234", "token")
        self.assertEqual(hub.id, "1.2.3.4::1234")

    @patch("aiohttp.request", new=fake_request)
    def test_start(self):
        """start() should request data from the Hubitat hub."""
        hub = Hub("1.2.3.4", "1234", "token")
        run(hub.start())
        self.assertGreaterEqual(len(requests), 2)
        self.assertRegex(requests[0]["url"], "/hub/edit$")
        self.assertRegex(requests[1]["url"], "devices$")

    @patch("aiohttp.request", new=fake_request)
    def test_info_parsed(self):
        """Started hub should have parsed Hubitat info."""
        hub = Hub("1.2.3.4", "1234", "token")
        run(hub.start())
        self.assertEqual(hub.id, "1.2.3.4::1234")
        self.assertEqual(hub.mac, "12:34:56:78:9A:BC")

    @patch("aiohttp.request", new=fake_request)
    def test_devices_loaded(self):
        """Started hub should have parsed device info."""
        hub = Hub("1.2.3.4", "1234", "token")
        run(hub.start())
        self.assertEqual(len(hub.devices), 9)

    @patch("aiohttp.request", new=fake_request)
    def test_process_event(self):
        """Started hub should process a device event."""
        hub = Hub("1.2.3.4", "1234", "token")
        run(hub.start())
        attr = hub.get_device_attribute("176", "switch")
        self.assertEqual(attr["currentValue"], "off")

        hub.process_event(events[0])

        attr = hub.get_device_attribute("176", "switch")
        self.assertEqual(attr["currentValue"], "on")

    @patch("aiohttp.request", new=fake_request)
    @patch("hubitatmaker.server.start_server")
    def test_start_server(self, mock_start_server):
        """Hub should start a server when asked to."""
        hub = Hub("1.2.3.4", "1234", "token", True)
        run(hub.start())
        self.assertTrue(mock_start_server.called)

    @patch("aiohttp.request", new=fake_request)
    @patch("hubitatmaker.server.stop_server")
    @patch("hubitatmaker.server.start_server")
    def test_stop_server(self, mock_start_server, mock_stop_server):
        """Hub should stop a server when stopped."""
        mock_start_server.return_value = FakeServer()
        hub = Hub("1.2.3.4", "1234", "token", True)
        run(hub.start())
        self.assertTrue(mock_start_server.called)
        self.assertFalse(mock_stop_server.called)
        hub.stop()
        self.assertTrue(mock_stop_server.called)
