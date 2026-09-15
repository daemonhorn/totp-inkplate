"""Camera-independent diagnostic for the "12"..."12" duplication seen in
text_size_small_probe.py (text_size=4 "123456" at cursor (300,380) rendered as
"12", a blank gap, then "12" again, with "3456" missing -- reproduced twice).

gfx_draw_char() and gfx_draw_bitmap() were confirmed (by reading gfx.c) to route
every pixel through gfx_set_pixel(), the SAME function fill_rect()/hline() use --
so there's no separate/inconsistent bit-blit path for text. That means if the
duplication is real, it must show up as EITHER (a) wrong pixel data already in
the framebuffer after print() -- a text_mixin.py cursor/advance bug -- or
(b) correct framebuffer data that gets mangled only in transmission
(build_mono_row / the just-patched inkplate_gen_nibble_lut in waveform.c).

This script never calls display() or touches the panel. It calls d.print() to
populate the framebuffer, then reads the raw framebuffer bytes back over the
serial connection and prints an ASCII '#'/'.' dump of the pixel rows spanning
the text, at full x-resolution (no camera, no lossy JPEG, no lighting/glare).
Comparing this dump directly against what "123456" should look like tells us,
with certainty, whether the duplication already exists in the framebuffer
(app-layer bug) or only appears after display() (transmission-layer bug).

Run with `mpremote run tools/experiments/text_framebuf_dump_probe.py` --
transient, never saved to the board. Output is plain text over the REPL, no
photo needed.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT)
d.begin()
d.clear_display()
d.set_text_size(4)
d.set_text_color(d.BLACK)
d.set_cursor(300, 380)
d.print("123456")

fb = d._framebuf()
row_bytes = d.width() >> 3  # mono: 1 bit/pixel packed LSB-first per byte (gfx.c mode 0)

x_start = 280
x_end = 620  # generous: "123456" at size 4 should span roughly 300..300+6*6*4=444
y_start = 375
y_end = 475

print("[probe] dumping framebuffer rows y=%d..%d, x=%d..%d (LSB-first mono bits)" % (
    y_start, y_end, x_start, x_end))
print("[probe] '#' = pixel set (black), '.' = pixel clear (white)")

for y in range(y_start, y_end, 2):  # every other row keeps the dump a reasonable size
    row_off = y * row_bytes
    line = []
    for x in range(x_start, x_end):
        byte = fb[row_off + (x >> 3)]
        bit = (byte >> (x & 7)) & 1
        line.append('#' if bit else '.')
    print("y=%4d: %s" % (y, ''.join(line)))

print("[probe] done. Compare column positions of '#' clusters against expected")
print("[probe] glyph shapes for '1','2','3','4','5','6' in left-to-right order.")
