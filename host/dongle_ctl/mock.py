"""Mock dongle: speaks the protocol and models the HID state the target would see.

Time is injected (`now_ms`) so the watchdog is testable without sleeping.
`reports` records every HID report the real dongle would send over BLE.
"""
from __future__ import annotations

import struct

from . import protocol as p


class MockDongle:
    def __init__(self) -> None:
        self.dec = p.Decoder()
        self.mods = 0
        self.keys: list[int] = []
        self.buttons = 0
        self.connected = True
        self.bonded = True
        self.last_rx_ms = 0
        self.reports: list[tuple] = []  # ("kbd", mods, keys) / ("mouse", btn, dx, dy, v, h)

    # -- HID output ---------------------------------------------------
    def _kbd(self) -> None:
        self.reports.append(("kbd", self.mods, tuple(self.keys)))

    def _mouse(self, dx=0, dy=0, v=0, h=0) -> None:
        self.reports.append(("mouse", self.buttons, dx, dy, v, h))

    def held(self) -> bool:
        return bool(self.mods or self.keys or self.buttons)

    def release_all(self) -> None:
        had_kbd, had_btn = bool(self.mods or self.keys), bool(self.buttons)
        self.mods, self.keys, self.buttons = 0, [], 0
        if had_kbd:
            self._kbd()
        if had_btn:
            self._mouse()

    # -- link ---------------------------------------------------------
    def rx(self, data: bytes, now_ms: int) -> bytes:
        """Feed bytes from the controller; returns bytes to send back."""
        out = b""
        for f in self.dec.feed(data):
            self.last_rx_ms = now_ms
            out += self._handle(f)
        return out

    def tick(self, now_ms: int) -> None:
        if self.held() and now_ms - self.last_rx_ms > p.WATCHDOG_MS:
            self.release_all()

    def _handle(self, f: p.Frame) -> bytes:
        t, d = f.type, f.payload
        if t == p.KEY_DOWN and len(d) == 1:
            if d[0] not in self.keys and len(self.keys) < 6:
                self.keys.append(d[0])
                self._kbd()
        elif t == p.KEY_UP and len(d) == 1:
            if d[0] in self.keys:
                self.keys.remove(d[0])
                self._kbd()
        elif t == p.MODS and len(d) == 1:
            self.mods = d[0]
            self._kbd()
        elif t == p.MOUSE_MOVE and len(d) == 4:
            dx, dy = struct.unpack("<hh", d)
            while dx or dy:  # HID reports carry i8 deltas
                sx, sy = max(-127, min(127, dx)), max(-127, min(127, dy))
                self._mouse(sx, sy)
                dx, dy = dx - sx, dy - sy
        elif t == p.MOUSE_BTN and len(d) == 1:
            self.buttons = d[0]
            self._mouse()
        elif t == p.WHEEL and len(d) == 2:
            v, h = struct.unpack("<bb", d)
            self._mouse(v=v, h=h)
        elif t == p.RELEASE_ALL:
            self.release_all()
        elif t == p.GET_STATUS:
            flags = int(self.connected) | (int(self.bonded) << 1)
            return p.encode(p.STATUS, struct.pack(
                "<BHBB", flags, self.dec.bad_crc, len(self.keys) + bin(self.mods).count("1"),
                bin(self.buttons).count("1")))
        elif t != p.PING:
            return b""
        return p.encode(p.ACK, bytes([t]))
