"""Config mode: brings up BLE + a WiFi captive portal at the same time (no
onboard button exists on this board to pick one transport over the other),
waits for either to deliver a valid config, saves it, and reboots.

Always ends by resetting the board -- `main.py`'s boot logic decides the
next mode based on whether `config.json` now exists.
"""

import time

import machine

import config_store
import display as display_mod
import wifi_manager
from ble_config import BLEConfigServer
from captive_portal import CaptivePortal

AP_SSID = "TOTP-Inkplate-Setup"
TIMEOUT_S = 600  # give up and reboot after 10 minutes of no config


def run():
    disp = display_mod.Display()
    disp.show_message(
        [
            "Setup mode",
            "",
            "WiFi: join '%s'" % AP_SSID,
            "then open http://192.168.4.1",
            "",
            "-- or --",
            "",
            "Use a BLE app to write JSON",
            "config to the TOTP-Inkplate",
            "service (see README)",
        ]
    )

    wifi_manager.start_ap(AP_SSID)
    portal = CaptivePortal()
    ble = BLEConfigServer(name=AP_SSID)

    result = None
    deadline = time.time() + TIMEOUT_S
    try:
        while time.time() < deadline:
            portal.poll()
            if portal.result:
                result = portal.result
                break
            if ble.poll():
                result = ble.result
                break
            time.sleep_ms(50)
    finally:
        portal.close()
        ble.stop()
        wifi_manager.stop_ap()

    if result:
        config_store.save(result)
        disp.show_message(["Configured!", "Rebooting..."])
    else:
        disp.show_message(["Setup timed out.", "Rebooting..."])

    time.sleep(2)
    machine.reset()
