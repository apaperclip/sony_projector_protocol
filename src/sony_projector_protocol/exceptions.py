"""Exception hierarchy for projector communication failures."""

from __future__ import annotations


class ProjectorError(Exception):
    """Base class for all package-specific errors."""

    def __init__(
        self,
        message: str = "",
        *,
        protocol: str | None = None,
        command: str | None = None,
        response: str | bytes | None = None,
    ) -> None:
        super().__init__(message)
        self.protocol = protocol
        self.command = command
        self.response = response

    @property
    def response_text(self) -> str | None:
        """Projector response decoded for logs, when available."""
        if self.response is None:
            return None
        if isinstance(self.response, bytes):
            return self.response.decode("ascii", errors="replace").strip()
        return self.response

    @property
    def response_hex(self) -> str | None:
        """Raw projector response as hexadecimal, when the response is bytes."""
        if isinstance(self.response, bytes):
            return self.response.hex(" ")
        return None


class ProjectorConnectionError(ProjectorError):
    """Raised when a projector cannot be reached or a connection is closed."""


class ProjectorTimeoutError(ProjectorError):
    """Raised when a projector command times out."""


class ProjectorProtocolError(ProjectorError):
    """Raised when a projector returns an invalid or unexpected response."""


class ProjectorAuthenticationError(ProjectorError):
    """Raised when a projector rejects authentication."""


class UnsupportedCommandError(ProjectorError):
    """Base class for requests that cannot be performed as requested."""


class PackageUnsupportedCommandError(UnsupportedCommandError):
    """Raised when this package or selected protocol cannot issue a request."""


class ProjectorUnsupportedCommandError(UnsupportedCommandError):
    """Raised when the projector rejects a supported request as unavailable."""
