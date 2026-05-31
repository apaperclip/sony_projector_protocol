# Home Assistant Integration Examples

These examples show package-level patterns an integration can wrap. They are not a full Home Assistant custom component.

## Protocol Selection

Discovery reports SDAP metadata only. It does not prove whether ADCP or SDCP should be used for control, and this package does not probe ports or auto-detect between protocols.

Choose the protocol from one of these integration-owned sources:

- user configuration from a config flow
- a model database maintained by the integration
- an integration-level user override

Use `protocol="sdcp"` for SDCP / PJ Talk projectors and `protocol="adcp"` for ADCP-capable projectors.

## Discovery

```python
from sony_projector_protocol import discover

devices = await discover()
for device in devices:
    print(device.ip, device.product_name, device.serial_number)
```

If the SDAP advertisement includes a `community`, treat it only as SDCP metadata. It is not useful for ADCP.

## Manual Configuration

```python
from sony_projector_protocol import Projector

projector = Projector(host="192.168.1.50", protocol="sdcp")
await projector.connect()
```

SDCP / PJ Talk uses the default community `SONY`. Pass a configured or discovered community when the projector is using a different one:

```python
projector = Projector(host="192.168.1.50", protocol="sdcp", community=device.community)
```

For ADCP, pass `adcp_password` only when the projector requires authentication:

```python
projector = Projector(
    host="192.168.1.50",
    protocol="adcp",
    adcp_password=user_configured_password,
)
```

If the projector does not require ADCP authentication, omit `adcp_password`.

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

## Select Entity Options

Use the static capability helpers during setup when a select entity needs valid options before the entity is created. Keep ADCP and SDCP feature keys separate.

```python
from sony_projector_protocol import (
    FEATURE_ADCP_PICTURE_MODE,
    FEATURE_SDCP_CALIBRATION_PRESET,
    PROTOCOL_ADCP,
    PROTOCOL_SDCP,
    get_adcp_picture_mode_options,
    get_feature_values,
)

identity = await projector.get_identity()
model = identity.model or ""

if configured_protocol == PROTOCOL_ADCP:
    options = get_adcp_picture_mode_options(model)
    # Equivalent:
    options = get_feature_values(model, FEATURE_ADCP_PICTURE_MODE, protocol=PROTOCOL_ADCP)
else:
    options = get_feature_values(model, FEATURE_SDCP_CALIBRATION_PRESET, protocol=PROTOCOL_SDCP)

if options is None:
    # Unknown model or unsupported feature. Do not create the select entity,
    # mark it unavailable, or use an integration-level override.
    return
```

Use returned values directly as command values. ADCP option lists are model-aware and follow Sony's model-to-series command-list mapping. Unknown ADCP models return `None`. SDCP calibration preset lookup returns the package-supported option list for any returned model when `protocol="sdcp"` is requested, but the projector may still reject a command as not applicable at runtime.

Integration rules:

- Do not call ADCP `--range` or `--info` to discover select options. They are not reliable on tested hardware.
- Do not use SDCP `community` for ADCP capability lookup.
- Do not reuse ADCP option lists for SDCP select entities.
- Store user overrides in the integration, not in this library.
- Catch `ProjectorUnsupportedCommandError` when setting any model-dependent option because the projector can still reject a command at runtime.

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
