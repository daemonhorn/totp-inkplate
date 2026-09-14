"""Tests whether content near the LEFT edge of each row gets dropped during
the full-refresh row transmission, independent of text/fonts entirely.

Both text probes so far show the same shape: content toward the low-X
(left) side of a row goes missing, while content toward the high-X (right)
side survives -- text_render_probe.py's "123456" (spanning x=240-960) lost
everything left of "half of the 5th digit", and text_render_probe2.py's
single digit at x=20 didn't show up AT ALL. That's suspicious given
epd_i2s.c's build_mono_row() walks each row's bytes from the LAST
(rightmost) byte down to the FIRST (leftmost) -- if something truncates a
row's transmission before it finishes, the leftmost content (built/sent
last) is exactly what would be missing.

panel_condition.py's earlier full-width (x=0 to d.width()) black fill came
back "solid black", which seems to contradict this -- but that was a
full-black-on-white-background judgement call by eye; a narrow dropped
strip at the very edge of an otherwise-solid black fill is easy to miss.
This test puts two separate black bars on an otherwise white background,
one hugging the left edge and one hugging the right edge, so a dropped
region shows up as an obvious gap instead of blending into a solid fill.

Run with `mpremote run tools/experiments/row_edge_probe.py` -- transient,
never saved to the board. No text/font code involved at all -- pure
fill_rect, to isolate this from every text-rendering hypothesis so far.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()  # white background

BAR_WIDTH = 200
d.fill_rect(0, 0, BAR_WIDTH, d.height(), d.BLACK)  # hugs the LEFT edge
d.fill_rect(d.width() - BAR_WIDTH, 0, BAR_WIDTH, d.height(), d.BLACK)  # hugs the RIGHT edge

d.display()

print("[probe] two black bars on white: one at the left edge (x=0-%d), one at the" % BAR_WIDTH)
print("[probe] right edge (x=%d-%d). Does EACH bar render solid, full-height, both" % (
    1200 - BAR_WIDTH, 1200))
print("[probe] edges? Or is one of them (which one?) missing / incomplete / faint?")
