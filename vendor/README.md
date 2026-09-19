# Vendored third-party files

These files are unmodified, byte-for-byte copies of third-party releases,
vendored here so installation doesn't depend on GitHub being reachable (or
unchanged) at install time. Do not edit them in place -- if you need a newer
version, re-download from the source below and update this file's version
and checksums.

## Source

[SolderedElectronics/Inkplate-micropython](https://github.com/SolderedElectronics/Inkplate-micropython),
release tag **`2.0.0`** (tagged 2026-07-21) for the Python driver files
below. License: MIT, Copyright (c) 2020 Thorsten von Eicken. Full text in
[`LICENSE`](LICENSE) in this directory (kept alongside the code it covers,
per the license's own terms).

**`firmware/inkplate-firmware.bin` is NOT from that tag or from upstream's
prebuilt release asset.** It's built from upstream source at commit
[`711ccca`](https://github.com/SolderedElectronics/Inkplate-micropython/commit/711cccaa849dda64dcd36e65e622a462b3618716)
(`master`, 2026-09-15) -- a fix for an I2S row-transmission-truncation bug
on classic ESP32 boards (see
[issue #51](https://github.com/SolderedElectronics/Inkplate-micropython/issues/51),
filed and root-caused by this project). Upstream's own prebuilt
`firmware/inkplate-firmware.bin` release asset had not been rebuilt with
this fix as of 2026-09-18 (last updated 2026-08-10) -- once upstream
publishes a release/rebuild that includes it, prefer re-vendoring from
that over this locally-built one.

Built with ESP-IDF v5.5.2, MicroPython 1.30.0-preview
(`micropython/ports/esp32`, `BOARD=ESP32_GENERIC BOARD_VARIANT=SPIRAM`,
`USER_C_MODULES=<checkout>/firmware/usermods/inkplate`), then merged into
a single flashable image with:
```sh
esptool --chip esp32 merge_bin -o inkplate-firmware.bin \
  --flash_mode dio --flash_size 4MB --flash_freq 40m --target-offset 0x1000 \
  0x1000 bootloader.bin 0x8000 partition-table.bin 0x10000 micropython.bin
```
Verified booting and rendering correctly (HIL, `mpremote` + probes in
`tools/experiments/`) on one Inkplate 10 V2 unit as of 2026-09-18; a
second unit (dormant ~3 years before this project started) shows an
unresolved, apparently unit-specific display defect under this same
firmware -- see issue #51 for details. Not necessarily reproducible from
a byte-for-byte-identical checkout going forward the way the Python
files below are (this is a source build, not a pinned release download).

## Layout

```
vendor/
├── firmware/inkplate-firmware.bin   -- shared by BOTH boards below (see why)
├── inkplate2/                       -- driver for the original board this
│                                        project targeted; kept for reference,
│                                        not imported by the app anymore
└── inkplate10/                      -- driver for the board the app
                                         currently targets
```

**The firmware binary is genuinely shared, not duplicated by accident.**
Per the upstream repo's own README, `inkplate-firmware.bin` is one build
(plain upstream MicroPython for the esp32 port, `BOARD=ESP32_GENERIC`) that
covers every classic-ESP32 Inkplate board -- Inkplate2, 5V2, 6, 6PLUS,
6FLICK, 6COLOR, 10, 4TEMPERA all included -- with the board-specific parts
living entirely in the Python driver files, not the firmware. Only the
ESP32-S3-based Inkplate13SPECTRA/7SPECTRA need a different firmware image
(`inkplate13spectra-firmware.bin`, not vendored here -- this project has no
use for it).

## Files and checksums

Verify with `sha256sum -c` (or `shasum -a 256 -c` on macOS) from this
directory:

```
d135c66e5c56545e046e0de5af87227057b16b9e692317729899d3381c0382ae  firmware/inkplate-firmware.bin
92fa5db339c05f925654604115eaae73daccdaa68aef21b2ae2fd19c849cbd2a  inkplate2/inkplate2.py
9d08115125cd7c0a6890030d4e3bb9075b3a38ac21bcc89d27fa79a7e6441ebf  inkplate2/gfx_standard_font_01.py
5e8c38c5fe5c5e32349c71d876bd15e1352c47dd5a352800ca635112b0a20734  inkplate10/inkplate10.py
21d2f23c331b87c791ffea2a2150ff591525ead1828df31645722a8d2dcf6a1b  inkplate10/gfx_standard_font_01.py
f737507afc85d6d39bd9327b08fbeabe74c49a6639daf6483842af29355dd654  inkplate10/pcal6416a.py
725de295c3236b1d914c556388e11882969467d44e59f1ba44c214bf0cb2e69c  inkplate10/mcp23017.py
4e02dc647bf8940396e31019344803ca856e2c6cb32ad4046108868e02bdb008  inkplate10/tps65186.py
3e6baf2d5cefcdc7b6fabd81102bfdcfbbe5b7d6c9f72a54eb54031c1682d348  inkplate10/rtc.py
3f8ea46bf1711fd9feb3034c85cc46274d272c62c5cde9746ac44bf854b64376  inkplate10/epd_power_pins.py
b879de8b70f760d00ad3883d251a5fec7abfb95b085fbd0e288345f53a0c559a  inkplate10/inkplate_gfx_mixin.py
141dccd2dc940ef6762385b0fd1fb66b555bf3d92bdcb09433c62f4a7eb37b15  inkplate10/inkplate_text_mixin.py
caa9d09ddfdbbf25d86e45bba63fb86c959817c6cad4812e3927196e28a809d7  inkplate10/inkplate_image_gs4_mixin.py
```

| File | Upstream path (at tag `2.0.0`) | Purpose |
|---|---|---|
| `firmware/inkplate-firmware.bin` | `firmware/inkplate-firmware.bin` | MicroPython firmware for classic-ESP32 Inkplate boards (includes the native e-paper driver as a `USER_C_MODULES` component -- flash this, not a generic esp32 MicroPython build) |
| `inkplate2/inkplate2.py` | `boards/inkplate2/inkplate2.py` | Inkplate 2 driver class (`from inkplate2 import Inkplate`) -- **not currently used by the app** |
| `inkplate2/gfx_standard_font_01.py` | `boards/inkplate2/gfx_standard_font_01.py` | Font data for the Inkplate 2 driver (different file/metrics than the Inkplate 10's font below, despite the identical filename) |
| `inkplate10/inkplate10.py` | `boards/inkplate10/inkplate10.py` | Inkplate 10 driver class (`from inkplate10 import Inkplate`) -- **what the app currently uses** |
| `inkplate10/gfx_standard_font_01.py` | `shared/gfx_standard_font_01.py` | Font data for the Inkplate 10 driver |
| `inkplate10/pcal6416a.py` | `shared/drivers/pcal6416a.py` | GPIO expander driver (V2 hardware revision) |
| `inkplate10/mcp23017.py` | `shared/drivers/mcp23017.py` | GPIO expander driver (v1/classic hardware revision) |
| `inkplate10/tps65186.py` | `shared/drivers/tps65186.py` | E-paper power-management IC driver |
| `inkplate10/rtc.py` | `shared/drivers/rtc.py` | Onboard RTC driver (not used by this app -- we use NTP + `machine.RTC()` instead, see `ntp_sync.py`) |
| `inkplate10/epd_power_pins.py` | `shared/drivers/epd_power_pins.py` | Tri-states the e-paper control bus during power-off |
| `inkplate10/inkplate_gfx_mixin.py` | `shared/mixins/inkplate_gfx_mixin.py` | Shared shape/pixel drawing primitives |
| `inkplate10/inkplate_text_mixin.py` | `shared/mixins/inkplate_text_mixin.py` | Shared cursor/print/text-wrap engine |
| `inkplate10/inkplate_image_gs4_mixin.py` | `shared/mixins/inkplate_image_gs4_mixin.py` | Shared image-decode support (unused by this app, but required by `inkplate10.py`'s own imports) |

Note: `import inkplate` and `import framebuf` (used by `inkplate10.py`) are
native/frozen modules baked into the firmware binary itself, not `.py`
source files in the upstream repo -- there is nothing to vendor for them.

## Re-vendoring a newer version

```sh
VERSION=<new-tag>
BASE="https://raw.githubusercontent.com/SolderedElectronics/Inkplate-micropython/$VERSION"

curl -sL "$BASE/firmware/inkplate-firmware.bin" -o vendor/firmware/inkplate-firmware.bin

curl -sL "$BASE/boards/inkplate10/inkplate10.py" -o vendor/inkplate10/inkplate10.py
curl -sL "$BASE/shared/gfx_standard_font_01.py" -o vendor/inkplate10/gfx_standard_font_01.py
curl -sL "$BASE/shared/drivers/pcal6416a.py" -o vendor/inkplate10/pcal6416a.py
curl -sL "$BASE/shared/drivers/mcp23017.py" -o vendor/inkplate10/mcp23017.py
curl -sL "$BASE/shared/drivers/tps65186.py" -o vendor/inkplate10/tps65186.py
curl -sL "$BASE/shared/drivers/rtc.py" -o vendor/inkplate10/rtc.py
curl -sL "$BASE/shared/drivers/epd_power_pins.py" -o vendor/inkplate10/epd_power_pins.py
curl -sL "$BASE/shared/mixins/inkplate_gfx_mixin.py" -o vendor/inkplate10/inkplate_gfx_mixin.py
curl -sL "$BASE/shared/mixins/inkplate_text_mixin.py" -o vendor/inkplate10/inkplate_text_mixin.py
curl -sL "$BASE/shared/mixins/inkplate_image_gs4_mixin.py" -o vendor/inkplate10/inkplate_image_gs4_mixin.py

curl -sL "$BASE/boards/inkplate2/inkplate2.py" -o vendor/inkplate2/inkplate2.py
curl -sL "$BASE/boards/inkplate2/gfx_standard_font_01.py" -o vendor/inkplate2/gfx_standard_font_01.py

curl -sL "$BASE/LICENSE" -o vendor/LICENSE

sha256sum vendor/firmware/inkplate-firmware.bin vendor/inkplate10/*.py vendor/inkplate2/*.py
```

Then update the version/checksums/tables above and in `install.md`.
