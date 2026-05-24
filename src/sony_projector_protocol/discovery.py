"""SDAP discovery helpers."""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass

<<<<<<< HEAD
=======
from sony_projector_protocol.models import Protocol

>>>>>>> 93e583af79eae1c27c0eb37444f1d23e02bd76d2
SDAP_PORT = 53862


@dataclass(frozen=True)
class DiscoveredProjector:
    """Projector details learned from SDAP."""

<<<<<<< HEAD
    ip: str
    id: str | None = None
    version: int | None = None
    category: int | None = None
    community: str | None = None
    product_name: str | None = None
    serial_number: int | None = None
    power_status: int | None = None
    location: str | None = None


def _decode_sdap_text_field(payload: bytes) -> str:
    return payload.split(b"\x00", 1)[0].decode("utf-8", errors="ignore").strip()


def _parse_optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


def _parse_binary_sdap_packet(payload: bytes, ip: str) -> DiscoveredProjector | None:
    if len(payload) < 26 or payload[:2] != b"DA":
        return None

    return DiscoveredProjector(
        ip=ip,
        id=payload[:2].decode("ascii", errors="ignore"),
        version=payload[2],
        category=payload[3],
        community=_decode_sdap_text_field(payload[4:8]),
        product_name=_decode_sdap_text_field(payload[8:20]) or None,
        serial_number=int.from_bytes(payload[20:24], byteorder="big"),
        power_status=int.from_bytes(payload[24:26], byteorder="big"),
        location=_decode_sdap_text_field(payload[26:50]) or None,
    )


def _parse_text_sdap_packet(payload: bytes, ip: str) -> DiscoveredProjector:
    """Parse a text-like advertisement into top-level discovery fields."""
=======
    host: str
    model: str | None = None
    serial: str | None = None
    protocol: Protocol | None = None
    raw: dict[str, str] | None = None


def parse_sdap_packet(payload: bytes, host: str) -> DiscoveredProjector:
    """Parse a text-like SDAP advertisement into normalized fields."""
>>>>>>> 93e583af79eae1c27c0eb37444f1d23e02bd76d2
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

<<<<<<< HEAD
    return DiscoveredProjector(
        ip=ip,
        id=fields.get("id"),
        version=_parse_optional_int(fields.get("version")),
        category=_parse_optional_int(fields.get("category")),
        community=fields.get("community"),
        product_name=fields.get("product_name") or fields.get("productname"),
        serial_number=_parse_optional_int(fields.get("serial_number") or fields.get("serialnumber")),
        power_status=_parse_optional_int(fields.get("power_status") or fields.get("powerstatus")),
        location=fields.get("location"),
    )


def parse_sdap_packet(payload: bytes, ip: str) -> DiscoveredProjector:
    """Parse an SDAP advertisement into normalized fields."""
    projector = _parse_binary_sdap_packet(payload, ip)
    if projector is not None:
        return projector
    return _parse_text_sdap_packet(payload, ip)


=======
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


>>>>>>> 93e583af79eae1c27c0eb37444f1d23e02bd76d2
class _SdapProtocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.devices: dict[str, DiscoveredProjector] = {}

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
<<<<<<< HEAD
        ip = addr[0]
        self.devices[ip] = parse_sdap_packet(data, ip)
=======
        host = addr[0]
        self.devices[host] = parse_sdap_packet(data, host)
>>>>>>> 93e583af79eae1c27c0eb37444f1d23e02bd76d2


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
