# Wireless PiKVM experiment — agent handoff

## Mission

Investigate and build a proof of concept for controlling a Windows laptop wirelessly from a Linux receiver, then remotely from a browser. Use the laptop’s built-in wireless projection for video and Bluetooth HID or Miracast input forwarding for keyboard/mouse. Prefer existing projects and minimal custom glue.

Start with hardware discovery and a working local display receiver. Do not build the web interface before proving that the laptop can cast reliably to Linux.

## User context and scope

- The user has already built a PiKVM and is comfortable with hardware and Linux projects.
- They have Bluetooth dongles used for keyboard projects; models and capabilities are unknown.
- Their work laptop discovers wireless displays at WeWork. Windows/Miracast is a working assumption, not yet confirmed.
- Linux host model, distribution, Wi-Fi chipset, Bluetooth hardware, and existing PiKVM model are unknown.
- Goal: no HDMI or USB cable between the target laptop and the receiver. The receiver can use wired power and Ethernet.
- Begin with the OS already running and the user manually initiating casting and pairing. Unattended reconnection is a later investigation.
- No implementation or hardware testing has been performed yet. Prior discussion established candidate components only.

## Proposed architecture

Video: target laptop → Miracast/Wi-Fi Direct → Linux receiver → local display, then browser stream.

Input: browser/local input → Linux → Bluetooth keyboard/mouse emulation → target laptop.

Alternative input: use Miracast User Input Back Channel (UIBC) if it works reliably with this Windows source and Linux receiver.

Use a dedicated Wi-Fi adapter for Miracast and Ethernet for management if possible. Avoid taking over the sole interface used for SSH. Miracast over Infrastructure (MS-MICE) is a separate capability; do not assume a Linux receiver supports it just because it supports ordinary Miracast.

## Existing components and primary references

1. MiracleCast receiver: https://github.com/albfan/miraclecast
   - Implements the display sink role; requires Wi-Fi Direct hardware and uses GStreamer.
   - Documented setup manages its own wpa_supplicant and asks to stop competing network services. Adapt carefully to the installed distribution rather than blindly stopping all networking.
   - Implements basic keyboard and mouse events through optional UIBC, enabled with `miracle-sinkctl --uibc`. Interoperability must be tested.
2. PiKVM Bluetooth HID: https://docs.pikvm.org/bluetooth_hid/
   - PiKVM already has a Bluetooth keyboard/mouse backend. Documentation describes configuration limitations, pairing, and relative mouse support.
   - Its documented Raspberry Pi configuration is not automatically applicable to arbitrary Linux hosts or external dongles.
3. PiKVM input API: https://docs.pikvm.org/api/
4. Microsoft receiver considerations: https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/wireless-projection-receiver-manufacturers
5. Miracast over Infrastructure overview: https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-mice/ab6341b7-4fc7-41fd-a74d-3fe023455482

Recheck current documentation, issues, package availability, and relevant alternatives. Confirm that alternatives are receivers: many Linux wireless-display projects only SEND a Linux screen to a TV.

## Phase 1 — identify hardware and protocol

Inspect available Linux hardware with read-only commands such as `cat /etc/os-release`, `uname -a`, `lsusb`, `lspci -nnk`, `iw dev`, `iw list`, `rfkill list`, `bluetoothctl list`, and `bluetoothctl show`. Run only commands available on the host; install prerequisites as needed within authorized scope.

Record Wi-Fi chipset/driver, advertised P2P modes and interface combinations, Bluetooth controller, video decode/encode support, and the interface carrying management traffic. P2P capability reports are necessary evidence, not a guarantee of interoperability.

Confirm whether the laptop uses Windows Win+K. If it is macOS/AirPlay or browser casting, revise the receiver choice before proceeding. Identify only genuinely missing hardware details that cannot be inspected locally.

Deliver: hardware inventory, confirmed protocol, recommended receiver configuration, and any hardware blocker.

## Phase 2 — prove video reception locally

Install/build the best supported receiver, beginning with MiracleCast if still appropriate. Record exact version or commit and dependencies. Preserve existing configuration and provide rollback for network changes. Use local console or a separate management interface when changing Wi-Fi ownership.

Advertise a distinct receiver name, manually connect from the laptop, and show its desktop locally. Start at 1080p/30 if negotiation allows, lowering resolution if needed. Verify ordinary desktop content, text readability, and changing windows.

Run for 15 minutes. Record negotiated resolution/frame rate, CPU/RAM load, hardware versus software decoding, connection failures, and approximate video latency with a stated measurement method. Test at least three disconnect/reconnect cycles. Keep logs focused on this test.

Deliver: repeatable commands, working video evidence, measured resource usage, and observed failures. Do not claim success based only on appearing in the Cast menu.

## Phase 3 — prove keyboard and mouse

Briefly test UIBC with explicit laptop-side input permission where offered. Verify typing, modifiers, pointer movement, clicking, and scrolling. If unreliable, use Bluetooth HID rather than spending excessive time debugging optional UIBC.

For Bluetooth, determine whether the available dongle can support the chosen emulation backend. Distinguish general Bluetooth adapters from proprietary keyboard receivers. Reuse PiKVM’s backend where practical; otherwise choose an existing Linux HID implementation.

Pair manually and test keyboard layout, held keys, modifier release, pointer behavior, reconnects, and input cleanup after a dropped client connection. Never leave keys or buttons held after disconnection. Explain any relative-mouse limitations.

Deliver: a stable input path and reproducible pairing/recovery instructions.

## Phase 4 — remote browser access

Only after video and input work separately, inspect how to reuse the existing PiKVM interface or implement a minimal authenticated browser viewer with input forwarding. Integration into PiKVM is an investigation, not an assumed supported video-source setting.

Prefer forwarding/repackaging the received compressed video when compatible with the browser transport. If transcoding is necessary, use hardware encoding where available and measure added CPU load and latency. Document the actual pipeline and codecs; do not promise zero-copy or zero-transcode operation without verification.

Keep management access on the LAN or existing private VPN, with authentication. Do not expose the prototype publicly by default. Use an explicit input-control session and release held input when it ends.

## Acceptance criteria and limitations

- Laptop connects using its native projection UI without installing a target-side remote desktop agent.
- No HDMI/USB tether to the laptop; Bluetooth pairing is acceptable.
- Video remains stable for 15 minutes and reconnects work in three trials.
- Keyboard/mouse work from the controller, including recovery after a disconnect.
- Report measured latency and resource usage. Suggested usability target: under 200 ms end-to-end for ordinary desktop work; this is a project target, not a known capability.
- Document behavior during locking, sleep/wake, reboot, lid closure, and Wi-Fi changes. Treat untested cases explicitly as untested.
- No expectation of BIOS, bootloader, or early-boot video: projection depends on the target OS and its casting session.
- Do not assume employer policy allows every projection/input mode; report an actual management restriction if encountered and do not bypass it.

## Final deliverables

Provide a concise go/no-go assessment, architecture that actually worked, setup/start/stop/rollback instructions, dependency versions, minimal reusable scripts or services, measured results, and known limitations. Clearly separate completed tests from proposed improvements.

If Linux reception proves impractical on the available hardware, explain the specific blocker. Evaluate a physical Miracast receiver with HDMI output feeding the existing PiKVM capture input plus Bluetooth HID as a fallback. This would remain wireless at the laptop while retaining short wired connections inside the receiver assembly; verify capture and receiver compatibility before recommending purchases.
