# Sony Projector Protocol

Async Python helpers for discovering and controlling Sony projectors from local automation systems.

## Current API

```python
from sony_projector_protocol import Projector, discover

devices = await discover(timeout=5.0)

projector = Projector(host="192.168.1.50", protocol="sdcp")
await projector.connect()
power = await projector.get_power()
await projector.set_power(True)
await projector.set_input("hdmi1")
await projector.close()
```

## Development

Run the offline unit tests with:

```bash
pytest
```

Choose `protocol="sdcp"` for PJ Talk/SDCP projectors and `protocol="adcp"` for ADCP projectors. The package currently provides the public facade, SDAP discovery parsing/listening, ADCP and SDCP client shells, structured exceptions, and fake transport support for tests.
