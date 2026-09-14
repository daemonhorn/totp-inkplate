# Vendored third-party files

These files are unmodified, byte-for-byte copies of third-party releases,
vendored here so installation doesn't depend on GitHub being reachable (or
unchanged) at install time. Do not edit them in place -- if you need a newer
version, re-download from the source below and update this file's version
and checksums.

## Source

[SolderedElectronics/Inkplate-micropython](https://github.com/SolderedElectronics/Inkplate-micropython),
release tag **`2.0.0`** (commit `b0f5b1c`'s ancestor tagged 2026-07-21;
`master` has since moved on, but `2.0.0` is the last labeled release and
what these files are pinned to).

License: MIT, Copyright (c) 2020 Thorsten von Eicken. Full text in
[`LICENSE`](LICENSE) in this directory (kept alongside the code it covers,
per the license's own terms).

## Files and checksums

Verify with `sha256sum -c` (or `shasum -a 256 -c` on macOS) from this
directory:

```
841859ea7aaffb3d553f4a8436871cb2bcf3e2ce819b716ebd41716890893713  firmware/inkplate-firmware.bin
92fa5db339c05f925654604115eaae73daccdaa68aef21b2ae2fd19c849cbd2a  inkplate2.py
9d08115125cd7c0a6890030d4e3bb9075b3a38ac21bcc89d27fa79a7e6441ebf  gfx_standard_font_01.py
```

| File | Upstream path (at tag `2.0.0`) | Purpose |
|---|---|---|
| `firmware/inkplate-firmware.bin` | `firmware/inkplate-firmware.bin` | MicroPython firmware for classic-ESP32 Inkplate boards (includes this board's native e-paper driver as a `USER_C_MODULES` component -- flash this, not a generic esp32 MicroPython build) |
| `inkplate2.py` | `boards/inkplate2/inkplate2.py` | Python driver class (`from inkplate2 import Inkplate`) for the Inkplate 2's display |
| `gfx_standard_font_01.py` | `boards/inkplate2/gfx_standard_font_01.py` | Font data `inkplate2.py` imports for text rendering |

Only `inkplate-firmware.bin` (for classic-ESP32 boards, which the Inkplate 2
is) is vendored -- the upstream `firmware/` directory also ships
`inkplate13spectra-firmware.bin` for a different (ESP32-S3) board family,
which this project has no use for and doesn't include.

## Re-vendoring a newer version

```sh
VERSION=<new-tag>
BASE="https://raw.githubusercontent.com/SolderedElectronics/Inkplate-micropython/$VERSION"
curl -sL "$BASE/firmware/inkplate-firmware.bin" -o vendor/firmware/inkplate-firmware.bin
curl -sL "$BASE/boards/inkplate2/inkplate2.py" -o vendor/inkplate2.py
curl -sL "$BASE/boards/inkplate2/gfx_standard_font_01.py" -o vendor/gfx_standard_font_01.py
curl -sL "$BASE/LICENSE" -o vendor/LICENSE
sha256sum vendor/firmware/inkplate-firmware.bin vendor/inkplate2.py vendor/gfx_standard_font_01.py
```

Then update the version/checksums/table above and in `install.md`.
