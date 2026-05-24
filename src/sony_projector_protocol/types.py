"""Public data types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectorIdentity:
    """Identity details reported by a projector."""

    model: str | None = None
    serial: str | None = None
    location: str | None = None
    mac_address: str | None = None
