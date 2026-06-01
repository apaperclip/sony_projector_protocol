"""SDCP / PJ Talk client implementation."""

from __future__ import annotations

from dataclasses import dataclass
from struct import pack_into, unpack

from sony_projector_protocol.exceptions import (
    PackageUnsupportedCommandError, ProjectorProtocolError,
    ProjectorUnsupportedCommandError)
from sony_projector_protocol.transport import StreamTransport, Transport
from sony_projector_protocol.types import ProjectorIdentity

SDCP_PORT = 53484
DEFAULT_SDCP_COMMUNITY = "SONY"

_ACTION_GET = 0x01
_ACTION_SET = 0x00

_COMMAND_SET_POWER = 0x0130
_COMMAND_INPUT = 0x0001
_COMMAND_CALIBRATION_PRESET = 0x0002
_COMMAND_COLOR_TEMP = 0x0017
_COMMAND_LAMP_CONTROL = 0x001A
_COMMAND_CONTRAST_ENHANCER = 0x001C
_COMMAND_ADVANCED_IRIS = 0x001D
_COMMAND_ASPECT_RATIO = 0x0020
_COMMAND_GAMMA_CORRECTION = 0x0022
_COMMAND_PICTURE_MUTING = 0x0030
_COMMAND_COLOR_SPACE = 0x003B
_COMMAND_MOTIONFLOW = 0x0059
_COMMAND_2D_3D_DISPLAY_SELECT = 0x0060
_COMMAND_3D_FORMAT = 0x0061
_COMMAND_PICTURE_POSITION = 0x0066
_COMMAND_REALITY_CREATION = 0x0067
_COMMAND_HDMI1_DYNAMIC_RANGE = 0x006E
_COMMAND_HDMI2_DYNAMIC_RANGE = 0x006F
_COMMAND_HDR = 0x007C
_COMMAND_INPUT_LAG_REDUCTION = 0x0099
_COMMAND_MENU_POSITION = 0x00A6
_COMMAND_STATUS_ERROR = 0x0101
_COMMAND_STATUS_POWER = 0x0102
_COMMAND_LAMP_TIMER = 0x0113
_COMMAND_MODEL_NAME = 0x8001
_COMMAND_SERIAL_NUMBER = 0x8002
_COMMAND_INSTALLATION_LOCATION = 0x8003
_COMMAND_MAC_ADDRESS = 0x9000

_POWER_STANDBY = 0x0000
_POWER_START_UP = 0x0001
_POWER_START_UP_LAMP = 0x0002
_POWER_ON = 0x0003
_POWER_COOLING = 0x0004
_POWER_COOLING2 = 0x0005

_INPUT_TO_DEVICE = {
    "hdmi1": 0x0002,
    "hdmi2": 0x0003,
    "hdmi_1": 0x0002,
    "hdmi_2": 0x0003,
}

_INPUT_FROM_DEVICE = {0x0002: "hdmi1", 0x0003: "hdmi2"}


def _invert(mapping: dict[int, str]) -> dict[str, int]:
    return {value: key for key, value in mapping.items()}


def _normalize_value(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


_POWER_FROM_DEVICE = {
    _POWER_STANDBY: "standby",
    _POWER_START_UP: "start_up",
    _POWER_START_UP_LAMP: "start_up_lamp",
    _POWER_ON: "on",
    _POWER_COOLING: "cooling",
    _POWER_COOLING2: "cooling2",
}

_CALIBRATION_PRESET_FROM_DEVICE = {
    0x0000: "cinema_film_1",
    0x0001: "cinema_film_2",
    0x0002: "ref",
    0x0003: "tv",
    0x0004: "photo",
    0x0005: "game",
    0x0006: "bright_cinema",
    0x0007: "bright_tv",
    0x0008: "user",
}

_LAMP_CONTROL_FROM_DEVICE = {0x0000: "low", 0x0001: "high"}
_CONTRAST_ENHANCER_FROM_DEVICE = {0x0000: "off", 0x0001: "low", 0x0002: "high", 0x0003: "middle"}
_ADVANCED_IRIS_FROM_DEVICE = {0x0000: "off", 0x0002: "full", 0x0003: "limited"}
_ASPECT_RATIO_FROM_DEVICE = {
    0x0001: "normal",
    0x000B: "v_stretch",
    0x000C: "zoom_1_85",
    0x000D: "zoom_2_35",
    0x000E: "stretch",
    0x000F: "squeeze",
}
_ON_OFF_FROM_DEVICE = {0x0000: "off", 0x0001: "on"}
_MOTIONFLOW_FROM_DEVICE = {
    0x0000: "off",
    0x0001: "smooth_high",
    0x0002: "smooth_low",
    0x0003: "impulse",
    0x0004: "combination",
    0x0005: "true_cinema",
}
_DISPLAY_SELECT_FROM_DEVICE = {0x0000: "auto", 0x0001: "3d", 0x0002: "2d"}
_THREE_D_FORMAT_FROM_DEVICE = {0x0000: "simulated_3d", 0x0001: "side_by_side", 0x0002: "over_under"}
_PICTURE_POSITION_FROM_DEVICE = {
    0x0000: "1_85",
    0x0001: "2_35",
    0x0002: "custom_1",
    0x0003: "custom_2",
    0x0004: "custom_3",
    0x0005: "custom_4",
    0x0006: "custom_5",
}
_COLOR_SPACE_FROM_DEVICE = {
    0x0000: "bt709",
    0x0003: "color_space1",
    0x0004: "color_space2",
    0x0005: "color_space3",
    0x0006: "custom",
    0x0008: "bt2020",
}
_DYNAMIC_RANGE_FROM_DEVICE = {0x0000: "auto", 0x0001: "limited", 0x0002: "full"}
_HDR_FROM_DEVICE = {0x0000: "off", 0x0001: "on", 0x0002: "auto"}
_MENU_POSITION_FROM_DEVICE = {0x0000: "bottom_left", 0x0001: "center"}
_ERROR_STATUS_FROM_DEVICE = {
    0x0000: "no_error",
    0x0001: "lamp_error",
    0x0002: "fan_error",
    0x0004: "cover_error",
    0x0008: "temp_error",
    0x000A: "d5v_error",
    0x0014: "power_error",
    0x0028: "temp_warning",
}

_CALIBRATION_PRESET_TO_DEVICE = _invert(_CALIBRATION_PRESET_FROM_DEVICE)
_LAMP_CONTROL_TO_DEVICE = _invert(_LAMP_CONTROL_FROM_DEVICE)
_CONTRAST_ENHANCER_TO_DEVICE = _invert(_CONTRAST_ENHANCER_FROM_DEVICE)
_ADVANCED_IRIS_TO_DEVICE = _invert(_ADVANCED_IRIS_FROM_DEVICE)
_ASPECT_RATIO_TO_DEVICE = _invert(_ASPECT_RATIO_FROM_DEVICE)
_ON_OFF_TO_DEVICE = _invert(_ON_OFF_FROM_DEVICE)
_MOTIONFLOW_TO_DEVICE = _invert(_MOTIONFLOW_FROM_DEVICE)
_DISPLAY_SELECT_TO_DEVICE = _invert(_DISPLAY_SELECT_FROM_DEVICE)
_THREE_D_FORMAT_TO_DEVICE = _invert(_THREE_D_FORMAT_FROM_DEVICE)
_PICTURE_POSITION_TO_DEVICE = _invert(_PICTURE_POSITION_FROM_DEVICE)
_COLOR_SPACE_TO_DEVICE = _invert(_COLOR_SPACE_FROM_DEVICE) | {
    "color_space_1": 0x0003,
    "color_space_2": 0x0004,
    "color_space_3": 0x0005,
}
_DYNAMIC_RANGE_TO_DEVICE = _invert(_DYNAMIC_RANGE_FROM_DEVICE)
_HDR_TO_DEVICE = _invert(_HDR_FROM_DEVICE)
_MENU_POSITION_TO_DEVICE = _invert(_MENU_POSITION_FROM_DEVICE)

_RESPONSE_ERRORS = {
    0x0101: "Item Error: Invalid Item",
    0x0102: "Item Error: Invalid Item Request",
    0x0103: "Item Error: Invalid Length",
    0x0104: "Item Error: Invalid Data",
    0x0111: "Item Error: Short Data",
    0x0180: "Item Error: Not Applicable Item",
    0x0201: "Community Error: Different Community",
    0x1001: "Request Error: Invalid Version",
    0x1002: "Request Error: Invalid Category",
    0x1003: "Request Error: Invalid Request",
    0x1011: "Request Error: Short Header",
    0x1012: "Request Error: Short Community",
    0x1013: "Request Error: Short Command",
    0xF001: "Comm Error: Timeout",
    0xF010: "Comm Error: Check Sum Error",
    0xF020: "Comm Error: Framing Error",
    0xF030: "Comm Error: Parity Error",
    0xF040: "Comm Error: Over Run Error",
    0xF050: "Comm Error: Other Comm Error",
    0xF0F0: "Comm Error: Unknown Response",
    0xF110: "NVRAM Error: Read Error",
    0xF120: "NVRAM Error: Write Error",
}


@dataclass(frozen=True)
class SdcpHeader:
    """PJ Talk command header."""

    version: int = 0x02
    category: int = 0x0A
    community: str = DEFAULT_SDCP_COMMUNITY


class SdcpClient:
    """Small async SDCP / PJ Talk command client."""

    def __init__(
        self,
        host: str,
        *,
        timeout: float = 5.0,
        transport: Transport | None = None,
        community: str | None = None,
    ) -> None:
        self.host = host
        self.timeout = timeout
        self.header = SdcpHeader(community=DEFAULT_SDCP_COMMUNITY if community is None else community)
        self.transport = transport or StreamTransport(host, SDCP_PORT, terminator=None)

    async def connect(self) -> None:
        await self.transport.connect()

    async def close(self) -> None:
        await self.transport.close()

    async def get_power(self) -> str:
        data = await self._command(_ACTION_GET, _COMMAND_STATUS_POWER)
        if data is None:
            return "unknown"
        return _POWER_FROM_DEVICE.get(data, f"0x{data:04x}")

    async def set_power(self, power: bool) -> None:
        await self._command(_ACTION_SET, _COMMAND_SET_POWER, _POWER_START_UP if power else _POWER_STANDBY)

    async def get_input(self) -> str:
        data = await self._command(_ACTION_GET, _COMMAND_INPUT)
        if data is None:
            return "unknown"
        return _INPUT_FROM_DEVICE.get(data, f"0x{data:04x}")

    async def set_input(self, value: str) -> None:
        input_value = _normalize_value(value)
        if input_value not in _INPUT_TO_DEVICE:
            raise PackageUnsupportedCommandError(f"Unsupported SDCP input: {value}")
        await self._command(_ACTION_SET, _COMMAND_INPUT, _INPUT_TO_DEVICE[input_value])

    async def set_calibration_preset(self, value: str) -> None:
        await self._set_mapped(_COMMAND_CALIBRATION_PRESET, value, _CALIBRATION_PRESET_TO_DEVICE, "calibration preset")

    async def set_lamp_control(self, value: str) -> None:
        await self._set_mapped(_COMMAND_LAMP_CONTROL, value, _LAMP_CONTROL_TO_DEVICE, "lamp control")

    async def set_contrast_enhancer(self, value: str) -> None:
        await self._set_mapped(_COMMAND_CONTRAST_ENHANCER, value, _CONTRAST_ENHANCER_TO_DEVICE, "contrast enhancer")

    async def set_advanced_iris(self, value: str) -> None:
        await self._set_mapped(_COMMAND_ADVANCED_IRIS, value, _ADVANCED_IRIS_TO_DEVICE, "advanced iris")

    async def set_aspect_ratio(self, value: str) -> None:
        await self._set_mapped(_COMMAND_ASPECT_RATIO, value, _ASPECT_RATIO_TO_DEVICE, "aspect ratio")

    async def set_picture_muting(self, value: bool | str) -> None:
        await self._set_on_off(_COMMAND_PICTURE_MUTING, value, "picture muting")

    async def set_motionflow(self, value: str) -> None:
        await self._set_mapped(_COMMAND_MOTIONFLOW, value, _MOTIONFLOW_TO_DEVICE, "motionflow")

    async def set_2d_3d_display_select(self, value: str) -> None:
        await self._set_mapped(_COMMAND_2D_3D_DISPLAY_SELECT, value, _DISPLAY_SELECT_TO_DEVICE, "2d/3d display select")

    async def set_3d_format(self, value: str) -> None:
        await self._set_mapped(_COMMAND_3D_FORMAT, value, _THREE_D_FORMAT_TO_DEVICE, "3d format")

    async def set_picture_position(self, value: str) -> None:
        await self._set_mapped(_COMMAND_PICTURE_POSITION, value, _PICTURE_POSITION_TO_DEVICE, "picture position")

    async def set_color_space(self, value: str) -> None:
        await self._set_mapped(_COMMAND_COLOR_SPACE, value, _COLOR_SPACE_TO_DEVICE, "color space")

    async def set_hdmi1_dynamic_range(self, value: str) -> None:
        await self._set_mapped(_COMMAND_HDMI1_DYNAMIC_RANGE, value, _DYNAMIC_RANGE_TO_DEVICE, "HDMI 1 dynamic range")

    async def set_hdmi2_dynamic_range(self, value: str) -> None:
        await self._set_mapped(_COMMAND_HDMI2_DYNAMIC_RANGE, value, _DYNAMIC_RANGE_TO_DEVICE, "HDMI 2 dynamic range")

    async def set_hdr(self, value: str) -> None:
        await self._set_mapped(_COMMAND_HDR, value, _HDR_TO_DEVICE, "HDR")

    async def set_input_lag_reduction(self, value: bool | str) -> None:
        await self._set_on_off(_COMMAND_INPUT_LAG_REDUCTION, value, "input lag reduction")

    async def set_menu_position(self, value: str) -> None:
        await self._set_mapped(_COMMAND_MENU_POSITION, value, _MENU_POSITION_TO_DEVICE, "menu position")

    async def get_calibration_preset(self) -> str:
        return self._decode(await self._get(_COMMAND_CALIBRATION_PRESET), _CALIBRATION_PRESET_FROM_DEVICE)

    async def get_color_temp(self) -> int | str:
        return self._value_or_unknown(await self._get(_COMMAND_COLOR_TEMP))

    async def get_lamp_control(self) -> str:
        return self._decode(await self._get(_COMMAND_LAMP_CONTROL), _LAMP_CONTROL_FROM_DEVICE)

    async def get_contrast_enhancer(self) -> str:
        return self._decode(await self._get(_COMMAND_CONTRAST_ENHANCER), _CONTRAST_ENHANCER_FROM_DEVICE)

    async def get_advanced_iris(self) -> str:
        return self._decode(await self._get(_COMMAND_ADVANCED_IRIS), _ADVANCED_IRIS_FROM_DEVICE)

    async def get_aspect_ratio(self) -> str:
        return self._decode(await self._get(_COMMAND_ASPECT_RATIO), _ASPECT_RATIO_FROM_DEVICE)

    async def get_gamma_correction(self) -> int | str:
        return self._value_or_unknown(await self._get(_COMMAND_GAMMA_CORRECTION))

    async def get_picture_muting(self) -> str:
        return self._decode(await self._get(_COMMAND_PICTURE_MUTING), _ON_OFF_FROM_DEVICE)

    async def get_color_space(self) -> int | str:
        return self._value_or_unknown(await self._get(_COMMAND_COLOR_SPACE), _COLOR_SPACE_FROM_DEVICE)

    async def get_motionflow(self) -> str:
        return self._decode(await self._get(_COMMAND_MOTIONFLOW), _MOTIONFLOW_FROM_DEVICE)

    async def get_2d_3d_display_select(self) -> str:
        return self._decode(await self._get(_COMMAND_2D_3D_DISPLAY_SELECT), _DISPLAY_SELECT_FROM_DEVICE)

    async def get_3d_format(self) -> str:
        return self._decode(await self._get(_COMMAND_3D_FORMAT), _THREE_D_FORMAT_FROM_DEVICE)

    async def get_picture_position(self) -> str:
        return self._decode(await self._get(_COMMAND_PICTURE_POSITION), _PICTURE_POSITION_FROM_DEVICE)

    async def get_reality_creation(self) -> int | str:
        return self._value_or_unknown(await self._get(_COMMAND_REALITY_CREATION))

    async def get_hdmi1_dynamic_range(self) -> str:
        return self._decode(await self._get(_COMMAND_HDMI1_DYNAMIC_RANGE), _DYNAMIC_RANGE_FROM_DEVICE)

    async def get_hdmi2_dynamic_range(self) -> str:
        return self._decode(await self._get(_COMMAND_HDMI2_DYNAMIC_RANGE), _DYNAMIC_RANGE_FROM_DEVICE)

    async def get_hdr(self) -> str:
        return self._decode(await self._get(_COMMAND_HDR), _HDR_FROM_DEVICE)

    async def get_input_lag_reduction(self) -> str:
        return self._decode(await self._get(_COMMAND_INPUT_LAG_REDUCTION), _ON_OFF_FROM_DEVICE)

    async def get_menu_position(self) -> str:
        return self._decode(await self._get(_COMMAND_MENU_POSITION), _MENU_POSITION_FROM_DEVICE)

    async def get_error_status(self) -> str:
        return self._decode(await self._get(_COMMAND_STATUS_ERROR), _ERROR_STATUS_FROM_DEVICE)

    async def get_lamp_timer(self) -> int | str:
        return self._value_or_unknown(await self._get(_COMMAND_LAMP_TIMER))

    async def get_model_name(self) -> str:
        return self._decode_text(await self._get_bytes(_COMMAND_MODEL_NAME))

    async def get_serial_number(self) -> str:
        data = await self._get_bytes(_COMMAND_SERIAL_NUMBER)
        if data is None:
            return "unknown"
        return str(int.from_bytes(data, byteorder="big")).zfill(8)

    async def get_installation_location(self) -> str:
        return self._decode_text(await self._get_bytes(_COMMAND_INSTALLATION_LOCATION))

    async def get_mac_address(self) -> str:
        data = await self._get_bytes(_COMMAND_MAC_ADDRESS)
        if data is None:
            return "unknown"
        return ":".join(f"{value:02X}" for value in data)

    async def get_identity(self) -> ProjectorIdentity:
        return ProjectorIdentity(
            model=await self.get_model_name(),
            serial=await self.get_serial_number(),
            location=await self.get_installation_location(),
            mac_address=await self.get_mac_address(),
        )

    async def _set_mapped(self, command: int, value: str, mapping: dict[str, int], label: str) -> None:
        key = _normalize_value(value)
        try:
            encoded = mapping[key]
        except KeyError as exc:
            supported = ", ".join(sorted(mapping))
            raise PackageUnsupportedCommandError(
                f"Unsupported SDCP {label}: {value}. Expected one of: {supported}"
            ) from exc
        await self._command(_ACTION_SET, command, encoded)

    async def _set_on_off(self, command: int, value: bool | str, label: str) -> None:
        if isinstance(value, bool):
            encoded = _ON_OFF_TO_DEVICE["on" if value else "off"]
            await self._command(_ACTION_SET, command, encoded)
            return
        await self._set_mapped(command, value, _ON_OFF_TO_DEVICE, label)

    async def _get(self, command: int) -> int | None:
        return await self._command(_ACTION_GET, command)

    async def _get_bytes(self, command: int) -> bytes | None:
        return await self._command_bytes(_ACTION_GET, command)

    def _decode(self, value: int | None, mapping: dict[int, str]) -> str:
        if value is None:
            return "unknown"
        return mapping.get(value, f"0x{value:04x}")

    def _decode_text(self, value: bytes | None) -> str:
        if value is None:
            return "unknown"
        return value.split(b"\x00", 1)[0].decode("ascii", errors="replace").strip()

    def _value_or_unknown(self, value: int | None, mapping: dict[int, str] | None = None) -> int | str:
        if value is None:
            return "unknown"
        if mapping is not None:
            return mapping.get(value, value)
        return value

    async def _command(self, action: int, command: int, data: int | None = None) -> int | None:
        response = await self._command_bytes(action, command, data)
        if response is None:
            return None
        if len(response) != 2:
            raise ProjectorProtocolError(
                f"Unsupported SDCP response data length: {len(response)}",
                protocol="sdcp",
                command=f"0x{command:04x}",
                response=response,
            )
        return unpack(">H", response)[0]

    async def _command_bytes(self, action: int, command: int, data: int | None = None) -> bytes | None:
        payload = self._create_command_buffer(action, command, data)
        raw = await self.transport.request(payload, timeout=self.timeout)
        return self._process_response(raw, command)

    def _create_command_buffer(self, action: int, command: int, data: int | None = None) -> bytes:
        community = self.header.community.encode("ascii")
        if len(community) != 4:
            raise ProjectorProtocolError("SDCP community must be exactly 4 ASCII characters")

        buffer = bytearray(12 if data is not None else 10)
        buffer[0] = self.header.version
        buffer[1] = self.header.category
        buffer[2:6] = community
        buffer[6] = action
        pack_into(">H", buffer, 7, command)
        if data is None:
            buffer[9] = 0
        else:
            buffer[9] = 2
            pack_into(">H", buffer, 10, data)
        return bytes(buffer)

    def _process_response(self, payload: bytes, expected_command: int) -> bytes | None:
        if len(payload) < 10:
            raise ProjectorProtocolError(
                "SDCP response is shorter than the PJ Talk header",
                protocol="sdcp",
                command=f"0x{expected_command:04x}",
                response=payload,
            )

        is_success = bool(payload[6])
        command = unpack(">H", payload[7:9])[0]
        data_len = payload[9]
        if len(payload) < 10 + data_len:
            raise ProjectorProtocolError(
                "SDCP response data is shorter than the declared data length",
                protocol="sdcp",
                command=f"0x{expected_command:04x}",
                response=payload,
            )
        data = payload[10 : 10 + data_len] if data_len else None

        if command != expected_command:
            raise ProjectorProtocolError(
                f"SDCP response command 0x{command:04x} did not match 0x{expected_command:04x}",
                protocol="sdcp",
                command=f"0x{expected_command:04x}",
                response=payload,
            )
        if not is_success:
            error = unpack(">H", data)[0] if data is not None and len(data) == 2 else None
            if error == 0x0180:
                raise ProjectorUnsupportedCommandError(
                    _RESPONSE_ERRORS[error],
                    protocol="sdcp",
                    command=f"0x{expected_command:04x}",
                    response=payload,
                )
            message = (
                _RESPONSE_ERRORS.get(error, f"Unknown SDCP error: 0x{error:04x}")
                if error is not None
                else "Unknown SDCP error"
            )
            raise ProjectorProtocolError(
                message,
                protocol="sdcp",
                command=f"0x{expected_command:04x}",
                response=payload,
            )
        return data
