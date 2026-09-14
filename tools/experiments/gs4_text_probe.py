"""Tests the same text draw as text_render_probe.py, but through the
grayscale (INKPLATE_2BIT) rendering path instead of mono (INKPLATE_1BIT).

gfx_draw_char_probe.py already confirmed the character blit itself is
correct -- it writes a plausible, non-empty glyph into a plain scratch
bytearray with no panel/waveform involved. Every panel-visible text draw
still comes out wrong, though, which localizes the problem to the actual
panel push (mono_display() -> build_mono_row(), firmware/usermods/inkplate/
display/epd_i2s.c) rather than the framebuffer write.

gs_display() drives the panel through a DIFFERENT native row builder
(build_gs3_row(), which applies its own swap logic at a different byte
granularity and reads the GS4_HMSB framebuffer format instead of 1bpp
mono). If text renders correctly here, the fault is specific to the mono
row builder -- both a diagnosis and a working configuration (grayscale
mode is display_mode=1, ~1.6s full refresh per Soldered's spec; note
partial_update() is a documented no-op in this mode, so this trades away
the fast partial refresh, but that's still fine for a 30s rotation). If
text is equally broken here, the mono-specific row builder isn't the
right explanation and the fault is further down (I2S/vscan init, or the
panel bus itself) -- the fix isn't "switch display modes" in that case.

Run with `mpremote run tools/experiments/gs4_text_probe.py` -- transient,
never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_2BIT)
d.begin()
d.clear_display()
d.set_text_size(10)
d.set_text_color(d.BLACK)
d.set_cursor(240, 292)
d.print("123456")
d.display()  # gs_display() -- different native row builder than mono_display()

print("[probe] grayscale mode: does '123456' render fully and correctly now?")
