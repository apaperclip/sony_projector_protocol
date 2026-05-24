"""Protocol-neutral projector facade."""

from __future__ import annotations

from sony_projector_protocol.adcp import AdcpClient
from sony_projector_protocol.exceptions import (ProjectorConnectionError,
                                                UnsupportedCommandError)
from sony_projector_protocol.sdcp import DEFAULT_SDCP_COMMUNITY, SdcpClient
from sony_projector_protocol.transport import Transport
from sony_projector_protocol.types import ProjectorIdentity

PROTOCOL_ADCP = "adcp"
PROTOCOL_SDCP = "sdcp"


class Projector:
    """Async protocol-neutral projector controller."""

    def __init__(
        self,
        host: str,
        *,
        protocol: str,
        timeout: float = 5.0,
        transport: Transport | None = None,
        community: str | None = None,
        adcp_password: str | None = None,
    ) -> None:
        self.host = host
        self.protocol = self._normalize_protocol(protocol)
        self.timeout = timeout
        self._transport = transport
        self.community = DEFAULT_SDCP_COMMUNITY if community is None else community
        self.adcp_password = adcp_password
        self._client: AdcpClient | SdcpClient | None = None

    async def connect(self) -> None:
        """Connect to the configured projector."""
        if self.protocol == PROTOCOL_ADCP:
            self._client = AdcpClient(
                self.host, timeout=self.timeout, transport=self._transport, password=self.adcp_password
            )
        else:
            self._client = SdcpClient(
                self.host, timeout=self.timeout, transport=self._transport, community=self.community
            )

        await self._client.connect()

    async def close(self) -> None:
        """Close the active connection."""
        if self._client is not None:
            await self._client.close()

    async def get_power(self) -> str:
        client = self._connected_client()
        return await client.get_power()

    async def set_power(self, power: bool) -> None:
        client = self._connected_client()
        await client.set_power(power)

    async def get_input(self) -> str:
        client = self._connected_client()
        return await client.get_input()

    async def set_input(self, value: str) -> None:
        client = self._connected_client()
        await client.set_input(value)

    async def get_signal(self) -> str:
        return await self._adcp_client().get_signal()

    async def get_temperature(self) -> int | float | str:
        return await self._adcp_client().get_temperature()

    async def get_timer(self) -> int | float | str:
        return await self._adcp_client().get_timer()

    async def get_picture_mode(self) -> str:
        return await self._adcp_client().get_picture_mode()

    async def set_picture_mode(self, value: str) -> None:
        await self._adcp_client().set_picture_mode(value)

    async def get_warning(self) -> list[str] | str:
        return await self._adcp_client().get_warning()

    async def get_error(self) -> list[str] | str:
        return await self._adcp_client().get_error()

    async def get_identity(self) -> ProjectorIdentity:
        client = self._connected_client()
        return await client.get_identity()

    async def get_model_name(self) -> str:
        client = self._connected_client()
        return await client.get_model_name()

    async def get_serial_number(self) -> str:
        client = self._connected_client()
        return await client.get_serial_number()

    async def get_version(self) -> str:
        return await self._adcp_client().get_version()

    async def get_mac_address(self) -> str:
        client = self._connected_client()
        return await client.get_mac_address()

    async def get_installation_location(self) -> str:
        return await self._sdcp_client().get_installation_location()

    async def get_calibration_preset(self) -> str:
        return await self._sdcp_client().get_calibration_preset()

    async def set_calibration_preset(self, value: str) -> None:
        await self._sdcp_client().set_calibration_preset(value)

    async def get_color_temp(self) -> int | str:
        return await self._sdcp_client().get_color_temp()

    async def get_lamp_control(self) -> str:
        client = self._connected_client()
        return await client.get_lamp_control()

    async def set_lamp_control(self, value: str) -> None:
        client = self._connected_client()
        await client.set_lamp_control(value)

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
        return await client.get_aspect_ratio()

    async def set_aspect_ratio(self, value: str) -> None:
        client = self._connected_client()
        await client.set_aspect_ratio(value)

    async def get_gamma_correction(self) -> int | str:
        return await self._sdcp_client().get_gamma_correction()

    async def get_picture_muting(self) -> str:
        return await self._sdcp_client().get_picture_muting()

    async def set_picture_muting(self, value: bool | str) -> None:
        await self._sdcp_client().set_picture_muting(value)

    async def get_color_space(self) -> int | str:
        client = self._connected_client()
        return await client.get_color_space()

    async def set_color_space(self, value: str) -> None:
        await self._adcp_client().set_color_space(value)

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
        return await client.get_hdmi1_dynamic_range()

    async def set_hdmi1_dynamic_range(self, value: str) -> None:
        client = self._connected_client()
        await client.set_hdmi1_dynamic_range(value)

    async def get_hdmi2_dynamic_range(self) -> str:
        client = self._connected_client()
        return await client.get_hdmi2_dynamic_range()

    async def set_hdmi2_dynamic_range(self, value: str) -> None:
        client = self._connected_client()
        await client.set_hdmi2_dynamic_range(value)

    async def get_hdr(self) -> str:
        client = self._connected_client()
        return await client.get_hdr()

    async def set_hdr(self, value: str) -> None:
        client = self._connected_client()
        await client.set_hdr(value)

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

    def _normalize_protocol(self, protocol: str) -> str:
        normalized = protocol.lower()
        if normalized not in {PROTOCOL_ADCP, PROTOCOL_SDCP}:
            raise ValueError(f"Unsupported protocol: {protocol}. Expected 'adcp' or 'sdcp'.")
        return normalized

    def _adcp_client(self) -> AdcpClient:
        client = self._connected_client()
        if not isinstance(client, AdcpClient):
            raise UnsupportedCommandError("This command is only supported by ADCP")
        return client

    def _sdcp_client(self) -> SdcpClient:
        client = self._connected_client()
        if not isinstance(client, SdcpClient):
            raise UnsupportedCommandError("This command is only supported by SDCP")
        return client

    def _connected_client(self) -> AdcpClient | SdcpClient:
        if self._client is None:
            raise ProjectorConnectionError("Projector is not connected")
        return self._client
