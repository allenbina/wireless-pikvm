# Wireless PiKVM experiment — agent handoff (rev 2)

Supersedes rev 1. Changes: software-only architecture (the HDMI/capture fallback is
**removed by the user's choice, do not propose it**), receiver candidates compared,
first milestone narrowed to receiver reliability.

## Mission

Control a work laptop (Windows, native Win+K Cast) with no cable to it. Video: native
Miracast to a self-hosted software receiver, then viewed in a browser. Input: BLE HID
dongle (see `docs/PROTOCOL.md`). No HDMI, capture device or physical monitor anywhere.

The user's core concern: **Miracast receivers are poorly supported.** Answer that with
concrete evidence (working setups, or exact failure reasons), not by routing around it.

## Intended architecture

- A general-purpose computer (Linux, Windows, Pi, server) runs the Miracast receiver.
  Platform is open; the goal is the most reliable self-hosted software receiver.
- One dedicated Wi-Fi adapter does Miracast / Wi-Fi Direct.
- A second interface (Ethernet, or another Wi-Fi adapter) serves the LAN and the webpage.
  The user often has no Ethernet nearby, so a second USB Wi-Fi adapter plus a USB-serial
  console are the likely bring-up tools.
- Received video goes through software into a browser stream (possibly WebRTC).
- Input uses the nRF52840 BLE HID dongle separately (firmware not started).
- The user has accepted: no BIOS/pre-boot access; remote control of a logged-in session only.
- Network is assumed trusted; no authentication yet (deliberate, revisit later).

## Why this is hard (scope of "receiver reliability")

Miracast is five stacked problems: (1) discovery via Wi-Fi management frames, (2) Wi-Fi
Direct role negotiation, pairing, security and IP setup, (3) RTSP capability/session
negotiation, (4) compressed video reception, timing, buffering and loss recovery,
(5) reconnection plus optional extras such as input. Failures can sit in adapter
firmware, driver, network management, protocol interop, or playback. A dedicated adapter
removes radio-sharing problems but does not fix unsupported driver behavior. The source
laptop may also share its own radio between normal Wi-Fi and Miracast.

Narrowing rule: support **one known laptop + one receiver OS + one chosen Wi-Fi chipset**,
not a universal receiver.

## Candidates and evidence status

"Verified" below means seen in a source this session; everything else is from the user's
earlier research and is unconfirmed by us. Nothing has been installed or tested on the
user's hardware.

| Candidate | What is known | Status |
|---|---|---|
| MiracleCast (albfan) on Linux | Real sink + source implementation. Maintainer demoed Android reception on a Pi 3 with onboard Wi-Fi (2016, from user research). `miracle-sinkctl --uibc` gives basic input. README says some hardware is not Wi-Fi-Direct compatible; run `res/test-hardware-capabilities.sh`. Needs NetworkManager/other wpa_supplicant stopped. No MS-MICE support. Known failure signatures: `Failed to create interface p2p-dev-wlan0: -16`; group formation failing with FORMATION_FAILED, worked around by `p2p_no_group_iface=1` in a different adapter's report. Pi 5 negotiation-failure reports were in the user's research; **we could not find them ourselves**. | Unverified on Pi 5 |
| LazyCast (homeworkc) on Linux | Pi 3/4 reception reports including Windows sources. Supports MS-MICE: README says tested with a Windows 10 PC and a Pi, both on Ethernet, manually assigned IPs. README recommends legacy 32-bit Raspberry Pi OS (Bullseye); Bookworm reportedly causes issues. Reports of pairing difficulty after Pi reboot (ARP/routing/power save; workaround: toggle source Wi-Fi). Issue #12: a user on Ethernet with static IP saw no Pi in Windows "connect", no resolution seen. | Partly verified (README/issues), not on our hardware |
| Microsoft Wireless Display (Windows 11) | Officially supported PC-to-PC receiver, free baseline. Reliability, browser capture, and whether the optional feature is still shipped on current builds are untested. Probably no input back-channel. | Untested |
| AirServer Windows Desktop | Supports Miracast, Windows 11; documents capture into OBS. Candidate pipeline AirServer -> OBS -> MediaMTX -> browser. Documented, not a verified deployment. Commercial, acceptable. | Untested |
| Newer open-source projects | Advertise Miracast but mark receiver unfinished/untested. None clearly mature. | Rejected for now |

Piracast (Raspberry Pi forum, ~2014) is historical: Pi 2/3 era, phone sources, one
reported-working dongle (TL-WN725N), HDCP unsupported. Not a recommendation.

## Wi-Fi hardware facts (Pi 5 onboard radio)

CYW43455 (Infineon/Cypress), driver `brcmfmac`, same as Pi 4. From searches: P2P exists
on the chip but is unproven for Miracast sinking; firmware versions in the wild range
7.45.206-7.45.265; the chip randomizes MACs by default (Wi-Fi Direct persistent groups
want stable ones); a kernel issue logs unhandled P2P action frames. An unrelated
brcmfmac report (BCM43602) showed `test-hardware-capabilities.sh` saying "P2P OK" while
`miracle-wifid` said unsupported, so a passing capability check is not proof.

## Milestone 1 (only goal until met): receiver reliability

Success = the work laptop connects via native Win+K **repeatedly** and video holds for
15 minutes, on one fixed receiver OS + chipset. Record negotiated resolution/fps, CPU/RAM,
failures with logs, and at least ten connect/disconnect cycles. A Cast-menu entry is not
success. Browser forwarding does not start until this is met.

Suggested order (cheapest first; stop at the first that works reliably):
1. **Microsoft Wireless Display on the dev laptop**: free baseline. Needs the optional
   feature present and the dev laptop's adapter to support it; the work laptop must see it.
2. **LazyCast on the spare Pi 5** (or Pi 4) with the OS version the README recommends,
   onboard radio for Miracast, USB-serial console for access.
3. **MiracleCast** on the Pi with `iw list`, `test-hardware-capabilities.sh`,
   NetworkManager stopped, `--log-level trace`, and `p2p_no_group_iface=1` if group
   formation fails.
4. **AirServer** trial on Windows, then OBS capture.
5. If the onboard radio fails P2P, repeat 2-3 with a USB adapter whose chipset has a
   documented working P2P report (check before buying; mt76 family is the lead guess).

Before step 2-3, run read-only discovery on the Pi: `cat /etc/os-release`, `uname -a`,
`iw list` (look for P2P-GO / P2P-client and interface combinations), `dmesg | grep
brcmfmac` (firmware version), `rfkill list`.

## Later milestones (after Milestone 1)

2. Receiver output -> browser stream (WebRTC/MediaMTX). Prefer repackaging compressed
   H.264 without transcoding; measure CPU/latency if transcoding is needed.
3. BLE HID dongle firmware (Zephyr on nice!nano) + serial/BLE command channel, per
   `docs/PROTOCOL.md`; mock dongle and tests already exist in `host/`.
4. Optional UIBC input, only if cheap; BLE HID is the primary input path.

## Constraints and caveats

- Untested items must be reported as untested. Do not claim a "most stable" receiver
  without a benchmark.
- Behavior on lock, sleep, lid close, reboot, Wi-Fi change is to be recorded. Expected:
  lock probably survives; sleep/lid/reboot drop the cast.
- Work laptop policy may block input or projection modes; report it, don't bypass it.
- Shared office Wi-Fi often has client isolation; a travel router or hotspot may be
  needed for the LAN side (unverified for the user's site).
- Don't manually run containers/changes that disrupt the user's other machines; this
  project's hardware is the spare Pi and this laptop.
- Prior assistant turns were too optimistic and drifted to HDMI; keep to the software-only
  design.
