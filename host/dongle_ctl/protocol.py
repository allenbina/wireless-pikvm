"""Framing and message definitions. See docs/PROTOCOL.md."""
from __future__ import annotations

import struct
from dataclasses import dataclass

SYNC = 0xA5
WATCHDOG_MS = 3000

PING, KEY_DOWN, KEY_UP, MODS, MOUSE_MOVE, MOUSE_BTN, WHEEL, RELEASE_ALL, GET_STATUS = (
    0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09)
ACK, STATUS = 0x80, 0x81


def crc8(data: bytes) -> int:
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def encode(msg_type: int, payload: bytes = b"") -> bytes:
    body = bytes([1 + len(payload), msg_type]) + payload
    if not 1 <= body[0] <= 32:
        raise ValueError("payload too long")
    return bytes([SYNC]) + body + bytes([crc8(body)])


@dataclass
class Frame:
    type: int
    payload: bytes


class Decoder:
    """Incremental decoder; resyncs on garbage, counts CRC failures."""

    def __init__(self) -> None:
        self.buf = bytearray()
        self.bad_crc = 0

    def feed(self, data: bytes) -> list[Frame]:
        self.buf += data
        out: list[Frame] = []
        while True:
            try:
                i = self.buf.index(SYNC)
            except ValueError:
                self.buf.clear()
                return out
            del self.buf[:i]
            if len(self.buf) < 2:
                return out
            length = self.buf[1]
            if not 1 <= length <= 32:
                del self.buf[0]  # false sync byte
                continue
            total = 3 + length
            if len(self.buf) < total:
                return out
            body = bytes(self.buf[1:total - 1])
            if crc8(body) == self.buf[total - 1]:
                out.append(Frame(body[1], body[2:]))
                del self.buf[:total]
            else:
                self.bad_crc += 1
                del self.buf[0]


def move_payload(dx: int, dy: int) -> bytes:
    return struct.pack("<hh", dx, dy)
