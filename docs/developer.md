# Developer Guide

## Adding Capability Data

Capability data is static source-reference data for model-specific option lists. It is not a runtime cache and it should not replace projector-side unsupported-command handling.

When adding a new model-specific option feature:

1. Find the official Sony protocol command list for the target protocol.
2. Add or update a protocol-scoped feature constant, such as `FEATURE_ADCP_COLOR_SPACE` or `FEATURE_SDCP_CALIBRATION_PRESET`.
3. Add values as `FeatureSupport(...)` entries on the official Sony series row.
4. Add new models only under the series column used by the official model list.
5. Do not infer support from model name prefixes.
6. Keep ADCP and SDCP data separate. Similar user-facing concepts can have different command names and encodings.
7. Add tests for a representative known model, an unknown model, a wrong or unknown feature, and duplicate models within the same protocol.

The same physical model may appear in both ADCP and SDCP capability data, but it must not appear twice within one protocol.

SDCP may use generic protocol fallback rows for package-supported option lists that are not model-specific. Runtime `ProjectorUnsupportedCommandError` handling is still required because projectors can reject an SDCP item as not applicable.

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
