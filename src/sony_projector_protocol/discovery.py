"""SDAP discovery helpers."""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass

from sony_projector_protocol.models import Protocol

SDAP_PORT = 53862


@dataclass(frozen=True)
class DiscoveredProjector:
    """Projector details learned from SDAP."""

    host: str
    model: str | None = None
    serial: str | None = None
    protocol: Protocol | None = None
    raw: dict[str, str] | None = None


def parse_sdap_packet(payload: bytes, host: str) -> DiscoveredProjector:
    """Parse a text-like SDAP advertisement into normalized fields."""
    text = payload.decode("utf-8", errors="ignore")
    fields: dict[str, str] = {}

    for raw_line in text.replace("\x00", "\n").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" in line:
            key, value = line.split(":", 1)
        elif "=" in line:
            key, value = line.split("=", 1)
        else:
            continue
        fields[key.strip().lower()] = value.strip()

    protocol_hint = fields.get("protocol") or fields.get("service") or fields.get("type")
    protocol = None
    if protocol_hint:
        lowered = protocol_hint.lower()
        if "adcp" in lowered:
            protocol = Protocol.ADCP
        elif "sdcp" in lowered or "pj" in lowered:
            protocol = Protocol.SDCP

    return DiscoveredProjector(
        host=host,
        model=fields.get("model") or fields.get("modelname") or fields.get("name"),
        serial=fields.get("serial") or fields.get("serialnumber"),
        protocol=protocol,
        raw=fields,
    )


class _SdapProtocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.devices: dict[str, DiscoveredProjector] = {}

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        host = addr[0]
        self.devices[host] = parse_sdap_packet(data, host)


async def discover(timeout: float = 5.0, *, port: int = SDAP_PORT) -> list[DiscoveredProjector]:
    """Listen for SDAP advertisements for a short period."""
    loop = asyncio.get_running_loop()
    protocol = _SdapProtocol()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: protocol,
        local_addr=("0.0.0.0", port),
        allow_broadcast=True,
    )
    try:
        await asyncio.sleep(timeout)
    finally:
        with contextlib.suppress(Exception):
            transport.close()

    return list(protocol.devices.values())
