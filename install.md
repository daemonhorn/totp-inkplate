# Installing on a real Inkplate 2

Step-by-step instructions to get this project running on physical
hardware. See `README.md` for how the device behaves once installed, and
for the trade-offs/caveats this design makes.

## What you'll need

- A Soldered Inkplate 2 board and a USB-C cable.
- A computer with Python 3 installed.
- Your home WiFi's SSID/password (2.4GHz -- classic ESP32 has no 5GHz radio).
- Your TOTP base32 seed (the same secret you'd normally scan as a QR code
  into an authenticator app).

## Dependency versions

Everything below is vendored in this repo under [`vendor/`](vendor/) (see
[`vendor/README.md`](vendor/README.md) for checksums and how to re-vendor a
newer version) -- no separate download or `mip install` step needed.

| Dependency | Version | Source |
|---|---|---|
| Inkplate MicroPython firmware + driver | `2.0.0` (release tag) | [SolderedElectronics/Inkplate-micropython](https://github.com/SolderedElectronics/Inkplate-micropython), MIT license |
| `mpremote` | any recent version (written against `1.29.0`) | [PyPI](https://pypi.org/project/mpremote/), installed via `pip` below, not vendored |

## 1. Install `mpremote`

`mpremote` is the standard MicroPython tool for flashing files and talking
to the board's REPL. It's a small standalone tool (not tied to a specific
firmware version), so it's installed via `pip` rather than vendored.

```sh
pip install mpremote
```

Plug the Inkplate 2 in via USB-C and confirm it's detected:

```sh
mpremote connect list
```

You should see a serial device (e.g. `/dev/ttyUSB0` on Linux, `/dev/cu.usbserial-*`
on macOS, `COM*` on Windows). If nothing shows up, install the CH340C USB-
serial driver for your OS (the Inkplate 2 uses a CH340C chip).

Everywhere below, `mpremote` without a `connect` argument will auto-pick the
board if it's the only serial device attached. If you have others plugged
in, prefix each command with `mpremote connect <port>`.

## 2. Flash the MicroPython firmware

The Inkplate 2 needs Soldered's own MicroPython build (it bundles a native
driver for the e-paper controller as a compiled module -- a generic esp32
MicroPython build won't have it). This repo vendors it at
[`vendor/firmware/inkplate-firmware.bin`](vendor/firmware/inkplate-firmware.bin)
(version `2.0.0` -- see the table above), so there's nothing to separately
download.

Optionally verify it hasn't been corrupted/altered before flashing:

```sh
sha256sum -c <(echo "841859ea7aaffb3d553f4a8436871cb2bcf3e2ce819b716ebd41716890893713  vendor/firmware/inkplate-firmware.bin")
```

Then flash it using one of:
   - **Thonny**: `Run` -> `Configure interpreter` -> `Install or update
     MicroPython` -> click `≡` -> `Select local MicroPython image` -> pick
     `vendor/firmware/inkplate-firmware.bin` -> `Install`.
   - **VSCode**: install the
     [Soldered MicroPython extension](https://marketplace.visualstudio.com/items?itemName=SolderedElectronics.soldered-micropython-helper),
     then `Install MicroPython on your board` -> `Upload Binary file from PC`
     -> pick `vendor/firmware/inkplate-firmware.bin`.

You only need to do this once. Re-flashing wipes the filesystem, so if
you're re-flashing a board that's already configured, back up `config.json`
first with `mpremote cp :config.json .` if you want to keep it.

## 3. Verify the firmware has what this project needs

Open a REPL and check both of the following before going further -- see
`README.md`'s "Known trade-offs" section for why these aren't 100% certain
to be present:

```sh
mpremote
```

At the `>>>` prompt:

```python
import bluetooth
import hashlib
hashlib.sha1(b"")
```

If either line raises an error, stop here -- this project's BLE config path
(or TOTP itself) needs a firmware rebuild with that module enabled. See the
"Building the firmware manually" section of the
[Inkplate-micropython README](https://github.com/SolderedElectronics/Inkplate-micropython#building-the-firmware-manually).
Otherwise, exit the REPL with Ctrl-] (or Ctrl-D then Ctrl-]) and continue.

## 4. Install the Inkplate 2 display driver

Also vendored, at [`vendor/inkplate2.py`](vendor/inkplate2.py) and
[`vendor/gfx_standard_font_01.py`](vendor/gfx_standard_font_01.py) (same
`2.0.0` version as the firmware -- they come from the same release). Copy
them onto the board's `/lib` directory, same place `mip install` would have
put them:

```sh
mpremote mkdir lib
mpremote cp vendor/inkplate2.py :lib/inkplate2.py
mpremote cp vendor/gfx_standard_font_01.py :lib/gfx_standard_font_01.py
```

(`mpremote mkdir lib` will print an error if `/lib` already exists -- that's
fine, ignore it.)

## 5. Copy this project's files onto the board

From this repository's root:

```sh
mpremote cp main.py config_mode.py normal_mode.py totp.py config_store.py \
    wifi_manager.py ntp_sync.py ble_config.py captive_portal.py display.py :
```

Do **not** copy `config.json` or `config.example.json` -- the board
generates its own `config.json` during setup mode (step 6).

Verify the files landed:

```sh
mpremote ls
```

You should see `main.py`, the other `.py` files above, and `lib/inkplate2.py`
+ `lib/gfx_standard_font_01.py` from step 4.

## 6. First boot: run setup mode

Reset the board (press the physical RST/EN button, or unplug/replug USB).
With no `config.json` present yet, it boots straight into setup mode and
the screen will show setup instructions once the AP/BLE come up (this first
draw takes ~20s -- the e-paper panel is slow).

Pick **one** of these two ways to send your config:

### Option A: WiFi captive portal

1. On your phone or laptop, join the WiFi network named
   `TOTP-Inkplate-Setup` (open, no password).
2. Your device should auto-prompt a captive-portal page; if not, open
   `http://192.168.4.1` in a browser.
3. Fill in your home WiFi SSID/password, an account name (whatever you want
   shown above the code), and your base32 TOTP seed. Submit.

### Option B: BLE

Using a generic BLE tool (e.g. [nRF Connect](https://www.nordicsemi.com/Products/Development-tools/nRF-Connect-for-mobile)
or LightBlue):

1. Scan for and connect to `TOTP-Inkplate-Setup`.
2. Find the service `b3d10001-0d51-4d6b-8f9a-9e6b2a0f1a01`.
3. Write to its characteristic `b3d10002-0d51-4d6b-8f9a-9e6b2a0f1a01` the
   UTF-8 bytes of:
   ```json
   {"ssid": "YourHomeWiFi", "password": "YourWiFiPassword", "seed": "YOURBASE32SEED", "account_name": "TOTP"}
   ```
   If your BLE client's write size is limited, you can split this JSON
   across multiple writes to the same characteristic -- they're
   concatenated and re-parsed after each write, so any split point works.

Either way, once a valid config is received the screen shows "Configured!"
and the board reboots into normal mode within a couple seconds.

## 7. Confirm it's working

After the reboot, the board should:
1. Briefly connect to your WiFi and sync time over NTP.
2. Show your account name, a 6-digit code, and a line reading
   `valid until HH:MM:SS UTC`.
3. Redraw with a new code roughly every 30 seconds, indefinitely.

Cross-check the shown code against another authenticator app fed the same
seed (e.g. run `oathtool --totp -b <seed>` on a computer) -- they should
match (allowing for the displayed "valid until" time, since the panel's
slow refresh means the code shown is for the window that will be current
once the draw finishes, not the instant you pressed reset).

## Reconfiguring later (new WiFi or new seed)

Press the board's physical EN/RESET button **twice within about 2 seconds**.
This re-enters setup mode (step 6) without erasing anything else on the
board. This mechanism is not yet confirmed on real hardware -- see
`README.md`'s "Known trade-offs" section for how to verify it and a
fallback if it doesn't work on your unit.

## Troubleshooting

- **Board never leaves the instructions screen / setup times out (10 min)**:
  make sure you're joining `TOTP-Inkplate-Setup` (not accidentally staying
  on your home WiFi), and that your WiFi/BLE payload includes both `ssid`
  and `seed` -- both are required for the config to be accepted.
- **Code doesn't match another authenticator**: double check the seed was
  typed/pasted correctly (no extra spaces; padding `=` characters are
  optional and stripped automatically), and that the board's WiFi
  connected successfully for NTP (a `NOT TIME-SYNCED` warning in place of
  the "valid until" line means the code is unreliable until WiFi/NTP
  succeeds -- check your SSID/password).
- **`import bluetooth` or `hashlib.sha1` failed in step 3**: see that
  step's link to rebuilding the firmware with the needed module enabled.
