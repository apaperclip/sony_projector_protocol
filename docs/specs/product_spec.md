# Sony Projector Protocol Package Product Spec

## Purpose

Build a Python package for discovering and controlling Sony projectors from home automation systems, especially Home Assistant integrations.

The package must support:

- Discovery of projectors that advertise with SDAP.
- Direct connection to a configured projector IP address.
- Control through SDCP / PJ Talk for projectors that expose SDCP.
- Control through ADCP for projectors that expose ADCP.
- A stable async-friendly API that a Home Assistant component can wrap without needing to know protocol details.

## Primary Users

- Home Assistant integration authors.
- Home theater owners who want local projector management.
- Developers building local control integrations for Sony VPL projectors.

## User Goals

- Discover projectors on the local network.
- Configure a projector by IP address when discovery is unavailable or disabled.
- Read projector state, including power, input, model identity, and supported capability hints.
- Control common projector features reliably.
- Handle offline, standby, authentication, unsupported command, and protocol mismatch cases cleanly.

## Supported Features

### MVP

- SDAP discovery listener.
- Discovery should listen for 60s
- Manual host connection.
- ADCP TCP client.
- SDCP TCP client.
- Protocol selection by explicit configuration, SDAP advertisement hints where available, or fallback probing.
- Power on/off.
- Power status.
- Input status and HDMI input selection.
- Model name and serial number where supported.
- Structured exceptions and timeouts.
- Unit tests with fake transports.
- Packaging metadata suitable for TestPyPI and PyPI.

### Version 0.2

- Calibration preset / picture mode controls.
- Picture mute / blanking controls.
- Lamp or light source hours where supported.
- Contrast, brightness, sharpness, and light output controls for ADCP-capable models.
- Capability reporting that records unsupported commands without failing the whole device.
- Home Assistant integration reference examples.

### Later

- Optional serial ADCP transport.
- Optional command tables per projector family.
- Persistent capability cache.
- Diagnostics payload for Home Assistant issue reports.
- Integration tests against captured projector sessions.

## Non-Goals

- Cloud control or Sony account integration.
- HDMI-CEC control.
- Full Home Assistant custom component implementation inside this package.
- Projector firmware updates.
- Full UI or web application.

## Design Principles

- Local first: never require internet at runtime.
- Home Assistant friendly: async APIs, predictable exceptions, fast setup, no blocking network calls in public async methods.
- Conservative control: expose advanced commands only through typed methods and capability checks.
- Protocol neutral API: callers should ask for `set_power(True)`, not build ADCP or SDCP packets.
- Testable transports: all protocol clients must work with fake readers/writers or socket abstractions.

## Public API Sketch

```python
from sony_projector_protocol import Projector, discover

devices = await discover(timeout=5.0)

projector = Projector(host="192.168.1.50", protocol="auto")
await projector.connect()

state = await projector.get_power()
await projector.set_power(True)
await projector.set_input("hdmi1")
await projector.close()
```

## Package Name

Recommended import package: `sony_projector_protocol`

Recommended distribution name: `sony-projector-protocol`

The current template package name (`python_package`) should be replaced before first TestPyPI publication.

## Runtime Compatibility

- Python 3.11+ is recommended for Home Assistant alignment.
- Runtime dependencies should be minimal. Prefer the standard library for sockets, asyncio streams, dataclasses, enums, and logging.
- Optional dependencies should be isolated behind extras.

## Source References

- Sony common protocol manual: SDAP, ADCP, network behavior, and command flow.
  https://pro.sony/s3/2018/07/19110324/Sony_Protocol-Manual_1st-Edition-Revised-1.pdf
- Sony supported command list: model command support and default ports.
  https://pro.sony/s3/2018/07/19110602/Sony_Protocol-Manual_Supported-Command-List_1st-Edition-Revised-1.pdf
- SDCP package reference implementation.
  https://github.com/kennymc-c/pySDCP-extended
- ADCP Home Assistant implementation reference.
  https://github.com/tokyotexture/homeassistant-custom-components
- ADCP Unfolded Circle implementation reference.
  https://github.com/kennymc-c/ucr-integration-sonyADCP
- ADCP Home Assistant implementation reference.
  https://github.com/Bcukier/sony_projector_adcp
