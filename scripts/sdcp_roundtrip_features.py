#!/usr/bin/env python3
"""Round-trip SDCP get/set features on a live Sony projector.

The script skips power, records original values, verifies setting each feature to
its current value, changes each supported value to another legal option, and
then restores the original values.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from sony_projector_protocol.sdcp import SdcpClient


def normalize(value: object) -> str:
    if isinstance(value, Enum):
        value = value.value
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


@dataclass(frozen=True)
class Feature:
    name: str
    getter: str
    setter: str
    options: tuple[str, ...]


FEATURES = (
    Feature("input", "get_input", "set_input", ("hdmi1", "hdmi2")),
    Feature(
        "calibration_preset",
        "get_calibration_preset",
        "set_calibration_preset",
        (
            "cinema_film_1",
            "cinema_film_2",
            "ref",
            "tv",
            "photo",
            "game",
            "bright_cinema",
            "bright_tv",
            "user",
        ),
    ),
    Feature("lamp_control", "get_lamp_control", "set_lamp_control", ("low", "high")),
    Feature("contrast_enhancer", "get_contrast_enhancer", "set_contrast_enhancer", ("off", "low", "high", "middle")),
    Feature("advanced_iris", "get_advanced_iris", "set_advanced_iris", ("off", "full", "limited")),
    Feature(
        "aspect_ratio",
        "get_aspect_ratio",
        "set_aspect_ratio",
        ("normal", "v_stretch", "zoom_1_85", "zoom_2_35", "stretch", "squeeze"),
    ),
    Feature("picture_muting", "get_picture_muting", "set_picture_muting", ("off", "on")),
    Feature(
        "motionflow",
        "get_motionflow",
        "set_motionflow",
        ("off", "smooth_high", "smooth_low", "impulse", "combination", "true_cinema"),
    ),
    Feature("2d_3d_display_select", "get_2d_3d_display_select", "set_2d_3d_display_select", ("auto", "3d", "2d")),
    Feature("3d_format", "get_3d_format", "set_3d_format", ("simulated_3d", "side_by_side", "over_under")),
    Feature(
        "picture_position",
        "get_picture_position",
        "set_picture_position",
        ("1_85", "2_35", "custom_1", "custom_2", "custom_3", "custom_4", "custom_5"),
    ),
    Feature("hdmi1_dynamic_range", "get_hdmi1_dynamic_range", "set_hdmi1_dynamic_range", ("auto", "limited", "full")),
    Feature("hdmi2_dynamic_range", "get_hdmi2_dynamic_range", "set_hdmi2_dynamic_range", ("auto", "limited", "full")),
    Feature("hdr", "get_hdr", "set_hdr", ("off", "on", "auto")),
    Feature("input_lag_reduction", "get_input_lag_reduction", "set_input_lag_reduction", ("off", "on")),
    Feature("menu_position", "get_menu_position", "set_menu_position", ("bottom_left", "center")),
)


def choose_alternate(original: str, options: tuple[str, ...]) -> str | None:
    for option in options:
        if normalize(option) != original:
            return option
    return None


async def prompt_yes_no(prompt: str, *, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        answer = await asyncio.to_thread(input, f"{prompt} {suffix} ")
        normalized = answer.strip().lower()
        if not normalized:
            return default
        if normalized in {"y", "yes"}:
            return True
        if normalized in {"n", "no"}:
            return False
        print("Please answer yes or no.")


async def get_feature(client: SdcpClient, feature: Feature) -> dict[str, Any]:
    try:
        value = await getattr(client, feature.getter)()
    except Exception as exc:  # noqa: BLE001 - live integration report should continue.
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "value": normalize(value), "raw_value": str(value)}


async def set_feature(client: SdcpClient, feature: Feature, value: str) -> dict[str, Any]:
    try:
        await getattr(client, feature.setter)(value)
    except Exception as exc:  # noqa: BLE001 - live integration report should continue.
        return {"ok": False, "value": value, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "value": value}


async def get_all(client: SdcpClient, features: tuple[Feature, ...], delay: float) -> dict[str, dict[str, Any]]:
    results = {}
    for feature in features:
        results[feature.name] = await get_feature(client, feature)
        if delay:
            await asyncio.sleep(delay)
    return results


def compare_to_initial(
    current: dict[str, dict[str, Any]], initial: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    comparison = {}
    for name, result in current.items():
        initial_result = initial.get(name, {})
        if not initial_result.get("ok"):
            comparison[name] = {"ok": False, "skipped": "initial get failed"}
        elif not result.get("ok"):
            comparison[name] = {"ok": False, "error": result.get("error")}
        else:
            comparison[name] = {
                "ok": result["value"] == initial_result["value"],
                "initial": initial_result["value"],
                "current": result["value"],
            }
    return comparison


async def run_roundtrip(
    host: str, community: str, timeout: float, delay: float, skip_input: bool, assume_yes: bool
) -> dict[str, Any]:
    features = tuple(feature for feature in FEATURES if not (skip_input and feature.name == "input"))
    client = SdcpClient(host, timeout=timeout, community=community)
    await client.connect()

    changed: dict[str, str] = {}
    report: dict[str, Any] = {
        "host": host,
        "community": community,
        "features": [feature.name for feature in features],
        "phases": {},
    }

    try:
        initial = await get_all(client, features, delay)
        report["phases"]["initial_get"] = initial

        set_same: dict[str, dict[str, Any]] = {}
        for feature in features:
            initial_result = initial[feature.name]
            if not initial_result.get("ok"):
                set_same[feature.name] = {"ok": False, "skipped": "initial get failed"}
                continue
            value = initial_result["value"]
            if value not in feature.options:
                set_same[feature.name] = {
                    "ok": False,
                    "skipped": f"initial value {value!r} is not a supported set option",
                }
                continue
            current = await get_feature(client, feature)
            current_value = current.get("value", value) if current.get("ok") else value
            if not assume_yes:
                proceed = await prompt_yes_no(
                    f"Set {feature.name}: current={current_value!r}; set same value {value!r}?",
                    default=False,
                )
                if not proceed:
                    set_same[feature.name] = {"ok": False, "skipped": "user skipped", "value": value}
                    continue
            set_same[feature.name] = await set_feature(client, feature, value)
            if delay:
                await asyncio.sleep(delay)
        report["phases"]["set_same"] = set_same

        after_same = await get_all(client, features, delay)
        report["phases"]["after_set_same_get"] = after_same
        report["phases"]["after_set_same_matches_initial"] = compare_to_initial(after_same, initial)

        set_alternate: dict[str, dict[str, Any]] = {}
        for feature in features:
            initial_result = initial[feature.name]
            if not initial_result.get("ok"):
                set_alternate[feature.name] = {"ok": False, "skipped": "initial get failed"}
                continue
            original = initial_result["value"]
            if original not in feature.options:
                set_alternate[feature.name] = {
                    "ok": False,
                    "skipped": f"initial value {original!r} is not a supported set option",
                }
                continue
            alternate = choose_alternate(original, feature.options)
            if alternate is None:
                set_alternate[feature.name] = {"ok": False, "skipped": "no alternate option available"}
                continue
            current = await get_feature(client, feature)
            current_value = current.get("value", original) if current.get("ok") else original
            if not assume_yes:
                proceed = await prompt_yes_no(
                    f"Change {feature.name}: current={current_value!r}; target={alternate!r}; original={original!r}?",
                    default=False,
                )
                if not proceed:
                    set_alternate[feature.name] = {
                        "ok": False,
                        "skipped": "user skipped",
                        "original": original,
                        "target": alternate,
                    }
                    continue
            result = await set_feature(client, feature, alternate)
            result["original"] = original
            result["target"] = alternate
            set_alternate[feature.name] = result
            if result.get("ok"):
                changed[feature.name] = original
            if delay:
                await asyncio.sleep(delay)
        report["phases"]["set_alternate"] = set_alternate

        after_alternate = await get_all(client, features, delay)
        report["phases"]["after_set_alternate_get"] = after_alternate
        report["phases"]["after_set_alternate_matches_target"] = {
            feature.name: (
                {
                    "ok": after_alternate[feature.name].get("ok")
                    and after_alternate[feature.name].get("value") == set_alternate[feature.name].get("target"),
                    "target": set_alternate[feature.name].get("target"),
                    "current": after_alternate[feature.name].get("value"),
                }
                if set_alternate[feature.name].get("ok")
                else {
                    "ok": False,
                    "skipped": set_alternate[feature.name].get("skipped") or set_alternate[feature.name].get("error"),
                }
            )
            for feature in features
        }

    finally:
        restore: dict[str, dict[str, Any]] = {}
        feature_by_name = {feature.name: feature for feature in features}
        for name, original in changed.items():
            restore[name] = await set_feature(client, feature_by_name[name], original)
            if delay:
                await asyncio.sleep(delay)
        if restore:
            report["phases"]["restore_original"] = restore
            final_get = await get_all(client, features, delay)
            report["phases"]["final_get"] = final_get
            initial = report["phases"].get("initial_get", {})
            report["phases"]["final_matches_initial"] = compare_to_initial(final_get, initial)
        await client.close()

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="Projector IP address or hostname")
    parser.add_argument("--community", default="SONY", help="4-character PJ Talk community")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-command timeout in seconds")
    parser.add_argument("--delay", type=float, default=0.25, help="Delay between commands in seconds")
    parser.add_argument("--skip-input", action="store_true", help="Do not switch HDMI inputs during the round-trip")
    parser.add_argument("--yes", action="store_true", help="Run non-interactively and approve every set operation")
    args = parser.parse_args()

    result = asyncio.run(run_roundtrip(args.host, args.community, args.timeout, args.delay, args.skip_input, args.yes))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
