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
    ) -> None:
        self.host = host
        self.protocol = Protocol(protocol)
        self.timeout = timeout
        self.capabilities = Capabilities()
        self._transport = transport
        self.community = community
        self._client: AdcpClient | SdcpClient | None = None

    async def connect(self) -> None:
        """Connect to the configured projector."""
        if self.protocol is Protocol.ADCP:
            self._client = AdcpClient(self.host, timeout=self.timeout, transport=self._transport)
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

    async def get_identity(self) -> ProjectorIdentity:
        client = self._connected_client()
        return await client.get_identity()

    async def get_calibration_preset(self) -> str:
        return await self._sdcp_client().get_calibration_preset()

    async def get_color_temp(self) -> int | str:
        return await self._sdcp_client().get_color_temp()

    async def get_lamp_control(self) -> str:
        return await self._sdcp_client().get_lamp_control()

    async def get_contrast_enhancer(self) -> str:
        return await self._sdcp_client().get_contrast_enhancer()

    async def get_advanced_iris(self) -> str:
        return await self._sdcp_client().get_advanced_iris()

    async def get_aspect_ratio(self) -> str:
        return await self._sdcp_client().get_aspect_ratio()

    async def get_gamma_correction(self) -> int | str:
        return await self._sdcp_client().get_gamma_correction()

    async def get_picture_muting(self) -> str:
        return await self._sdcp_client().get_picture_muting()

    async def get_color_space(self) -> int | str:
        return await self._sdcp_client().get_color_space()

    async def get_motionflow(self) -> str:
        return await self._sdcp_client().get_motionflow()

    async def get_2d_3d_display_select(self) -> str:
        return await self._sdcp_client().get_2d_3d_display_select()

    async def get_3d_format(self) -> str:
        return await self._sdcp_client().get_3d_format()

    async def get_picture_position(self) -> str:
        return await self._sdcp_client().get_picture_position()

    async def get_reality_creation(self) -> int | str:
        return await self._sdcp_client().get_reality_creation()

    async def get_hdmi1_dynamic_range(self) -> str:
        return await self._sdcp_client().get_hdmi1_dynamic_range()

    async def get_hdmi2_dynamic_range(self) -> str:
        return await self._sdcp_client().get_hdmi2_dynamic_range()

    async def get_hdr(self) -> str:
        return await self._sdcp_client().get_hdr()

    async def get_input_lag_reduction(self) -> str:
        return await self._sdcp_client().get_input_lag_reduction()

    async def get_menu_position(self) -> str:
        return await self._sdcp_client().get_menu_position()

    async def get_error_status(self) -> str:
        return await self._sdcp_client().get_error_status()

    async def get_lamp_timer(self) -> int | str:
        return await self._sdcp_client().get_lamp_timer()

    async def _probe_client(self) -> AdcpClient | SdcpClient:
        if self._transport is not None:
            raise ProjectorProtocolError("protocol='auto' cannot infer a protocol from an injected transport")

        errors: list[ProjectorError] = []
        for client in (
            AdcpClient(self.host, timeout=self.timeout),
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
