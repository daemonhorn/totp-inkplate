"""Consistency check for the column_map_probe.py truncation finding.

column_map_probe.py drew 9 separate 8px columns; only the 3 rightmost
(x=900, 1050, 1192) survived as crisp black lines on white -- the region
x=0-750 came back uniform mid-gray with no visible structure at all, not
white. That's the signature of a truncated row transfer (the undriven
tail of each row's shift-in sequence sits at whatever mid-state it was
already in) landing on the FIRST ~2/3 of what's transmitted per row
(row_buf's front = high-x, per build_mono_row's end-to-start walk -- see
column_map_probe.py and epd_i2s.c), not a coincidence specific to columns.

If that's right, `panel_condition.py`'s earlier "solid black" full-fill
judgement (relied on to rule out panel/PMIC/waveform hardware entirely)
was an eyeball miscall -- a fully truncated left 2/3 sitting at mid-gray
next to a correctly-driven black right 1/3 can look "basically black" at a
glance, especially on a glossy panel under uneven lighting.

This fills the ENTIRE row (x=0 to width, all rows) solid black through the
same display() path column_map_probe.py used (not panel_condition.py's
clean()-only cycles). Two possible outcomes:
- Left ~2/3 stays gray, right ~1/3 goes solid black: confirms truncation
  as the mechanism, and refutes "uniform fills work perfectly" as a ruled-
  out item in the investigation notes.
- Whole panel goes solid black: truncation is wrong, the column result
  needs a different explanation.

Run with `mpremote run tools/experiments/full_black_probe.py` --
transient, never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()
d.fill_rect(0, 0, d.width(), d.height(), d.BLACK)
d.display()

print("[probe] full-panel black fill via display() (not clean()). Photograph the panel:")
print("[probe] solid black everywhere, or gray on the left ~2/3 with black only on the right?")
