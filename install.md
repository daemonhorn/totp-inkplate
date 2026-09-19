# Installing on a real Inkplate 10

Step-by-step instructions to get this project running on physical
hardware. See `README.md` for how the device behaves once installed, and
for the trade-offs/caveats this design makes.

This project originally targeted a Soldered Inkplate 2 and was later
ported to the Inkplate 10 (this document) once real-hardware testing
showed the Inkplate 2's full-refresh-only panel made a 30-second-rotating
display more disruptive than usable -- see README's "Known trade-offs"
and the git history around that decision if you're curious. The Inkplate
2 driver/firmware are still vendored under `vendor/inkplate2/` for
reference, but nothing in the app imports them anymore.

## What you'll need

- A Soldered Inkplate 10 board and a USB-C cable.
- A computer with Python 3 installed.
- Your home WiFi's SSID/password (2.4GHz -- classic ESP32 has no 5GHz radio).
- Your TOTP base32 seed (the same secret you'd normally scan as a QR code
  into an authenticator app).

## Dependency versions

The Inkplate firmware/driver are vendored in this repo under
[`vendor/`](vendor/) (see [`vendor/README.md`](vendor/README.md) for
checksums and how to re-vendor a newer version) -- no separate download or
`mip install` step needed for those. The host-side tools below are small,
platform-provided utilities instead, so they're installed via your package
manager rather than vendored.

| Dependency | Version | Source |
|---|---|---|
| Inkplate MicroPython firmware + driver | driver: `2.0.0` (release tag); firmware: source-built from commit `711ccca` (see `vendor/README.md`) | [SolderedElectronics/Inkplate-micropython](https://github.com/SolderedElectronics/Inkplate-micropython), MIT license -- vendored in `vendor/` |
| `mpremote` | any recent version (written against PyPI `1.29.0` / Debian 13's `1.24.1-1`) | [PyPI](https://pypi.org/project/mpremote/) or Debian package `micropython-mpremote` |
| `esptool` | any recent version (written against PyPI `5.4.0` / Debian 13's `4.7.0+dfsg-0.1`) | [PyPI](https://pypi.org/project/esptool/) or Debian package `esptool` -- used by Thonny/VSCode to flash firmware, or directly as a fallback (step 2). **Debian's `esptool` apt package is broken for this board**: see the warning in step 2. |
| `ptyprocess` | any recent version (written against `0.7.0`, same on PyPI and Debian 13) | [PyPI](https://pypi.org/project/ptyprocess/) or Debian package `python3-ptyprocess` -- pseudo-terminal support, useful if you want to script an interactive REPL session (e.g. via `pexpect`) instead of typing into `mpremote repl` by hand |

## 1. Install the host-side tools

`mpremote` is the standard MicroPython tool for flashing files and talking
to the board's REPL; `esptool` talks to the ESP32's ROM bootloader directly
and is what Thonny/VSCode use under the hood to flash firmware (and what you
can use directly -- see step 2); `ptyprocess` is optional, for scripting an
interactive REPL session. None of these are tied to a specific firmware
version, so install them via your package manager rather than vendoring:

**Via `pip`** (any OS):

```sh
pip install mpremote esptool ptyprocess
```

**Via `apt`, on Debian 13 (trixie) or derivatives**:

```sh
sudo apt install micropython-mpremote esptool python3-ptyprocess
```

(Debian's package for `mpremote` is named `micropython-mpremote`, but it
installs the same `mpremote` command used throughout this guide -- every
command below is identical regardless of which install method you used.)

> **If you plan to flash via Thonny or VSCode** (step 2), install `esptool`
> via `pip`, not `apt`. Debian's `esptool` package is missing the classic-
> ESP32 stub-flasher data file it needs
> ([Debian bug #1043168](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1043168),
> filed 2023, still open) -- Thonny/VSCode both shell out to whatever
> `esptool` your system's `python3 -m esptool` resolves to, and on Debian
> 13 that crashes with `FileNotFoundError:
> .../stub_flasher/stub_flasher_32.json` partway through flashing (you may
> have already hit this). `pip install --user esptool` installs a working
> copy that takes precedence over the broken system one. If you only ever
> flash via the `esptool` CLI directly, the `apt` package still needs
> `--no-stub` to work around this bug (see step 2) -- but note `--no-stub`
> can't do a whole-chip erase (the bare ROM bootloader doesn't support
> that command at all), so `pip install --user esptool` is the better fix
> if you need `erase-flash`.

Plug the Inkplate 10 in via USB-C and confirm it's detected:

```sh
mpremote connect list
```

You should see a serial device (e.g. `/dev/ttyUSB0` on Linux, `/dev/cu.usbserial-*`
on macOS, `COM*` on Windows). If nothing shows up, install the CH340C USB-
serial driver for your OS (the Inkplate 10 uses a CH340C chip).

Everywhere below, `mpremote` without a `connect` argument will auto-pick the
board if it's the only serial device attached. If you have others plugged
in, prefix each command with `mpremote connect <port>`.

## 2. Flash the MicroPython firmware

The Inkplate 10 needs Soldered's own MicroPython build (it bundles a native
driver for the e-paper controller as a compiled module -- a generic esp32
MicroPython build won't have it). This is the same firmware image used for
every classic-ESP32 Inkplate board (including the Inkplate 2 this project
originally targeted) -- see `vendor/README.md` for why. This repo vendors it at
[`vendor/firmware/inkplate-firmware.bin`](vendor/firmware/inkplate-firmware.bin),
so there's nothing to separately download. **This is currently a locally
source-built image, not upstream's `2.0.0` release binary** -- it includes
an I2S row-truncation fix (upstream commit `711ccca`) that hadn't made it
into upstream's own prebuilt release asset as of 2026-09-18. See
`vendor/README.md` for full provenance/build details.

Optionally verify it hasn't been corrupted/altered before flashing:

```sh
sha256sum -c <(echo "d135c66e5c56545e046e0de5af87227057b16b9e692317729899d3381c0382ae  vendor/firmware/inkplate-firmware.bin")
```

Then flash it using one of:
   - **Thonny** (tested against the click-path in 4.1.x -- if your version
     differs, the general idea is the same):
     1. `Run` -> `Configure interpreter...` (or `Tools` -> `Options` ->
        `Interpreter`, or click the interpreter indicator in the bottom-right
        corner of the window).
     2. At the top of that page, change the dropdown **"Which kind of
        interpreter should Thonny use for running your code?"** from
        `Local Python 3` to **`MicroPython (ESP32)`**. This step is easy to
        miss -- the firmware-flashing option below doesn't exist at all
        until you do this; it's not that Thonny lacks the feature, it's
        that it's hidden behind the interpreter-kind dropdown.
     3. The page reloads with a small hyperlink-style label in its
        bottom-right corner: **"Install or update MicroPython (esptool)"**
        (not a button, easy to miss).
     4. In the dialog that opens, click the **☰ / ≡** ("tribar") menu
        button, choose **"Select local MicroPython image..."**, pick
        `vendor/firmware/inkplate-firmware.bin`, then click **Install**.
     5. If you get an error that `esptool` is missing, install it (see the
        dependency table above) via `Tools` -> `Manage plug-ins...`, or use
        the system copy you already installed in step 1 -- but see the
        `esptool`-on-Debian warning in step 1 first if you're on Debian/apt:
        this exact combination (Thonny + Debian's `esptool` package + a
        classic-ESP32 board like this one) crashes with
        `FileNotFoundError: ...stub_flasher_32.json` partway through
        flashing. On Windows, a separate known Thonny bug
        ([#2841](https://github.com/thonny/thonny/issues/2841)) can throw
        `shutil.SameFileError` when installing a local image. Either way,
        use one of the two options below instead.
   - **VSCode**: install the
     [Soldered MicroPython extension](https://marketplace.visualstudio.com/items?itemName=SolderedElectronics.soldered-micropython-helper),
     then `Install MicroPython on your board` -> `Upload Binary file from PC`
     -> pick `vendor/firmware/inkplate-firmware.bin`.
   - **`esptool` directly**, skipping the IDE entirely (find your port from
     `mpremote connect list` in step 1). **Do not add `--no-stub`** if
     you're on a working (non-Debian-apt, e.g. `pip install`ed) `esptool` --
     `--no-stub` talks straight to the ESP32's bare ROM bootloader instead
     of uploading esptool's own helper program first, and the bare ROM
     loader on classic ESP32 **does not implement a whole-chip erase at
     all**: `erase-flash`/`erase_flash` fails there with `ESP32 ROM does
     not support function erase_flash`, no matter how the port/board are
     configured -- this isn't specific to a stale or third-party firmware,
     it's a ROM-level limitation. `--no-stub` is only a fallback for the
     Debian packaging bug above (a broken *stub*, i.e. missing
     `stub_flasher_32.json`) -- if you fixed that with `pip install --user
     esptool`, you have a working stub and don't need `--no-stub` at all;
     use it only if you're still stuck on Debian's broken apt package and
     `write_flash` alone (without erasing first) is enough for your case:
     ```sh
     esptool --chip esp32 --port /dev/ttyUSB0 erase-flash
     esptool --chip esp32 --port /dev/ttyUSB0 write-flash -z 0x1000 \
         vendor/firmware/inkplate-firmware.bin
     ```
     (Older esptool releases used underscored subcommand names --
     `erase_flash`/`write_flash` -- rather than the hyphenated
     `erase-flash`/`write-flash` above; both exist as of 5.x, use whichever
     yours accepts.)
     `0x1000` is the standard bootloader offset for classic ESP32 boards
     (this is the same board family the Inkplate 10 uses) and matches how
     official MicroPython ESP32 firmware images are normally flashed. This
     wasn't verified against Soldered's own build tooling specifically, so
     if it fails, fall back to Thonny or VSCode above, which determine the
     correct offset themselves.

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

## 4. Install the Inkplate 10 display driver

Also vendored, under [`vendor/inkplate10/`](vendor/inkplate10/) (`2.0.0`
release tag -- see `vendor/README.md` for what each file is, and for why
the firmware binary itself is no longer from that same tag). Unlike the
Inkplate 2, this driver is split across several
shared support files (GPIO expander drivers, the power-management IC
driver, shared drawing/text mixins), so there are more files to copy --
all of them go in the board's `/lib` directory, same place `mip install`
would have put them:

```sh
mpremote mkdir lib
mpremote cp vendor/inkplate10/inkplate10.py :lib/inkplate10.py
mpremote cp vendor/inkplate10/gfx_standard_font_01.py :lib/gfx_standard_font_01.py
mpremote cp vendor/inkplate10/pcal6416a.py :lib/pcal6416a.py
mpremote cp vendor/inkplate10/mcp23017.py :lib/mcp23017.py
mpremote cp vendor/inkplate10/tps65186.py :lib/tps65186.py
mpremote cp vendor/inkplate10/rtc.py :lib/rtc.py
mpremote cp vendor/inkplate10/epd_power_pins.py :lib/epd_power_pins.py
mpremote cp vendor/inkplate10/inkplate_gfx_mixin.py :lib/inkplate_gfx_mixin.py
mpremote cp vendor/inkplate10/inkplate_text_mixin.py :lib/inkplate_text_mixin.py
mpremote cp vendor/inkplate10/inkplate_image_gs4_mixin.py :lib/inkplate_image_gs4_mixin.py
```

(`mpremote mkdir lib` will print an error if `/lib` already exists -- that's
fine, ignore it.)

## 5. Copy this project's files onto the board

From this repository's root:

```sh
mpremote cp main.py config_mode.py normal_mode.py totp.py timezone.py \
    config_store.py wifi_manager.py ntp_sync.py ble_config.py \
    captive_portal.py display.py :
```

Do **not** copy `config.json` or `config.example.json` -- the board
generates its own `config.json` during setup mode (step 6).

Verify the files landed:

```sh
mpremote ls
```

You should see `main.py`, the other `.py` files above (`timezone.py`
included -- `normal_mode.py` imports it directly for the "valid until"
line's UTC-offset/DST math, so a boot without it fails with
`ImportError: no module named 'timezone'`), and the ten `lib/*.py` driver
files from step 4.

## 6. First boot: run setup mode

Reset the board (press the physical RST/EN button, or unplug/replug USB).
With no `config.json` present yet, it boots straight into setup mode and
the screen will show setup instructions once the AP/BLE come up (this
first draw is a full refresh, ~1.6s per Soldered's spec -- not yet
confirmed on this specific unit, see README's Debugging section).

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
2. Show a 6-digit code (by default, just the code -- no account name or
   "valid until" line; see `README.md`'s Configuration section to bring
   those back via `show_labels`). If you do turn that line on, it's
   computed by `timezone.py`'s own pure-integer calendar math (not
   MicroPython's `time.localtime()` -- see that module's docstring for
   why) from two hand-editable `config.json` fields, `tz_offset_hours`
   (standard-time UTC offset, default `-5` for US Eastern) and `tz_dst`
   (whether to auto-add 1 hour for US daylight saving, default `true`) --
   neither is exposed in the setup UI (see step 6), so change them by
   hand-editing `config.json` (`mpremote edit config.json`) if the default
   doesn't match your timezone. This only affects the displayed label,
   never the generated code itself -- TOTP always computes off true UTC
   internally.
3. Redraw with a new code roughly every 30 seconds, indefinitely.

Cross-check the shown code against another authenticator app fed the same
seed (e.g. run `oathtool --totp -b <seed>` on a computer) -- they should
match (allowing for a small draw delay: the code shown is for the window
that will be current once the draw finishes, not the instant a cycle
started -- much less noticeable on this board than the original Inkplate
2 target, since refreshes here are ~1-2s instead of ~20s).

If codes don't match, see `README.md`'s Debugging section -- `normal_mode.py`
prints the loaded seed, the time it thinks it is, and each generated code
live over the serial connection (`mpremote`), which is the fastest way to
tell whether it's a seed problem, a time-sync problem, or something else.

## Reconfiguring later (new WiFi or new seed)

Press the board's physical EN/RESET button **twice within about 2 seconds**.
This re-enters setup mode (step 6) without erasing anything else on the
board. This mechanism is not yet confirmed on real hardware -- see
`README.md`'s "Known trade-offs" section for how to verify it and a
fallback if it doesn't work on your unit.

## Troubleshooting

- **Flashing fails with `FileNotFoundError: ...stub_flasher/stub_flasher_32.json`**:
  this is [Debian bug #1043168](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1043168)
  -- Debian's `esptool` apt package ships without the stub-flasher data
  file this classic-ESP32 board needs. Either run
  `esptool --no-stub ...` directly (see step 2), or `pip install --user
  esptool` to get a working copy for Thonny/VSCode to use instead.
- **`erase-flash`/`erase_flash` fails with `ESP32 ROM does not support
  function erase_flash`**: you're running with `--no-stub`, which talks
  directly to the bare ROM bootloader -- and that ROM loader doesn't
  implement a whole-chip erase at all, on any classic ESP32, regardless of
  what's currently flashed. Drop `--no-stub` (it's only needed to work
  around the Debian packaging bug above; if you're on a `pip`-installed
  `esptool` you don't need it) and re-run with the normal stub-based
  `erase-flash`/`write-flash`.
- **Board never leaves the instructions screen / setup times out (10 min)**:
  make sure you're joining `TOTP-Inkplate-Setup` (not accidentally staying
  on your home WiFi), and that your WiFi/BLE payload includes both `ssid`
  and `seed` -- both are required for the config to be accepted.
- **Code doesn't match another authenticator**: double check the seed was
  typed/pasted correctly (no extra spaces; padding `=` characters are
  optional and stripped automatically), and that the board's WiFi
  connected successfully for NTP (an inverted black-banner
  `not synced, code unreliable` warning on the panel -- this board has no
  red channel, so it's a filled bar instead of red text -- means the code
  is unreliable until WiFi/NTP succeeds -- check your SSID/password). Use
  the live debug output (`README.md`'s Debugging section) to see the exact
  seed, time, and window the board is actually using -- it's much faster
  than guessing.
- **`import bluetooth` or `hashlib.sha1` failed in step 3**: see that
  step's link to rebuilding the firmware with the needed module enabled.
