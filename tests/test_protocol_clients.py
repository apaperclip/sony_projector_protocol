from __future__ import annotations

import asyncio

import pytest

from sony_projector_protocol import Input, PowerState, Projector, Protocol, parse_sdap_packet
from sony_projector_protocol.adcp import AdcpClient
from sony_projector_protocol.discovery import DiscoveredProjector
from sony_projector_protocol.exceptions import ProjectorProtocolError
from sony_projector_protocol.sdcp import SdcpClient
from sony_projector_protocol.transport import FakeTransport


def test_adcp_power_commands() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"power ?\r":
                return b"power=on\r"
            if payload == b"power off\r":
                return b"ok\r"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_power() is PowerState.ON
        await client.set_power(False)

        assert transport.requests == [b"power ?\r", b"power off\r"]

    asyncio.run(run())


def test_sdcp_input_commands_use_pj_talk_frames() -> None:
    async def run() -> None:
        get_input = bytes.fromhex("02 0A 53 4F 4E 59 01 00 01 00")
        set_hdmi2 = bytes.fromhex("02 0A 53 4F 4E 59 00 00 01 02 00 03")
        input_hdmi1_response = bytes.fromhex("02 0A 53 4F 4E 59 01 00 01 02 00 02")
        ok_response = bytes.fromhex("02 0A 53 4F 4E 59 01 00 01 00")

        def respond(payload: bytes) -> bytes:
            if payload == get_input:
                return input_hdmi1_response
            if payload == set_hdmi2:
                return ok_response
            raise AssertionError(payload.hex(" "))

        transport = FakeTransport(respond)
        client = SdcpClient("192.0.2.10", transport=transport)

        assert await client.get_input() is Input.HDMI1
        await client.set_input(Input.HDMI2)
        assert transport.requests == [get_input, set_hdmi2]

    asyncio.run(run())


def test_sdcp_power_status_exposes_projector_state() -> None:
    async def run() -> None:
        get_power = bytes.fromhex("02 0A 53 4F 4E 59 01 01 02 00")
        startup_lamp_response = bytes.fromhex("02 0A 53 4F 4E 59 01 01 02 02 00 02")

        def respond(payload: bytes) -> bytes:
            if payload == get_power:
                return startup_lamp_response
            raise AssertionError(payload.hex(" "))

        transport = FakeTransport(respond)
        client = SdcpClient("192.0.2.10", transport=transport)

        assert await client.get_power() == "start_up_lamp"
        assert transport.requests == [get_power]

    asyncio.run(run())


def test_projector_facade_uses_configured_protocol() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"power=standby\r")
        projector = Projector("192.0.2.10", protocol=Protocol.ADCP, transport=transport)

        await projector.connect()

        assert transport.connected is True
        assert await projector.get_power() is PowerState.STANDBY
        assert "power" in projector.capabilities.supported

    asyncio.run(run())


def test_projector_facade_uses_configured_sdcp_protocol() -> None:
    async def run() -> None:
        get_input = bytes.fromhex("02 0A 53 4F 4E 59 01 00 01 00")
        input_hdmi2_response = bytes.fromhex("02 0A 53 4F 4E 59 01 00 01 02 00 03")

        def respond(payload: bytes) -> bytes:
            if payload == get_input:
                return input_hdmi2_response
            raise AssertionError(payload.hex(" "))

        transport = FakeTransport(respond)
        projector = Projector("192.0.2.10", protocol=Protocol.SDCP, transport=transport)

        await projector.connect()

        assert await projector.get_input() is Input.HDMI2
        assert transport.requests == [get_input]

    asyncio.run(run())


def test_projector_auto_protocol_rejects_injected_transport() -> None:
    async def run() -> None:
        projector = Projector("192.0.2.10", protocol=Protocol.AUTO, transport=FakeTransport(lambda payload: b""))

        with pytest.raises(ProjectorProtocolError):
            await projector.connect()

    asyncio.run(run())


def test_parse_binary_sdap_packet() -> None:
    packet = b"".join(
        [
            b"DA",
            bytes([0x01, 0x0A]),
            b"SONY",
            b"VPL-XW5000ES",
            (12345).to_bytes(4, byteorder="big"),
            (2).to_bytes(2, byteorder="big"),
            b"Theater\x00" + b"\x00" * 16,
        ]
    )

    projector = parse_sdap_packet(packet, "192.0.2.10")

    assert projector == DiscoveredProjector(
        ip="192.0.2.10",
        id="DA",
        version=1,
        category=10,
        community="SONY",
        product_name="VPL-XW5000ES",
        serial_number=12345,
        power_status=2,
        location="Theater",
    )


def test_parse_text_sdap_packet_fallback_uses_discovery_fields_only() -> None:
    packet = b"PRODUCT_NAME: VPL-XW5000ES\nSERIAL_NUMBER: 12345\nPOWER_STATUS: 2\n"

    projector = parse_sdap_packet(packet, "192.0.2.10")

    assert projector == DiscoveredProjector(
        ip="192.0.2.10",
        product_name="VPL-XW5000ES",
        serial_number=12345,
        power_status=2,
    )
