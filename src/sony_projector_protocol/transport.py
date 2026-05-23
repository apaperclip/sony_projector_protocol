"""Async transport abstractions used by protocol clients."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol as TypingProtocol

from sony_projector_protocol.exceptions import ProjectorConnectionError, ProjectorTimeoutError


class Transport(TypingProtocol):
    """Minimal async transport required by protocol clients."""

    async def connect(self) -> None:
        """Open the transport."""

    async def request(self, payload: bytes, *, timeout: float) -> bytes:
        """Send a request and return one response payload."""

    async def close(self) -> None:
        """Close the transport."""


@dataclass
class StreamTransport:
    """TCP stream transport with delimiter-based responses."""

    host: str
    port: int
    terminator: bytes = b"\r"
    reader: asyncio.StreamReader | None = None
    writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        """Open the TCP connection."""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        except OSError as exc:
            raise ProjectorConnectionError(f"Could not connect to {self.host}:{self.port}") from exc

    async def request(self, payload: bytes, *, timeout: float) -> bytes:
        """Write one payload and read until the configured terminator."""
        if self.reader is None or self.writer is None:
            await self.connect()

        assert self.reader is not None
        assert self.writer is not None

        try:
            self.writer.write(payload)
            await self.writer.drain()
            if self.terminator is None:
                return await asyncio.wait_for(self.reader.read(1024), timeout)
            return await asyncio.wait_for(self.reader.readuntil(self.terminator), timeout)
        except TimeoutError as exc:
            raise ProjectorTimeoutError("Timed out waiting for projector response") from exc
        except (OSError, asyncio.IncompleteReadError) as exc:
            raise ProjectorConnectionError("Projector connection closed") from exc

    async def close(self) -> None:
        """Close the stream if it is open."""
        if self.writer is None:
            return

        self.writer.close()
        await self.writer.wait_closed()
        self.writer = None
        self.reader = None


class FakeTransport:
    """In-memory transport for unit tests and examples."""

    def __init__(self, responder: Callable[[bytes], bytes | Awaitable[bytes]]) -> None:
        self._responder = responder
        self.requests: list[bytes] = []
        self.connected = False
        self.closed = False

    async def connect(self) -> None:
        self.connected = True

    async def request(self, payload: bytes, *, timeout: float) -> bytes:
        del timeout
        self.requests.append(payload)
        response = self._responder(payload)
        if asyncio.iscoroutine(response):
            return await response
        return response

    async def close(self) -> None:
        self.closed = True
