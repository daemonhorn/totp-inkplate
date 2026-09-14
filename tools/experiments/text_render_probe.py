"""Isolates whether the display-corruption bug is in text rendering itself,
or specific to partial_update()'s diff path.

Earlier probes ruled out two things: the panel refreshes cleanly
(panel_condition.py's full-black test came up solid), and get_ch()/ord()
correctly raise TypeError on a 6-character string so inkplate_text_mixin.py
falls back to its per-character render loop as intended
(text_mixin_probe.py). Neither of those actually confirmed real *text*
renders correctly, though -- they tested the font lookup in isolation, not
the native gfx_draw_char() blit a real d.print() call goes through.

This script draws the same 6-digit layout display.py uses, but with a
guaranteed-fresh Inkplate object so this is definitely the FIRST display()
call (full refresh, not partial_update() -- see Inkplate._first_draw in
display.py for why that matters: partial_update() is never used until a
second draw happens). If "123456" renders correctly here, the bug is
specific to partial_update()'s native diff path (epd_i2s_push_partial_frame/
build_partial_row -- firmware C code, not this app or the driver's Python).
If it's already corrupted here, on a plain full refresh with real text, the
bug is in text rendering itself (gfx_draw_char, or something in this app's
own display.py) and partial_update() was never the culprit.

Run with `mpremote run tools/experiments/text_render_probe.py` -- transient,
never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()
d.set_text_size(10)
d.set_text_color(d.BLACK)
d.set_cursor(240, 292)
d.print("123456")
d.display()  # guaranteed full refresh -- this is the object's first draw

print("[probe] look at the panel: does '123456' render fully and correctly?")
