from __future__ import annotations

import asyncio
import hashlib

import pytest

from sony_projector_protocol import Input, PowerState, Projector, Protocol, parse_sdap_packet
from sony_projector_protocol.adcp import AdcpClient
from sony_projector_protocol.discovery import DiscoveredProjector
from sony_projector_protocol.exceptions import ProjectorProtocolError, UnsupportedCommandError
from sony_projector_protocol.models import ProjectorIdentity
from sony_projector_protocol.sdcp import SdcpClient
from sony_projector_protocol.transport import FakeTransport, StreamTransport


def test_adcp_power_commands() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"power ?\r\n":
                return b"power=on\r\n"
            if payload == b"power off\r\n":
                return b"ok\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_power() is PowerState.ON
        await client.set_power(False)

        assert transport.requests == [b"power ?\r\n", b"power off\r\n"]

    asyncio.run(run())


def test_adcp_signal_command() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"signal ?\r\n":
                return b"signal=3840x2160/60p HDR10\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_signal() == "3840x2160/60p HDR10"
        assert transport.requests == [b"signal ?\r\n"]

    asyncio.run(run())


def test_adcp_picture_mode_command() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"picture_mode ?\r\n":
                return b"picture_mode=cinema_film1\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_picture_mode() == "cinema_film1"
        assert transport.requests == [b"picture_mode ?\r\n"]

    asyncio.run(run())


def test_adcp_color_space_command() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"color_space ?\r\n":
                return b"color_space=bt709\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_color_space() == "bt709"
        assert transport.requests == [b"color_space ?\r\n"]

    asyncio.run(run())


def test_adcp_lamp_control_command() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"lamp_control ?\r\n":
                return b"lamp_control=high\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_lamp_control() == "high"
        assert transport.requests == [b"lamp_control ?\r\n"]

    asyncio.run(run())


def test_adcp_warning_command_parses_list() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"warning ?\r\n":
                return b'warning=["warn_temp", "warn_signal_freq"]\r\n'
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_warning() == ["warn_temp", "warn_signal_freq"]
        assert transport.requests == [b"warning ?\r\n"]

    asyncio.run(run())


def test_adcp_error_command_parses_list() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"error ?\r\n":
                return b'error=["err_temp", "err_fan"]\r\n'
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_error() == ["err_temp", "err_fan"]
        assert transport.requests == [b"error ?\r\n"]

    asyncio.run(run())


def test_adcp_warning_command_keeps_unexpected_response() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"warning=none\r\n")
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_warning() == "none"

    asyncio.run(run())


def test_adcp_hdr_aspect_and_dynamic_range_commands() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"hdr ?\r\n":
                return b"hdr=hdr10\r\n"
            if payload == b"aspect ?\r\n":
                return b"aspect=normal\r\n"
            if payload == b"dynamic_range --hdmi1 ?\r\n":
                return b"dynamic_range=full\r\n"
            if payload == b"dynamic_range --hdmi2 ?\r\n":
                return b"dynamic_range=limited\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_hdr() == "hdr10"
        assert await client.get_aspect_ratio() == "normal"
        assert await client.get_hdmi1_dynamic_range() == "full"
        assert await client.get_hdmi2_dynamic_range() == "limited"
        assert transport.requests == [
            b"hdr ?\r\n",
            b"aspect ?\r\n",
            b"dynamic_range --hdmi1 ?\r\n",
            b"dynamic_range --hdmi2 ?\r\n",
        ]

    asyncio.run(run())


def test_adcp_dynamic_range_rejects_unknown_input() -> None:
    async def run() -> None:
        client = AdcpClient("192.0.2.10", transport=FakeTransport(lambda payload: b""))

        with pytest.raises(UnsupportedCommandError):
            await client.get_dynamic_range("displayport")

    asyncio.run(run())


def test_adcp_identity_system_commands() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"modelname ?\r\n":
                return b"modelname=VPL-VW285ES\r\n"
            if payload == b"serialnum ?\r\n":
                return b"serialnum=5102851\r\n"
            if payload == b"version ?\r\n":
                return b"version=1.000\r\n"
            if payload == b"mac_address ?\r\n":
                return b"mac_address=00:11:22:33:44:55\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_model_name() == "VPL-VW285ES"
        assert await client.get_serial_number() == "5102851"
        assert await client.get_version() == "1.000"
        assert await client.get_mac_address() == "00:11:22:33:44:55"
        assert transport.requests == [
            b"modelname ?\r\n",
            b"serialnum ?\r\n",
            b"version ?\r\n",
            b"mac_address ?\r\n",
        ]

    asyncio.run(run())


def test_adcp_identity_uses_sony_command_names() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"modelname ?\r\n":
                return b"modelname=VPL-XW5000ES\r\n"
            if payload == b"serialnum ?\r\n":
                return b"serialnum=12345\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_identity() == ProjectorIdentity(model="VPL-XW5000ES", serial="12345")
        assert transport.requests == [b"modelname ?\r\n", b"serialnum ?\r\n"]

    asyncio.run(run())


def test_adcp_temperature_command_extracts_intake_air() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"temperature ?\r\n":
                return b'temperature=[{"intake_air": 31}, {"exhaust_air": 42}]\r\n'
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_temperature() == 31
        assert transport.requests == [b"temperature ?\r\n"]

    asyncio.run(run())


def test_adcp_temperature_command_keeps_unexpected_response() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"temperature=unknown\r\n")
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_temperature() == "unknown"

    asyncio.run(run())


def test_adcp_timer_command_extracts_light_source() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"timer ?\r\n":
                return b'timer=[{"light_src": 862}, {"projector": 1200}]\r\n'
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_timer() == 862
        assert transport.requests == [b"timer ?\r\n"]

    asyncio.run(run())


def test_adcp_timer_command_keeps_unexpected_response() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"timer=unknown\r\n")
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_timer() == "unknown"

    asyncio.run(run())


def test_adcp_password_authentication() -> None:
    async def run() -> None:
        challenge = "1a2b3c4d"
        expected_digest = hashlib.sha256((challenge + "Projector1").encode("ascii")).hexdigest().encode("ascii")
        requests: list[bytes] = []

        async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            writer.write(challenge.encode("ascii") + b"\r\n")
            await writer.drain()

            digest = await reader.readuntil(b"\r\n")
            requests.append(digest)
            writer.write(b"ok\r\n")
            await writer.drain()

            command = await reader.readuntil(b"\r\n")
            requests.append(command)
            writer.write(b'"on"\r\n')
            await writer.drain()
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
        try:
            port = server.sockets[0].getsockname()[1]
            transport = StreamTransport("127.0.0.1", port, terminator=b"\r\n")
            client = AdcpClient("127.0.0.1", transport=transport, password="Projector1")

            await client.connect()
            try:
                assert await client.get_power() is PowerState.ON
            finally:
                await client.close()

            assert requests == [expected_digest + b"\r\n", b"power ?\r\n"]
        finally:
            server.close()
            await server.wait_closed()

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


def test_sdcp_getters_use_expected_item_numbers() -> None:
    async def run() -> None:
        cases = [
            ("get_calibration_preset", 0x0002, 0x0008, "user"),
            ("get_color_temp", 0x0017, 0x0002, 2),
            ("get_lamp_control", 0x001A, 0x0001, "high"),
            ("get_contrast_enhancer", 0x001C, 0x0003, "middle"),
            ("get_advanced_iris", 0x001D, 0x0002, "full"),
            ("get_aspect_ratio", 0x0020, 0x000C, "zoom_1_85"),
            ("get_gamma_correction", 0x0022, 0x0005, 5),
            ("get_picture_muting", 0x0030, 0x0000, "off"),
            ("get_color_space", 0x003B, 0x0008, 8),
            ("get_motionflow", 0x0059, 0x0005, "true_cinema"),
            ("get_2d_3d_display_select", 0x0060, 0x0002, "2d"),
            ("get_3d_format", 0x0061, 0x0001, "side_by_side"),
            ("get_picture_position", 0x0066, 0x0003, "custom_2"),
            ("get_reality_creation", 0x0067, 0x0001, 1),
            ("get_hdmi1_dynamic_range", 0x006E, 0x0002, "full"),
            ("get_hdmi2_dynamic_range", 0x006F, 0x0001, "limited"),
            ("get_hdr", 0x007C, 0x0002, "auto"),
            ("get_input_lag_reduction", 0x0099, 0x0001, "on"),
            ("get_menu_position", 0x00A6, 0x0001, "center"),
            ("get_error_status", 0x0101, 0x0000, "no_error"),
            ("get_lamp_timer", 0x0113, 0x035E, 862),
        ]
        values = {command: value for _, command, value, _ in cases}

        def respond(payload: bytes) -> bytes:
            command = int.from_bytes(payload[7:9], byteorder="big")
            value = values[command]
            return b"\x02\x0aSONY\x01" + command.to_bytes(2, "big") + b"\x02" + value.to_bytes(2, "big")

        transport = FakeTransport(respond)
        client = SdcpClient("192.0.2.10", transport=transport)

        for method_name, command, _value, expected in cases:
            assert await getattr(client, method_name)() == expected
            assert transport.requests[-1] == b"\x02\x0aSONY\x01" + command.to_bytes(2, "big") + b"\x00"

    asyncio.run(run())


def test_sdcp_setters_use_expected_item_numbers_and_values() -> None:
    async def run() -> None:
        cases = [
            ("set_calibration_preset", "user", 0x0002, 0x0008),
            ("set_lamp_control", "high", 0x001A, 0x0001),
            ("set_contrast_enhancer", "middle", 0x001C, 0x0003),
            ("set_advanced_iris", "full", 0x001D, 0x0002),
            ("set_aspect_ratio", "zoom 1 85", 0x0020, 0x000C),
            ("set_picture_muting", True, 0x0030, 0x0001),
            ("set_motionflow", "true-cinema", 0x0059, 0x0005),
            ("set_2d_3d_display_select", "2d", 0x0060, 0x0002),
            ("set_3d_format", "side_by_side", 0x0061, 0x0001),
            ("set_picture_position", "custom_2", 0x0066, 0x0003),
            ("set_hdmi1_dynamic_range", "full", 0x006E, 0x0002),
            ("set_hdmi2_dynamic_range", "limited", 0x006F, 0x0001),
            ("set_hdr", "auto", 0x007C, 0x0002),
            ("set_input_lag_reduction", "on", 0x0099, 0x0001),
            ("set_menu_position", "center", 0x00A6, 0x0001),
        ]

        def respond(payload: bytes) -> bytes:
            command = payload[7:9]
            return b"\x02\x0aSONY\x01" + command + b"\x00"

        transport = FakeTransport(respond)
        client = SdcpClient("192.0.2.10", transport=transport)

        for method_name, value, command, expected_value in cases:
            await getattr(client, method_name)(value)
            assert transport.requests[-1] == (
                b"\x02\x0aSONY\x00" + command.to_bytes(2, "big") + b"\x02" + expected_value.to_bytes(2, "big")
            )

    asyncio.run(run())


def test_sdcp_setter_rejects_unknown_value() -> None:
    async def run() -> None:
        client = SdcpClient("192.0.2.10", transport=FakeTransport(lambda payload: b""))

        with pytest.raises(UnsupportedCommandError):
            await client.set_hdr("definitely_not_hdr")

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


def test_projector_facade_exposes_adcp_signal_getter() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"signal=1080p/24\r\n")
        projector = Projector("192.0.2.10", protocol=Protocol.ADCP, transport=transport)

        await projector.connect()

        assert await projector.get_signal() == "1080p/24"
        assert "signal" in projector.capabilities.supported
        assert transport.requests == [b"signal ?\r\n"]

    asyncio.run(run())


def test_projector_facade_exposes_adcp_temperature_getter() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b'temperature=[{"intake_air": 29}]\r\n')
        projector = Projector("192.0.2.10", protocol=Protocol.ADCP, transport=transport)

        await projector.connect()

        assert await projector.get_temperature() == 29
        assert "temperature" in projector.capabilities.supported
        assert transport.requests == [b"temperature ?\r\n"]

    asyncio.run(run())


def test_projector_facade_exposes_adcp_timer_getter() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b'timer=[{"light_src": 864}]\r\n')
        projector = Projector("192.0.2.10", protocol=Protocol.ADCP, transport=transport)

        await projector.connect()

        assert await projector.get_timer() == 864
        assert "timer" in projector.capabilities.supported
        assert transport.requests == [b"timer ?\r\n"]

    asyncio.run(run())


def test_projector_facade_exposes_adcp_picture_mode_getter() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"picture_mode=reference\r\n")
        projector = Projector("192.0.2.10", protocol=Protocol.ADCP, transport=transport)

        await projector.connect()

        assert await projector.get_picture_mode() == "reference"
        assert "picture_mode" in projector.capabilities.supported
        assert transport.requests == [b"picture_mode ?\r\n"]

    asyncio.run(run())


def test_projector_facade_exposes_adcp_color_space_getter() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"color_space=bt2020\r\n")
        projector = Projector("192.0.2.10", protocol=Protocol.ADCP, transport=transport)

        await projector.connect()

        assert await projector.get_color_space() == "bt2020"
        assert "color_space" in projector.capabilities.supported
        assert transport.requests == [b"color_space ?\r\n"]

    asyncio.run(run())


def test_projector_facade_exposes_adcp_lamp_control_getter() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"lamp_control=low\r\n")
        projector = Projector("192.0.2.10", protocol=Protocol.ADCP, transport=transport)

        await projector.connect()

        assert await projector.get_lamp_control() == "low"
        assert "lamp_control" in projector.capabilities.supported
        assert transport.requests == [b"lamp_control ?\r\n"]

    asyncio.run(run())


def test_projector_facade_exposes_adcp_warning_and_error_getters() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"warning ?\r\n":
                return b'warning=["warn_temp"]\r\n'
            if payload == b"error ?\r\n":
                return b"error=[]\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        projector = Projector("192.0.2.10", protocol=Protocol.ADCP, transport=transport)

        await projector.connect()

        assert await projector.get_warning() == ["warn_temp"]
        assert await projector.get_error() == []
        assert "warning" in projector.capabilities.supported
        assert "error" in projector.capabilities.supported
        assert transport.requests == [b"warning ?\r\n", b"error ?\r\n"]

    asyncio.run(run())


def test_projector_facade_exposes_adcp_hdr_aspect_and_dynamic_range_getters() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"hdr ?\r\n":
                return b"hdr=auto\r\n"
            if payload == b"aspect ?\r\n":
                return b"aspect=zoom\r\n"
            if payload == b"dynamic_range --hdmi1 ?\r\n":
                return b"dynamic_range=auto\r\n"
            if payload == b"dynamic_range --hdmi2 ?\r\n":
                return b"dynamic_range=full\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        projector = Projector("192.0.2.10", protocol=Protocol.ADCP, transport=transport)

        await projector.connect()

        assert await projector.get_hdr() == "auto"
        assert await projector.get_aspect_ratio() == "zoom"
        assert await projector.get_hdmi1_dynamic_range() == "auto"
        assert await projector.get_hdmi2_dynamic_range() == "full"
        assert "hdr" in projector.capabilities.supported
        assert "aspect_ratio" in projector.capabilities.supported
        assert "hdmi1_dynamic_range" in projector.capabilities.supported
        assert "hdmi2_dynamic_range" in projector.capabilities.supported

    asyncio.run(run())


def test_projector_facade_exposes_adcp_identity_system_getters() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"modelname ?\r\n":
                return b"modelname=VPL-VW285ES\r\n"
            if payload == b"serialnum ?\r\n":
                return b"serialnum=5102851\r\n"
            if payload == b"version ?\r\n":
                return b"version=1.000\r\n"
            if payload == b"mac_address ?\r\n":
                return b"mac_address=00:11:22:33:44:55\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        projector = Projector("192.0.2.10", protocol=Protocol.ADCP, transport=transport)

        await projector.connect()

        assert await projector.get_model_name() == "VPL-VW285ES"
        assert await projector.get_serial_number() == "5102851"
        assert await projector.get_version() == "1.000"
        assert await projector.get_mac_address() == "00:11:22:33:44:55"
        assert "model_name" in projector.capabilities.supported
        assert "serial_number" in projector.capabilities.supported
        assert "version" in projector.capabilities.supported
        assert "mac_address" in projector.capabilities.supported

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


def test_projector_facade_exposes_sdcp_specific_getters() -> None:
    async def run() -> None:
        get_lamp_timer = bytes.fromhex("02 0A 53 4F 4E 59 01 01 13 00")
        lamp_timer_response = bytes.fromhex("02 0A 53 4F 4E 59 01 01 13 02 03 5E")

        def respond(payload: bytes) -> bytes:
            if payload == get_lamp_timer:
                return lamp_timer_response
            raise AssertionError(payload.hex(" "))

        transport = FakeTransport(respond)
        projector = Projector("192.0.2.10", protocol=Protocol.SDCP, transport=transport)

        await projector.connect()

        assert await projector.get_lamp_timer() == 862
        assert transport.requests == [get_lamp_timer]

    asyncio.run(run())


def test_projector_facade_exposes_sdcp_specific_setters() -> None:
    async def run() -> None:
        set_hdr_auto = bytes.fromhex("02 0A 53 4F 4E 59 00 00 7C 02 00 02")
        ok_response = bytes.fromhex("02 0A 53 4F 4E 59 01 00 7C 00")

        def respond(payload: bytes) -> bytes:
            if payload == set_hdr_auto:
                return ok_response
            raise AssertionError(payload.hex(" "))

        transport = FakeTransport(respond)
        projector = Projector("192.0.2.10", protocol=Protocol.SDCP, transport=transport)

        await projector.connect()

        await projector.set_hdr("auto")
        assert transport.requests == [set_hdr_auto]

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
