# totp-inkplate

Displays a 6-digit TOTP code on a [Soldered Inkplate 2](https://soldered.com/product/inkplate-2/)
e-paper board, from a base32 seed you provide once during setup.

## Hardware

- Soldered Inkplate 2 (classic ESP32-WROVER, 212×104 3-color black/white/red
  e-paper, WiFi + BLE). No extra wiring needed -- this design deliberately
  avoids relying on any onboard button/touch pad, because **the Inkplate 2
  has none** (unlike other Inkplate boards).

## How it works

- **First boot** (or whenever `config.json` is missing): the board enters
  **setup mode** and brings up *both* a WiFi captive portal and a BLE config
  service at once, since there's no button to pick one over the other.
  Supply your WiFi SSID/password, a display name, and your base32 TOTP seed
  through whichever is more convenient:
  - **WiFi**: join the `TOTP-Inkplate-Setup` access point from your phone/
    laptop, then open `http://192.168.4.1` (most phones will auto-open a
    captive-portal prompt).
  - **BLE**: using a generic BLE tool (e.g. nRF Connect, LightBlue), connect
    to `TOTP-Inkplate-Setup` and write a JSON blob to the characteristic
    below (see `ble_config.py`):
    - Service UUID: `b3d10001-0d51-4d6b-8f9a-9e6b2a0f1a01`
    - Characteristic UUID (write): `b3d10002-0d51-4d6b-8f9a-9e6b2a0f1a01`
    - Payload: `{"ssid": "...", "password": "...", "seed": "BASE32SEED", "account_name": "..."}`
      (UTF-8 JSON bytes; can be split across multiple BLE writes if your
      client's MTU is small -- they're concatenated and re-parsed after
      each write.)
- Once configured, the board reboots into **normal mode**: it briefly joins
  your WiFi to sync time over NTP, then continuously redraws the current
  6-digit code every 30 seconds, re-syncing NTP roughly every 15 minutes.
  No BLE and no WiFi access point run outside setup mode.
- By default only the 6-digit code is shown (no account name, no "valid
  until" line) -- each of those needs its own text-size change, which adds
  real time on a panel that's already slow to redraw. Set `"show_labels":
  true` in `config.json` to bring them back (see Configuration below).
- To **reconfigure** later (new WiFi or new seed), press the board's
  physical EN/RESET button twice within ~2 seconds -- this is detected via
  `machine.RTC().memory()` and re-enters setup mode without needing any
  extra hardware.

## Known trade-offs (read before relying on this)

- **The display can't do a quick partial refresh.** The Inkplate 2's 3-color
  panel only supports a full refresh, taking roughly 21 seconds. Since a
  TOTP code is valid for only 30 seconds, `normal_mode.py` computes the code
  for the window that will be current *when the draw finishes* (see
  `DRAW_LATENCY_S`) and shows an absolute **"valid until HH:MM:SS (UTC±HH:MM)"**
  instead of a countdown, which would be visibly wrong given the delay --
  though this line is hidden by default now (see above).
- **MicroPython's `time.time()` on this board counts from 2000-01-01, not
  the Unix epoch (1970-01-01) TOTP is defined against.** This isn't a
  trade-off so much as a landmine: get it wrong and every generated code is
  wrong, not just occasionally off, since the HOTP counter is computed from
  it directly. `normal_mode.py`'s `_unix_time()`/`_to_device_time()` add/
  remove the fixed 946684800s offset between the two epochs -- if you touch
  time-handling code here, keep true-Unix-epoch values (for TOTP math) and
  device-epoch values (for anything passed to `time.localtime()`) straight;
  mixing them up reproduces this exact bug. `timezone.py` sidesteps the
  question entirely for its own calendar math (see its module docstring).
- **No deep sleep in normal mode.** Continuous 30-second rotation means the
  board never sleeps, so this is realistically a USB-powered device, not a
  battery one, and the e-paper panel undergoes a full refresh roughly every
  30 seconds around the clock (~2,880/day) -- worth knowing given these
  panels are typically rated for on the order of 10^6 full refreshes over
  their lifetime.
- **The double-reset reconfigure trick is unverified on hardware.** It
  relies on `machine.RTC().memory()` surviving a reset via the board's
  physical EN pin; that's true for `machine.reset()` and deep-sleep wake on
  classic ESP32, but EN resets the RTC domain on some boards. Verify with
  `machine.RTC().memory(b"DR")` → press EN → check `machine.RTC().memory()`
  on the next boot, before relying on double-reset to reconfigure. If it
  doesn't survive, swap `main.py`'s detector for a flash-file marker
  (write → sleep 2s → delete) instead.
- **`bluetooth` and `hashlib.sha1` are assumed present** in Soldered's
  prebuilt firmware (this is plain upstream MicroPython for the esp32 port
  with Bluetooth enabled), but this hasn't been confirmed by running code on
  real hardware. Before relying on `ble_config.py`, check on-device:
  ```python
  import bluetooth
  import hashlib
  hashlib.sha1(b"")
  ```
  If either import fails, BLE config (or TOTP itself) needs a custom
  firmware rebuild -- see the "Building the firmware manually" section of
  [SolderedElectronics/Inkplate-micropython](https://github.com/SolderedElectronics/Inkplate-micropython).

## Setup

See [`install.md`](install.md) for full step-by-step installation
instructions (flashing firmware, installing the driver, copying files onto
the board, and running setup mode for the first time).

## Configuration

The setup UI (BLE/captive portal) only asks for `ssid`, `password`, `seed`,
and `account_name`. A few more knobs exist in `config.json` but are only
settable by hand-editing it (e.g. `mpremote cp` a new copy, or
`mpremote edit config.json`) -- see `config.example.json` for the full set:

| Field | Default | Meaning |
|---|---|---|
| `show_labels` | `false` | Show the account name and "valid until" line, not just the bare code (see "How it works" above) |
| `tz_offset_hours` | `-5` | Standard-time UTC offset used for the "valid until" line (default: US Eastern Standard Time). Doesn't affect the generated code itself -- TOTP always uses true UTC internally, this only changes a display label |
| `tz_dst` | `true` | Auto-add 1 hour on top of `tz_offset_hours` during US daylight saving (2nd Sunday of March - 1st Sunday of November). Set `false` if your offset doesn't observe DST, or observes a different schedule than the US |

`config_store.py` merges whatever you hand-set here with what the setup UI
sends, so these survive reconfiguring WiFi/seed through BLE or the captive
portal later.

## Debugging

`normal_mode.py` has a `DEBUG = True` flag (on by default) that prints the
loaded seed/account name once at startup, then every 30-second cycle prints
the raw and UTC-formatted time, the TOTP window/counter, the generated
code, and whether NTP is synced -- to whatever is watching the board's
serial console. To watch it live: `mpremote` (opens a REPL), then Ctrl-D to
soft-reset the board so `main.py` runs again with your session attached, or
`mpremote resume` to attach without resetting if it's already running.
Cross-check a printed code against an independent tool at the same seed and
window, e.g. `oathtool --totp -b <seed>`. Set `DEBUG = False` once you don't
need it -- it's a real (if small) amount of extra serial I/O every cycle.

## Running the tests

`totp.py` and `timezone.py` have no `machine`/`network` imports, so their
logic is fully testable without hardware:

```sh
python3 -m unittest discover -s tests -v
```

## Project layout

| File | Purpose |
|---|---|
| `main.py` | Boot entry point; double-reset detection and mode selection |
| `config_mode.py` | Runs BLE + captive portal concurrently, saves config, reboots |
| `normal_mode.py` | Continuous 30-second TOTP display loop |
| `totp.py` | Base32 decode, HMAC-SHA1, HOTP/TOTP (RFC 4226 / RFC 6238) |
| `timezone.py` | UTC offset + optional US DST, for display formatting only |
| `config_store.py` | Load/save `config.json` |
| `wifi_manager.py` | WiFi STA connect/disconnect, AP start/stop |
| `ntp_sync.py` | NTP time sync with a fallback server list |
| `ble_config.py` | BLE GATT peripheral for receiving setup config |
| `captive_portal.py` | DNS redirector + HTTP form server for setup config |
| `display.py` | Renders the code screen via the Inkplate 2 driver |
| `tests/test_totp.py` | CPython-runnable unit tests for `totp.py` |
| `tests/test_timezone.py` | CPython-runnable unit tests for `timezone.py` |
| `vendor/` | Vendored third-party firmware + display driver (see `vendor/README.md`) |
