"""Async control helpers for Sony projectors."""

from __future__ import annotations

from sony_projector_protocol.discovery import DiscoveredProjector, discover, parse_sdap_packet
from sony_projector_protocol.exceptions import (
    ProjectorAuthenticationError,
    ProjectorConnectionError,
    ProjectorError,
    ProjectorProtocolError,
    ProjectorTimeoutError,
    UnsupportedCommandError,
)
from sony_projector_protocol.models import Input, PowerState, Protocol
from sony_projector_protocol.projector import Projector

__all__ = [
    "DiscoveredProjector",
    "Input",
    "PowerState",
    "Projector",
    "ProjectorAuthenticationError",
    "ProjectorConnectionError",
    "ProjectorError",
    "ProjectorProtocolError",
    "ProjectorTimeoutError",
    "Protocol",
    "UnsupportedCommandError",
    "discover",
    "parse_sdap_packet",
]

__version__ = "0.1.0"
