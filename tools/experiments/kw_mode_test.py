"""EXPERIMENTAL -- not part of the app, not deployed by install.md.

Run manually: `mpremote run tools/experiments/kw_mode_test.py`
(mpremote run uploads and executes this script transiently -- it is never
saved to the board's filesystem, so there's nothing to clean up afterwards
beyond a reset if the panel ends up showing garbage.)

Tests whether putting the Inkplate 2's e-paper controller into "KW"
(black/white-only) mode produces a genuinely faster refresh than the
tri-color "KWR" mode the shipped inkplate2.py driver always uses.

## Why this exists

The panel is a Good Display GDEH0213Z19, driven by a UC8151D controller
(confirmed from Soldered's own hardware schematic + the panel's real
datasheet -- not inferred from command numbers). Its Panel Setting
Register (command 0x00, byte 0) has a documented KW/R bit (bit D4, mask
0x10): 0 = tri-color KWR mode (the driver's default), 1 = mono-only KW
mode. Whether KW mode is actually faster is NOT documented -- the
datasheet's "Update Time" row is blank for both modes. This script
measures it directly, since nobody seems to have published that number
for this specific panel.

## Why this is risky enough to be a separate opt-in script, not app code

- Switching KW/R also redefines what commands 0x10/0x13 carry. In KWR
  mode (normal operation) they're "B/W plane" and "Red plane". In KW mode
  they become "OLD data" and "NEW data" -- a before/after pair the
  controller diffs internally to compute its waveform. This script sends
  OLD=all-white and NEW=your drawn image, which is the standard
  convention for this controller family's mono updates, but was NOT
  confirmed against a working example for this exact panel.
- KW and KWR modes use DIFFERENT on-chip LUT (waveform) tables, loaded
  from OTP memory (the driver's PSR write leaves REG=0, "use OTP LUT").
  The datasheet never confirms this panel's OTP actually contains a valid
  KW-mode table. If it doesn't: expect a garbled, ghosted, or otherwise
  wrong-looking image -- NOT permanent damage. Nothing here writes to
  OTP or flash; it's all volatile controller register state, so a plain
  reset (or power cycle) fully undoes anything this script does.
- This script deliberately reaches into two things the rest of this
  project avoids: `d._framebuf_BW` (a private/underscored driver
  attribute -- there's no public getter for "what did clear_display() +
  print() draw", and reimplementing text rendering to avoid it isn't
  worth it for a one-off experiment) and the low-level `inkplate` C
  module's `spi_panel_wait_busy` directly (needed to time the manual
  refresh accurately; the public `display()` method doesn't expose a way
  to trigger a refresh with a modified PSR byte). Do not copy this
  pattern into `display.py` -- see vendor/README.md's "do not edit /
  don't depend on internals" stance for why.

## What to look for

1. Two timings printed: the normal baseline (tri-color) refresh, and the
   KW-mode refresh.
2. Look at the physical panel after each phase. The interesting outcomes:
   - KW-mode image looks correct AND is meaningfully faster: worth
     building into the app properly (would also mean giving up red --
     the not-synced warning would need a different visual marker, e.g. a
     black border/inverted text, since red wouldn't be usable anymore).
   - KW-mode image is garbled/ghosted/wrong: the OTP doesn't have a
     usable KW LUT for this panel, and that's the end of this
     investigation -- KW mode isn't usable as-is.
   - No meaningful time difference: not worth the added complexity and
     lost red channel either way.
   All three are useful, conclusive results.
"""

import time

from inkplate2 import Inkplate

import inkplate as _inkplate_native  # low-level C module; see docstring

_PSR_BYTE0_TRICOLOR = 0x0F  # KW/R bit (D4) = 0 -- matches the driver's own default
_PSR_BYTE0_MONO = _PSR_BYTE0_TRICOLOR | 0x10  # KW/R bit (D4) = 1
_PSR_BYTE1 = b"\x89"  # unchanged; driver sends this second byte too (see module docstring)

_REFRESH_TIMEOUT_MS = 60000


def _draw_test_pattern(d):
    d.clear_display()
    d.set_text_size(4)
    d.set_text_color(d.BLACK)
    d.set_cursor(10, 20)
    d.print("123456")


def _manual_refresh(d, psr_byte0, plane_0x10, plane_0x13):
    """Replicates display()'s wire sequence, but with a caller-chosen PSR
    byte 0 and explicit plane contents for commands 0x10/0x13 (whose
    meaning depends on that PSR byte -- see module docstring).
    """
    d.set_panel_deep_sleep_state(False)  # wake + reinit, same as display()

    d.send_command(0x00)
    d.send_data(bytes([psr_byte0]))
    d.send_data(_PSR_BYTE1)

    t0 = time.ticks_ms()
    d.send_command(0x10)
    d.send_data(plane_0x10)
    d.send_command(0x13)
    d.send_data(plane_0x13)
    d.send_command(0x11)
    d.send_data(b"\x00")
    d.send_command(0x12)  # refresh trigger
    time.sleep_us(500)
    _inkplate_native.spi_panel_wait_busy(1, _REFRESH_TIMEOUT_MS)
    elapsed_ms = time.ticks_diff(time.ticks_ms(), t0)

    d.set_panel_deep_sleep_state(True)
    return elapsed_ms


def main():
    d = Inkplate()
    d.begin()

    print("[kw-mode experiment] phase 1: baseline tri-color (KWR) refresh")
    _draw_test_pattern(d)
    t0 = time.ticks_ms()
    d.display()
    baseline_ms = time.ticks_diff(time.ticks_ms(), t0)
    print("[kw-mode experiment] baseline KWR refresh: %dms" % baseline_ms)
    print("[kw-mode experiment] check the panel: '123456' should be showing correctly")
    time.sleep(3)

    print("[kw-mode experiment] phase 2: clearing to white (still KWR) so the KW "
          "test's OLD=all-white claim is actually true")
    d.fill_screen(d.WHITE)
    d.display()

    print("[kw-mode experiment] phase 3: redrawing test pattern for the KW-mode NEW plane")
    _draw_test_pattern(d)
    new_plane = bytes(d._framebuf_BW)
    old_plane = b"\xff" * len(new_plane)

    print("[kw-mode experiment] phase 4: KW (mono) refresh")
    kw_ms = _manual_refresh(d, _PSR_BYTE0_MONO, old_plane, new_plane)
    print("[kw-mode experiment] KW refresh: %dms" % kw_ms)
    print("[kw-mode experiment] check the panel now: correct, garbled, or blank?")

    print("[kw-mode experiment] restoring tri-color PSR for normal operation afterwards")
    d.set_panel_deep_sleep_state(False)
    d.send_command(0x00)
    d.send_data(bytes([_PSR_BYTE0_TRICOLOR]))
    d.send_data(_PSR_BYTE1)
    d.set_panel_deep_sleep_state(True)

    print(
        "[kw-mode experiment] done. baseline(KWR)=%dms kw=%dms delta=%dms"
        % (baseline_ms, kw_ms, baseline_ms - kw_ms)
    )


main()
