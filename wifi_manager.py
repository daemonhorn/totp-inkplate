"""WiFi STA (for NTP) and AP (for the config-mode captive portal) helpers."""

import time

import network


def connect_sta(ssid, password, timeout_s=20):
    """Connect to `ssid` in station mode. Returns True on success."""
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        sta.connect(ssid, password)
        deadline = time.time() + timeout_s
        while not sta.isconnected() and time.time() < deadline:
            time.sleep_ms(200)
    return sta.isconnected()


def disconnect_sta():
    sta = network.WLAN(network.STA_IF)
    if sta.active():
        sta.disconnect()
        sta.active(False)


def start_ap(ssid, password=None):
    """Start an open (or WPA2-PSK, if `password` given) access point."""
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    if password:
        ap.config(essid=ssid, password=password, authmode=network.AUTH_WPA_WPA2_PSK)
    else:
        ap.config(essid=ssid, authmode=network.AUTH_OPEN)
    return ap


def stop_ap():
    ap = network.WLAN(network.AP_IF)
    if ap.active():
        ap.active(False)
