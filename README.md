# Sony Projector Protocol

Async Python helpers for discovering and controlling Sony projectors from local automation systems.

This package is intended to be wrapped by applications such as Home Assistant integrations. It handles Sony protocol framing, parsing, timeouts, and protocol-specific errors while leaving model selection and entity policy to the upstream application.

## How It Works

Sony projectors can expose several local protocols:

- **SDAP** is the discovery advertisement protocol. It reports metadata such as IP address, product name, serial number, power status, installation location, and SDCP community when the projector advertises it.
- **SDCP / PJ Talk** is a control protocol used by many Sony projectors. SDCP commands include a 4-character community value. The default community is `SONY`, and callers can provide another one when needed.
- **ADCP** is another Sony control protocol. Some projectors require password authentication before ADCP commands can be used.

Discovery does not decide which control protocol to use. An upstream application should choose `protocol="sdcp"` or `protocol="adcp"` from user configuration, a model database, or its own integration logic. This package does not probe ports or auto-detect ADCP versus SDCP.

## Install

```bash
pip install sony-projector-protocol
```

## Discover Projectors

`discover()` listens for SDAP advertisements and returns the metadata that was advertised.

```python
from sony_projector_protocol import discover

devices = await discover()

for device in devices:
    print(device.ip, device.product_name, device.serial_number, device.community)
```

The discovered `community` is not a password or decryption key for SDAP. It is metadata that can be passed into SDCP commands if the projector uses a non-default community.

## Control With SDCP

```python
from sony_projector_protocol import Projector

projector = Projector(host="192.168.1.50", protocol="sdcp")

await projector.connect()
try:
    power = await projector.get_power()
    active_input = await projector.get_input()

    await projector.set_power(True)
    await projector.set_input("hdmi1")
finally:
    await projector.close()
```

To use a discovered or configured SDCP community:

```python
projector = Projector(
    host=device.ip,
    protocol="sdcp",
    community=device.community,
)
```

If `community` is omitted or `None`, SDCP uses the default community `SONY`.

## Control With ADCP

```python
from sony_projector_protocol import Projector

projector = Projector(
    host="192.168.1.50",
    protocol="adcp",
    adcp_password="Projector"
)

await projector.connect()
try:
    power = await projector.get_power()
    signal = await projector.get_signal()

    await projector.set_power(False)
finally:
    await projector.close()
```

If the projector does not require ADCP authentication, omit `adcp_password`.

## Identity

Both protocol clients expose identity helpers where the selected projector supports them:

```python
identity = await projector.get_identity()

print(identity.model)
print(identity.serial)
print(identity.location)
print(identity.mac_address)
```

SDCP identity reads model name, serial number, installation location, and MAC address. ADCP identity reads model name, serial number, and MAC address; installation location is returned as `None` because the ADCP command set does not expose it.

## Model Capability Helpers

The package includes static, model-aware capability helpers for integrations that need setup-time option lists. The first supported feature is ADCP `picture_mode`, which can be used by Home Assistant select entities.

```python
from sony_projector_protocol import get_adcp_picture_mode_options

identity = await projector.get_identity()
options = get_adcp_picture_mode_options(identity.model or "")

if options is not None:
    print(options)
```

Capability data is organized as model-to-series mappings and series-to-feature mappings, matching Sony's supported command lists. Unknown or unlisted models return `None` so integrations can omit the entity, disable it, or apply their own override policy. The helpers do not rely on ADCP `--range` or `--info` metadata commands.

## Unsupported Commands

Projector features vary by model and protocol. Unsupported requests raise `UnsupportedCommandError`.
Use the more specific subclasses when an integration needs to tell local request
validation apart from a projector response:

- `PackageUnsupportedCommandError` means this package or the selected protocol cannot issue the request, such as calling an SDCP-only method on an ADCP connection or passing a value this package does not encode.
- `ProjectorUnsupportedCommandError` means the request was sent and the projector rejected it as unsupported or not available.

Projector response errors include troubleshooting metadata when available:
`protocol`, `command`, `response`, `response_text`, and `response_hex`.

```python
from sony_projector_protocol import ProjectorUnsupportedCommandError

try:
    lamp_timer = await projector.get_lamp_timer()
except ProjectorUnsupportedCommandError as err:
    print(err.protocol, err.command, err.response_text or err.response_hex)
    lamp_timer = None
```

This lets upstream applications create optional entities for advanced calls and mark them disabled or unavailable when the projector reports that it does not support them. Applications that do not need the distinction can catch `UnsupportedCommandError`.

## Command Areas

Protocol-neutral methods include power, input, lamp control, aspect ratio, HDR, HDMI dynamic range, identity, and MAC address where the selected protocol supports them.

ADCP-specific methods include signal, temperature, timer, picture mode, warning/error details, version, and ADCP-only setters such as color space.

SDCP-specific methods include calibration preset, color temperature, contrast enhancer, advanced iris, gamma correction, picture muting, motionflow, 2D/3D controls, picture position, reality creation, input lag reduction, menu position, error status, installation location, and lamp timer.

## Development

Run the offline unit tests with:

```bash
pytest
```
