# Command Matrix

This matrix records the current public facade surface and whether each command is protocol-neutral or protocol-specific.

## Getter / Setter Coverage By Protocol

| Feature | ADCP getter | ADCP setter | SDCP getter | SDCP setter |
| --- | --- | --- | --- | --- |
| Power | `get_power` | `set_power` | `get_power` | `set_power` |
| Input | `get_input` | `set_input` | `get_input` | `set_input` |
| Signal | `get_signal` | _None_ | _None_ | _None_ |
| Temperature | `get_temperature` | _None_ | _None_ | _None_ |
| Timer / light source hours | `get_timer` | _None_ | `get_lamp_timer` | _None_ |
| Picture mode / calibration preset | `get_picture_mode` | `set_picture_mode` | `get_calibration_preset` | `set_calibration_preset` |
| Warning details | `get_warning` | _None_ | _None_ | _None_ |
| Error details / status | `get_error` | _None_ | `get_error_status` | _None_ |
| Model name | `get_model_name` | _None_ | `get_model_name` | _None_ |
| Serial number | `get_serial_number` | _None_ | `get_serial_number` | _None_ |
| Firmware / protocol version | `get_version` | _None_ | _None_ | _None_ |
| MAC address | `get_mac_address` | _None_ | `get_mac_address` | _None_ |
| Installation location | _None_ | _None_ | `get_installation_location` | _None_ |
| Color temperature | _None_ | _None_ | `get_color_temp` | _None_ |
| Lamp control | `get_lamp_control` | `set_lamp_control` | `get_lamp_control` | `set_lamp_control` |
| Contrast enhancer | _None_ | _None_ | `get_contrast_enhancer` | `set_contrast_enhancer` |
| Advanced iris | _None_ | _None_ | `get_advanced_iris` | `set_advanced_iris` |
| Aspect ratio | `get_aspect_ratio` | `set_aspect_ratio` | `get_aspect_ratio` | `set_aspect_ratio` |
| Gamma correction | _None_ | _None_ | `get_gamma_correction` | _None_ |
| Picture muting | _None_ | _None_ | `get_picture_muting` | `set_picture_muting` |
| Color space | `get_color_space` | `set_color_space` | `get_color_space` | _None_ |
| Motionflow | _None_ | _None_ | `get_motionflow` | `set_motionflow` |
| 2D / 3D display select | _None_ | _None_ | `get_2d_3d_display_select` | `set_2d_3d_display_select` |
| 3D format | _None_ | _None_ | `get_3d_format` | `set_3d_format` |
| Picture position | _None_ | _None_ | `get_picture_position` | `set_picture_position` |
| Reality creation | _None_ | _None_ | `get_reality_creation` | _None_ |
| HDMI 1 dynamic range | `get_hdmi1_dynamic_range` | `set_hdmi1_dynamic_range` | `get_hdmi1_dynamic_range` | `set_hdmi1_dynamic_range` |
| HDMI 2 dynamic range | `get_hdmi2_dynamic_range` | `set_hdmi2_dynamic_range` | `get_hdmi2_dynamic_range` | `set_hdmi2_dynamic_range` |
| HDR | `get_hdr` | `set_hdr` | `get_hdr` | `set_hdr` |
| Input lag reduction | _None_ | _None_ | `get_input_lag_reduction` | `set_input_lag_reduction` |
| Menu position | _None_ | _None_ | `get_menu_position` | `set_menu_position` |

## Static Option Helpers

Some commands need model-aware option lists before an integration creates a select entity.

| Feature key | Protocol | Command methods | Lookup behavior |
| --- | --- | --- | --- |
| `FEATURE_ADCP_PICTURE_MODE` | ADCP | `get_picture_mode`, `set_picture_mode` | Uses Sony model-to-series mappings. Unknown or unlisted ADCP models return `None`. |
| `FEATURE_SDCP_CALIBRATION_PRESET` | SDCP | `get_calibration_preset`, `set_calibration_preset` | Uses the package-supported SDCP fallback for any returned model. Projectors may still reject unsupported values at runtime. |

Use `get_feature_values(model, feature, protocol=...)` for generic lookup, or `get_adcp_picture_mode_options(model)` for the ADCP picture-mode convenience helper. Do not reuse ADCP option lists for SDCP entities.

## Protocol-Neutral Facade Methods

These methods are exposed on `Projector` for both protocols where the selected client supports the command:

| Methods | Release |
| --- | --- |
| `get_power`, `set_power` | MVP |
| `get_input`, `set_input` | MVP |
| `get_model_name` | MVP |
| `get_serial_number` | MVP |
| `get_lamp_control`, `set_lamp_control` | Version 0.2 |
| `get_aspect_ratio`, `set_aspect_ratio` | Version 0.2 |
| `get_color_space` | Version 0.2 |
| `get_hdmi1_dynamic_range`, `set_hdmi1_dynamic_range` | Version 0.2 |
| `get_hdmi2_dynamic_range`, `set_hdmi2_dynamic_range` | Version 0.2 |
| `get_hdr`, `set_hdr` | Version 0.2 |
| `get_mac_address` | Version 0.2 |

## ADCP-Only Facade Methods

| Methods | Release |
| --- | --- |
| `get_signal` | Version 0.2 |
| `get_temperature` | Version 0.2 |
| `get_timer` | Version 0.2 |
| `get_picture_mode`, `set_picture_mode` | Version 0.2 |
| `get_warning` | Version 0.2 |
| `get_error` | Version 0.2 |
| `get_version` | Version 0.2 |
| `set_color_space` | Version 0.2 |

## SDCP-Only Facade Methods

| Methods | Release |
| --- | --- |
| `get_calibration_preset`, `set_calibration_preset` | Version 0.2 |
| `get_color_temp` | Experimental |
| `get_contrast_enhancer`, `set_contrast_enhancer` | Experimental |
| `get_advanced_iris`, `set_advanced_iris` | Experimental |
| `get_gamma_correction` | Experimental |
| `get_picture_muting`, `set_picture_muting` | Version 0.2 |
| `get_motionflow`, `set_motionflow` | Experimental |
| `get_2d_3d_display_select`, `set_2d_3d_display_select` | Experimental |
| `get_3d_format`, `set_3d_format` | Experimental |
| `get_picture_position`, `set_picture_position` | Experimental |
| `get_reality_creation` | Experimental |
| `get_input_lag_reduction`, `set_input_lag_reduction` | Experimental |
| `get_menu_position`, `set_menu_position` | Experimental |
| `get_error_status` | Experimental |
| `get_lamp_timer` | Version 0.2 |
| `get_installation_location` | Version 0.2 |

## Identity

ADCP exposes model, serial, and MAC helper methods where the projector supports them. SDCP/PJ Talk identity reads use equipment information items `0x8001` for model name, `0x8002` for serial number, `0x8003` for installation location, and network information item `0x9000` for MAC address.
