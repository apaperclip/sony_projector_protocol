"""Exception hierarchy for projector communication failures."""

from __future__ import annotations


class ProjectorError(Exception):
    """Base class for all package-specific errors."""


class ProjectorConnectionError(ProjectorError):
    """Raised when a projector cannot be reached or a connection is closed."""


class ProjectorTimeoutError(ProjectorError):
    """Raised when a projector command times out."""


class ProjectorProtocolError(ProjectorError):
    """Raised when a projector returns an invalid or unexpected response."""


class ProjectorAuthenticationError(ProjectorError):
    """Raised when a projector rejects authentication."""


class UnsupportedCommandError(ProjectorError):
    """Raised when a projector does not support a requested command."""
