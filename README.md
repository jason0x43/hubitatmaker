# hubitatmaker

This library provides an async Python interface for Hubitat Elevation’s Maker API. It is primarily intended for use with Home Assistant.

## Features

The main public API in hubitatmaker is the Hub class. This class represents a Maker API instance on a Hubitat hub. When started, a Hub instance will determine the Hubitat hub's MAC address and and download a list of available devices and details about each device.

The Hub instance caches state information about each device. It relies on events posted from the Hubitat hub to update its internal state. Each Hub instance starts a new event listener server to receive events from the hub, and updates the Maker API instance with an accessible URL for this listener server.

## Basic usage

```python
import asyncio
from hubitatmaker import Hub

async def print_devices(host, app_id, token):
	hub = Hub(host, app_id, token)
	await hub.start()
	for device in hub.devices:
		print(f"{device.name} ({device.id})")

if __name__ == '__main__':
	host = 'http://10.0.1.99'
	app_id = '1234'
	token = '<apitoken>'
	asyncio.run(print_devices(host, app_id, token))
```

## API

### Hub

#### Properties

##### devices

The list of devices managed by the hub.

##### mode

The hub's mode (e.g., "Away", "Day", "Night").

##### modes

The available hub modes.

##### hsm_status

The hub's HSM status (e.g., "armedAway", "disarmed"). See [this post](https://community.hubitat.com/t/hubitat-safety-monitor-api/934/3) for more information.

#### Methods

##### \_\_init\_\_(host, app_id, access_token, port, event_url)

| Parameter      | Type          | Description            |
| -------------- | ------------- | ---------------------- |
| `host`         | str           | URL to Hubitat hub     |
| `app_id`       | str           | Maker API app ID       |
| `access_token` | str           | Maker API access token |
| `port`         | Optional[int] | Event server port      |
| `event_url`    | Optional[str] | Event server URL       |

Initialize a new Hub.

##### add_device_listener(device_id, listener)

Add a listener for device events for the given device ID. The listener should have the signature `listener(event) -> None`.

##### add_hsm_listener(listener)

Add a listener for HSM change events. The listener should have the signature `listener(event) -> None`.

##### add_mode_listener(listener)

Add a listener for mode change events. The listener should have the signature `listener(event) -> None`.

##### async check_config()

Verify that the hub is accessible.

##### async refresh_device(device_id)

Refresh the cached state for the given device ID.

##### remove_device_listeners(device_id)

Remove all listeners registered for the given device ID.

##### remove_hsm_listeners()

Remove all listeners for HSM events.

##### remove_mode_listeners()

Remove all listeners for mode events.

##### async send_command(device_id, command, arg)

Send a command to a device.

| Parameter   | Type                      | Description               |
| ----------- | ------------------------- | ------------------------- |
| `device_id` | str                       | Device to send command to |
| `command`   | str                       | Command name              |
| `arg`       | Optional[Union[str, int]] | Command argument          |

##### async set_event_url(event_url)

Set the URL that Hubitat should POST events to.

##### async set_hsm(hsm_state)

Set Hubitat's HSM state.

##### async set_host(mode)

Set URL that the Hubitat hub is available at.

##### async set_mode(mode)

Set Hubitat's mode.

##### async set_port(port)

Set the port the event server will listen on.

##### async stop()

Remove all listeners and stop the event server.

## Developing

To get setup for development, run

```
$ poetry run init
```

To test the code, which will type check it and run unit tests, run

```
$ poetry run test
```
