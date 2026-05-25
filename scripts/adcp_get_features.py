#!/usr/bin/env python3
"""Poll all implemented Sony ADCP getter values from a live projector."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sony_projector_protocol.adcp import AdcpClient


@dataclass(frozen=True)
class Getter:
    name: str
    method: str


GETTERS = (
    Getter("power", "get_power"),
    Getter("input", "get_input"),
    Getter("signal", "get_signal"),
    Getter("temperature", "get_temperature"),
    Getter("timer", "get_timer"),
    Getter("picture_mode", "get_picture_mode"),
    Getter("color_space", "get_color_space"),
    Getter("lamp_control", "get_lamp_control"),
    Getter("warning", "get_warning"),
    Getter("error", "get_error"),
    Getter("hdr", "get_hdr"),
    Getter("aspect_ratio", "get_aspect_ratio"),
    Getter("hdmi1_dynamic_range", "get_hdmi1_dynamic_range"),
    Getter("hdmi2_dynamic_range", "get_hdmi2_dynamic_range"),
    Getter("model_name", "get_model_name"),
    Getter("serial_number", "get_serial_number"),
    Getter("version", "get_version"),
    Getter("mac_address", "get_mac_address"),
    Getter("identity", "get_identity"),
)


def jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return value


async def poll_getter(client: AdcpClient, getter: Getter) -> dict[str, Any]:
    try:
        value = await getattr(client, getter.method)()
    except Exception as exc:  # noqa: BLE001 - live probe should keep polling.
        return {
            "name": getter.name,
            "method": getter.method,
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "name": getter.name,
        "method": getter.method,
        "ok": True,
        "value": jsonable(value),
    }


async def poll_once(client: AdcpClient, delay: float) -> list[dict[str, Any]]:
    results = []
    for getter in GETTERS:
        results.append(await poll_getter(client, getter))
        if delay:
            await asyncio.sleep(delay)
    return results


async def probe(
    host: str,
    *,
    password: str | None,
    timeout: float,
    delay: float,
    count: int,
    interval: float,
) -> dict[str, Any]:
    client = AdcpClient(host, timeout=timeout, password=password)
    await client.connect()
    try:
        polls = []
        for index in range(count):
            polls.append({"index": index + 1, "features": await poll_once(client, delay)})
            if index < count - 1 and interval:
                await asyncio.sleep(interval)
    finally:
        await client.close()

    return {"host": host, "protocol": "adcp", "polls": polls}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="Projector IP address or hostname")
    parser.add_argument("--password", help="ADCP password, if the projector requires authentication")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-command timeout in seconds")
    parser.add_argument("--delay", type=float, default=0.05, help="Delay between getter requests in seconds")
    parser.add_argument("--count", type=int, default=1, help="Number of full getter polling passes")
    parser.add_argument("--interval", type=float, default=1.0, help="Delay between polling passes in seconds")
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be at least 1")

    result = asyncio.run(
        probe(
            args.host,
            password=args.password,
            timeout=args.timeout,
            delay=args.delay,
            count=args.count,
            interval=args.interval,
        )
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
