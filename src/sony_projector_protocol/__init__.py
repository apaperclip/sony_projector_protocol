"""Async control helpers for Sony projectors."""

from __future__ import annotations

import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from sony_projector_protocol.capabilities import (
    ADCP_PICTURE_MODE_LABELS, ADCP_PICTURE_MODE_VALUES, CAPABILITIES_BY_SERIES,
    FEATURE_PICTURE_MODE, MODEL_TO_SERIES, SERIES_BY_KEY, FeatureSupport,
    ProjectorSeries, SeriesCapabilities, get_adcp_picture_mode_options,
    get_feature_values, get_projector_series, get_series_feature_values,
    normalize_model_name)
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
    "ADCP_PICTURE_MODE_LABELS",
    "ADCP_PICTURE_MODE_VALUES",
    "CAPABILITIES_BY_SERIES",
    "DEFAULT_SDCP_COMMUNITY",
    "DiscoveredProjector",
    "FEATURE_PICTURE_MODE",
    "FeatureSupport",
    "MODEL_TO_SERIES",
    "Projector",
    "ProjectorIdentity",
    "ProjectorSeries",
    "ProjectorAuthenticationError",
    "ProjectorConnectionError",
    "ProjectorError",
    "ProjectorProtocolError",
    "ProjectorTimeoutError",
    "PackageUnsupportedCommandError",
    "ProjectorUnsupportedCommandError",
    "SERIES_BY_KEY",
    "SeriesCapabilities",
    "UnsupportedCommandError",
    "discover",
    "get_adcp_picture_mode_options",
    "get_feature_values",
    "get_projector_series",
    "get_series_feature_values",
    "normalize_model_name",
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
