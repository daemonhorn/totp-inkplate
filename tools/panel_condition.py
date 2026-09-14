"""One-time diagnostic + remedy for a panel that's sat unpowered for a long
time (this project's Inkplate 10 had been idle ~3 years with a stale image
still showing -- e-paper holds its image with zero power, so that alone
isn't unusual, but it raised the question of whether the panel would do a
*clean* full refresh after that long a dormancy).

Symptom this was written to diagnose: after porting to this board, the very
first screen drawn (config_mode's setup-instructions screen, a plain
`display()` full refresh -- partial_update() is never called that early)
already came out corrupted: only the last character and part of the one
before it visible. Since that happened on a *full* refresh, before any
partial-update diffing was ever exercised, it can't be explained by this
app's own code (display.py, inkplate_text_mixin.py's chunking) -- app code
wasn't even doing anything unusual there, just d.print("...") + d.display().
That points at either (a) a real driver/text-rendering bug independent of
this app, or (b) the panel itself not fully responding to a refresh yet
after long dormancy -- a documented real phenomenon with e-paper (residual
pigment-particle position from years of no refreshes; usually clears after
a few forced full black/white cycles). This script tells them apart with no
text involved at all, then doubles as the fix if it's (b).

Run with `mpremote run tools/panel_condition.py` -- transient, never saved
to the board. Uses only this project's already-vendored driver and only its
public API (Inkplate.fill_rect/clear_display/display/begin) -- no reaching
into private driver internals, unlike kw_mode_test.py's justified exception
for a one-off register-level probe.

Interpreting the result: watch the actual panel after each step, not the
console.
  - If the very first full-black frame comes up solid black edge-to-edge,
    the panel is refreshing fine -- the corruption is a text-rendering bug
    in this app or the vendored driver, not a hardware/dormancy issue. Stop
    here and look at display.py / inkplate_text_mixin.py instead of running
    more cycles.
  - If it's streaky, patchy, or only partially fills, that's the dormancy
    symptom -- keep watching through the remaining cycles. Each full
    black/white pair exercises the panel's waveform and should be visibly
    cleaner than the last; by the last cycle the fills should be solid and
    even. If they still aren't after all the cycles below, bump CYCLES up
    and run again rather than concluding it's hopeless -- there's no fixed
    number of cycles a truly long-dormant panel needs.
"""

import time

from inkplate10 import Inkplate

CYCLES = 4
PAUSE_S = 3  # time to actually look at the panel between fills

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()

print("[panel_condition] watch the physical panel, not this console")

for i in range(CYCLES):
    print("[panel_condition] cycle %d/%d: full BLACK" % (i + 1, CYCLES))
    d.fill_rect(0, 0, d.width(), d.height(), d.BLACK)
    d.display()
    time.sleep(PAUSE_S)

    print("[panel_condition] cycle %d/%d: full WHITE" % (i + 1, CYCLES))
    d.clear_display()  # fills the RAM framebuffer with white (0x00 -- see
    # clear_display()'s docstring caveat in display.py); this is a genuine
    # full white frame, same mechanism the app uses on every draw
    d.display()
    time.sleep(PAUSE_S)

print("[panel_condition] done -- see this file's docstring for how to read the result")
