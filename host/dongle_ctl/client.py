"""Controller-side client. Transport is anything with write(bytes) -> None."""
from __future__ import annotations

from typing import Protocol

from . import protocol as p


class Transport(Protocol):
    def write(self, data: bytes) -> None: ...


class Client:
    def __init__(self, transport: Transport) -> None:
        self.t = transport

    def _send(self, typ: int, payload: bytes = b"") -> None:
        self.t.write(p.encode(typ, payload))

    def ping(self) -> None: self._send(p.PING)
    def key_down(self, usage: int) -> None: self._send(p.KEY_DOWN, bytes([usage]))
    def key_up(self, usage: int) -> None: self._send(p.KEY_UP, bytes([usage]))
    def mods(self, mask: int) -> None: self._send(p.MODS, bytes([mask]))
    def move(self, dx: int, dy: int) -> None: self._send(p.MOUSE_MOVE, p.move_payload(dx, dy))
    def buttons(self, mask: int) -> None: self._send(p.MOUSE_BTN, bytes([mask]))
    def wheel(self, v: int, h: int = 0) -> None: self._send(p.WHEEL, bytes([v & 0xFF, h & 0xFF]))
    def release_all(self) -> None: self._send(p.RELEASE_ALL)
    def get_status(self) -> None: self._send(p.GET_STATUS)

    def tap(self, usage: int) -> None:
        self.key_down(usage)
        self.key_up(usage)
