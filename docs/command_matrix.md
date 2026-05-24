# Command Matrix

This matrix records the current public facade surface and whether each command is protocol-neutral or protocol-specific.

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
