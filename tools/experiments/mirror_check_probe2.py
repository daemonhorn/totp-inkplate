"""Follow-up to mirror_check_probe.py's unexplained result: drawing ONE 8px
column at x=100 produced TWO lines on the panel (measured panel_x~88 and
panel_x~514), reproduced 3x including once right after a full 4-cycle
panel_condition.py run (ruling out ghosting/residual from a prior probe).
Checked other photos from this session with different content near x=514:
no spurious line there, so it isn't a fixed physical panel seam either.

This draws ONE 8px column at x=514 instead (swapping which position is the
"real" draw and which was the mystery duplicate) to see whether the
duplicate relationship is symmetric: does content at x=514 ALSO show up
doubled (at ~514 and ~100), or does it render as a single clean line at
~514 with nothing at ~100? That distinguishes a genuine content-triggered
duplication mechanism (should reproduce a similar pattern) from something
coincidentally specific to x=100 (should NOT).

Run with `mpremote run tools/experiments/mirror_check_probe2.py` --
transient, never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()
d.fill_rect(514, 0, 8, d.height(), d.BLACK)
d.display()

print("[probe] drew ONE 8px column at x=514 (not 100 this time).")
print("[probe] photograph: one clean line near x=514, or does it duplicate")
print("[probe] again (e.g. a second line near x=100 or elsewhere)?")
