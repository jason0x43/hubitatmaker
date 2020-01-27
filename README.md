# hubitatmaker

This library provides an async Python interface for Hubitat Elevation’s Maker
API. It is primarily intended for use with Home Assistant.

## Features

The main public API in hubitatmaker is the Hub class. This class represents a
Maker API instance on a Hubitat hub. When started, a Hub instance will download
some basic information from the Hubitat hub, as well as a list of available
devices and details about each device.

The Hub instance caches state information about each device. It relies on events
posted from the Hubitat hub to update its internal state. When used in a Home
Assistant integration, the assumption is that a webhook will be used to receive
the events, and the integration will pass them to a Hub instance via
`process_event`. However, Hub can also start a standalone event receiver.

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
