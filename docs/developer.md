# Developer Guide

## Adding Capability Data

Capability data is static source-reference data for setup-time option lists. It is not a runtime cache and it should not replace projector-side unsupported-command handling.

When adding a new model-specific option feature:

1. Find the official Sony protocol command list for the target protocol.
2. Add or update a protocol-scoped feature constant, such as `FEATURE_ADCP_COLOR_SPACE` or `FEATURE_SDCP_CALIBRATION_PRESET`.
3. Add values as `FeatureSupport(...)` entries on the official Sony series row.
4. Add new models only under the series column used by the official model list.
5. Do not infer support from model name prefixes.
6. Keep ADCP and SDCP data separate. Similar user-facing concepts can have different command names and encodings.
7. Add tests for a representative known model, an unknown model, a wrong or unknown feature, and duplicate models within the same protocol.

The same physical model may appear in both ADCP and SDCP capability data, but it must not appear twice within one protocol.

ADCP capability rows should normally be official Sony series rows. Unknown or unlisted ADCP models should return `None` so integrations can decide whether to omit the entity, mark it unavailable, or apply their own override.

SDCP may use generic protocol fallback rows for package-supported option lists that are not model-specific. Use an empty `models=()` tuple for these fallback rows and register the fallback in `_FALLBACK_SERIES_BY_PROTOCOL`. Runtime `ProjectorUnsupportedCommandError` handling is still required because projectors can reject an SDCP item as not applicable.

When adding or changing fallback behavior, add tests for all of these cases:

1. Explicit protocol lookup returns the fallback for an unknown model.
2. Feature-key inference returns the fallback for that protocol-scoped feature.
3. A wrong protocol and feature combination returns `None`.
4. The fallback does not make unrelated protocols appear supported.

Example:

```python
_series_definition(
    key="adcp_video_xw5000",
    protocol=PROTOCOL_ADCP,
    family="video",
    display_name="XW5000",
    models=("VPL-XW5000",),
    features=(
        FeatureSupport(FEATURE_ADCP_PICTURE_MODE, ("cinema_film1", "reference")),
    ),
)
```

## Testing Template Project
