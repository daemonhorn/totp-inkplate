"""Renders the TOTP screen on the Inkplate 2's black/white/red e-paper.

Wraps Soldered's `inkplate2` driver (installed separately -- see README --
via `mpremote mip install github:SolderedElectronics/Inkplate-micropython/boards/inkplate2`,
not vendored in this repo).
"""

from inkplate2 import Inkplate

_CODE_TEXT_SIZE = 4
_LABEL_TEXT_SIZE = 1


class Display:
    def __init__(self):
        self._d = Inkplate()
        self._began = False

    def _ensure_began(self):
        if not self._began:
            self._d.begin()
            self._began = True

    def show_code(self, account_name, code, valid_until_str, time_synced=True):
        d = self._d
        self._ensure_began()
        d.clear_display()

        d.set_text_size(_LABEL_TEXT_SIZE)
        d.set_text_color(d.RED)
        d.set_cursor(4, 4)
        d.print(account_name)

        d.set_text_size(_CODE_TEXT_SIZE)
        d.set_text_color(d.BLACK)
        d.set_cursor(10, 28)
        # Space the digits out a bit for readability at this size.
        d.print(" ".join(code))

        d.set_text_size(_LABEL_TEXT_SIZE)
        d.set_text_color(d.RED if not time_synced else d.BLACK)
        d.set_cursor(4, 90)
        if time_synced:
            d.print("valid until %s" % valid_until_str)
        else:
            d.print("NOT TIME-SYNCED - code may be wrong")

        d.display()

    def show_message(self, lines):
        """Simple status screen (e.g. config-mode instructions)."""
        d = self._d
        self._ensure_began()
        d.clear_display()
        d.set_text_size(_LABEL_TEXT_SIZE)
        d.set_text_color(d.BLACK)
        y = 4
        for line in lines:
            d.set_cursor(4, y)
            d.print(line)
            y += 12
        d.display()
