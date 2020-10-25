# API

<!-- vim-markdown-toc GFM -->

* [Hub](#hub)
	* [Properties](#properties)
		* [devices](#devices)
		* [mode](#mode)
		* [modes](#modes)
		* [hsm_status](#hsm_status)
	* [Methods](#methods)
		* [\_\_init\_\_(host, app_id, access_token, port, event_url)](#__init__host-app_id-access_token-port-event_url)
		* [add_device_listener(device_id, listener)](#add_device_listenerdevice_id-listener)
		* [add_hsm_listener(listener)](#add_hsm_listenerlistener)
		* [add_mode_listener(listener)](#add_mode_listenerlistener)
		* [async check_config()](#async-check_config)
		* [async refresh_device(device_id)](#async-refresh_devicedevice_id)
		* [remove_device_listeners(device_id)](#remove_device_listenersdevice_id)
		* [remove_hsm_listeners()](#remove_hsm_listeners)
		* [remove_mode_listeners()](#remove_mode_listeners)
		* [async send_command(device_id, command, arg)](#async-send_commanddevice_id-command-arg)
		* [async set_event_url(event_url)](#async-set_event_urlevent_url)
		* [async set_hsm(hsm_state)](#async-set_hsmhsm_state)
		* [async set_host(mode)](#async-set_hostmode)
		* [async set_mode(mode)](#async-set_modemode)
		* [async set_port(port)](#async-set_portport)
		* [async stop()](#async-stop)

<!-- vim-markdown-toc -->

## Hub

### Properties

#### devices

The list of devices managed by the hub.

#### mode

The hub's mode (e.g., "Away", "Day", "Night").

#### modes

The available hub modes.

#### hsm_status

The hub's HSM status (e.g., "armedAway", "disarmed"). See [this post](https://community.hubitat.com/t/hubitat-safety-monitor-api/934/3) for more information.

### Methods

#### \_\_init\_\_(host, app_id, access_token, port, event_url)

| Parameter      | Type          | Description            |
| -------------- | ------------- | ---------------------- |
| `host`         | str           | URL to Hubitat hub     |
| `app_id`       | str           | Maker API app ID       |
| `access_token` | str           | Maker API access token |
| `port`         | Optional[int] | Event server port      |
| `event_url`    | Optional[str] | Event server URL       |

Initialize a new Hub.

#### add_device_listener(device_id, listener)

Add a listener for device events for the given device ID. The listener should have the signature `listener(event) -> None`.

#### add_hsm_listener(listener)

Add a listener for HSM change events. The listener should have the signature `listener(event) -> None`.

#### add_mode_listener(listener)

Add a listener for mode change events. The listener should have the signature `listener(event) -> None`.

#### async check_config()

Verify that the hub is accessible.

#### async refresh_device(device_id)

Refresh the cached state for the given device ID.

#### remove_device_listeners(device_id)

Remove all listeners registered for the given device ID.

#### remove_hsm_listeners()

Remove all listeners for HSM events.

#### remove_mode_listeners()

Remove all listeners for mode events.

#### async send_command(device_id, command, arg)

Send a command to a device.

| Parameter   | Type                      | Description               |
| ----------- | ------------------------- | ------------------------- |
| `device_id` | str                       | Device to send command to |
| `command`   | str                       | Command name              |
| `arg`       | Optional[Union[str, int]] | Command argument          |

#### async set_event_url(event_url)

Set the URL that Hubitat should POST events to.

#### async set_hsm(hsm_state)

Set Hubitat's HSM state.

#### async set_host(mode)

Set URL that the Hubitat hub is available at.

#### async set_mode(mode)

Set Hubitat's mode.

#### async set_port(port)

Set the port the event server will listen on.

#### async stop()

Remove all listeners and stop the event server.
