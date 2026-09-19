"""Normal mode: continuously rotates the displayed TOTP code every 30s.

No radios except a periodic, brief WiFi STA connection to re-sync NTP (no
BLE, no AP here). Originally written for an Inkplate 2 (full-refresh-only,
~17-19s per update -- continuous 30s rotation was a hard trade-off there).
Ported to run on an Inkplate 10, which supports real partial refresh
(~0.6s typical per Soldered's spec, full refresh ~1.6s) -- the same
30s-rotation model works much better here since the refresh is no longer
most of the cycle. See display.py for the full/partial refresh handling.
"""

import time

import config_store
import display as display_mod
import ntp_sync
import timezone
import totp
import wifi_manager

# NOT YET MEASURED on this board -- set from Soldered's documented spec
# (full refresh ~1.6s, partial ~0.6s) plus a healthy margin for the
# ~1-in-10 cycles that are a full refresh (see display.py's _display()).
# Watch display.py's DEBUG timing output on real hardware and tighten
# this the same way it was tuned for the Inkplate 2 (was 22s -> 19s after
# real measurements came in). The code shown is computed for the window
# that will be current when the draw finishes, not the window at draw
# *start* -- see README/plan for why a naive "code for right now" would
# often be stale by the time it's readable.
DRAW_LATENCY_S = 3

NTP_RESYNC_INTERVAL_S = 900
WIFI_TIMEOUT_S = 20
NTP_TIMEOUT_S = 5

# Most embedded MicroPython ports (this esp32 build included) count
# time.time() from 2000-01-01, not the Unix epoch (1970-01-01) that RFC 6238
# TOTP is defined against. Getting this wrong produces a completely
# different (wrong) HOTP counter -- every generated code is wrong, not just
# occasionally off -- which is exactly the bug this constant fixes. See
# _unix_time()/_to_device_time() below; verified independently via
# `python3 -c "import calendar; print(calendar.timegm((2000,1,1,0,0,0,0,0,0)))"`.
_UNIX_EPOCH_OFFSET = 946684800

DEBUG = True


def _unix_time():
    """True Unix-epoch seconds -- what TOTP math must use."""
    return time.time() + _UNIX_EPOCH_OFFSET


def _to_device_time(unix_time):
    """Inverse of _unix_time() -- what this board's time.localtime() (and
    hence anything printed via it) expects.
    """
    return unix_time - _UNIX_EPOCH_OFFSET


def _sync_time(cfg):
    connected = wifi_manager.connect_sta(
        cfg["ssid"], cfg["password"], timeout_s=WIFI_TIMEOUT_S
    )
    synced = ntp_sync.sync(timeout_s=NTP_TIMEOUT_S) if connected else False
    wifi_manager.disconnect_sta()
    if DEBUG:
        y, m, d, hh, mm, ss = timezone.unix_to_ymdhms(_unix_time())
        print(
            "[debug] wifi_connected=%s ntp_synced=%s utc_now=%04d-%02d-%02d %02d:%02d:%02d"
            % (connected, synced, y, m, d, hh, mm, ss)
        )
    return synced


def run():
    cfg = config_store.load()
    account_name = cfg["account_name"]
    seed = cfg["seed"]
    show_labels = cfg["show_labels"]
    tz_offset_hours = cfg["tz_offset_hours"]
    tz_dst = cfg["tz_dst"]

    if DEBUG:
        # %s, not %r -- not all MicroPython builds implement every str
        # formatting/method feature CPython does (str.zfill() didn't exist
        # on this board's build either; see git history).
        print("[debug] account_name=%s" % account_name)
        print("[debug] seed (base32)=%s" % seed)
        print(
            "[debug] show_labels=%s tz_offset_hours=%s tz_dst=%s"
            % (show_labels, tz_offset_hours, tz_dst)
        )

    disp = display_mod.Display()

    time_synced = _sync_time(cfg)
    last_sync = time.time()

    while True:
        if time.time() - last_sync > NTP_RESYNC_INTERVAL_S:
            time_synced = _sync_time(cfg) or time_synced
            last_sync = time.time()

        now = _unix_time()
        target = now + DRAW_LATENCY_S
        window = totp.current_window(target)
        code = totp.generate(seed, window)
        window_end = totp.window_end(window)
        valid_until = timezone.format_local(window_end, tz_offset_hours, tz_dst)
        now_str = timezone.format_local(now, tz_offset_hours, tz_dst)

        if DEBUG:
            y, m, d, hh, mm, ss = timezone.unix_to_ymdhms(now)
            print(
                "[debug] unix_now=%d utc=%04d-%02d-%02d %02d:%02d:%02d window=%d "
                "code=%s valid_until=%s synced=%s"
                % (now, y, m, d, hh, mm, ss, window, code, valid_until, time_synced)
            )

        disp.show_code(
            account_name,
            code,
            valid_until,
            now_str=now_str,
            time_synced=time_synced,
            show_labels=show_labels,
        )

        sleep_s = window_end - _unix_time()
        if sleep_s > 0:
            time.sleep(sleep_s)
