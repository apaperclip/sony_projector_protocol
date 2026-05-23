"""ADCP client implementation."""

from __future__ import annotations

from sony_projector_protocol.exceptions import ProjectorProtocolError, UnsupportedCommandError
from sony_projector_protocol.models import Input, PowerState, ProjectorIdentity
from sony_projector_protocol.transport import StreamTransport, Transport

ADCP_PORT = 53595

_POWER_FROM_DEVICE = {
    "0": PowerState.OFF,
    "1": PowerState.ON,
    "off": PowerState.OFF,
    "on": PowerState.ON,
    "standby": PowerState.STANDBY,
    "startup": PowerState.STARTING,
    "starting": PowerState.STARTING,
    "cooling": PowerState.COOLING,
}

_POWER_TO_DEVICE = {
    True: "on",
    False: "off",
}

_INPUT_TO_DEVICE = {
    Input.HDMI1: "hdmi1",
    Input.HDMI2: "hdmi2",
}

_INPUT_FROM_DEVICE = {value: key for key, value in _INPUT_TO_DEVICE.items()}


class AdcpClient:
    """Small async ADCP command client."""

    def __init__(self, host: str, *, timeout: float = 5.0, transport: Transport | None = None) -> None:
        self.host = host
        self.timeout = timeout
        self.transport = transport or StreamTransport(host, ADCP_PORT)

    async def connect(self) -> None:
        await self.transport.connect()

    async def close(self) -> None:
        await self.transport.close()

    async def get_power(self) -> PowerState:
        response = await self._command("power ?")
        return _POWER_FROM_DEVICE.get(response.lower(), PowerState.UNKNOWN)

    async def set_power(self, power: bool) -> None:
        await self._command(f"power {_POWER_TO_DEVICE[power]}")

    async def get_input(self) -> Input | str:
        response = await self._command("input ?")
        return _INPUT_FROM_DEVICE.get(response.lower(), response.lower())

    async def set_input(self, value: Input | str) -> None:
        try:
            input_value: Input | str = Input(value)
        except ValueError:
            input_value = value
        if isinstance(input_value, Input):
            input_value = _INPUT_TO_DEVICE[input_value]
        await self._command(f"input {input_value}")

    async def get_identity(self) -> ProjectorIdentity:
        model = await self._optional_command("model ?")
        serial = await self._optional_command("serial ?")
        return ProjectorIdentity(model=model, serial=serial)

    async def _optional_command(self, command: str) -> str | None:
        try:
            return await self._command(command)
        except UnsupportedCommandError:
            return None

    async def _command(self, command: str) -> str:
        payload = f"{command}\r".encode("ascii")
        raw = await self.transport.request(payload, timeout=self.timeout)
        text = raw.decode("ascii", errors="replace").strip()
        lowered = text.lower()

        if lowered in {"ok", "success"}:
            return lowered
        if lowered in {"unsupported", "not_available", "na"}:
            raise UnsupportedCommandError(command)
        if lowered.startswith("err") or lowered.startswith("ng"):
            raise ProjectorProtocolError(f"ADCP command failed: {text}")
        if "=" in text:
            return text.split("=", 1)[1].strip()
        return text
