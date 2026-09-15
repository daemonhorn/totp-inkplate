"""Follow-up to the waveform.c nibble-order patch: text_render_probe.py's
huge text_size=10 "123456" doesn't fit in the panel/camera frame, making it
hard to judge overall correctness even though individual visible glyphs (a
clean "1", a clean "6") now look right. This draws the same string at a
smaller size so the whole thing fits in view for a clean pass/fail read.

Run with `mpremote run tools/experiments/text_size_small_probe.py` --
transient, never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()
d.set_text_size(4)
d.set_text_color(d.BLACK)
d.set_cursor(300, 380)
d.print("123456")
d.display()

print("[probe] does '123456' render fully and correctly at text_size=4?")
