"""Pins the row-transmission cutoff to +/-10px with a self-calibrating layout.

Prior probes (column_map_probe.py, boundary_narrow_probe.py, x0_isolation_probe.py)
converged on: content below roughly x=790-800 never reaches the panel, content
at/above it always does -- one positional cutoff, not the "content-triggered"
or "fixed wide boundary" framings tried and retracted earlier (see this
project's memory / git history). The x=800 guess matters because
(1200-800)/4 = 100 bytes -- exactly 1/3 of the 300-byte per-row transmission
-- which would point at a FIFO/channel CONFIG mismatch in epd_i2s_init rather
than a FIFO-drain timing race, but that number came from a bezel-edge
detector that returned a bad reading on one earlier photo, so it needs a
tighter, self-calibrating remeasurement.

This draws columns at x=760, 780, 800, 820, 840 (the candidates) PLUS x=1192,
which every probe so far has shown renders correctly -- so its known position
in the resulting photo pins the right-hand side of the pixel-to-panel-x
mapping directly, without needing to trust a separately-computed bezel edge.
Run this TWICE back to back and compare -- this investigation has had to
retract conclusions drawn from a single run twice already.

Run with `mpremote run tools/experiments/boundary_calibrated_probe.py` --
transient, never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()

COL_W = 8
XS = [760, 780, 800, 820, 840, 1192]
for x in XS:
    d.fill_rect(x, 0, COL_W, d.height(), d.BLACK)

d.display()

print("[probe] drew columns at x=%s on white (1192 is the known-good calibration anchor)" % XS)
print("[probe] photograph, locate x=1192's column in the photo to calibrate pixel->panel-x,")
print("[probe] then read off which of 760/780/800/820/840 survive.")
