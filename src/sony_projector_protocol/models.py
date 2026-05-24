"""Shared data models and enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Protocol(StrEnum):
    """Supported projector control protocols."""

    AUTO = "auto"
    ADCP = "adcp"
    SDCP = "sdcp"


class PowerState(StrEnum):
    """Normalized projector power states."""

    ON = "on"
    OFF = "off"
    STANDBY = "standby"
    STARTING = "starting"
    COOLING = "cooling"
    UNKNOWN = "unknown"


class Input(StrEnum):
    """Common projector input names."""

    HDMI1 = "hdmi1"
    HDMI2 = "hdmi2"


@dataclass(frozen=True)
class ProjectorIdentity:
    """Identity details reported by a projector."""

    model: str | None = None
    serial: str | None = None


@dataclass
class Capabilities:
    """Best-effort command support hints for a projector."""

    supported: set[str] = field(default_factory=set)
    unsupported: set[str] = field(default_factory=set)

    def mark_supported(self, command: str) -> None:
        """Record a supported command name."""
        self.unsupported.discard(command)
        self.supported.add(command)

    def mark_unsupported(self, command: str) -> None:
        """Record an unsupported command name."""
        self.supported.discard(command)
        self.unsupported.add(command)
