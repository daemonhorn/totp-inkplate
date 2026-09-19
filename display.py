"""Renders the TOTP screen on the Inkplate 10's grayscale e-paper.

Wraps Soldered's `inkplate10` driver (vendored in `vendor/inkplate10/`,
copied onto the board's `/lib` -- see `install.md`).

Ported from the original Inkplate 2 version of this file: same overall
structure (show_code/show_message, width-aware truncation using the
font's real glyph metrics, a DEBUG timing wrapper), but sized for this
board's much larger 1200x825 panel and its different color model (no red
channel here -- see _NOT_SYNCED_MSG below) and refresh model (this driver
supports real partial refresh, unlike the Inkplate 2's full-refresh-only
panel -- see _display()).
"""

import time

from inkplate10 import Inkplate

import gfx_standard_font_01 as _font

# Prints how long each panel refresh takes, and whether it was a full or
# partial update -- see README's Debugging section. Unlike the Inkplate 2
# (where every refresh was a full ~17-19s flash no matter what), most
# cycles here should be a fast partial update; only every ~10th is a full
# refresh (see _display()'s docstring).
DEBUG = True

_CODE_TEXT_SIZE = 10
_LABEL_TEXT_SIZE = 3

_PANEL_WIDTH = 1200
_PANEL_HEIGHT = 825
_MARGIN = 20

# Layout, top to bottom. Chosen with generous slack -- this panel has
# ~7x the Inkplate 2's pixel budget, so unlike that board's tight
# 212x104 fit, there's no need to compute these to the pixel.
_HEADER_Y = 20
_CODE_Y = 292  # (825 - code height 240) // 2 -- centers the code when
# show_labels is off; leaves comfortable slack above/below it either way
# when labels are on, since this panel has room to spare.
_FOOTER_Y = 620

# 6 digits at size 10, no separators: this font's digits are 12px wide
# natively (verified via gfx_standard_font_01.get_ch, not assumed --
# different vendored font than the Inkplate 2 used, so its metrics don't
# transfer), giving 6*12*10 = 720px, centered in the 1200px panel.
_CODE_X = (_PANEL_WIDTH - 6 * 12 * _CODE_TEXT_SIZE) // 2

_NOT_SYNCED_MSG = "not synced, code unreliable"

_STATUS_Y = 733  # below the footer/banner area (which extends to ~712 at
# _LABEL_TEXT_SIZE, see _FOOTER_Y/_draw_banner) with room to spare before
# the panel's bottom margin (825 - 20 - 24*_LABEL_TEXT_SIZE = 733).

# Single-cell Li-ion/LiPo voltage range for the percentage estimate below --
# NOT a precise fuel-gauge reading (no coulomb counting, just voltage), so
# treat the displayed percentage as approximate, particularly near the ends
# of the curve where voltage sag/recovery under load is least linear.
_BATTERY_EMPTY_V = 3.3
_BATTERY_FULL_V = 4.2


def _battery_percent(voltage):
    pct = (voltage - _BATTERY_EMPTY_V) / (_BATTERY_FULL_V - _BATTERY_EMPTY_V) * 100
    return max(0, min(100, int(round(pct))))


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
        self._d = Inkplate(Inkplate.INKPLATE_1BIT)  # 1-bit mode is
        # required for partial_update() to do anything -- it's a documented
        # no-op in the 2-bit grayscale mode (confirmed from driver source).
        self._began = False
        self._first_draw = True  # first draw must be a full display() to
        # give the driver's partial-update diffing something to diff
        # against; every draw after that uses partial_update() instead.

    def _ensure_began(self):
        if not self._began:
            self._d.begin()
            self._began = True

    def _display(self):
        if self._first_draw:
            op, fn = "display (full)", self._d.display
            self._first_draw = False
        else:
            op, fn = "partial_update", self._d.partial_update

        if not DEBUG:
            fn()
            return
        t0 = time.ticks_ms()
        fn()
        elapsed_ms = time.ticks_diff(time.ticks_ms(), t0)
        print("[debug] display.%s took %dms" % (op, elapsed_ms))

    def show_code(
        self, account_name, code, valid_until_str, now_str=None, time_synced=True, show_labels=False
    ):
        """Draws the code, centered, at a single text size by default.

        `show_labels` (off by default -- same config knob as the Inkplate 2
        version, kept for consistency even though this board's fast
        refresh removes the original performance motivation for hiding
        them) additionally draws the account name above it and a "valid
        until" line below it. The not-synced warning is always shown
        regardless of `show_labels`, since it's a correctness signal
        rather than a decorative label -- rendered as an inverted (black
        banner, white text) bar rather than red text, since this panel
        has no red channel.

        `now_str` (a pre-formatted local-time string -- see
        timezone.format_local, same as `valid_until_str`) and the battery
        level are drawn as a single status line regardless of
        `show_labels`, same reasoning as the not-synced banner: this is
        status info, not decoration. Battery is read fresh from hardware
        on every call (see _battery_percent's caveats about accuracy).
        """
        d = self._d
        self._ensure_began()
        d.clear_display()

        if show_labels:
            header = _truncate_to_width(
                account_name, _LABEL_TEXT_SIZE, _PANEL_WIDTH - 2 * _MARGIN
            )
            d.set_text_size(_LABEL_TEXT_SIZE)
            d.set_text_color(d.BLACK)
            d.set_cursor(_MARGIN, _HEADER_Y)
            d.print(header)

        d.set_text_size(_CODE_TEXT_SIZE)
        d.set_text_color(d.BLACK)
        d.set_cursor(_CODE_X, _CODE_Y)
        d.print(code)

        if not time_synced:
            self._draw_banner(_NOT_SYNCED_MSG)
        elif show_labels:
            footer = _truncate_to_width(
                "valid until %s" % valid_until_str,
                _LABEL_TEXT_SIZE,
                _PANEL_WIDTH - 2 * _MARGIN,
            )
            d.set_text_size(_LABEL_TEXT_SIZE)
            d.set_text_color(d.BLACK)
            d.set_cursor(_MARGIN, _FOOTER_Y)
            d.print(footer)

        self._draw_status_line(now_str)

        self._display()

    def _draw_status_line(self, now_str):
        battery_pct = _battery_percent(self._d.read_battery())
        parts = []
        if now_str:
            parts.append(now_str)
        parts.append("Battery %d%%" % battery_pct)
        text = "   ".join(parts)

        d = self._d
        text = _truncate_to_width(text, _LABEL_TEXT_SIZE, _PANEL_WIDTH - 2 * _MARGIN)
        d.set_text_size(_LABEL_TEXT_SIZE)
        d.set_text_color(d.BLACK)
        d.set_cursor(_MARGIN, _STATUS_Y)
        d.print(text)

    def _draw_banner(self, text):
        """Inverted (black background, white text) warning bar -- this
        panel has no red channel, so this stands in for the Inkplate 2
        version's red not-synced text.
        """
        d = self._d
        text = _truncate_to_width(text, _LABEL_TEXT_SIZE, _PANEL_WIDTH - 4 * _MARGIN)
        banner_height = _font.height() * _LABEL_TEXT_SIZE + 2 * _MARGIN
        d.fill_rect(0, _FOOTER_Y - _MARGIN, _PANEL_WIDTH, banner_height, d.BLACK)
        d.set_text_size(_LABEL_TEXT_SIZE)
        d.set_text_color(d.WHITE)
        d.set_cursor(_MARGIN, _FOOTER_Y)
        d.print(text)

    def show_message(self, lines):
        """Simple status screen (e.g. config-mode instructions). Wraps and
        clips (with a trailing "...") to the panel via the driver's own
        draw_text_box, rather than a fixed per-line pixel step.
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
            _PANEL_HEIGHT - _MARGIN,
            text,
            line_height=_font.height() * _LABEL_TEXT_SIZE + 8,
            text_size=_LABEL_TEXT_SIZE,
        )
        self._display()
