# Captured Session Test Plan

Captured sessions should cover real projector responses without storing private network details or credentials.

## Fixture Format

Use JSON fixtures with this shape:

```json
{
  "protocol": "adcp",
  "model": "VPL-EXAMPLE",
  "commands": [
    {
      "request_hex": "706f776572203f0d0a",
      "response_hex": "706f7765723d6f6e0d0a",
      "method": "get_power"
    }
  ]
}
```

Rules:

- Store request and response bytes as hex strings.
- Replace serial numbers, MAC addresses, IP addresses, room names, and passwords with obvious placeholders.
- Keep one fixture per protocol family at minimum.
- Replay fixtures through fake transports, not live sockets.

## Initial Coverage Targets

- ADCP power, input, identity, signal, warning/error, and one unsupported command response.
- SDCP power, input, lamp timer, HDR, and one unsupported item response.

Initial sanitized replay fixtures live in `tests/fixtures/captured_sessions/` and are exercised by `test_captured_session_fixture_replays_through_client`.
