"""Renders the TOTP screen on the Inkplate 2's black/white/red e-paper.

Wraps Soldered's `inkplate2` driver (vendored in `vendor/`, copied onto the
board's `/lib` -- see `install.md`).

Layout constants below are derived from the vendored font's actual glyph
metrics (`gfx_standard_font_01.get_ch()`), not guessed: this font is
proportional (not monospaced), and the driver does not clip or wrap text
that runs past the panel's edge -- it silently draws off-canvas -- so widths
must be computed, not assumed. Panel is 212x104px.
"""

from inkplate2 import Inkplate

import gfx_standard_font_01 as _font

_CODE_TEXT_SIZE = 4
_LABEL_TEXT_SIZE = 1

_PANEL_WIDTH = 212
_MARGIN = 4

# Layout, top to bottom, sized to the panel's 104px height:
# header (16px) -> code (64px) -> footer (16px), with a few px of slack.
_HEADER_Y = 2
_CODE_Y = 20
_FOOTER_Y = 87

# 6 digits at size 4, no separators, is exactly 192px (6 * 8px-wide-digit *
# 4) -- verified against the font's actual per-digit width, which fits the
# 212px panel with this x offset. A space-separated version was tried
# first and silently overflowed the panel by ~40px, cutting off the last
# digit(s) -- see git history if reintroducing spacing, and recompute the
# x offset from the font's real glyph widths, not by eye.
_CODE_X = 10

_NOT_SYNCED_MSG = "not synced, code unreliable"


def _text_width(text, size=1):
    total = 0
    for ch in text:
        try:
            _data, _h, w = _font.get_ch(ch)
        except (ValueError, TypeError, KeyError):
            _data, _h, w = _font.get_ch("?")
        total += w * size
    return total


def _truncate_to_width(text, size, max_width):
    if _text_width(text, size) <= max_width:
        return text
    ellipsis = "..."
    budget = max_width - _text_width(ellipsis, size)
    out = ""
    width = 0
    for ch in text:
        ch_width = _text_width(ch, size)
        if width + ch_width > budget:
            break
        out += ch
        width += ch_width
    return out + ellipsis


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

        header = _truncate_to_width(
            account_name, _LABEL_TEXT_SIZE, _PANEL_WIDTH - 2 * _MARGIN
        )
        d.set_text_size(_LABEL_TEXT_SIZE)
        d.set_text_color(d.RED)
        d.set_cursor(_MARGIN, _HEADER_Y)
        d.print(header)

        d.set_text_size(_CODE_TEXT_SIZE)
        d.set_text_color(d.BLACK)
        d.set_cursor(_CODE_X, _CODE_Y)
        d.print(code)

        d.set_text_size(_LABEL_TEXT_SIZE)
        d.set_text_color(d.RED if not time_synced else d.BLACK)
        d.set_cursor(_MARGIN, _FOOTER_Y)
        if time_synced:
            footer = _truncate_to_width(
                "valid until %s" % valid_until_str,
                _LABEL_TEXT_SIZE,
                _PANEL_WIDTH - 2 * _MARGIN,
            )
        else:
            footer = _NOT_SYNCED_MSG
        d.print(footer)

        d.display()

    def show_message(self, lines):
        """Simple status screen (e.g. config-mode instructions). Wraps and
        clips (with a trailing "...") to the panel via the driver's own
        draw_text_box, rather than a fixed per-line pixel step that can
        silently run past the bottom of the 104px-tall panel.
        """
        d = self._d
        self._ensure_began()
        d.clear_display()
        d.set_text_color(d.BLACK)
        text = "\n".join(lines)
        d.draw_text_box(
            _MARGIN,
            _MARGIN,
            _PANEL_WIDTH - _MARGIN,
            100,
            text,
            line_height=16,
            text_size=_LABEL_TEXT_SIZE,
        )
        d.display()
