"""Full-row version of text_duplication_staircase_probe.py's bar-by-y-position
trick: that probe (narrow window, x=308..584) proved bars 1-2 (the row's
head-most digit positions) appear TWICE -- once correct, once at a measured
offset of roughly 430-450 logical px -- while bars 3-6 never appear at all.
That's a real, camera-measured (not eyeballed) result, but it only samples
23% of the row's width, so the exact displacement mechanism (shift? fold?
chunk replay? two regions swapped?) is underdetermined.

This draws 8 bars spanning the FULL row width (x=0,150,300,450,600,750,900,
1050; 40px wide), each at its own distinct y (60,160,260,...,760), so a
single photo gives the complete input-x -> output-x map for one row: every
bar is identified unambiguously by vertical position, and any bar that shows
up at an unexpected x (or fails to show up at all) is immediately visible
without glyph-shape or narrow-window ambiguity.

Run with `mpremote run tools/experiments/full_row_staircase_probe.py` --
transient, never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()

bar_x = [0, 150, 300, 450, 600, 750, 900, 1050]
bar_w = 40
bar_h = 80
for i, x in enumerate(bar_x):
    y = 60 + i * 100
    d.fill_rect(x, y, bar_w, bar_h, d.BLACK)

d.display()

print("[probe] drew 8 bars at x=%r, each at a distinct y=60,160,...,760" % bar_x)
print("[probe] photograph: for each bar (identified by its y/vertical slot),")
print("[probe] does it appear at its correct x, a wrong x, twice, or not at all?")
