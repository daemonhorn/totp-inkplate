"""Isolates whether a fill_rect() call starting at x=0 is itself what triggers the
gray-region corruption, independent of column count or total span.

Repeating column_map_probe.py (9 columns, x=0..1192) and boundary_narrow_probe.py
(7 columns, all x>=770) back-to-back, twice each, gave IDENTICAL results both
times for each script -- ruling out run-to-run timing jitter in the I2S
transfer (same probe, same result every time) and ruling out gradual panel
conditioning improving with repeated cycles (the 9-column probe stayed bad on
its second run, after ~12 cumulative clean+draw cycles this session). The
result is deterministic per PROBE CONTENT, not per run -- which points at
something in how the framebuffer gets built for each probe, not a hardware
transfer race.

The one content difference between the two probes: every "bad" probe so far
(column_map_probe.py, full_black_probe.py) includes a fill_rect() call whose x
starts at 0. boundary_narrow_probe.py, the one clean probe, never calls
fill_rect with x=0 -- its lowest x is 770. If a single fill_rect() starting at
x=0 corrupts a broad swath of the framebuffer (not just the 8px it's supposed
to touch -- e.g. a pointer/offset bug in the native gfx_fill_rect call that
only manifests at x=0), that would explain the gray region directly as
corrupted RAM content being transmitted correctly, rather than content being
dropped in transmission.

This draws exactly ONE fill_rect at x=0 (8px wide, full height) on an
otherwise untouched cleared-white background -- nothing else. If the gray
corruption reappears from this single call, x=0 (or low-x) is implicated
directly, independent of column count or multi-rect interaction.

Run with `mpremote run tools/experiments/x0_isolation_probe.py` --
transient, never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()
d.fill_rect(0, 0, 8, d.height(), d.BLACK)
d.display()

print("[probe] drew exactly ONE 8px black column at x=0, nothing else, on white.")
print("[probe] photograph: is the rest of the panel clean white, or is there gray")
print("[probe] corruption beyond the intended 8px column?")
