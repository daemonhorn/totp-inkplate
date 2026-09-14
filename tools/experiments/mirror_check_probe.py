"""Discriminates a full-row horizontal mirror from a sub-byte bit-order issue,
after the two-register I2S patch (out_eof_mode=1 + tx_stop_en=1, see
~/esp/epd_i2s_fix.patch) fixed column_map_probe.py's 9-column test (all
columns now render, full width, no gray corruption) but text_render_probe.py
still shows scrambled/recognizable-but-wrong glyphs.

column_map_probe.py's x set -- {0, 150, 300, 450, 600, 750, 900, 1050, 1192}
-- is symmetric about x=600 (mirroring x -> 1200-x maps the set back onto
itself, to within 8px), so "all 9 columns present, evenly spaced" is exactly
what a full-row horizontal mirror would ALSO photograph as. It cannot rule
out a mirror. Glyphs (asymmetric content) revealing a problem while that
symmetric column set didn't is consistent with either a row-level mirror
(build_mono_row's walk direction/pair-emission order) or a sub-byte bit-order
issue (gfx_set_pixel writes LSB-first per gfx.c, but epd_i2s.h documents
push_mono_frame's input as MSB-first framebuf -- a mismatch invisible on a
byte-aligned solid run of 1-bits, but would scramble glyph detail).

This draws exactly ONE 8px column at x=100 -- deliberately NOT symmetric --
on white, full refresh. Where it actually lands settles which:
- Renders at x~100 (near the left edge, close to intended): no full mirror;
  the remaining bug is sub-byte (bit order within a byte).
- Renders at x~1100 (near the right edge instead): full-row mirror; the fix
  is build_mono_row's walk direction/pair order, not bit order.

Run with `mpremote run tools/experiments/mirror_check_probe.py` --
transient, never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()
d.fill_rect(100, 0, 8, d.height(), d.BLACK)
d.display()

print("[probe] drew ONE 8px column at x=100 (asymmetric, unlike column_map_probe's set).")
print("[probe] photograph: does it land near the LEFT edge (~x=100, correct) or")
print("[probe] near the RIGHT edge (~x=1100, full-row mirror)?")
