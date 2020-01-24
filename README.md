# hubitatmaker

This library provides an async Python interface for Hubitat Elevation’s Maker
API.

## Basic usage

```python
import asyncio
from hubitatmaker import Hub

async def print_devices(host, app_id, token):
	hub = Hub(host, app_id, token)
	await hub.connect()
	for device in hub.devices:
		print(f"{device.name} ({device.id})")

if __name__ == '__main__':
	host = 'http://10.0.1.99'
	app_id = '1234'
	token = '<apitoken>'
	asyncio.run(print_devices(host, app_id, token))
```
