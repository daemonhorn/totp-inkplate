"""Calls the native gfx_draw_char() blit directly into a plain scratch
bytearray -- no panel, no waveform, no PMIC involved at all.

Every probe so far that drew TEXT rendered nothing or a partial/garbled
result (text_render_probe.py, text_render_probe2.py, upstream's own
unmodified hello_world.py). The one probe that drew SHAPES instead
(row_edge_probe.py, via fill_rect -- a different native entry point,
gfx_fill_rect, not gfx_draw_char) produced visible structure, just
distorted. That split -- shapes work, glyphs don't -- doesn't fit
degraded/flaky hardware (a marginal PMIC wouldn't selectively spare one
native call and not another); it fits one code path having a real bug the
other doesn't hit.

One thing hasn't actually been confirmed yet: inkplate_text_mixin.py's
blit() (which calls gfx_draw_char) sits OUTSIDE the
`except (ValueError, TypeError):` in _print_text() -- so if gfx_draw_char
raises, it propagates out of print() silently in a script whose next line
is just a print() statement. That would look exactly like "nothing
rendered" with no visible traceback. This checks that directly.

Run with `mpremote run tools/experiments/gfx_draw_char_probe.py` --
transient, never saved to the board.
"""

import inkplate
from gfx_standard_font_01 import get_ch

char_data, ch_h, ch_w = get_ch("1")
fb = bytearray(1200 * 825 // 8)

try:
    inkplate.gfx_draw_char(fb, 1200, 825, 0, 0, 100, 100, char_data, ch_w, ch_h, 10, 1)
    nonzero = sum(1 for b in fb if b)
    print("[probe] gfx_draw_char() returned OK, nonzero bytes in buffer:", nonzero)
except Exception as e:
    print("[probe] gfx_draw_char() RAISED %s: %s" % (type(e).__name__, e))

print("[probe] inkplate.version():", inkplate.version())
