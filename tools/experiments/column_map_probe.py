"""Quantitative follow-up to row_edge_probe.py's black-fraction anomaly.

row_edge_probe.py drew two 200px bars (x=0-200 and x=1000-1200) on white --
400/1200 = 1/3 of the row should read black. The photographed result was
closer to 7/8 black. No pixel *reordering* (byte-pair swap, wrong variant's
pin mapping, etc.) can change that ratio -- permuting bits conserves the
count of set bits. Something downstream is duplicating/smearing content,
not just moving it around. That also reframes every earlier "compress
toward one edge" observation in the investigation notes: they're equally
consistent with a truncated/smeared transfer as with a remap, and the
black-fraction math only fits the former.

build_mono_row() (epd_i2s.c) and board_config_row_bytes() (board_config.h,
width>>2 = 300 bytes for width=1200) were checked directly against each
other: build_mono_row emits exactly 4 output bytes per 2 input bytes, 150
input bytes (width>>3) -> 300 output bytes, matching s_state.row_len from
epd_i2s_init exactly. So it is NOT a simple output-buffer-size-vs-write-size
mismatch -- that specific hypothesis is now ruled out too.

This draws nine independent 8px-wide black columns spanning the full panel
height, spread across the row (x=0, 150, 300, 450, 600, 750, 900, 1050,
1192 -- the last one flush against the right edge since 1200-8=1192), on
an otherwise-white background. Photographing which columns appear, at what
x they actually land, whether any are duplicated/widened/merged, and
whether the smear-vs-drop pattern differs near either edge gives the
transfer function directly -- more informative than a pass/fail on two
wide bars. Pure fill_rect, no text/font code, same isolation
row_edge_probe.py already established.

Run with `mpremote run tools/experiments/column_map_probe.py` -- transient,
never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()  # known white background before drawing anything

COL_W = 8
XS = [0, 150, 300, 450, 600, 750, 900, 1050, 1192]
for x in XS:
    d.fill_rect(x, 0, COL_W, d.height(), d.BLACK)

d.display()

print("[probe] drew %d columns (%dpx wide) at x=%s on white, full height/refresh" % (
    len(XS), COL_W, XS))
print("[probe] photograph the panel: which columns are visible, at roughly what x,")
print("[probe] and does anything look duplicated/widened/merged rather than just moved?")
