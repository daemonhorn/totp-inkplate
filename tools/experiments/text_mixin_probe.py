"""One-off diagnostic for the Inkplate 10 display-corruption bug: only the
last digit (and part of the one before it) of a 6-digit code render.

`inkplate_text_mixin.py`'s `_print_text()` tries to look up an entire string
as if it were one glyph (`self.font_family.get_ch(chunk)`, where `chunk` is
the whole 6-digit code when it contains no literal "__") before falling
back to rendering it one character at a time:

    try:
        char_data, ch_h, ch_w = self.font_family.get_ch(chunk)
        ...
        blit(x, y, char_data, ch_w, ch_h)   # single blit for the WHOLE chunk
        x += ch_w * size
    except (ValueError, TypeError):
        for char in chunk:                  # correct per-character path
            ...

That fallback only kicks in if `get_ch("123456")` -- which calls
`ord("123456")` first -- actually raises `ValueError` or `TypeError` on
this exact firmware. This script checks that directly, with no display
calls involved, isolating the question to just `ord()` and `get_ch()`.

We already ruled out a panel/hardware cause: tools/panel_condition.py's
full-black test came up solid on the very first cycle, and the corruption
appeared even on config_mode's very first (full-refresh) screen, before
partial_update() was ever exercised -- so this really is a text-rendering
question, not a refresh-timing or dormancy one.

Run with `mpremote run tools/experiments/text_mixin_probe.py` -- transient,
never saved to the board. Requires the Inkplate 10 driver files already
copied to /lib (see install.md) since it imports the vendored font module.
"""

try:
    result = ord("123456")
    print("[probe] ord('123456') did NOT raise -- returned:", result)
except Exception as e:
    print("[probe] ord('123456') raised %s: %s" % (type(e).__name__, e))

try:
    from gfx_standard_font_01 import get_ch

    result = get_ch("123456")
    print("[probe] get_ch('123456') did NOT raise -- returned:", result)
except Exception as e:
    print("[probe] get_ch('123456') raised %s: %s" % (type(e).__name__, e))

print("[probe] done")
