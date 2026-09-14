"""Differential test: does the row-transmission cutoff (x0_isolation_probe.py:
one 8px black column at x=0 corrupts a broad region up to ~x=790-840) also
happen over partial_update(), or only over the full mono display() path?

epd_i2s_push_partial_frame and epd_i2s_push_mono_frame (epd_i2s.c) share the
exact same epd_i2s_start_row/epd_i2s_wait_row calls, the same s_state ping-pong
buffers, the same row_len/descriptors, and the same epd_i2s_init setup -- they
differ ONLY in the row-building function (build_partial_row vs build_mono_row),
the LUT size (256 vs 16 entries), and how many phases run. That makes this a
clean differential:
- Same gray corruption under partial_update() -> the fault is in the SHARED
  DMA/FIFO layer (epd_i2s_start_row/wait_row/epd_i2s_init) -- everything in
  build_mono_row and the phase loop is exonerated.
- Clean single black line at x=0, no broad corruption -> the fault is specific
  to build_mono_row or the mono phase loop; the DMA/FIFO layer is fine.

Either answer eliminates about half the remaining code, and doesn't require
precise photo measurement -- just "is there a gray region, yes or no", which
photos have read reliably throughout this investigation (unlike the x-position
of a boundary, which turned out to be at/beyond this webcam's resolution).

Sequence: establish a known white baseline via a real display() (this also
primes InkplatePartial's reference framebuffer to all-white -- see
inkplate10.py's display()/partial_update()), THEN draw one black column at
x=0 and push it via partial_update() instead of display(). fullUpdateThreshold
defaults to 10 and partialUpdateCounter starts at 0, so this first
partial_update() call is guaranteed to actually take the partial path, not
silently fall back to a full display() -- checked inkplate10.py directly
before writing this, per this project's "never guess" rule.

Run with `mpremote run tools/experiments/partial_update_differential_probe.py`
-- transient, never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()
d.display()  # known white baseline; also primes partial-update's reference copy

d.fill_rect(0, 0, 8, d.height(), d.BLACK)
d.partial_update()

print("[probe] pushed one 8px black column at x=0 via partial_update() (not display()).")
print("[probe] photograph: clean white panel with just a thin black line at the left")
print("[probe] edge, or the same broad gray corruption x0_isolation_probe.py showed?")
