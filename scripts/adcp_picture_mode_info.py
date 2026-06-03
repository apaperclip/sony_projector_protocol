#!/usr/bin/env python3
"""Probe ADCP picture_mode metadata from a live Sony projector."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sony_projector_protocol.adcp import AdcpClient

COMMANDS = (
    "picture_mode ?",
    "picture_mode --range",
    "picture_mode --info",
)


def parse_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


async def probe(host: str, *, password: str | None, timeout: float) -> dict[str, Any]:
    client = AdcpClient(host, timeout=timeout, password=password)
    await client.connect()
    try:
        results = []
        for command in COMMANDS:
            try:
                response = await client._command(command)
            except Exception as exc:  # noqa: BLE001 - one-off probe should report every command.
                results.append(
                    {
                        "command": command,
                        "ok": False,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            else:
                results.append(
                    {
                        "command": command,
                        "ok": True,
                        "response": parse_json(response),
                    }
                )
    finally:
        await client.close()

    return {"host": host, "protocol": "adcp", "results": results}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="Projector IP address or hostname")
    parser.add_argument("--password", help="ADCP password, if authentication is enabled")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-command timeout in seconds")
    args = parser.parse_args()

    result = asyncio.run(probe(args.host, password=args.password, timeout=args.timeout))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
