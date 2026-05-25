# Home Assistant Integration Examples

These examples show package-level patterns an integration can wrap. They are not a full Home Assistant custom component.

## Discovery

```python
from sony_projector_protocol import discover

devices = await discover()
for device in devices:
    print(device.ip, device.product_name, device.serial_number)
```

Discovery reports SDAP metadata only. The integration should still ask the user, configuration flow, or model database whether to use SDCP or ADCP.

## Manual Configuration

```python
from sony_projector_protocol import Projector

projector = Projector(host="192.168.1.50", protocol="sdcp")
await projector.connect()
```

SDCP/PJ Talk uses the default community `SONY`. Pass a configured or discovered community when the projector is using a different one:

```python
projector = Projector(host="192.168.1.50", protocol="sdcp", community=device.community)
```

Use `protocol="adcp"` for ADCP-capable projectors.

## Polling State

```python
power = await projector.get_power()
active_input = await projector.get_input()
```

## Control

```python
await projector.set_power(True)
await projector.set_input("hdmi1")
```

## Exceptions

```python
from sony_projector_protocol import (
    PackageUnsupportedCommandError,
    ProjectorConnectionError,
    ProjectorTimeoutError,
    ProjectorUnsupportedCommandError,
)

try:
    signal = await projector.get_signal()
except ProjectorUnsupportedCommandError as err:
    _LOGGER.debug("Projector rejected %s: %s", err.command, err.response_text or err.response_hex)
    signal = None
except PackageUnsupportedCommandError:
    signal = None
except ProjectorTimeoutError:
    signal = None
except ProjectorConnectionError:
    await projector.close()
```

Integrations can create optional disabled-by-default entities for model-dependent commands and mark them unavailable if an enabled command raises `ProjectorUnsupportedCommandError`. A `PackageUnsupportedCommandError` means the selected package API or protocol cannot make that request, so the integration should not create or enable that entity for the current configuration.
