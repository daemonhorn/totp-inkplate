"""Boot entry point.

Decides between config mode and normal mode:
- No `config.json` yet -> config mode (first-ever boot).
- Board's EN/RESET button pressed twice within ~2s -> config mode (this
  board has no other buttons/touch pads to dedicate to "enter setup").
- Otherwise -> normal mode.

The double-reset detector uses `machine.RTC().memory()`, which is documented
to survive `machine.reset()` and deep-sleep wake, and cleared on power loss
-- exactly the "did the user just reset me again on purpose" signal we want.

NOT YET VERIFIED ON HARDWARE: whether RTC memory also survives a reset via
the board's physical EN pin specifically (as opposed to `machine.reset()`),
since EN resets the RTC domain on some ESP32 boards. Test before relying on
this: `machine.RTC().memory(b"DR")`, press EN, then check
`machine.RTC().memory()` on the next boot. If it comes back empty, replace
this with a flash-file marker instead (write a marker file, sleep 2s, delete
it -- a reset inside that window leaves it on disk).
"""

import time

import machine

import config_store

_DOUBLE_RESET_WINDOW_MS = 2000
_MAGIC = b"DR"


def _double_reset_requested():
    rtc = machine.RTC()
    previous = rtc.memory()
    rtc.memory(_MAGIC)

    if previous == _MAGIC:
        rtc.memory(b"")
        return True

    time.sleep_ms(_DOUBLE_RESET_WINDOW_MS)
    if rtc.memory() == _MAGIC:
        rtc.memory(b"")  # no second reset arrived in time
    return False


def main():
    double_reset = _double_reset_requested()

    if double_reset or not config_store.exists():
        import config_mode

        config_mode.run()
    else:
        import normal_mode

        normal_mode.run()


main()
