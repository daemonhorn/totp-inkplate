"""Determines whether the "12"..."12" pattern seen in text_size_small_probe.py
is a genuine REPEAT of the row's head (same source bytes shown twice) or a
SPLIT (all content transmits once, but a chunk lands at the wrong x) --
advisor flagged that reading "12" vs "56" off a ~12-image-px-wide glyph in a
640px webcam JPEG is exactly the kind of eyeball read this project's own
methodology forbids, and the two mechanisms point at completely different
root causes (source-read/DMA-restart bug vs. CL-pulse-count-vs-bytes-supplied
bug).

Draws 6 solid black bars at the exact x positions of the six digit clusters
measured by text_framebuf_dump_probe.py (308, 352, 400, 444, 496, 544; each
~40px wide) so the x geometry matches the real text case 1:1 -- but each bar
sits at a DIFFERENT y (100, 200, ..., 600), so which bar(s) reappear in the
second cluster is readable from vertical position alone, at full camera
resolution, with no glyph-shape ambiguity and no nibble-order dependency
(solid fills are invariant to intra-byte bit order).

If the duplicate cluster contains bars 1-2 (the same ones as the first
cluster): genuine repeat -- same source x-range shown twice.
If it contains bars 5-6 (the tail of the row): a split -- everything
transmitted once, but misplaced.

Run with `mpremote run tools/experiments/text_duplication_staircase_probe.py`
-- transient, never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()

bar_x = [308, 352, 400, 444, 496, 544]
bar_w = 40
bar_h = 80
for i, x in enumerate(bar_x):
    y = 100 + i * 100
    d.fill_rect(x, y, bar_w, bar_h, d.BLACK)

d.display()

print("[probe] drew 6 bars at x=%r, each at a distinct y=100,200,...,600" % bar_x)
print("[probe] photograph: besides the bars at their real y positions, is")
print("[probe] there a SECOND cluster of bars elsewhere? If so, which bar")
print("[probe] number(s) (by y position, top-to-bottom = bar 1-6) appear")
print("[probe] in it -- the first ones (1-2) or the last ones (5-6)?")
