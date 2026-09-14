"""Tests whether the auto-detected hardware variant is actually correct,
by forcing the OTHER one and re-running the exact same text draw.

Both mono (INKPLATE_1BIT) and grayscale (INKPLATE_2BIT) modes show the
same class of corruption on non-uniform content -- two independent native
row-builder implementations, with different swap logic and different
framebuffer formats, both wrong the same way. Two independent
implementations don't share a bug; they share INPUTS. The input neither
implementation controls, and this project has never actually verified
against the physical panel, is which pin/board configuration
select_board() handed the C side.

upstream_detect_variant.py reported "inkplate10v2", based on reading
0xff from register 0x40 at I2C address 0x20 -- and 0xff is exactly what
an I2C read returns when nothing on the bus actually drives it, so it's
worth checking whether that's a real V2 signature or a fall-through
default (see _detect_variant's branch logic in
vendor/inkplate10/inkplate10.py). If the wrong variant got selected, the
C side received the wrong PIN ASSIGNMENTS for the gate/source control
lines (both v1/v2 board_config_t entries share the same 1200x825
width/height, so this was never a resolution mismatch -- but the actual
physical control pins genuinely differ between the two). Wrong control
pins would produce exactly this signature: uniform fills still work,
anything with real structure scrambles, in every display mode -- since
this is upstream of both mono and grayscale, common to both.

This forces variant="inkplate10v1" (the one auto-detect did NOT pick)
and re-runs the identical text_render_probe.py draw. If it renders
correctly, the fix is passing the correct variant explicitly in
display.py -- auto-detect was wrong on this unit. If it's identical,
the variant isn't the cause and the next thing to check is whether this
panel is physically 1200x825 at all (see this project's chat log for
why that's the next question).

Run with `mpremote run tools/experiments/variant_override_probe.py` --
transient, never saved to the board.
"""

from inkplate10 import Inkplate

d = Inkplate(Inkplate.INKPLATE_1BIT, variant="inkplate10v1")
d.begin()
d.clear_display()
d.set_text_size(10)
d.set_text_color(d.BLACK)
d.set_cursor(240, 292)
d.print("123456")
d.display()

print("[probe] forced variant=inkplate10v1 (auto-detect picked inkplate10v2)")
print("[probe] does '123456' render fully and correctly now?")
