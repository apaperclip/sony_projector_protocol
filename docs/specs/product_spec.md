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
- Read projector state, including power, input, and model identity.
- Control common projector features reliably.
- Handle offline, standby, authentication, unsupported command, and protocol mismatch cases cleanly.

## Supported Features

### MVP

- SDAP discovery listener.
- Discovery should listen for 60s
- Manual host connection.
- ADCP TCP client.
- SDCP TCP client.
- Protocol selection by explicit upstream configuration.
- SDCP default community `SONY`, with upstream override support.
- Power on/off.
- Power status.
- Input status and HDMI input selection.
- Model name and serial number where supported.
- Structured exceptions and timeouts.
- Unit tests with fake transports.
- Packaging metadata suitable for TestPyPI and PyPI.

### Version 0.2

- Calibration preset / picture mode controls.
- Static source-reference option helpers for setup-time integration decisions.
- Picture mute / blanking controls.
- Lamp or light source hours where supported.
- Clear unsupported-command errors that upstream integrations can map to disabled or unavailable entities.
- Home Assistant integration reference examples.

### Later

- ADCP image adjustment controls:
- Contrast.
- Brightness.
- Sharpness.
- Light output.
- Optional serial ADCP transport.
- Diagnostics payload for Home Assistant issue reports.
- Integration tests against captured projector sessions.

## Non-Goals

- Cloud control or Sony account integration.
- HDMI-CEC control.
- Full Home Assistant custom component implementation inside this package.
- Projector firmware updates.
- Runtime or persistent capability cache; integrations should own cached decisions and user overrides.
- Full UI or web application.

## Design Principles

- Local first: never require internet at runtime.
- Home Assistant friendly: async APIs, predictable exceptions, fast setup, no blocking network calls in public async methods.
- Conservative control: expose advanced commands through explicit methods and raise `PackageUnsupportedCommandError` when the package or selected protocol cannot issue a request, and `ProjectorUnsupportedCommandError` when the projector rejects a request as unsupported or unavailable. Both inherit from `UnsupportedCommandError`. Projector response errors should expose the protocol, command, and raw or decoded projector response for troubleshooting.
- Static capability data may expose source-reference option lists for setup-time integration helpers. ADCP option lists are model-aware where official Sony series mappings are available. SDCP may expose generic package-supported fallback option lists for a protocol-scoped feature, but projectors can still reject an item at runtime.
- Protocol neutral API: callers should ask for `set_power(True)`, not build ADCP or SDCP packets.
- Testable transports: all protocol clients must work with fake readers/writers or socket abstractions.

## Public API Sketch

```python
from sony_projector_protocol import Projector, discover

devices = await discover()

projector = Projector(host="192.168.1.50", protocol="sdcp")
await projector.connect()

state = await projector.get_power()
await projector.set_power(True)
await projector.set_input("hdmi1")
await projector.close()
```

## Package Name

Import package: `sony_projector_protocol`

Distribution name: `sony-projector-protocol`

Template package names should not appear in distributed metadata or documentation.

## Runtime Compatibility

- Python 3.14.2+ is required for Home Assistant alignment.
- Runtime dependencies should be minimal. Prefer the standard library for sockets, asyncio streams, dataclasses, enums, and logging.
- Optional dependencies should be isolated behind extras.

## Source References

- Sony common protocol manual: SDAP, ADCP, network behavior, and command flow.
  https://pro.sony/s3/2018/07/19110324/Sony_Protocol-Manual_1st-Edition-Revised-1.pdf
- Sony supported command list: model command support and default ports.
  https://pro.sony/s3/2018/07/19110602/Sony_Protocol-Manual_Supported-Command-List_1st-Edition-Revised-1.pdf
- Sony video projector supported command list: model command support for current ADCP video-projector series.
  https://www.sony.com/electronics/support/res/manuals/9932/68bf8c3b38750c56cb60dcb8f1dfa909/99327615M.pdf
- SDCP package reference implementation.
  https://github.com/kennymc-c/pySDCP-extended
- ADCP Home Assistant implementation reference.
  https://github.com/tokyotexture/homeassistant-custom-components
- ADCP Unfolded Circle implementation reference.
  https://github.com/kennymc-c/ucr-integration-sonyADCP
- ADCP Home Assistant implementation reference.
  https://github.com/Bcukier/sony_projector_adcp
