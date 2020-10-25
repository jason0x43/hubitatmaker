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

See the [API doc](doc/api.md).

## Developing

To get setup for development, run

```
$ poetry run init
```

To test the code, which will type check it and run unit tests, run

```
$ poetry run test
```
