import asyncio
import json
from os.path import dirname, join
import re
from typing import Any, Coroutine, Dict, List, Union
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import unquote

from hubitatmaker.const import HSM_DISARM
from hubitatmaker.hub import Hub, InvalidConfig

hub_edit_page: str
devices: Dict[str, Any]
device_details: Dict[str, Any]
events: Dict[str, Dict[str, Any]]
modes: List[Dict[str, Any]]
hsm: Dict[str, str]


def load_data():
    global hub_edit_page
    global devices
    global device_details
    global events
    global modes
    global hsm

    with open(join(dirname(__file__), "hub_edit.html")) as f:
        hub_edit_page = f.read()

    with open(join(dirname(__file__), "devices.json")) as f:
        devices = json.loads(f.read())

    with open(join(dirname(__file__), "device_details.json")) as f:
        device_details = json.loads(f.read())

    with open(join(dirname(__file__), "events.json")) as f:
        events = json.loads(f.read())

    with open(join(dirname(__file__), "modes.json")) as f:
        modes = json.loads(f.read())

    with open(join(dirname(__file__), "hsm.json")) as f:
        hsm = json.loads(f.read())


def wait_for(cr: Coroutine) -> Any:
    return asyncio.get_event_loop().run_until_complete(cr)


class FakeResponse:
    def __init__(self, status=200, data: Union[str, Dict, List] = ""):
        self.status = status
        self._data = data

    async def json(self):
        if isinstance(self._data, str):
            return json.loads(self._data)
        return self._data

    async def text(self):
        if isinstance(self._data, str):
            return self._data
        return json.dumps(self._data)


class FakeServer:
    url = "http://localhost:9999"


requests: List[Dict[str, Any]] = []


class fake_request:
    def __init__(self, method: str, url: str, **kwargs: Any):
        if url.endswith("/hub/edit"):
            self.response = FakeResponse(data=hub_edit_page)
        elif url.endswith("/devices"):
            self.response = FakeResponse(data=devices)
        elif url.endswith("/modes"):
            self.response = FakeResponse(data=modes)
        elif url.endswith("/hsm"):
            self.response = FakeResponse(data=hsm)
        elif re.match(".*/modes/(\\d+)$", url):
            mode_match = re.match(".*/modes/(\\d+)$", url)
            mode_id = mode_match.group(1)
            valid_mode = False
            for mode in modes:
                if mode["id"] == mode_id:
                    valid_mode = True
                    break
            if valid_mode:
                for mode in modes:
                    if mode["id"] == mode_id:
                        mode["active"] = True
                    else:
                        mode["active"] = False
            self.response = FakeResponse(data=modes)
        elif re.match(".*/hsm/(\\w+)$", url):
            hsm_match = re.match(".*/hsm/(\\w+)$", url)
            hsm_mode = hsm_match.group(1)
            new_mode = "disarmed"
            if hsm_mode == HSM_DISARM:
                new_mode = "disarmed"
            self.response = FakeResponse(data={"hsm": new_mode})
        elif re.match(".*/devices/(\\d+)$", url):
            dev_match = re.match(".*/devices/(\\d+)$", url)
            dev_id = dev_match.group(1)
            self.response = FakeResponse(data=device_details.get(dev_id, {}))
        else:
            self.response = FakeResponse(data="{}")

        requests.append({"method": method, "url": url, "data": kwargs})

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc, tb):
        pass


def fake_get_mac_address(**kwargs: str):
    return "aa:bb:cc:dd:ee:ff"


class TestHub(TestCase):
    def setUp(self):
        global requests
        requests = []
        load_data()

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
        wait_for(hub.start())
        self.assertTrue(MockServer.called)

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_start(self, MockServer) -> None:
        """start() should request data from the Hubitat hub."""
        hub = Hub("1.2.3.4", "1234", "token")
        wait_for(hub.start())
        # 13 requests:
        #   0: set event URL
        #   1: request modes
        #   2: request hsm status
        #   3: request devices
        #   4...: request device details
        self.assertEqual(len(requests), 13)
        self.assertRegex(requests[1]["url"], "modes$")
        self.assertRegex(requests[2]["url"], "hsm$")
        self.assertRegex(requests[3]["url"], "devices$")
        self.assertRegex(requests[4]["url"], r"devices/\d+$")
        self.assertRegex(requests[-1]["url"], r"devices/\d+$")

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_default_event_url(self, MockServer) -> None:
        """Default event URL should be server URL."""
        MockServer.return_value.url = "http://127.0.0.1:81"
        hub = Hub("1.2.3.4", "1234", "token")
        wait_for(hub.start())
        url = unquote(requests[0]["url"])
        self.assertRegex(url, r"http://127.0.0.1:81$")

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_custom_event_url(self, MockServer) -> None:
        """Event URL should be configurable."""
        MockServer.return_value.url = "http://127.0.0.1:81"
        hub = Hub("1.2.3.4", "1234", "token", event_url="http://foo.local")
        wait_for(hub.start())
        url = unquote(requests[0]["url"])
        self.assertRegex(url, r"http://foo\.local$")

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_stop_server(self, MockServer) -> None:
        """Hub should stop a server when stopped."""
        hub = Hub("1.2.3.4", "1234", "token", True)
        wait_for(hub.start())
        self.assertTrue(MockServer.return_value.start.called)
        hub.stop()
        self.assertTrue(MockServer.return_value.stop.called)

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_devices_loaded(self, MockServer) -> None:
        """Started hub should have parsed device info."""
        hub = Hub("1.2.3.4", "1234", "token")
        wait_for(hub.start())
        self.assertEqual(len(hub.devices), 9)

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_process_event(self, MockServer) -> None:
        """Started hub should process a device event."""
        hub = Hub("1.2.3.4", "1234", "token")
        wait_for(hub.start())
        device = hub.devices["176"]
        attr = device.attributes["switch"]
        self.assertEqual(attr.value, "off")

        hub._process_event(events["device"])

        attr = device.attributes["switch"]
        self.assertEqual(attr.value, "on")

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_process_mode_event(self, MockServer) -> None:
        """Started hub should emit mode events."""
        hub = Hub("1.2.3.4", "1234", "token")
        wait_for(hub.start())

        handler_called = False

        def listener(_: Any):
            nonlocal handler_called
            handler_called = True

        hub._process_event(events["mode"])
        self.assertFalse(handler_called)

        hub.add_mode_listener(listener)
        hub._process_event(events["mode"])
        self.assertTrue(handler_called)

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_process_hsm_event(self, MockServer) -> None:
        """Started hub should emit HSM events."""
        hub = Hub("1.2.3.4", "1234", "token")
        wait_for(hub.start())

        handler_called = False

        def listener(_: Any):
            nonlocal handler_called
            handler_called = True

        hub._process_event(events["hsm"])
        self.assertFalse(handler_called)

        hub.add_hsm_listener(listener)
        hub._process_event(events["hsm"])
        self.assertTrue(handler_called)

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_process_other_event(self, MockServer) -> None:
        """Started hub should ignore non-device, non-mode events."""
        hub = Hub("1.2.3.4", "1234", "token")
        wait_for(hub.start())
        device = hub.devices["176"]
        attr = device.attributes["switch"]
        self.assertEqual(attr.value, "off")

        hub._process_event(events["other"])

        attr = device.attributes["switch"]
        self.assertEqual(attr.value, "off")

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_process_set_hsm(self, MockServer) -> None:
        """Started hub should allow mode to be updated."""
        hub = Hub("1.2.3.4", "1234", "token")
        wait_for(hub.start())
        self.assertEqual(hub.hsm_status, "armedAway")
        wait_for(hub.set_hsm(HSM_DISARM))
        self.assertRegex(requests[-1]["url"], f"hsm/{HSM_DISARM}$")

        hub._process_event(events["hsm"])
        self.assertEqual(hub.hsm_status, "armedAway")

    @patch("aiohttp.request", new=fake_request)
    @patch("getmac.get_mac_address", new=fake_get_mac_address)
    @patch("hubitatmaker.server.Server")
    def test_process_set_mode(self, MockServer) -> None:
        """Started hub should allow mode to be updated."""
        hub = Hub("1.2.3.4", "1234", "token")
        wait_for(hub.start())
        self.assertEqual(hub.mode, "Day")
        wait_for(hub.set_mode("Evening"))
        self.assertRegex(requests[-1]["url"], "modes/2$")

        hub._process_event(events["mode"])
        self.assertEqual(hub.mode, "Evening")
