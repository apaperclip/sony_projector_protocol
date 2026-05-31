#!/usr/bin/env python3
"""Probe Sony SDCP/PJ Talk GET values from a live projector."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from struct import unpack
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sony_projector_protocol import (FEATURE_SDCP_CALIBRATION_PRESET,
                                     PROTOCOL_SDCP, get_feature_values,
                                     get_projector_series)
from sony_projector_protocol.sdcp import SdcpClient

ACTION_GET = 0x01

RESPONSE_ERRORS = {
    0x0101: "Item Error: Invalid Item",
    0x0102: "Item Error: Invalid Item Request",
    0x0103: "Item Error: Invalid Length",
    0x0104: "Item Error: Invalid Data",
    0x0111: "Item Error: Short Data",
    0x0180: "Item Error: Not Applicable Item",
    0x0201: "Community Error: Different Community",
    0x1001: "Request Error: Invalid Version",
    0x1002: "Request Error: Invalid Category",
    0x1003: "Request Error: Invalid Request",
    0x1011: "Request Error: Short Header",
    0x1012: "Request Error: Short Community",
    0x1013: "Request Error: Short Command",
    0xF001: "Comm Error: Timeout",
    0xF010: "Comm Error: Check Sum Error",
    0xF020: "Comm Error: Framing Error",
    0xF030: "Comm Error: Parity Error",
    0xF040: "Comm Error: Over Run Error",
    0xF050: "Comm Error: Other Comm Error",
    0xF0F0: "Comm Error: Unknown Response",
    0xF110: "NVRAM Error: Read Error",
    0xF120: "NVRAM Error: Write Error",
}


def invert(values: dict[str, int]) -> dict[int, str]:
    return {value: key.lower() for key, value in values.items()}


VALUE_MAPS = {
    "input": invert({"hdmi1": 0x0002, "hdmi2": 0x0003}),
    "calibration_preset": invert(
        {
            "cinema_film_1": 0x0000,
            "cinema_film_2": 0x0001,
            "ref": 0x0002,
            "tv": 0x0003,
            "photo": 0x0004,
            "game": 0x0005,
            "bright_cinema": 0x0006,
            "bright_tv": 0x0007,
            "user": 0x0008,
        }
    ),
    "lamp_control": invert({"low": 0x0000, "high": 0x0001}),
    "contrast_enhancer": invert({"off": 0x0000, "low": 0x0001, "high": 0x0002, "middle": 0x0003}),
    "advanced_iris": invert({"off": 0x0000, "full": 0x0002, "limited": 0x0003}),
    "aspect_ratio": invert(
        {
            "normal": 0x0001,
            "v_stretch": 0x000B,
            "zoom_1_85": 0x000C,
            "zoom_2_35": 0x000D,
            "stretch": 0x000E,
            "squeeze": 0x000F,
        }
    ),
    "picture_muting": invert({"off": 0x0000, "on": 0x0001}),
    "motionflow": invert(
        {
            "off": 0x0000,
            "smooth_high": 0x0001,
            "smooth_low": 0x0002,
            "impulse": 0x0003,
            "combination": 0x0004,
            "true_cinema": 0x0005,
        }
    ),
    "2d_3d_display_select": invert({"auto": 0x0000, "3d": 0x0001, "2d": 0x0002}),
    "3d_format": invert({"simulated_3d": 0x0000, "side_by_side": 0x0001, "over_under": 0x0002}),
    "picture_position": invert(
        {
            "1_85": 0x0000,
            "2_35": 0x0001,
            "custom_1": 0x0002,
            "custom_2": 0x0003,
            "custom_3": 0x0004,
            "custom_4": 0x0005,
            "custom_5": 0x0006,
        }
    ),
    "dynamic_range": invert({"auto": 0x0000, "limited": 0x0001, "full": 0x0002}),
    "hdr": invert({"off": 0x0000, "on": 0x0001, "auto": 0x0002}),
    "input_lag_reduction": invert({"off": 0x0000, "on": 0x0001}),
    "menu_position": invert({"bottom_left": 0x0000, "center": 0x0001}),
    "power_status": invert(
        {
            "standby": 0x0000,
            "start_up": 0x0001,
            "start_up_lamp": 0x0002,
            "on": 0x0003,
            "cooling": 0x0004,
            "cooling2": 0x0005,
        }
    ),
    "error_status": invert(
        {
            "no_error": 0x0000,
            "lamp_error": 0x0001,
            "fan_error": 0x0002,
            "cover_error": 0x0004,
            "temp_error": 0x0008,
            "d5v_error": 0x000A,
            "power_error": 0x0014,
            "temp_warning": 0x0028,
        }
    ),
}


@dataclass(frozen=True)
class Feature:
    name: str
    command: int
    value_map: str | None = None
    unit: str | None = None


FEATURES = [
    Feature("input", 0x0001, "input"),
    Feature("calibration_preset", 0x0002, "calibration_preset"),
    Feature("color_temp", 0x0017),
    Feature("lamp_control", 0x001A, "lamp_control"),
    Feature("contrast_enhancer", 0x001C, "contrast_enhancer"),
    Feature("advanced_iris", 0x001D, "advanced_iris"),
    Feature("aspect_ratio", 0x0020, "aspect_ratio"),
    Feature("gamma_correction", 0x0022),
    Feature("picture_muting", 0x0030, "picture_muting"),
    Feature("color_space", 0x003B),
    Feature("motionflow", 0x0059, "motionflow"),
    Feature("2d_3d_display_select", 0x0060, "2d_3d_display_select"),
    Feature("3d_format", 0x0061, "3d_format"),
    Feature("picture_position", 0x0066, "picture_position"),
    Feature("reality_creation", 0x0067),
    Feature("hdmi1_dynamic_range", 0x006E, "dynamic_range"),
    Feature("hdmi2_dynamic_range", 0x006F, "dynamic_range"),
    Feature("hdr", 0x007C, "hdr"),
    Feature("input_lag_reduction", 0x0099, "input_lag_reduction"),
    Feature("menu_position", 0x00A6, "menu_position"),
    Feature("error_status", 0x0101, "error_status"),
    Feature("power_status", 0x0102, "power_status"),
    Feature("lamp_timer", 0x0113, unit="hours"),
]


def parse_response(payload: bytes, expected_command: int) -> dict[str, Any]:
    if len(payload) < 10:
        return {"ok": False, "error": "short_response", "response_hex": payload.hex(" ")}

    response_command = unpack(">H", payload[7:9])[0]
    data_len = payload[9]
    data = unpack(">H", payload[10:12])[0] if data_len else None
    ok = bool(payload[6])

    result: dict[str, Any] = {
        "ok": ok,
        "response_hex": payload.hex(" "),
        "response_command": f"0x{response_command:04x}",
        "data_length": data_len,
        "value": data,
    }

    if response_command != expected_command:
        result["ok"] = False
        result["error"] = f"unexpected command 0x{response_command:04x}"
    elif not ok:
        result["error"] = RESPONSE_ERRORS.get(
            data, f"Unknown SDCP error: 0x{data:04x}" if data else "Unknown SDCP error"
        )

    return result


def decode_value(feature: Feature, value: int | None) -> str | None:
    if value is None:
        return None
    if feature.value_map is None:
        return f"{value} {feature.unit}" if feature.unit else None
    return VALUE_MAPS[feature.value_map].get(value, f"0x{value:04x}")


async def capability_snapshot(client: SdcpClient) -> dict[str, Any]:
    try:
        identity = await client.get_identity()
    except Exception as exc:  # noqa: BLE001 - live probe should report capability lookup failures.
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    model = identity.model or ""
    series = get_projector_series(model, protocol=PROTOCOL_SDCP)
    calibration_preset_options = get_feature_values(
        model,
        FEATURE_SDCP_CALIBRATION_PRESET,
        protocol=PROTOCOL_SDCP,
    )

    return {
        "ok": True,
        "model": model or None,
        "series": series.__dict__ if series is not None else None,
        "features": {
            FEATURE_SDCP_CALIBRATION_PRESET: calibration_preset_options,
        },
    }


async def probe(host: str, community: str, timeout: float, delay: float) -> dict[str, Any]:
    client = SdcpClient(host, timeout=timeout, community=community)
    try:
        await client.connect()
    except Exception as exc:  # noqa: BLE001 - live probe should report startup failures as JSON.
        return {
            "host": host,
            "community": community,
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    try:
        capabilities = await capability_snapshot(client)
        results = []
        for feature in FEATURES:
            request = client._create_command_buffer(ACTION_GET, feature.command)
            try:
                raw = await client.transport.request(request, timeout=timeout)
                result = parse_response(raw, feature.command)
                result.update(
                    {
                        "name": feature.name,
                        "command": f"0x{feature.command:04x}",
                        "request_hex": request.hex(" "),
                    }
                )
                decoded = decode_value(feature, result.get("value"))
                if decoded is not None:
                    result["decoded"] = decoded
            except Exception as exc:  # noqa: BLE001 - live probe should keep going.
                result = {
                    "name": feature.name,
                    "command": f"0x{feature.command:04x}",
                    "request_hex": request.hex(" "),
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            results.append(result)
            if delay:
                await asyncio.sleep(delay)
    finally:
        await client.close()

    return {"host": host, "community": community, "ok": True, "capabilities": capabilities, "features": results}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="Projector IP address or hostname")
    parser.add_argument("--community", default="SONY", help="4-character PJ Talk community")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-command timeout in seconds")
    parser.add_argument("--delay", type=float, default=0.05, help="Delay between GET requests in seconds")
    args = parser.parse_args()

    result = asyncio.run(probe(args.host, args.community, args.timeout, args.delay))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
