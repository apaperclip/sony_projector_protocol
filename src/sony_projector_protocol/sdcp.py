"""SDCP / PJ Talk client implementation."""

from __future__ import annotations

from dataclasses import dataclass
from struct import pack_into, unpack

from sony_projector_protocol.exceptions import ProjectorProtocolError, UnsupportedCommandError
from sony_projector_protocol.models import Input, ProjectorIdentity
from sony_projector_protocol.transport import StreamTransport, Transport

SDCP_PORT = 53484

_ACTION_GET = 0x01
_ACTION_SET = 0x00

_COMMAND_SET_POWER = 0x0130
_COMMAND_INPUT = 0x0001
_COMMAND_STATUS_POWER = 0x0102

_POWER_STANDBY = 0x0000
_POWER_START_UP = 0x0001
_POWER_START_UP_LAMP = 0x0002
_POWER_ON = 0x0003
_POWER_COOLING = 0x0004
_POWER_COOLING2 = 0x0005

_INPUT_TO_DEVICE = {
    Input.HDMI1: 0x0002,
    Input.HDMI2: 0x0003,
}

_INPUT_FROM_DEVICE = {value: key for key, value in _INPUT_TO_DEVICE.items()}

_POWER_FROM_DEVICE = {
    _POWER_STANDBY: "standby",
    _POWER_START_UP: "start_up",
    _POWER_START_UP_LAMP: "start_up_lamp",
    _POWER_ON: "on",
    _POWER_COOLING: "cooling",
    _POWER_COOLING2: "cooling2",
}

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
    community: str = "SONY"


class SdcpClient:
    """Small async SDCP / PJ Talk command client."""

    def __init__(
        self,
        host: str,
        *,
        timeout: float = 5.0,
        transport: Transport | None = None,
        community: str = "SONY",
    ) -> None:
        self.host = host
        self.timeout = timeout
        self.header = SdcpHeader(community=community)
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

    async def get_input(self) -> Input | str:
        data = await self._command(_ACTION_GET, _COMMAND_INPUT)
        if data is None:
            return "unknown"
        return _INPUT_FROM_DEVICE.get(data, f"0x{data:04x}")

    async def set_input(self, value: Input | str) -> None:
        try:
            input_value: Input | str = Input(value)
        except ValueError:
            input_value = value
        if not isinstance(input_value, Input):
            raise UnsupportedCommandError(f"Unsupported SDCP input: {value}")
        await self._command(_ACTION_SET, _COMMAND_INPUT, _INPUT_TO_DEVICE[input_value])

    async def get_identity(self) -> ProjectorIdentity:
        return ProjectorIdentity()

    async def _command(self, action: int, command: int, data: int | None = None) -> int | None:
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

    def _process_response(self, payload: bytes, expected_command: int) -> int | None:
        if len(payload) < 10:
            raise ProjectorProtocolError("SDCP response is shorter than the PJ Talk header")

        is_success = bool(payload[6])
        command = unpack(">H", payload[7:9])[0]
        data_len = payload[9]
        data = unpack(">H", payload[10:12])[0] if data_len else None

        if command != expected_command:
            raise ProjectorProtocolError(
                f"SDCP response command 0x{command:04x} did not match 0x{expected_command:04x}"
            )
        if not is_success:
            if data == 0x0180:
                raise UnsupportedCommandError(_RESPONSE_ERRORS[data])
            message = _RESPONSE_ERRORS.get(data, f"Unknown SDCP error: 0x{data:04x}" if data else "Unknown SDCP error")
            raise ProjectorProtocolError(message)
        if data_len not in {0, 2}:
            raise ProjectorProtocolError(f"Unsupported SDCP response data length: {data_len}")
        return data
