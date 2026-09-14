"""Follow-up to text_render_probe.py: that one proved the corruption happens
even on a guaranteed first-draw full refresh with real text (not just
get_ch()/ord() in isolation, and not partial_update()) -- "123456" showed up
as only "half of 5 and all of 6" visible, the earlier characters missing.

That pattern (later characters surviving, earlier ones gone) doesn't fit a
mid-loop crash (a crash would leave the *earlier* characters drawn and the
*later* ones missing, the opposite). Two things haven't actually been
checked yet, both cheap to check directly:

1. What get_ch() returns for each individual digit '1'..'6' -- the
   multi-char probe only confirmed get_ch("123456") raises; it never
   confirmed get_ch('1') (what the per-character fallback loop actually
   calls) returns sane (data_len, height, width) values.
2. Whether each digit blits correctly *in isolation*, one per row at the
   same x, which rules out the x-accumulation logic (`x += ch_w * size`)
   as a variable entirely -- if a single isolated glyph is already wrong,
   the bug is in the blit itself, not in multi-character positioning.

Run with `mpremote run tools/experiments/text_render_probe2.py` -- transient,
never saved to the board.
"""

from gfx_standard_font_01 import get_ch
from inkplate10 import Inkplate

print("[probe2] per-digit get_ch() metadata:")
for ch in "123456":
    data, h, w = get_ch(ch)
    print("  get_ch(%r) -> len(data)=%d height=%d width=%d" % (ch, len(data), h, w))

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()
d.set_text_size(10)
d.set_text_color(d.BLACK)

# One representative early/mid/late digit, each alone on its own row, far
# apart both horizontally (all at x=20, unambiguous) and vertically (a
# size-10 glyph is 24*10=240px tall, so 260px of row spacing leaves a clean
# gap -- at most 3 such rows fit on this 825px-tall panel).
SAMPLE_DIGITS = ["1", "4", "6"]
y = 20
for ch in SAMPLE_DIGITS:
    d.set_cursor(20, y)
    d.print(ch)
    y += 260

d.display()

print("[probe2] look at the panel: 3 rows, top to bottom: '1', '4', '6', each alone")
print("[probe2] does EVERY row show its digit correctly, alone, with nothing else drawn?")
