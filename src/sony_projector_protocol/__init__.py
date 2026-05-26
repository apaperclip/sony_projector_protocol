"""Async control helpers for Sony projectors."""

from __future__ import annotations

import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from sony_projector_protocol.discovery import (DiscoveredProjector, discover,
                                               parse_sdap_packet)
from sony_projector_protocol.exceptions import (
    PackageUnsupportedCommandError, ProjectorAuthenticationError,
    ProjectorConnectionError, ProjectorError, ProjectorProtocolError,
    ProjectorTimeoutError, ProjectorUnsupportedCommandError,
    UnsupportedCommandError)
from sony_projector_protocol.projector import Projector
from sony_projector_protocol.sdcp import DEFAULT_SDCP_COMMUNITY
from sony_projector_protocol.types import ProjectorIdentity

__all__ = [
    "DEFAULT_SDCP_COMMUNITY",
    "DiscoveredProjector",
    "Projector",
    "ProjectorIdentity",
    "ProjectorAuthenticationError",
    "ProjectorConnectionError",
    "ProjectorError",
    "ProjectorProtocolError",
    "ProjectorTimeoutError",
    "PackageUnsupportedCommandError",
    "ProjectorUnsupportedCommandError",
    "UnsupportedCommandError",
    "discover",
    "parse_sdap_packet",
]


def _package_version() -> str:
    try:
        return version("sony-projector-protocol")
    except PackageNotFoundError:
        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        try:
            return tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
        except (FileNotFoundError, KeyError, tomllib.TOMLDecodeError):
            return "0.0.0"


__version__ = _package_version()
