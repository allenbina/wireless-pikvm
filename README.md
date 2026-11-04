# wireless-pikvm

Control a Windows laptop with no cable to it: video via Miracast to a Linux receiver,
keyboard/mouse via a Bluetooth LE HID dongle (nRF52840, nice!nano class).

Status: protocol + mock dongle + tests done. Firmware, Miracast receiver and browser
UI are not started. See `wireless-pikvm-agent-handoff.md` for the full plan.

## Requirements / constraints

- The target laptop must be within Bluetooth (BLE) range of the dongle.
- The target laptop and the receiver/controller must be on the same Wi-Fi.
  (Plain Miracast is Wi-Fi Direct and doesn't strictly need a shared network;
  this is a project requirement, and matters for Miracast-over-infrastructure.)
- Remote control of a running, logged-in session only. No BIOS, boot menu or
  BitLocker pre-boot PIN: BLE isn't up yet. Sleep, lid close and reboot drop the cast.
- A bonded BLE keyboard works at the Windows lock screen.

## Layout

- `docs/PROTOCOL.md`: dongle command protocol (transport-agnostic frames, watchdog rule)
- `host/dongle_ctl/`: framing, client, and `mock.py` (mock dongle, executable spec)
- `tests/`: pytest suite
- `firmware/`: plan only
- `Dockerfile`: `test` stage works; `fw` stage is an untested scaffold

## Run tests

    docker build --target test -t dongle-test . && docker run --rm dongle-test

or natively: `PYTHONPATH=host python -m pytest -q tests`

## Dev notes

- Build firmware in Docker, flash from Windows by copying the `.uf2` to the
  nice!nano drive (double-tap reset). No USB passthrough needed.
- Start with USB serial as the control link, then add a BLE GATT command
  channel (dongle holds two connections: HID to target, commands from controller).
