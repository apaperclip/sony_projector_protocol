"""ADCP client implementation."""

from __future__ import annotations

import asyncio
import hashlib
import json

from sony_projector_protocol.capabilities import ADCP_PICTURE_MODE_VALUES
from sony_projector_protocol.exceptions import (
    PackageUnsupportedCommandError, ProjectorAuthenticationError,
    ProjectorConnectionError, ProjectorProtocolError,
    ProjectorUnsupportedCommandError, UnsupportedCommandError)
from sony_projector_protocol.transport import StreamTransport, Transport
from sony_projector_protocol.types import ProjectorIdentity

ADCP_PORT = 53595

_POWER_TO_DEVICE = {
    True: "on",
    False: "off",
}

_INPUT_TO_DEVICE = {
    "hdmi1": "hdmi1",
    "hdmi2": "hdmi2",
}

_INPUT_FROM_DEVICE = {value: key for key, value in _INPUT_TO_DEVICE.items()}

_PICTURE_MODE_TO_DEVICE = {value: value for value in ADCP_PICTURE_MODE_VALUES} | {
    "bright_cinema": "brt_cinema",
    "bright_tv": "brt_tv",
}


class AdcpClient:
    """Small async ADCP command client."""

    def __init__(
        self,
        host: str,
        *,
        timeout: float = 5.0,
        transport: Transport | None = None,
        password: str | None = None,
    ) -> None:
        self.host = host
        self.timeout = timeout
        self.password = password
        self.transport = transport or StreamTransport(host, ADCP_PORT, terminator=b"\r\n")

    async def connect(self) -> None:
        await self.transport.connect()
        if self.password is not None:
            await self._authenticate()

    async def close(self) -> None:
        await self.transport.close()

    async def get_power(self) -> str:
        return await self._command("power_status ?")

    async def set_power(self, power: bool) -> None:
        await self._command(f"power {self._quoted(_POWER_TO_DEVICE[power])}")

    async def get_input(self) -> str:
        response = await self._command("input ?")
        return _INPUT_FROM_DEVICE.get(response.lower(), response.lower())

    async def get_signal(self) -> str:
        return await self._command("signal ?")

    async def get_temperature(self) -> int | float | str:
        return await self._json_value_command("temperature ?", "intake_air")

    async def get_timer(self) -> int | float | str:
        return await self._json_value_command("timer ?", "light_src")

    async def get_picture_mode(self) -> str:
        return await self._command("picture_mode ?")

    async def set_picture_mode(self, value: str) -> None:
        picture_mode = self._mapped_value(value, _PICTURE_MODE_TO_DEVICE, "picture mode")
        await self._command(f"picture_mode {self._quoted(picture_mode)}")

    async def get_color_space(self) -> str:
        return await self._command("color_space ?")

    async def set_color_space(self, value: str) -> None:
        await self._command(f"color_space {self._quoted(value)}")

    async def get_lamp_control(self) -> str:
        return await self._command("lamp_control ?")

    async def set_lamp_control(self, value: str) -> None:
        await self._command(f"lamp_control {self._quoted(value)}")

    async def get_warning(self) -> list[str] | str:
        return await self._json_list_command("warning ?")

    async def get_error(self) -> list[str] | str:
        return await self._json_list_command("error ?")

    async def get_hdr(self) -> str:
        return await self._command("hdr ?")

    async def set_hdr(self, value: str) -> None:
        await self._command(f"hdr {self._quoted(value)}")

    async def get_aspect_ratio(self) -> str:
        return await self._command("aspect ?")

    async def set_aspect_ratio(self, value: str) -> None:
        await self._command(f"aspect {self._quoted(value)}")

    async def get_hdmi1_dynamic_range(self) -> str:
        return await self._command("dynamic_range --hdmi1 ?")

    async def set_hdmi1_dynamic_range(self, value: str) -> None:
        await self.set_dynamic_range("hdmi1", value)

    async def get_hdmi2_dynamic_range(self) -> str:
        return await self._command("dynamic_range --hdmi2 ?")

    async def set_hdmi2_dynamic_range(self, value: str) -> None:
        await self.set_dynamic_range("hdmi2", value)

    async def get_dynamic_range(self, input_name: str) -> str:
        normalized = self._dynamic_range_input(input_name)
        return await self._command(f"dynamic_range --{normalized} ?")

    async def set_dynamic_range(self, input_name: str, value: str) -> None:
        normalized = self._dynamic_range_input(input_name)
        await self._command(f"dynamic_range --{normalized} {self._quoted(value)}")

    async def get_model_name(self) -> str:
        return await self._command("modelname ?")

    async def get_serial_number(self) -> str:
        return await self._command("serialnum ?")

    async def get_version(self) -> str:
        return await self._command("version ?")

    async def get_mac_address(self) -> str:
        return await self._command("mac_address ?")

    async def set_input(self, value: str) -> None:
        input_value = _INPUT_TO_DEVICE.get(value.lower(), value)
        await self._command(f"input {input_value}")

    async def get_identity(self) -> ProjectorIdentity:
        model = await self._optional_command("modelname ?")
        serial = await self._optional_command("serialnum ?")
        mac_address = await self._optional_command("mac_address ?")
        return ProjectorIdentity(model=model, serial=serial, mac_address=mac_address)

    async def _optional_command(self, command: str) -> str | None:
        try:
            return await self._command(command)
        except UnsupportedCommandError:
            return None

    def _dynamic_range_input(self, input_name: str) -> str:
        normalized = input_name.lower().replace("_", "")
        if normalized not in {"hdmi1", "hdmi2"}:
            raise PackageUnsupportedCommandError(f"Unsupported dynamic range input: {input_name}")
        return normalized

    def _mapped_value(self, value: str, mapping: dict[str, str], label: str) -> str:
        normalized = value.strip().strip('"').lower().replace("-", "_").replace(" ", "_")
        if normalized not in mapping:
            raise PackageUnsupportedCommandError(f"Unsupported ADCP {label}: {value}")
        return mapping[normalized]

    def _quoted(self, value: str) -> str:
        return value if value.startswith('"') and value.endswith('"') else f'"{value}"'

    def _response_value(self, text: str) -> str:
        if "=" in text:
            return text.split("=", 1)[1].strip().strip('"')

        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            return parts[1].strip().strip('"')

        return text.strip('"')

    def _is_error_response(self, lowered: str) -> bool:
        return lowered.startswith("ng") or (lowered.startswith("err") and not lowered.startswith("error"))

    async def _json_value_command(self, command: str, key: str) -> int | float | str:
        response = await self._command(command)
        try:
            values = json.loads(response)
        except json.JSONDecodeError:
            return response

        if isinstance(values, list):
            item = next((item for item in values if isinstance(item, dict) and key in item), None)
            if item is not None:
                return item[key]
        if isinstance(values, dict) and key in values:
            return values[key]
        return response

    async def _json_list_command(self, command: str) -> list[str] | str:
        response = await self._command(command)
        try:
            values = json.loads(response)
        except json.JSONDecodeError:
            return response

        if isinstance(values, list):
            return [str(value) for value in values]
        return response

    async def _authenticate(self) -> None:
        if not isinstance(self.transport, StreamTransport):
            return
        if self.transport.reader is None or self.transport.writer is None:
            raise ProjectorConnectionError("ADCP transport is not connected")

        try:
            challenge_raw = await asyncio.wait_for(self.transport.reader.readuntil(b"\r\n"), self.timeout)
            challenge = challenge_raw.decode("ascii", errors="replace").strip().strip('"')
            if challenge.upper() == "NOKEY":
                return

            digest = hashlib.sha256((challenge + self.password).encode("ascii")).hexdigest()
            self.transport.writer.write(f"{digest}\r\n".encode("ascii"))
            await self.transport.writer.drain()
            response_raw = await asyncio.wait_for(self.transport.reader.readuntil(b"\r\n"), self.timeout)
        except TimeoutError as exc:
            raise ProjectorConnectionError("Timed out during ADCP authentication") from exc
        except (OSError, asyncio.IncompleteReadError) as exc:
            raise ProjectorConnectionError("Projector connection closed during ADCP authentication") from exc

        response = response_raw.decode("ascii", errors="replace").strip().strip('"').lower()
        if response.startswith("err") or response.startswith("ng"):
            raise ProjectorAuthenticationError(
                f"ADCP authentication failed: {response}",
                protocol="adcp",
                command="authentication",
                response=response,
            )

    async def _command(self, command: str) -> str:
        payload = f"{command}\r\n".encode("ascii")
        raw = await self.transport.request(payload, timeout=self.timeout)
        text = raw.decode("ascii", errors="replace").strip()
        lowered = text.lower()

        if lowered in {"ok", "success"}:
            return lowered
        if lowered in {"unsupported", "not_available", "na"}:
            raise ProjectorUnsupportedCommandError(
                f"ADCP command unsupported: {command}",
                protocol="adcp",
                command=command,
                response=text,
            )
        if "=" in text:
            return self._response_value(text)
        if self._is_error_response(lowered):
            raise ProjectorProtocolError(
                f"ADCP command failed: {text}",
                protocol="adcp",
                command=command,
                response=text,
            )
        return self._response_value(text)
