"""Normal mode: continuously rotates the displayed TOTP code every 30s.

No radios except a periodic, brief WiFi STA connection to re-sync NTP (no
BLE, no AP here). See README for why this board can't do deep sleep +
manual-refresh instead -- it has no buttons, and continuous rotation was the
user's explicit choice once that was known.
"""

import time

import config_store
import display as display_mod
import ntp_sync
import totp
import wifi_manager

# Measured/estimated Inkplate 2 full-refresh duration (3-color panel), plus a
# small margin. The code shown is computed for the window that will be
# current when the draw finishes, not the window at draw *start* -- see
# README/plan for why a naive "code for right now" would often be stale by
# the time it's readable.
DRAW_LATENCY_S = 22

NTP_RESYNC_INTERVAL_S = 900
WIFI_TIMEOUT_S = 20
NTP_TIMEOUT_S = 5


def _sync_time(cfg):
    connected = wifi_manager.connect_sta(
        cfg["ssid"], cfg["password"], timeout_s=WIFI_TIMEOUT_S
    )
    synced = ntp_sync.sync(timeout_s=NTP_TIMEOUT_S) if connected else False
    wifi_manager.disconnect_sta()
    return synced


def _format_utc(unix_time):
    _year, _month, _mday, hh, mm, ss, *_rest = time.localtime(unix_time)
    return "%02d:%02d:%02d UTC" % (hh, mm, ss)


def run():
    cfg = config_store.load()
    account_name = cfg["account_name"]
    seed = cfg["seed"]

    disp = display_mod.Display()

    time_synced = _sync_time(cfg)
    last_sync = time.time()

    while True:
        if time.time() - last_sync > NTP_RESYNC_INTERVAL_S:
            time_synced = _sync_time(cfg) or time_synced
            last_sync = time.time()

        target = time.time() + DRAW_LATENCY_S
        window = totp.current_window(target)
        code = totp.generate(seed, window)
        valid_until = _format_utc(totp.window_end(window))

        disp.show_code(account_name, code, valid_until, time_synced=time_synced)

        sleep_s = totp.window_end(window) - time.time()
        if sleep_s > 0:
            time.sleep(sleep_s)
