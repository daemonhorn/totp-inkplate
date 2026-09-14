# totp-inkplate

Displays a 6-digit TOTP code on a [Soldered Inkplate 10](https://soldered.com/product/inkplate-10/)
e-paper board, from a base32 seed you provide once during setup.

## Hardware

- Soldered Inkplate 10 (classic ESP32-WROVER, 1200×825 grayscale e-paper,
  WiFi + BLE, 9.7"). No extra wiring needed.
- **This project originally targeted a Soldered Inkplate 2** (a much
  smaller 3-color board) and was ported here after real-hardware testing
  showed the Inkplate 2's panel -- full-refresh-only, ~17-19s per update --
  made a display that rotates every 30 seconds more disruptive than
  usable. The Inkplate 10 supports genuine partial refresh (~0.6s
  typical), which is the actual fix; see "Known trade-offs" below for
  what's still worth knowing. The Inkplate 2 driver/firmware are still
  vendored under `vendor/inkplate2/` for reference; nothing in the app
  imports them anymore.
- The Inkplate 10 ships in two hardware revisions (v1/"classic" and V2)
  that the driver auto-detects; this only matters if you want to use its
  three physical touch pads (`touch1()`/`touch2()`/`touch3()` in the
  vendored driver) -- **v1 only, V2 has none** (those pins are repurposed
  for SD card control on V2). This app doesn't use the touch pads at all
  in its current design (see "How it works"), so which revision you have
  doesn't affect whether it works, only whether the touch pads would be
  available if you wanted to extend it.

## How it works

- **First boot** (or whenever `config.json` is missing): the board enters
  **setup mode** and brings up *both* a WiFi captive portal and a BLE config
  service at once (this predates the port to Inkplate 10 -- the Inkplate 2
  it was originally designed for has no touch pads/buttons at all, so
  "concurrently, since there's nothing to pick a transport with" was the
  reasoning; kept as-is here rather than redesigned around the Inkplate
  10's touch pads, since it works fine and isn't part of what changed).
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
  until" line) -- this was originally to avoid extra text-size changes on
  the Inkplate 2's slow full-refresh-only panel; that reasoning doesn't
  really apply to the Inkplate 10's fast refresh, but the default was left
  as-is during the port rather than changed without being asked. Set
  `"show_labels": true` in `config.json` to bring them back (see
  Configuration below) -- there's no real cost to doing so on this board.
- To **reconfigure** later (new WiFi or new seed), press the board's
  physical EN/RESET button twice within ~2 seconds -- this is detected via
  `machine.RTC().memory()` and re-enters setup mode without needing any
  extra hardware.

## Known trade-offs (read before relying on this)

- **`DRAW_LATENCY_S` (in `normal_mode.py`) is not yet measured on real
  Inkplate 10 hardware** -- it's set from Soldered's documented spec
  (full refresh ~1.6s, partial ~0.6s) plus margin, the same way the
  Inkplate 2 version started at a 22s guess before being tuned down to
  19s once real `display.py` DEBUG timing came in. Watch that output and
  tighten this the same way. Since a TOTP code is valid for only 30
  seconds, `normal_mode.py` computes the code for the window that will be
  current *when the draw finishes*, not when it started, and shows an
  absolute **"valid until HH:MM:SS (UTC±HH:MM)"** instead of a countdown --
  though this line is hidden by default (see above), and matters far less
  here than it did on the Inkplate 2, where the draw could take up to
  60%+ of the 30s window.
- **Only every ~10th update is a full refresh; the rest are partial.**
  `display.py`'s `Display._display()` always does one full `display()`
  first (needed to give the driver's partial-diffing something to diff
  against), then uses `partial_update()` after that -- which internally
  alternates in a genuinely fast diff-based partial refresh for ~10 calls,
  then one full refresh, per the vendored driver's own
  `fullUpdateThreshold` (adjustable via `set_full_update_threshold()` if
  you want to trade ghosting control against speed differently). Partial
  refresh only works in the 1-bit mode this app uses (`INKPLATE_1BIT`) --
  the 2-bit grayscale mode silently no-ops `partial_update()`, so don't
  switch modes without accounting for that.
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
  battery one (despite this board having a battery connector + charging
  circuit) -- ~2,880 refreshes/day, though only ~1 in 10 of those is a
  full refresh (the rest are the faster partial updates -- see above), so
  panel wear from full refreshes specifically is roughly 10x lower than a
  naive reading of that number would suggest.
- **The double-reset reconfigure trick is unverified on hardware.** It
  relies on `machine.RTC().memory()` surviving a reset via the board's
  physical EN pin; that's true for `machine.reset()` and deep-sleep wake on
  classic ESP32, but EN resets the RTC domain on some boards. Verify with
  `machine.RTC().memory(b"DR")` → press EN → check `machine.RTC().memory()`
  on the next boot, before relying on double-reset to reconfigure. If it
  doesn't survive, swap `main.py`'s detector for a flash-file marker
  (write → sleep 2s → delete) instead.
- **`hashlib.sha1` is confirmed present** in this vendored firmware --
  proven indirectly but solidly: TOTP codes generated on real hardware
  (an Inkplate 2, during this project's earlier phase, running the exact
  same shared firmware image this board uses) matched an independent
  `oathtool` check, which isn't possible without a working `sha1`.
  **`bluetooth` is still unconfirmed** -- setup was done via the WiFi
  captive portal in that same testing, not BLE, so there's no direct
  evidence `import bluetooth` succeeds on this firmware. Check before
  relying on `ble_config.py`:
  ```python
  import bluetooth
  ```
  If it fails, BLE config needs a custom firmware rebuild with Bluetooth
  enabled -- see the "Building the firmware manually" section of
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
serial console. `display.py` has its own separate `DEBUG = True` flag that
prints how long each panel refresh actually took *and whether it was a
full or partial update* (`[debug] display.display (full) took Xms` /
`[debug] display.partial_update took Xms`) -- the number to watch if
you're tuning `normal_mode.py`'s `DRAW_LATENCY_S`, which hasn't been
measured on real Inkplate 10 hardware yet (see "Known trade-offs"). To
watch it live: `mpremote` (opens a REPL), then Ctrl-D to soft-reset the
board so `main.py` runs again with your session attached, or `mpremote
resume` to attach without resetting if it's already running. Cross-check
a printed code against an independent tool at the same seed and window,
e.g. `oathtool --totp -b <seed>`. Set either `DEBUG` flag to `False` once
you don't need it -- it's a real (if small) amount of extra serial I/O
every cycle.

## Troubleshooting: corrupted/partial display after long dormancy

If a screen comes up with most of its content missing or cut off (e.g. only
the last character or two visible) -- especially on a board that's sat
unpowered for a long time with a stale image already on the panel -- run
`mpremote run tools/panel_condition.py`. It cycles the panel through several
full black/white refreshes with no text involved at all, which both
diagnoses whether the problem is the panel itself (long-dormant e-paper
sometimes needs a few forced full refreshes before it responds cleanly
again) versus a text-rendering bug, and fixes it if it's the former. See the
script's own docstring for how to read the result.

## Experiments (not part of the app)

`tools/experiments/kw_mode_test.py` -- **Inkplate 2-specific, not
applicable to the Inkplate 10** this app now targets (it probes a
tri-color-vs-mono controller mode bit that only exists on the Inkplate
2's 3-color panel; the Inkplate 10 is grayscale-only and gets genuine
partial refresh a different way, via `partial_update()` -- see "Known
trade-offs"). Kept for reference alongside the Inkplate 2 driver files in
`vendor/inkplate2/`. **Measured result on that hardware: KW mode was
slower** (21897ms vs. a 17234ms tri-color baseline), not faster -- see the
script's own docstring for the full readout. Not referenced by
`install.md`, nothing in the app imports it.

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
| `display.py` | Renders the code screen via the Inkplate 10 driver, full/partial refresh handling |
| `tests/test_totp.py` | CPython-runnable unit tests for `totp.py` |
| `tests/test_timezone.py` | CPython-runnable unit tests for `timezone.py` |
| `vendor/` | Vendored third-party firmware + display drivers, both boards (see `vendor/README.md`) |
| `tools/experiments/` | One-off hardware experiments, not part of the app (see "Experiments" above) |
