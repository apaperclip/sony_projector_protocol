"""Protocol-neutral projector facade."""

from __future__ import annotations

from sony_projector_protocol.adcp import AdcpClient
from sony_projector_protocol.exceptions import (
    ProjectorConnectionError,
    ProjectorError,
    ProjectorProtocolError,
    UnsupportedCommandError,
)
from sony_projector_protocol.models import Capabilities, Input, PowerState, ProjectorIdentity, Protocol
from sony_projector_protocol.sdcp import SdcpClient
from sony_projector_protocol.transport import Transport


class Projector:
    """Async protocol-neutral projector controller."""

    def __init__(
        self,
        host: str,
        *,
        protocol: Protocol | str = Protocol.AUTO,
        timeout: float = 5.0,
        transport: Transport | None = None,
        community: str = "SONY",
        adcp_password: str | None = None,
    ) -> None:
        self.host = host
        self.protocol = Protocol(protocol)
        self.timeout = timeout
        self.capabilities = Capabilities()
        self._transport = transport
        self.community = community
        self.adcp_password = adcp_password
        self._client: AdcpClient | SdcpClient | None = None

    async def connect(self) -> None:
        """Connect to the configured projector."""
        if self.protocol is Protocol.ADCP:
            self._client = AdcpClient(
                self.host, timeout=self.timeout, transport=self._transport, password=self.adcp_password
            )
        elif self.protocol is Protocol.SDCP:
            self._client = SdcpClient(
                self.host, timeout=self.timeout, transport=self._transport, community=self.community
            )
        else:
            self._client = await self._probe_client()

        await self._client.connect()

    async def close(self) -> None:
        """Close the active connection."""
        if self._client is not None:
            await self._client.close()

    async def get_power(self) -> PowerState | str:
        client = self._connected_client()
        self.capabilities.mark_supported("power")
        return await client.get_power()

    async def set_power(self, power: bool) -> None:
        client = self._connected_client()
        await client.set_power(power)
        self.capabilities.mark_supported("power")

    async def get_input(self) -> Input | str:
        client = self._connected_client()
        self.capabilities.mark_supported("input")
        return await client.get_input()

    async def set_input(self, value: Input | str) -> None:
        client = self._connected_client()
        await client.set_input(value)
        self.capabilities.mark_supported("input")

    async def get_signal(self) -> str:
        client = self._connected_client()
        if not isinstance(client, AdcpClient):
            raise UnsupportedCommandError("This command is only supported by ADCP")
        self.capabilities.mark_supported("signal")
        return await client.get_signal()

    async def get_temperature(self) -> int | float | str:
        client = self._connected_client()
        if not isinstance(client, AdcpClient):
            raise UnsupportedCommandError("This command is only supported by ADCP")
        self.capabilities.mark_supported("temperature")
        return await client.get_temperature()

    async def get_timer(self) -> int | float | str:
        client = self._connected_client()
        if not isinstance(client, AdcpClient):
            raise UnsupportedCommandError("This command is only supported by ADCP")
        self.capabilities.mark_supported("timer")
        return await client.get_timer()

    async def get_picture_mode(self) -> str:
        client = self._connected_client()
        if not isinstance(client, AdcpClient):
            raise UnsupportedCommandError("This command is only supported by ADCP")
        self.capabilities.mark_supported("picture_mode")
        return await client.get_picture_mode()

    async def get_warning(self) -> list[str] | str:
        client = self._connected_client()
        if not isinstance(client, AdcpClient):
            raise UnsupportedCommandError("This command is only supported by ADCP")
        self.capabilities.mark_supported("warning")
        return await client.get_warning()

    async def get_error(self) -> list[str] | str:
        client = self._connected_client()
        if not isinstance(client, AdcpClient):
            raise UnsupportedCommandError("This command is only supported by ADCP")
        self.capabilities.mark_supported("error")
        return await client.get_error()

    async def get_identity(self) -> ProjectorIdentity:
        client = self._connected_client()
        return await client.get_identity()

    async def get_model_name(self) -> str:
        client = self._connected_client()
        if not isinstance(client, AdcpClient):
            raise UnsupportedCommandError("This command is only supported by ADCP")
        self.capabilities.mark_supported("model_name")
        return await client.get_model_name()

    async def get_serial_number(self) -> str:
        client = self._connected_client()
        if not isinstance(client, AdcpClient):
            raise UnsupportedCommandError("This command is only supported by ADCP")
        self.capabilities.mark_supported("serial_number")
        return await client.get_serial_number()

    async def get_version(self) -> str:
        client = self._connected_client()
        if not isinstance(client, AdcpClient):
            raise UnsupportedCommandError("This command is only supported by ADCP")
        self.capabilities.mark_supported("version")
        return await client.get_version()

    async def get_mac_address(self) -> str:
        client = self._connected_client()
        if not isinstance(client, AdcpClient):
            raise UnsupportedCommandError("This command is only supported by ADCP")
        self.capabilities.mark_supported("mac_address")
        return await client.get_mac_address()

    async def get_calibration_preset(self) -> str:
        return await self._sdcp_client().get_calibration_preset()

    async def set_calibration_preset(self, value: str) -> None:
        await self._sdcp_client().set_calibration_preset(value)

    async def get_color_temp(self) -> int | str:
        return await self._sdcp_client().get_color_temp()

    async def get_lamp_control(self) -> str:
        client = self._connected_client()
        self.capabilities.mark_supported("lamp_control")
        return await client.get_lamp_control()

    async def set_lamp_control(self, value: str) -> None:
        await self._sdcp_client().set_lamp_control(value)

    async def get_contrast_enhancer(self) -> str:
        return await self._sdcp_client().get_contrast_enhancer()

    async def set_contrast_enhancer(self, value: str) -> None:
        await self._sdcp_client().set_contrast_enhancer(value)

    async def get_advanced_iris(self) -> str:
        return await self._sdcp_client().get_advanced_iris()

    async def set_advanced_iris(self, value: str) -> None:
        await self._sdcp_client().set_advanced_iris(value)

    async def get_aspect_ratio(self) -> str:
        client = self._connected_client()
        self.capabilities.mark_supported("aspect_ratio")
        return await client.get_aspect_ratio()

    async def set_aspect_ratio(self, value: str) -> None:
        await self._sdcp_client().set_aspect_ratio(value)

    async def get_gamma_correction(self) -> int | str:
        return await self._sdcp_client().get_gamma_correction()

    async def get_picture_muting(self) -> str:
        return await self._sdcp_client().get_picture_muting()

    async def set_picture_muting(self, value: bool | str) -> None:
        await self._sdcp_client().set_picture_muting(value)

    async def get_color_space(self) -> int | str:
        client = self._connected_client()
        self.capabilities.mark_supported("color_space")
        return await client.get_color_space()

    async def get_motionflow(self) -> str:
        return await self._sdcp_client().get_motionflow()

    async def set_motionflow(self, value: str) -> None:
        await self._sdcp_client().set_motionflow(value)

    async def get_2d_3d_display_select(self) -> str:
        return await self._sdcp_client().get_2d_3d_display_select()

    async def set_2d_3d_display_select(self, value: str) -> None:
        await self._sdcp_client().set_2d_3d_display_select(value)

    async def get_3d_format(self) -> str:
        return await self._sdcp_client().get_3d_format()

    async def set_3d_format(self, value: str) -> None:
        await self._sdcp_client().set_3d_format(value)

    async def get_picture_position(self) -> str:
        return await self._sdcp_client().get_picture_position()

    async def set_picture_position(self, value: str) -> None:
        await self._sdcp_client().set_picture_position(value)

    async def get_reality_creation(self) -> int | str:
        return await self._sdcp_client().get_reality_creation()

    async def get_hdmi1_dynamic_range(self) -> str:
        client = self._connected_client()
        self.capabilities.mark_supported("hdmi1_dynamic_range")
        return await client.get_hdmi1_dynamic_range()

    async def set_hdmi1_dynamic_range(self, value: str) -> None:
        await self._sdcp_client().set_hdmi1_dynamic_range(value)

    async def get_hdmi2_dynamic_range(self) -> str:
        client = self._connected_client()
        self.capabilities.mark_supported("hdmi2_dynamic_range")
        return await client.get_hdmi2_dynamic_range()

    async def set_hdmi2_dynamic_range(self, value: str) -> None:
        await self._sdcp_client().set_hdmi2_dynamic_range(value)

    async def get_hdr(self) -> str:
        client = self._connected_client()
        self.capabilities.mark_supported("hdr")
        return await client.get_hdr()

    async def set_hdr(self, value: str) -> None:
        await self._sdcp_client().set_hdr(value)

    async def get_input_lag_reduction(self) -> str:
        return await self._sdcp_client().get_input_lag_reduction()

    async def set_input_lag_reduction(self, value: bool | str) -> None:
        await self._sdcp_client().set_input_lag_reduction(value)

    async def get_menu_position(self) -> str:
        return await self._sdcp_client().get_menu_position()

    async def set_menu_position(self, value: str) -> None:
        await self._sdcp_client().set_menu_position(value)

    async def get_error_status(self) -> str:
        return await self._sdcp_client().get_error_status()

    async def get_lamp_timer(self) -> int | str:
        return await self._sdcp_client().get_lamp_timer()

    async def _probe_client(self) -> AdcpClient | SdcpClient:
        if self._transport is not None:
            raise ProjectorProtocolError("protocol='auto' cannot infer a protocol from an injected transport")

        errors: list[ProjectorError] = []
        for client in (
            AdcpClient(self.host, timeout=self.timeout, password=self.adcp_password),
            SdcpClient(self.host, timeout=self.timeout, community=self.community),
        ):
            try:
                await client.connect()
                await client.close()
                return client
            except ProjectorError as exc:
                errors.append(exc)

        raise ProjectorConnectionError(f"Could not connect to {self.host} with ADCP or SDCP") from errors[-1]

    def _sdcp_client(self) -> SdcpClient:
        client = self._connected_client()
        if not isinstance(client, SdcpClient):
            raise UnsupportedCommandError("This command is only supported by SDCP")
        return client

    def _connected_client(self) -> AdcpClient | SdcpClient:
        if self._client is None:
            raise ProjectorConnectionError("Projector is not connected")
        return self._client
