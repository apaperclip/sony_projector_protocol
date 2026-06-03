"""Async control helpers for Sony projectors."""

from __future__ import annotations

import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from sony_projector_protocol.capabilities import (
    ADCP_COLOR_SPACE_LABELS,
    ADCP_COLOR_SPACE_VALUES,
    ADCP_INPUT_VALUES,
    ADCP_PICTURE_MODE_LABELS,
    ADCP_PICTURE_MODE_VALUES,
    CAPABILITIES_BY_SERIES,
    FEATURE_ADCP_COLOR_SPACE,
    FEATURE_ADCP_INPUT,
    FEATURE_ADCP_PICTURE_MODE,
    FEATURE_SDCP_CALIBRATION_PRESET,
    FEATURE_SDCP_COLOR_SPACE,
    FEATURE_SDCP_INPUT,
    MODEL_TO_SERIES,
    PROTOCOL_ADCP,
    PROTOCOL_SDCP,
    SDCP_CALIBRATION_PRESET_VALUES,
    SDCP_COLOR_SPACE_VALUES,
    SDCP_INPUT_VALUES,
    SERIES_BY_KEY,
    FeatureSupport,
    ProjectorSeries,
    SeriesCapabilities,
    get_adcp_picture_mode_options,
    get_feature_values,
    get_projector_series,
    get_series_feature_values,
    normalize_model_name,
)
from sony_projector_protocol.discovery import DiscoveredProjector, discover, parse_sdap_packet
from sony_projector_protocol.exceptions import (
    PackageUnsupportedCommandError,
    ProjectorAuthenticationError,
    ProjectorConnectionError,
    ProjectorError,
    ProjectorProtocolError,
    ProjectorTimeoutError,
    ProjectorUnsupportedCommandError,
    UnsupportedCommandError,
)
from sony_projector_protocol.projector import Projector
from sony_projector_protocol.sdcp import DEFAULT_SDCP_COMMUNITY
from sony_projector_protocol.types import ProjectorIdentity

__all__ = [
    "ADCP_PICTURE_MODE_LABELS",
    "ADCP_PICTURE_MODE_VALUES",
    "ADCP_COLOR_SPACE_LABELS",
    "ADCP_COLOR_SPACE_VALUES",
    "ADCP_INPUT_VALUES",
    "CAPABILITIES_BY_SERIES",
    "DEFAULT_SDCP_COMMUNITY",
    "DiscoveredProjector",
    "FEATURE_ADCP_COLOR_SPACE",
    "FEATURE_ADCP_INPUT",
    "FEATURE_ADCP_PICTURE_MODE",
    "FEATURE_SDCP_CALIBRATION_PRESET",
    "FEATURE_SDCP_COLOR_SPACE",
    "FEATURE_SDCP_INPUT",
    "FeatureSupport",
    "MODEL_TO_SERIES",
    "PROTOCOL_ADCP",
    "PROTOCOL_SDCP",
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
    "SDCP_CALIBRATION_PRESET_VALUES",
    "SDCP_COLOR_SPACE_VALUES",
    "SDCP_INPUT_VALUES",
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
