from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from sony_projector_protocol import (DEFAULT_SDCP_COMMUNITY,
                                     FEATURE_ADCP_PICTURE_MODE,
                                     FEATURE_SDCP_CALIBRATION_PRESET,
                                     PROTOCOL_ADCP, PROTOCOL_SDCP,
                                     SDCP_CALIBRATION_PRESET_VALUES,
                                     SERIES_BY_KEY,
                                     PackageUnsupportedCommandError, Projector,
                                     ProjectorIdentity,
                                     ProjectorUnsupportedCommandError,
                                     discover, get_adcp_picture_mode_options,
                                     get_feature_values, get_projector_series,
                                     get_series_feature_values,
                                     normalize_model_name, parse_sdap_packet)
from sony_projector_protocol.adcp import AdcpClient
from sony_projector_protocol.discovery import DiscoveredProjector
from sony_projector_protocol.exceptions import UnsupportedCommandError
from sony_projector_protocol.sdcp import SdcpClient
from sony_projector_protocol.transport import FakeTransport, StreamTransport

_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "captured_sessions"


def test_adcp_power_commands() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"power_status ?\r\n":
                return b"power_status=on\r\n"
            if payload == b'power "off"\r\n':
                return b"ok\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_power() == "on"
        await client.set_power(False)

        assert transport.requests == [b"power_status ?\r\n", b'power "off"\r\n']

    asyncio.run(run())


def test_adcp_power_status_values_follow_sony_command_list() -> None:
    async def run() -> None:
        values = (
            "standby",
            "startup",
            "on",
            "cooling1",
            "cooling2",
            "saving_cooling1",
            "saving_cooling2",
            "saving_standby",
            "update",
        )

        for value in values:
            transport = FakeTransport(lambda payload, value=value: f'power_status="{value}"\r\n'.encode("ascii"))
            client = AdcpClient("192.0.2.10", transport=transport)

            assert await client.get_power() == value
            assert transport.requests == [b"power_status ?\r\n"]

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
            if payload == b'picture_mode "reference"\r\n':
                return b"ok\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_picture_mode() == "cinema_film1"
        await client.set_picture_mode("reference")
        assert transport.requests == [b"picture_mode ?\r\n", b'picture_mode "reference"\r\n']

    asyncio.run(run())


@pytest.mark.parametrize(
    ("response", "expected"),
    (
        (b"picture_mode=cinema_film1\r\n", "cinema_film1"),
        (b'picture_mode="cinema_film1"\r\n', "cinema_film1"),
        (b'picture_mode "cinema_film1"\r\n', "cinema_film1"),
        (b'"cinema_film1"\r\n', "cinema_film1"),
        (b"cinema_film1\r\n", "cinema_film1"),
    ),
)
def test_adcp_picture_mode_getter_parses_response_shapes(response: bytes, expected: str) -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: response)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_picture_mode() == expected
        assert transport.requests == [b"picture_mode ?\r\n"]

    asyncio.run(run())


def test_adcp_picture_mode_getter_parses_command_value_response() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b'picture_mode "cinema_film1"\r\n')
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_picture_mode() == "cinema_film1"

    asyncio.run(run())


@pytest.mark.parametrize(
    "mode",
    (
        "cinema_film1",
        "cinema_film2",
        "reference",
        "tv",
        "photo",
        "brt_cinema",
        "brt_tv",
        "user",
        "user1",
        "user2",
        "user3",
        "cinema_digital",
        "game",
    ),
)
def test_adcp_picture_mode_accepts_sony_video_projector_values(mode: str) -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"ok\r\n")
        client = AdcpClient("192.0.2.10", transport=transport)

        await client.set_picture_mode(mode)

        assert transport.requests == [f'picture_mode "{mode}"\r\n'.encode("ascii")]

    asyncio.run(run())


@pytest.mark.parametrize(
    "mode",
    (
        "dynamic",
        "standard",
        "brt_priority",
        "multi_screen",
        "presentation",
        "blackboard",
        "whiteboard",
        "cinema",
        "vivid",
        "srgb",
    ),
)
def test_adcp_picture_mode_accepts_sony_data_projector_values(mode: str) -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"ok\r\n")
        client = AdcpClient("192.0.2.10", transport=transport)

        await client.set_picture_mode(mode)

        assert transport.requests == [f'picture_mode "{mode}"\r\n'.encode("ascii")]

    asyncio.run(run())


@pytest.mark.parametrize(
    ("mode", "device_value"),
    (
        ("bright_cinema", "brt_cinema"),
        ("Bright TV", "brt_tv"),
        ('"cinema_film1"', "cinema_film1"),
    ),
)
def test_adcp_picture_mode_normalizes_common_aliases(mode: str, device_value: str) -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"ok\r\n")
        client = AdcpClient("192.0.2.10", transport=transport)

        await client.set_picture_mode(mode)

        assert transport.requests == [f'picture_mode "{device_value}"\r\n'.encode("ascii")]

    asyncio.run(run())


@pytest.mark.parametrize("mode", ("sports", "movie_bright", "cinema_bright"))
def test_adcp_picture_mode_rejects_unsupported_value(mode: str) -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"ok\r\n")
        client = AdcpClient("192.0.2.10", transport=transport)

        with pytest.raises(PackageUnsupportedCommandError):
            await client.set_picture_mode(mode)

        assert transport.requests == []

    asyncio.run(run())


@pytest.mark.parametrize(
    ("model", "expected"),
    (
        (
            "VPL-XW5000",
            (
                "cinema_film1",
                "cinema_film2",
                "reference",
                "tv",
                "photo",
                "brt_cinema",
                "brt_tv",
                "game",
                "user1",
                "user3",
            ),
        ),
        (
            "VPL-VW5000",
            (
                "cinema_film1",
                "cinema_film2",
                "reference",
                "tv",
                "photo",
                "brt_cinema",
                "brt_tv",
                "game",
                "user1",
                "user2",
                "user3",
                "cinema_digital",
            ),
        ),
        (
            "VPL-VW285ES",
            (
                "cinema_film1",
                "cinema_film2",
                "reference",
                "tv",
                "photo",
                "brt_cinema",
                "brt_tv",
                "game",
                "user",
            ),
        ),
        (
            "VPL-VW315ES",
            (
                "cinema_film1",
                "cinema_film2",
                "reference",
                "tv",
                "photo",
                "brt_cinema",
                "brt_tv",
                "game",
                "user",
            ),
        ),
        ("VPL-FHZ120L", ("dynamic", "standard", "brt_priority", "multi_screen", "srgb")),
        (
            "VPL-EX345",
            ("dynamic", "standard", "presentation", "blackboard", "whiteboard", "cinema", "srgb"),
        ),
        (
            "VPL-EX575",
            ("dynamic", "standard", "presentation", "blackboard", "whiteboard", "cinema", "vivid"),
        ),
    ),
)
def test_adcp_picture_mode_options_for_known_models(model: str, expected: tuple[str, ...]) -> None:
    assert get_adcp_picture_mode_options(model) == expected
    assert get_feature_values(model, FEATURE_ADCP_PICTURE_MODE) == expected
    assert get_feature_values(model, FEATURE_ADCP_PICTURE_MODE, protocol=PROTOCOL_ADCP) == expected


@pytest.mark.parametrize(
    ("model", "normalized"),
    (
        (" vpl-xw5000 ", "VPL-XW5000"),
        ("xw5000", "VPL-XW5000"),
        ("vw-365es", "VPL-VW365ES"),
        ("VPL_XW5000", "VPL-XW5000"),
    ),
)
def test_capability_model_normalization(model: str, normalized: str) -> None:
    assert normalize_model_name(model) == normalized
    assert get_adcp_picture_mode_options(model) == get_adcp_picture_mode_options(normalized)


def test_capability_lookup_returns_none_for_unknown_model_or_feature() -> None:
    assert get_projector_series("VPL-NOTREAL") is None
    assert get_adcp_picture_mode_options("VPL-NOTREAL") is None
    assert get_feature_values("VPL-XW5000", "not_a_feature") is None
    assert get_feature_values("VPL-XW5000", "picture_mode") is None
    assert get_feature_values("VPL-XW5000", FEATURE_SDCP_CALIBRATION_PRESET) == SDCP_CALIBRATION_PRESET_VALUES


def test_capability_series_lookup() -> None:
    series = get_projector_series("VPL-XW5000")

    assert series is not None
    assert series.key == "adcp_video_xw5000"
    assert series.display_name == "XW5000"
    assert get_projector_series("VPL-XW5000", protocol=PROTOCOL_ADCP) == series
    assert get_series_feature_values(series.key, FEATURE_ADCP_PICTURE_MODE) == get_adcp_picture_mode_options(
        "VPL-XW5000"
    )
    assert get_series_feature_values(series.key, "not_a_feature") is None


def test_sdcp_capability_lookup_allows_any_returned_model() -> None:
    known_model_series = get_projector_series("VPL-XW5000", protocol=PROTOCOL_SDCP)
    unknown_model_series = get_projector_series("VPL-NOTREAL", protocol=PROTOCOL_SDCP)

    assert known_model_series is not None
    assert known_model_series.key == "sdcp_any_model"
    assert unknown_model_series == known_model_series
    assert get_feature_values("VPL-XW5000", FEATURE_SDCP_CALIBRATION_PRESET, protocol=PROTOCOL_SDCP) == (
        SDCP_CALIBRATION_PRESET_VALUES
    )
    assert get_feature_values("VPL-NOTREAL", FEATURE_SDCP_CALIBRATION_PRESET, protocol=PROTOCOL_SDCP) == (
        SDCP_CALIBRATION_PRESET_VALUES
    )


def test_capability_video_model_list_uses_official_series_mapping() -> None:
    assert get_projector_series("VPL-VW315ES").display_name == "VW365ES"  # type: ignore[union-attr]
    assert get_projector_series("VPL-VW385ES").display_name == "VW360ES"  # type: ignore[union-attr]
    assert get_projector_series("VPL-VW1025ES").display_name == "VW890ES/VW870ES"  # type: ignore[union-attr]
    assert get_projector_series("VPL-XW5100").display_name == "XW5100"  # type: ignore[union-attr]


def test_capability_models_map_to_one_series() -> None:
    models_by_protocol: dict[tuple[str, str], list[str]] = {}
    for series in SERIES_BY_KEY.values():
        for model in series.models:
            key = (series.protocol, normalize_model_name(model))
            models_by_protocol.setdefault(key, []).append(series.key)

    assert {model: keys for model, keys in models_by_protocol.items() if len(keys) > 1} == {}


def test_adcp_color_space_command() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"color_space ?\r\n":
                return b"color_space=bt709\r\n"
            if payload == b'color_space "bt2020"\r\n':
                return b"ok\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_color_space() == "bt709"
        await client.set_color_space("bt2020")
        assert transport.requests == [b"color_space ?\r\n", b'color_space "bt2020"\r\n']

    asyncio.run(run())


def test_adcp_lamp_control_command() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"lamp_control ?\r\n":
                return b"lamp_control=high\r\n"
            if payload == b'lamp_control "low"\r\n':
                return b"ok\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_lamp_control() == "high"
        await client.set_lamp_control("low")
        assert transport.requests == [b"lamp_control ?\r\n", b'lamp_control "low"\r\n']

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
            if payload == b'hdr "auto"\r\n':
                return b"ok\r\n"
            if payload == b"aspect ?\r\n":
                return b"aspect=normal\r\n"
            if payload == b'aspect "zoom"\r\n':
                return b"ok\r\n"
            if payload == b"dynamic_range --hdmi1 ?\r\n":
                return b"dynamic_range=full\r\n"
            if payload == b'dynamic_range --hdmi1 "auto"\r\n':
                return b"ok\r\n"
            if payload == b"dynamic_range --hdmi2 ?\r\n":
                return b"dynamic_range=limited\r\n"
            if payload == b'dynamic_range --hdmi2 "full"\r\n':
                return b"ok\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_hdr() == "hdr10"
        await client.set_hdr("auto")
        assert await client.get_aspect_ratio() == "normal"
        await client.set_aspect_ratio("zoom")
        assert await client.get_hdmi1_dynamic_range() == "full"
        await client.set_hdmi1_dynamic_range("auto")
        assert await client.get_hdmi2_dynamic_range() == "limited"
        await client.set_hdmi2_dynamic_range("full")
        assert transport.requests == [
            b"hdr ?\r\n",
            b'hdr "auto"\r\n',
            b"aspect ?\r\n",
            b'aspect "zoom"\r\n',
            b"dynamic_range --hdmi1 ?\r\n",
            b'dynamic_range --hdmi1 "auto"\r\n',
            b"dynamic_range --hdmi2 ?\r\n",
            b'dynamic_range --hdmi2 "full"\r\n',
        ]

    asyncio.run(run())


def test_adcp_dynamic_range_rejects_unknown_input() -> None:
    async def run() -> None:
        client = AdcpClient("192.0.2.10", transport=FakeTransport(lambda payload: b""))

        with pytest.raises(PackageUnsupportedCommandError):
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
            if payload == b"mac_address ?\r\n":
                return b"mac_address=00:11:22:33:44:55\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        client = AdcpClient("192.0.2.10", transport=transport)

        assert await client.get_identity() == ProjectorIdentity(
            model="VPL-XW5000ES",
            serial="12345",
            mac_address="00:11:22:33:44:55",
        )
        assert transport.requests == [b"modelname ?\r\n", b"serialnum ?\r\n", b"mac_address ?\r\n"]

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

        class FakeReader:
            def __init__(self, responses: list[bytes]) -> None:
                self.responses = responses

            async def readuntil(self, separator: bytes) -> bytes:
                del separator
                return self.responses.pop(0)

        class FakeWriter:
            def write(self, payload: bytes) -> None:
                requests.append(payload)

            async def drain(self) -> None:
                return None

            def close(self) -> None:
                return None

            async def wait_closed(self) -> None:
                return None

        class MemoryStreamTransport(StreamTransport):
            async def connect(self) -> None:
                self.reader = FakeReader([challenge.encode("ascii") + b"\r\n", b"ok\r\n", b'"on"\r\n'])  # type: ignore[assignment]
                self.writer = FakeWriter()  # type: ignore[assignment]

        transport = MemoryStreamTransport("127.0.0.1", 0, terminator=b"\r\n")
        client = AdcpClient("127.0.0.1", transport=transport, password="Projector1")

        await client.connect()
        try:
            assert await client.get_power() == "on"
        finally:
            await client.close()

        assert requests == [expected_digest + b"\r\n", b"power_status ?\r\n"]

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

        assert await client.get_input() == "hdmi1"
        await client.set_input("hdmi2")
        assert transport.requests == [get_input, set_hdmi2]

    asyncio.run(run())


def test_sdcp_uses_default_community_when_not_provided() -> None:
    async def run() -> None:
        get_power = b"\x02\x0a" + DEFAULT_SDCP_COMMUNITY.encode("ascii") + b"\x01\x01\x02\x00"
        power_response = b"\x02\x0a" + DEFAULT_SDCP_COMMUNITY.encode("ascii") + b"\x01\x01\x02\x02\x00\x03"

        transport = FakeTransport(lambda payload: power_response)
        client = SdcpClient("192.0.2.10", transport=transport)

        assert await client.get_power() == "on"
        assert transport.requests == [get_power]

    asyncio.run(run())


def test_sdcp_uses_configured_community() -> None:
    async def run() -> None:
        get_power = b"\x02\x0aABCD\x01\x01\x02\x00"
        power_response = b"\x02\x0aABCD\x01\x01\x02\x02\x00\x03"

        transport = FakeTransport(lambda payload: power_response)
        client = SdcpClient("192.0.2.10", transport=transport, community="ABCD")

        assert await client.get_power() == "on"
        assert transport.requests == [get_power]

    asyncio.run(run())


def test_sdcp_none_community_uses_default() -> None:
    async def run() -> None:
        get_power = b"\x02\x0aSONY\x01\x01\x02\x00"
        power_response = b"\x02\x0aSONY\x01\x01\x02\x02\x00\x03"

        transport = FakeTransport(lambda payload: power_response)
        client = SdcpClient("192.0.2.10", transport=transport, community=None)

        assert await client.get_power() == "on"
        assert transport.requests == [get_power]

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

        with pytest.raises(PackageUnsupportedCommandError):
            await client.set_hdr("definitely_not_hdr")

    asyncio.run(run())


def test_projector_facade_uses_configured_protocol() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"power=standby\r")
        projector = Projector("192.0.2.10", protocol="adcp", transport=transport)

        await projector.connect()

        assert transport.connected is True
        assert await projector.get_power() == "standby"

    asyncio.run(run())


def test_projector_requires_explicit_protocol() -> None:
    with pytest.raises(TypeError):
        Projector("192.0.2.10")  # type: ignore[call-arg]


def test_projector_rejects_auto_protocol() -> None:
    with pytest.raises(ValueError):
        Projector("192.0.2.10", protocol="auto")


def test_projector_facade_exposes_adcp_signal_getter() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b"signal=1080p/24\r\n")
        projector = Projector("192.0.2.10", protocol="adcp", transport=transport)

        await projector.connect()

        assert await projector.get_signal() == "1080p/24"
        assert transport.requests == [b"signal ?\r\n"]

    asyncio.run(run())


def test_projector_facade_rejects_wrong_protocol_command() -> None:
    async def run() -> None:
        projector = Projector("192.0.2.10", protocol="sdcp", transport=FakeTransport(lambda payload: b""))

        await projector.connect()

        with pytest.raises(PackageUnsupportedCommandError):
            await projector.get_signal()

    asyncio.run(run())


def test_projector_facade_reraises_device_unsupported_command() -> None:
    async def run() -> None:
        projector = Projector(
            "192.0.2.10",
            protocol="adcp",
            transport=FakeTransport(lambda payload: b"unsupported\r\n"),
        )

        await projector.connect()

        with pytest.raises(ProjectorUnsupportedCommandError) as exc_info:
            await projector.get_signal()

        assert exc_info.value.protocol == "adcp"
        assert exc_info.value.command == "signal ?"
        assert exc_info.value.response == "unsupported"
        assert exc_info.value.response_text == "unsupported"
        assert exc_info.value.response_hex is None

    asyncio.run(run())


def test_sdcp_projector_unsupported_error_exposes_response_frame() -> None:
    async def run() -> None:
        unsupported_lamp_timer = bytes.fromhex("02 0A 53 4F 4E 59 00 01 13 02 01 80")
        client = SdcpClient("192.0.2.10", transport=FakeTransport(lambda payload: unsupported_lamp_timer))

        with pytest.raises(ProjectorUnsupportedCommandError) as exc_info:
            await client.get_lamp_timer()

        assert exc_info.value.protocol == "sdcp"
        assert exc_info.value.command == "0x0113"
        assert exc_info.value.response == unsupported_lamp_timer
        assert exc_info.value.response_hex == unsupported_lamp_timer.hex(" ")
        assert "Item Error: Not Applicable Item" in str(exc_info.value)

    asyncio.run(run())


def test_projector_facade_exposes_adcp_temperature_getter() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b'temperature=[{"intake_air": 29}]\r\n')
        projector = Projector("192.0.2.10", protocol="adcp", transport=transport)

        await projector.connect()

        assert await projector.get_temperature() == 29
        assert transport.requests == [b"temperature ?\r\n"]

    asyncio.run(run())


def test_projector_facade_exposes_adcp_timer_getter() -> None:
    async def run() -> None:
        transport = FakeTransport(lambda payload: b'timer=[{"light_src": 864}]\r\n')
        projector = Projector("192.0.2.10", protocol="adcp", transport=transport)

        await projector.connect()

        assert await projector.get_timer() == 864
        assert transport.requests == [b"timer ?\r\n"]

    asyncio.run(run())


def test_projector_facade_exposes_adcp_picture_mode_getter_and_setter() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"picture_mode ?\r\n":
                return b"picture_mode=reference\r\n"
            if payload == b'picture_mode "cinema_film1"\r\n':
                return b"ok\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        projector = Projector("192.0.2.10", protocol="adcp", transport=transport)

        await projector.connect()

        assert await projector.get_picture_mode() == "reference"
        await projector.set_picture_mode("cinema_film1")
        assert transport.requests == [b"picture_mode ?\r\n", b'picture_mode "cinema_film1"\r\n']

    asyncio.run(run())


def test_projector_facade_exposes_adcp_color_space_getter_and_setter() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"color_space ?\r\n":
                return b"color_space=bt2020\r\n"
            if payload == b'color_space "bt709"\r\n':
                return b"ok\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        projector = Projector("192.0.2.10", protocol="adcp", transport=transport)

        await projector.connect()

        assert await projector.get_color_space() == "bt2020"
        await projector.set_color_space("bt709")
        assert transport.requests == [b"color_space ?\r\n", b'color_space "bt709"\r\n']

    asyncio.run(run())


def test_projector_facade_exposes_adcp_lamp_control_getter_and_setter() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"lamp_control ?\r\n":
                return b"lamp_control=low\r\n"
            if payload == b'lamp_control "high"\r\n':
                return b"ok\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        projector = Projector("192.0.2.10", protocol="adcp", transport=transport)

        await projector.connect()

        assert await projector.get_lamp_control() == "low"
        await projector.set_lamp_control("high")
        assert transport.requests == [b"lamp_control ?\r\n", b'lamp_control "high"\r\n']

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
        projector = Projector("192.0.2.10", protocol="adcp", transport=transport)

        await projector.connect()

        assert await projector.get_warning() == ["warn_temp"]
        assert await projector.get_error() == []
        assert transport.requests == [b"warning ?\r\n", b"error ?\r\n"]

    asyncio.run(run())


def test_projector_facade_exposes_adcp_hdr_aspect_and_dynamic_range_getters() -> None:
    async def run() -> None:
        def respond(payload: bytes) -> bytes:
            if payload == b"hdr ?\r\n":
                return b"hdr=auto\r\n"
            if payload == b'hdr "hdr10"\r\n':
                return b"ok\r\n"
            if payload == b"aspect ?\r\n":
                return b"aspect=zoom\r\n"
            if payload == b'aspect "normal"\r\n':
                return b"ok\r\n"
            if payload == b"dynamic_range --hdmi1 ?\r\n":
                return b"dynamic_range=auto\r\n"
            if payload == b'dynamic_range --hdmi1 "full"\r\n':
                return b"ok\r\n"
            if payload == b"dynamic_range --hdmi2 ?\r\n":
                return b"dynamic_range=full\r\n"
            if payload == b'dynamic_range --hdmi2 "auto"\r\n':
                return b"ok\r\n"
            raise AssertionError(payload)

        transport = FakeTransport(respond)
        projector = Projector("192.0.2.10", protocol="adcp", transport=transport)

        await projector.connect()

        assert await projector.get_hdr() == "auto"
        await projector.set_hdr("hdr10")
        assert await projector.get_aspect_ratio() == "zoom"
        await projector.set_aspect_ratio("normal")
        assert await projector.get_hdmi1_dynamic_range() == "auto"
        await projector.set_hdmi1_dynamic_range("full")
        assert await projector.get_hdmi2_dynamic_range() == "full"
        await projector.set_hdmi2_dynamic_range("auto")

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
        projector = Projector("192.0.2.10", protocol="adcp", transport=transport)

        await projector.connect()

        assert await projector.get_model_name() == "VPL-VW285ES"
        assert await projector.get_serial_number() == "5102851"
        assert await projector.get_version() == "1.000"
        assert await projector.get_mac_address() == "00:11:22:33:44:55"

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
        projector = Projector("192.0.2.10", protocol="sdcp", transport=transport)

        await projector.connect()

        assert await projector.get_input() == "hdmi2"
        assert transport.requests == [get_input]

    asyncio.run(run())


def test_projector_facade_passes_sdcp_community() -> None:
    async def run() -> None:
        get_input = bytes.fromhex("02 0A 41 42 43 44 01 00 01 00")
        input_hdmi2_response = bytes.fromhex("02 0A 41 42 43 44 01 00 01 02 00 03")

        def respond(payload: bytes) -> bytes:
            if payload == get_input:
                return input_hdmi2_response
            raise AssertionError(payload.hex(" "))

        transport = FakeTransport(respond)
        projector = Projector("192.0.2.10", protocol="sdcp", transport=transport, community="ABCD")

        await projector.connect()

        assert await projector.get_input() == "hdmi2"
        assert transport.requests == [get_input]

    asyncio.run(run())


def test_projector_facade_defaults_missing_sdcp_community() -> None:
    async def run() -> None:
        get_input = bytes.fromhex("02 0A 53 4F 4E 59 01 00 01 00")
        input_hdmi2_response = bytes.fromhex("02 0A 53 4F 4E 59 01 00 01 02 00 03")

        transport = FakeTransport(lambda payload: input_hdmi2_response)
        projector = Projector("192.0.2.10", protocol="sdcp", transport=transport, community=None)

        await projector.connect()

        assert await projector.get_input() == "hdmi2"
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
        projector = Projector("192.0.2.10", protocol="sdcp", transport=transport)

        await projector.connect()

        assert await projector.get_lamp_timer() == 862
        assert transport.requests == [get_lamp_timer]

    asyncio.run(run())


def test_sdcp_identity_uses_equipment_info_items() -> None:
    async def run() -> None:
        get_model = bytes.fromhex("02 0A 53 4F 4E 59 01 80 01 00")
        get_serial = bytes.fromhex("02 0A 53 4F 4E 59 01 80 02 00")
        get_location = bytes.fromhex("02 0A 53 4F 4E 59 01 80 03 00")
        get_mac = bytes.fromhex("02 0A 53 4F 4E 59 01 90 00 00")
        model_response = b"\x02\x0aSONY\x01\x80\x01\x0cVPL-VW285ES\x00"
        serial_response = b"\x02\x0aSONY\x01\x80\x02\x04" + (12345).to_bytes(4, byteorder="big")
        location_response = b"\x02\x0aSONY\x01\x80\x03\x18Theater\x00" + b"\x00" * 16
        mac_response = b"\x02\x0aSONY\x01\x90\x00\x06\x00\x11\x22\x33\x44\x55"

        def respond(payload: bytes) -> bytes:
            if payload == get_model:
                return model_response
            if payload == get_serial:
                return serial_response
            if payload == get_location:
                return location_response
            if payload == get_mac:
                return mac_response
            raise AssertionError(payload.hex(" "))

        transport = FakeTransport(respond)
        client = SdcpClient("192.0.2.10", transport=transport)

        assert await client.get_model_name() == "VPL-VW285ES"
        assert await client.get_serial_number() == "00012345"
        assert await client.get_installation_location() == "Theater"
        assert await client.get_mac_address() == "00:11:22:33:44:55"
        assert await client.get_identity() == ProjectorIdentity(
            model="VPL-VW285ES",
            serial="00012345",
            location="Theater",
            mac_address="00:11:22:33:44:55",
        )
        assert transport.requests == [
            get_model,
            get_serial,
            get_location,
            get_mac,
            get_model,
            get_serial,
            get_location,
            get_mac,
        ]

    asyncio.run(run())


def test_projector_facade_exposes_sdcp_identity() -> None:
    async def run() -> None:
        get_model = bytes.fromhex("02 0A 53 4F 4E 59 01 80 01 00")
        get_serial = bytes.fromhex("02 0A 53 4F 4E 59 01 80 02 00")
        get_location = bytes.fromhex("02 0A 53 4F 4E 59 01 80 03 00")
        get_mac = bytes.fromhex("02 0A 53 4F 4E 59 01 90 00 00")

        def respond(payload: bytes) -> bytes:
            if payload == get_model:
                return b"\x02\x0aSONY\x01\x80\x01\x0cVPL-XW5000ES"
            if payload == get_serial:
                return b"\x02\x0aSONY\x01\x80\x02\x04" + (5102851).to_bytes(4, byteorder="big")
            if payload == get_location:
                return b"\x02\x0aSONY\x01\x80\x03\x18Ceiling\x00" + b"\x00" * 16
            if payload == get_mac:
                return b"\x02\x0aSONY\x01\x90\x00\x06\xaa\xbb\xcc\xdd\xee\xff"
            raise AssertionError(payload.hex(" "))

        projector = Projector("192.0.2.10", protocol="sdcp", transport=FakeTransport(respond))

        await projector.connect()

        assert await projector.get_identity() == ProjectorIdentity(
            model="VPL-XW5000ES",
            serial="05102851",
            location="Ceiling",
            mac_address="AA:BB:CC:DD:EE:FF",
        )
        assert await projector.get_model_name() == "VPL-XW5000ES"
        assert await projector.get_serial_number() == "05102851"
        assert await projector.get_installation_location() == "Ceiling"
        assert await projector.get_mac_address() == "AA:BB:CC:DD:EE:FF"

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
        projector = Projector("192.0.2.10", protocol="sdcp", transport=transport)

        await projector.connect()

        await projector.set_hdr("auto")
        assert transport.requests == [set_hdr_auto]

    asyncio.run(run())


@pytest.mark.parametrize("fixture_name", ["adcp_basic.json", "sdcp_basic.json"])
def test_captured_session_fixture_replays_through_client(fixture_name: str) -> None:
    async def run() -> None:
        fixture = json.loads((_FIXTURE_DIR / fixture_name).read_text(encoding="utf-8"))
        commands = fixture["commands"]
        responses = {bytes.fromhex(item["request_hex"]): bytes.fromhex(item["response_hex"]) for item in commands}

        def respond(payload: bytes) -> bytes:
            try:
                return responses[payload]
            except KeyError as exc:
                raise AssertionError(payload.hex()) from exc

        if fixture["protocol"] == "adcp":
            client = AdcpClient("192.0.2.10", transport=FakeTransport(respond))
        else:
            client = SdcpClient("192.0.2.10", transport=FakeTransport(respond))

        for item in commands:
            method = getattr(client, item["method"])
            args = item.get("args", [])
            if item.get("expected_exception") == "UnsupportedCommandError":
                with pytest.raises(UnsupportedCommandError):
                    await method(*args)
            else:
                assert await method(*args) == item["expected"]

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


def test_discover_defaults_to_sixty_seconds() -> None:
    assert inspect.signature(discover).parameters["timeout"].default == 60.0
