"""Static projector capability helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

PROTOCOL_ADCP = "adcp"
PROTOCOL_SDCP = "sdcp"

FEATURE_ADCP_PICTURE_MODE = "adcp.picture_mode"
FEATURE_SDCP_CALIBRATION_PRESET = "sdcp.calibration_preset"

_KNOWN_PROTOCOLS = {PROTOCOL_ADCP, PROTOCOL_SDCP}

ADCP_VIDEO_COMMON_PICTURE_MODES = (
    "cinema_film1",
    "cinema_film2",
    "reference",
    "tv",
    "photo",
    "brt_cinema",
    "brt_tv",
    "game",
)

ADCP_DATA_BASE_PICTURE_MODES = (
    "dynamic",
    "standard",
)

SDCP_CALIBRATION_PRESET_VALUES = (
    "cinema_film_1",
    "cinema_film_2",
    "ref",
    "tv",
    "photo",
    "game",
    "bright_cinema",
    "bright_tv",
    "user",
)

ADCP_PICTURE_MODE_VALUES = tuple(
    dict.fromkeys(
        (
            *ADCP_VIDEO_COMMON_PICTURE_MODES,
            "user",
            "user1",
            "user2",
            "user3",
            "cinema_digital",
            *ADCP_DATA_BASE_PICTURE_MODES,
            "brt_priority",
            "multi_screen",
            "presentation",
            "blackboard",
            "whiteboard",
            "cinema",
            "vivid",
            "srgb",
        )
    )
)

ADCP_PICTURE_MODE_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "blackboard": "Blackboard",
        "brt_cinema": "Bright Cinema",
        "brt_priority": "Brightness Priority",
        "brt_tv": "Bright TV",
        "cinema": "Cinema",
        "cinema_digital": "Cinema Digital",
        "cinema_film1": "Cinema Film 1",
        "cinema_film2": "Cinema Film 2",
        "dynamic": "Dynamic",
        "game": "Game",
        "multi_screen": "Multi Screen",
        "photo": "Photo",
        "presentation": "Presentation",
        "reference": "Reference",
        "srgb": "sRGB",
        "standard": "Standard",
        "tv": "TV",
        "user": "User",
        "user1": "User 1",
        "user2": "User 2",
        "user3": "User 3",
        "vivid": "Vivid",
        "whiteboard": "Whiteboard",
    }
)


@dataclass(frozen=True)
class ProjectorSeries:
    """Official Sony projector series used for static capability lookup."""

    key: str
    family: str
    protocol: str
    display_name: str
    models: tuple[str, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class FeatureSupport:
    """Supported values for one feature in a projector series."""

    feature: str
    values: tuple[str, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class SeriesCapabilities:
    """Feature support attached to one projector series."""

    series_key: str
    features: Mapping[str, FeatureSupport]


@dataclass(frozen=True)
class _SeriesDefinition:
    series: ProjectorSeries
    capabilities: SeriesCapabilities


def _feature_map(*features: FeatureSupport) -> Mapping[str, FeatureSupport]:
    return MappingProxyType({feature.feature: feature for feature in features})


def _adcp_picture_modes(*values: str, notes: tuple[str, ...] = ()) -> FeatureSupport:
    return FeatureSupport(FEATURE_ADCP_PICTURE_MODE, values, notes)


def _sdcp_calibration_presets(*values: str, notes: tuple[str, ...] = ()) -> FeatureSupport:
    return FeatureSupport(FEATURE_SDCP_CALIBRATION_PRESET, values, notes)


def _feature_protocol(feature: str) -> str | None:
    protocol, separator, _name = feature.partition(".")
    if separator and protocol in _KNOWN_PROTOCOLS:
        return protocol
    return None


def _series_definition(
    *,
    key: str,
    protocol: str,
    family: str,
    display_name: str,
    models: tuple[str, ...],
    features: tuple[FeatureSupport, ...],
    notes: tuple[str, ...] = (),
) -> _SeriesDefinition:
    normalized_protocol = protocol.lower()
    feature_names = [feature.feature for feature in features]
    if len(feature_names) != len(set(feature_names)):
        raise ValueError(f"Duplicate feature support in series {key}")
    if any(_feature_protocol(feature_name) != normalized_protocol for feature_name in feature_names):
        raise ValueError(f"Feature support in series {key} must use {normalized_protocol} feature keys")

    return _SeriesDefinition(
        series=ProjectorSeries(
            key=key,
            family=family,
            protocol=normalized_protocol,
            display_name=display_name,
            models=models,
            notes=notes,
        ),
        capabilities=SeriesCapabilities(
            key,
            _feature_map(*features),
        ),
    )


_VIDEO_VW5000_MODES = (
    *ADCP_VIDEO_COMMON_PICTURE_MODES,
    "user1",
    "user2",
    "user3",
    "cinema_digital",
)

_VIDEO_LEGACY_USER_MODES = (
    *ADCP_VIDEO_COMMON_PICTURE_MODES,
    "user",
)

_VIDEO_XW_MODES = (
    *ADCP_VIDEO_COMMON_PICTURE_MODES,
    "user1",
    "user3",
)

_DATA_INSTALLATION_MODES = (
    *ADCP_DATA_BASE_PICTURE_MODES,
    "brt_priority",
    "multi_screen",
)

_DATA_INSTALLATION_SRGB_MODES = (
    *_DATA_INSTALLATION_MODES,
    "srgb",
)

_DATA_PRESENTATION_MODES = (
    *ADCP_DATA_BASE_PICTURE_MODES,
    "presentation",
)

_DATA_EDUCATION_SRGB_MODES = (
    *_DATA_PRESENTATION_MODES,
    "blackboard",
    "whiteboard",
    "cinema",
    "srgb",
)

_DATA_EDUCATION_VIVID_MODES = (
    *_DATA_PRESENTATION_MODES,
    "blackboard",
    "whiteboard",
    "cinema",
    "vivid",
)

_SERIES_DEFINITIONS = (
    _series_definition(
        protocol=PROTOCOL_SDCP,
        key="sdcp_any_model",
        family="generic",
        display_name="Any SDCP model",
        models=(),
        features=(
            _sdcp_calibration_presets(
                *SDCP_CALIBRATION_PRESET_VALUES,
                notes=("Generic SDCP package-supported values; projectors may still reject unsupported items.",),
            ),
        ),
        notes=("Generic SDCP option list for models returned by projector identity.",),
    ),
    # Video projector series columns.
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_vw5000",
        family="video",
        display_name="VW5000",
        models=("VPL-VW5000",),
        features=(_adcp_picture_modes(*_VIDEO_VW5000_MODES),),
        notes=("Supports user1/user2/user3 and cinema_digital instead of user.",),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_vw760es",
        family="video",
        display_name="VW760ES",
        models=("VPL-VW745", "VPL-VW768", "VPL-VW760ES", "VPL-VW885ES"),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
        notes=("Supports user instead of user1/user2/user3/cinema_digital.",),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_vw675es",
        family="video",
        display_name="VW675ES",
        models=("VPL-VW535", "VPL-VW550ES", "VPL-VW558", "VPL-VW675ES"),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_vw665es",
        family="video",
        display_name="VW665ES",
        models=("VPL-VW515ES", "VPL-VW520ES", "VPL-VW528", "VPL-VW665ES"),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_vw365es",
        family="video",
        display_name="VW365ES",
        models=("VPL-VW315ES", "VPL-VW320ES", "VPL-VW328", "VPL-VW365ES"),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_vw360es",
        family="video",
        display_name="VW360ES",
        models=("VPL-VW360ES", "VPL-VW368", "VPL-VW385ES"),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_vw260es",
        family="video",
        display_name="VW260ES",
        models=("VPL-VW245", "VPL-VW260ES", "VPL-VW268", "VPL-VW285ES"),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_vz1000",
        family="video",
        display_name="VZ1000",
        models=("VPL-VZ1000", "VPL-VZ1000ES"),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_hw65es",
        family="video",
        display_name="HW65ES",
        models=("VPL-HW60ES", "VPL-HW65ES", "VPL-HW68", "VPL-HW69", "VPL-HW79"),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_hw45es",
        family="video",
        display_name="HW45ES",
        models=("VPL-HW45ES", "VPL-HW48", "VPL-HW49"),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_vw890es_vw870es",
        family="video",
        display_name="VW890ES/VW870ES",
        models=(
            "VPL-VW855",
            "VPL-VW870ES",
            "VPL-VW878",
            "VPL-VW995ES",
            "VPL-VW875",
            "VPL-VW898",
            "VPL-VW890ES",
            "VPL-VW1025ES",
        ),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_vw570es",
        family="video",
        display_name="VW570ES",
        models=("VPL-VW555", "VPL-VW570ES", "VPL-VW578", "VPL-VW695ES"),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_vw290es_vw270es",
        family="video",
        display_name="VW290ES/VW270ES",
        models=(
            "VPL-VW255",
            "VPL-VW270ES",
            "VPL-VW278",
            "VPL-VW295ES",
            "VPL-VW275",
            "VPL-VW298",
            "VPL-VW290ES",
            "VPL-VW325ES",
        ),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_vw790es",
        family="video",
        display_name="VW790ES",
        models=("VPL-VW775", "VPL-VW790ES", "VPL-VW798", "VPL-VW915ES"),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_vw590es",
        family="video",
        display_name="VW590ES",
        models=("VPL-VW575ES", "VPL-VW590ES", "VPL-VW598ES", "VPL-VW715ES"),
        features=(_adcp_picture_modes(*_VIDEO_LEGACY_USER_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_xw7000",
        family="video",
        display_name="XW7000",
        models=("VPL-XW7000",),
        features=(_adcp_picture_modes(*_VIDEO_XW_MODES),),
        notes=("Supports user1 and user3; does not support user, user2, or cinema_digital.",),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_xw6000",
        family="video",
        display_name="XW6000",
        models=("VPL-XW6000",),
        features=(_adcp_picture_modes(*_VIDEO_XW_MODES),),
        notes=("Supports user1 and user3; does not support user, user2, or cinema_digital.",),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_xw5000",
        family="video",
        display_name="XW5000",
        models=("VPL-XW5000",),
        features=(_adcp_picture_modes(*_VIDEO_XW_MODES),),
        notes=("Supports user1 and user3; does not support user, user2, or cinema_digital.",),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_xw8100",
        family="video",
        display_name="XW8100",
        models=("VPL-XW8100",),
        features=(_adcp_picture_modes(*_VIDEO_XW_MODES),),
        notes=("Supports user1 and user3; does not support user, user2, or cinema_digital.",),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_xw6100",
        family="video",
        display_name="XW6100",
        models=("VPL-XW6100",),
        features=(_adcp_picture_modes(*_VIDEO_XW_MODES),),
        notes=("Supports user1 and user3; does not support user, user2, or cinema_digital.",),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_video_xw5100",
        family="video",
        display_name="XW5100",
        models=("VPL-XW5100",),
        features=(_adcp_picture_modes(*_VIDEO_XW_MODES),),
        notes=("Supports user1 and user3; does not support user, user2, or cinema_digital.",),
    ),
    # Data projector series columns.
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_data_fhz120_fhz90_f1200_f900",
        family="data",
        display_name="FHZ120/FHZ90/F1200/F900",
        models=("VPL-FHZ120L", "VPL-FHZ90L", "VPL-F1200ZL", "VPL-F1205ZL", "VPL-F900ZL", "VPL-F905ZL"),
        features=(
            _adcp_picture_modes(
                *_DATA_INSTALLATION_SRGB_MODES,
                notes=("srgb applies only to FHZ120/F1200 models in this official series group.",),
            ),
        ),
        notes=("The official srgb support note applies only to FHZ120/F1200 models in this group.",),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_data_fhz60_fhz50_fwz60_f630hz_f530hz_f430hz_f630wz_f530wz",
        family="data",
        display_name="FHZ60/FHZ50/FWZ60/F630HZ/F530HZ/F430HZ/F630WZ/F530WZ",
        models=(
            "VPL-FHZ50",
            "VPL-FHZ57",
            "VPL-FHZ58",
            "VPL-FHZ60",
            "VPL-FHZ65",
            "VPL-FHZ66",
            "VPL-FHZ70",
            "VPL-FHZ75",
            "VPL-FWZ60",
            "VPL-FWZ65",
            "VPL-F430HZ",
            "VPL-F530HZ",
            "VPL-F530WZ",
            "VPL-F630HZ",
            "VPL-F630WZ",
        ),
        features=(_adcp_picture_modes(*_DATA_INSTALLATION_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_data_fh60_fw60_f530h_f630h_f630w_f530w",
        family="data",
        display_name="FH60/FW60/F530H/F630H/F630W/F530W",
        models=("VPL-FH60", "VPL-FH65", "VPL-FW60", "VPL-FW65", "VPL-F530H", "VPL-F630H", "VPL-F630W", "VPL-F530W"),
        features=(_adcp_picture_modes(*_DATA_INSTALLATION_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_data_fhz700_f700hz",
        family="data",
        display_name="FHZ700/F700HZ",
        models=("VPL-FHZ700L", "VPL-F720HZL", "VPL-F725HZL"),
        features=(_adcp_picture_modes(*ADCP_DATA_BASE_PICTURE_MODES, "brt_priority", "presentation"),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_data_fh30_f400h_f500h",
        family="data",
        display_name="FH30/F400H/F500H",
        models=("VPL-F401H", "VPL-FH31"),
        features=(_adcp_picture_modes(*_DATA_PRESENTATION_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_data_c300",
        family="data",
        display_name="C300",
        models=(
            "VPL-CH350",
            "VPL-CH353",
            "VPL-CH355",
            "VPL-CH358",
            "VPL-CH370",
            "VPL-CH373",
            "VPL-CH375",
            "VPL-CH378",
        ),
        features=(_adcp_picture_modes(*_DATA_PRESENTATION_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_data_e200",
        family="data",
        display_name="E200",
        models=("VPL-EW235", "VPL-EW255", "VPL-EW275", "VPL-EX235", "VPL-EX255", "VPL-EX275"),
        features=(_adcp_picture_modes(*_DATA_EDUCATION_SRGB_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_data_e300",
        family="data",
        display_name="E300",
        models=("VPL-EW295", "VPL-EW315", "VPL-EW345", "VPL-EW348", "VPL-EX295", "VPL-EX315", "VPL-EX345", "VPL-EX348"),
        features=(_adcp_picture_modes(*_DATA_EDUCATION_SRGB_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_data_e400_e500",
        family="data",
        display_name="E400/E500",
        models=(
            "VPL-EW435",
            "VPL-EW455",
            "VPL-EW575",
            "VPL-EW578",
            "VPL-EX435",
            "VPL-EX455",
            "VPL-EX575",
            "VPL-EX578",
        ),
        features=(_adcp_picture_modes(*_DATA_EDUCATION_VIVID_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_data_s200",
        family="data",
        display_name="S200",
        models=("VPL-SW225", "VPL-SW235", "VPL-SX225", "VPL-SX235"),
        features=(_adcp_picture_modes(*_DATA_EDUCATION_SRGB_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_data_s600",
        family="data",
        display_name="S600",
        models=("VPL-SW525", "VPL-SW535", "VPL-SW536", "VPL-SW630", "VPL-SW631", "VPL-SX535", "VPL-SX536", "VPL-SX630", "VPL-SX631"),
        features=(_adcp_picture_modes(*_DATA_EDUCATION_SRGB_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_data_p10_p500",
        family="data",
        display_name="P10/P500",
        models=("VPL-PHZ10", "VPL-PWZ10", "VPL-PXZ10", "VPL-P500HZ", "VPL-P500WZ", "VPL-P500XZ"),
        features=(_adcp_picture_modes(*_DATA_PRESENTATION_MODES),),
    ),
    _series_definition(
        protocol=PROTOCOL_ADCP,
        key="adcp_data_u300",
        family="data",
        display_name="U300",
        models=("VPL-U300WZ",),
        features=(_adcp_picture_modes(*_DATA_PRESENTATION_MODES),),
    ),
)

SERIES_BY_KEY: Mapping[str, ProjectorSeries] = MappingProxyType(
    {definition.series.key: definition.series for definition in _SERIES_DEFINITIONS}
)

CAPABILITIES_BY_SERIES: Mapping[str, SeriesCapabilities] = MappingProxyType(
    {definition.series.key: definition.capabilities for definition in _SERIES_DEFINITIONS}
)

_FALLBACK_SERIES_BY_PROTOCOL = MappingProxyType(
    {
        PROTOCOL_SDCP: "sdcp_any_model",
    }
)


def normalize_model_name(model: str) -> str:
    """Normalize model names for static capability lookup."""
    normalized = model.strip().upper().replace("_", "-").replace(" ", "")
    if normalized and not normalized.startswith("VPL-"):
        normalized = f"VPL-{normalized}"
    normalized = re.sub(r"^(VPL-[A-Z]+)-(?=[0-9])", r"\1", normalized)
    return normalized


MODEL_TO_SERIES: Mapping[tuple[str, str], str] = MappingProxyType(
    {
        (series.protocol, normalize_model_name(model)): series.key
        for series in SERIES_BY_KEY.values()
        for model in series.models
    }
)


def _normalize_protocol(protocol: str) -> str:
    return protocol.strip().lower()


def get_projector_series(model: str, *, protocol: str | None = None) -> ProjectorSeries | None:
    """Return the official series entry for a projector model."""
    normalized_model = normalize_model_name(model)
    if protocol is not None:
        normalized_protocol = _normalize_protocol(protocol)
        series_key = MODEL_TO_SERIES.get(
            (normalized_protocol, normalized_model),
            _FALLBACK_SERIES_BY_PROTOCOL.get(normalized_protocol),
        )
        if series_key is None:
            return None
        return SERIES_BY_KEY.get(series_key)

    matches = {
        series_key
        for (_protocol, model_name), series_key in MODEL_TO_SERIES.items()
        if model_name == normalized_model
    }
    if len(matches) != 1:
        return None
    return SERIES_BY_KEY.get(next(iter(matches)))


def get_series_feature_values(series_key: str, feature: str) -> tuple[str, ...] | None:
    """Return supported values for a feature on an official series key."""
    capabilities = CAPABILITIES_BY_SERIES.get(series_key)
    if capabilities is None:
        return None

    support = capabilities.features.get(feature)
    if support is None:
        return None
    return support.values


def get_feature_values(model: str, feature: str, *, protocol: str | None = None) -> tuple[str, ...] | None:
    """Return supported values for a feature on a projector model."""
    series = get_projector_series(model, protocol=protocol or _feature_protocol(feature))
    if series is None:
        return None
    return get_series_feature_values(series.key, feature)


def get_adcp_picture_mode_options(model: str) -> tuple[str, ...] | None:
    """Return official ADCP picture_mode options for a projector model."""
    return get_feature_values(model, FEATURE_ADCP_PICTURE_MODE, protocol=PROTOCOL_ADCP)
