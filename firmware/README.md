# Firmware (nice!nano / nRF52840) — NOT STARTED

Scaffold only. Plan:

1. Zephyr app, board `nice_nano_v2`, produces a `.uf2` for drag-and-drop flashing.
2. HID over GATT (HOGP): keyboard + mouse report maps, bonding enabled, so Windows
   treats it as a normal BLE keyboard/mouse.
3. Command channel, in order: (a) USB CDC-ACM, (b) custom GATT characteristic.
   Both carry the frames in `docs/PROTOCOL.md`; the parser is a direct port of
   `host/dongle_ctl/protocol.py` and must pass the same test vectors.
4. Watchdog per the protocol's safety rule.

`Dockerfile` target `fw` and the `west` project files (`CMakeLists.txt`, `prj.conf`,
`src/main.c`) are not written yet. Pin the Zephyr version when they are.
The Python mock in `host/dongle_ctl/mock.py` is the executable spec until then.
