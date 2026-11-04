# Dongle command protocol v1

Transport-agnostic byte stream. Today: USB CDC serial. Later: a BLE GATT
characteristic (write-without-response in, notify out) carrying the same frames.

## Frame

```
+------+-----+------+-----------+------+
| 0xA5 | LEN | TYPE | PAYLOAD.. | CRC8 |
+------+-----+------+-----------+------+
```

- `LEN` = number of bytes in TYPE + PAYLOAD (1..32).
- `CRC8` = CRC-8 (poly 0x07, init 0x00) over LEN, TYPE, PAYLOAD.
- Receiver resyncs by scanning for 0xA5; bad CRC frames are dropped silently
  and counted in STATUS.

## Host -> dongle

| Type | Name          | Payload                        | Effect |
|------|---------------|--------------------------------|--------|
| 0x01 | PING          | -                              | replies ACK |
| 0x02 | KEY_DOWN      | u8 HID usage (kbd page 0x07)   | add to report (max 6, else dropped) |
| 0x03 | KEY_UP        | u8 usage                       | remove from report |
| 0x04 | MODS          | u8 modifier bitmask            | set modifiers (bit0 LCtrl .. bit7 RGui) |
| 0x05 | MOUSE_MOVE    | i16le dx, i16le dy             | relative move (split into i8 reports) |
| 0x06 | MOUSE_BTN     | u8 button mask                 | set held buttons (bit0 L, bit1 R, bit2 M) |
| 0x07 | WHEEL         | i8 v, i8 h                     | scroll |
| 0x08 | RELEASE_ALL   | -                              | clear keys, modifiers, buttons |
| 0x09 | GET_STATUS    | -                              | replies STATUS |

## Dongle -> host

| Type | Name   | Payload |
|------|--------|---------|
| 0x80 | ACK    | u8 echoed type |
| 0x81 | STATUS | u8 flags (bit0 target connected, bit1 target bonded), u16le bad_crc count, u8 keys_held, u8 buttons_held |

## Safety rule (hard requirement)

The dongle MUST run a watchdog: if any key, modifier or button is held and no
valid frame has arrived for `WATCHDOG_MS` (3000), it performs RELEASE_ALL.
The host sends PING every 1000 ms while a control session is open. Losing the
controller link can therefore never leave input stuck on the target.
