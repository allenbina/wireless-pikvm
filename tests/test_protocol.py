import struct

from dongle_ctl import protocol as p
from dongle_ctl.client import Client
from dongle_ctl.mock import MockDongle


class Loop:
    """Client transport wired straight into a MockDongle with a fake clock."""

    def __init__(self):
        self.dongle = MockDongle()
        self.now = 0
        self.replies = p.Decoder()
        self.got = []

    def write(self, data):
        self.got += self.replies.feed(self.dongle.rx(data, self.now))

    def advance(self, ms):
        self.now += ms
        self.dongle.tick(self.now)


def setup():
    t = Loop()
    return t, Client(t), t.dongle


def test_crc_known_vector():
    assert p.crc8(b"123456789") == 0xF4  # CRC-8/SMBUS check value


def test_decoder_resync_and_bad_crc():
    good = p.encode(p.PING)
    bad = bytearray(p.encode(p.KEY_DOWN, b"\x04"))
    bad[-1] ^= 0xFF
    d = p.Decoder()
    frames = d.feed(b"\x00\xA5\xFF" + bytes(bad) + good)
    assert [f.type for f in frames] == [p.PING]
    assert d.bad_crc == 1


def test_decoder_split_across_reads():
    raw = p.encode(p.MOUSE_MOVE, p.move_payload(5, -5))
    d = p.Decoder()
    assert d.feed(raw[:3]) == []
    assert d.feed(raw[3:])[0].type == p.MOUSE_MOVE


def test_typing_and_release():
    t, c, d = setup()
    c.mods(0x02)
    c.key_down(0x04)
    c.key_up(0x04)
    c.mods(0)
    assert d.reports == [("kbd", 2, ()), ("kbd", 2, (4,)), ("kbd", 2, ()), ("kbd", 0, ())]
    assert not d.held()


def test_rollover_limit():
    t, c, d = setup()
    for k in range(4, 12):
        c.key_down(k)
    assert len(d.keys) == 6


def test_large_move_is_split_to_i8():
    t, c, d = setup()
    c.move(300, -200)
    moves = [r for r in d.reports if r[0] == "mouse"]
    assert sum(r[2] for r in moves) == 300 and sum(r[3] for r in moves) == -200
    assert all(-127 <= r[2] <= 127 and -127 <= r[3] <= 127 for r in moves)


def test_watchdog_releases_stuck_input():
    t, c, d = setup()
    c.key_down(0x04)
    c.buttons(1)
    t.advance(2999)
    assert d.held()
    t.advance(2)  # controller went silent
    assert not d.held()
    assert d.reports[-1][0] == "mouse" and d.reports[-1][1] == 0


def test_ping_keeps_session_alive():
    t, c, d = setup()
    c.key_down(0x04)
    for _ in range(10):
        t.advance(1000)
        c.ping()
    assert d.held()


def test_release_all_and_status():
    t, c, d = setup()
    c.key_down(0x04)
    c.buttons(3)
    c.release_all()
    assert not d.held()
    c.get_status()
    st = t.got[-1]
    assert st.type == p.STATUS
    flags, bad, keys, btns = struct.unpack("<BHBB", st.payload)
    assert flags == 3 and keys == 0 and btns == 0
