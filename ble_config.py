"""Minimal BLE GATT peripheral for config-mode: advertises one write-only
characteristic that accepts a JSON config blob:

    {"ssid": "...", "password": "...", "seed": "BASE32SEED...", "account_name": "..."}

Written from e.g. a phone BLE-scanner app (nRF Connect, LightBlue) targeting
the service/characteristic UUIDs below, or a small companion app built
against them.

NOTE: relies on `bluetooth` (ubluetooth) being present in the flashed
firmware. Research strongly suggests it is (this is plain upstream
MicroPython for the esp32 port with `CONFIG_BT_ENABLED`), but this was not
confirmed by running code on real hardware -- verify with `import bluetooth`
before depending on this module. See README.
"""

import json

import bluetooth
from micropython import const

_IRQ_GATTS_WRITE = const(3)

_FLAG_WRITE = const(0x0008)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)

# Arbitrary, project-specific UUIDs (not a registered/reserved range).
CONFIG_SERVICE_UUID = "b3d10001-0d51-4d6b-8f9a-9e6b2a0f1a01"
CONFIG_CHAR_UUID = "b3d10002-0d51-4d6b-8f9a-9e6b2a0f1a01"

_CONFIG_CHAR = (
    bluetooth.UUID(CONFIG_CHAR_UUID),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_CONFIG_SERVICE = (bluetooth.UUID(CONFIG_SERVICE_UUID), (_CONFIG_CHAR,))


class BLEConfigServer:
    def __init__(self, name="TOTP-Inkplate"):
        self.result = None
        self._buf = bytearray()

        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._config_handle,),) = self._ble.gatts_register_services(
            (_CONFIG_SERVICE,)
        )
        self._advertise(name)

    def _advertise(self, name):
        name_bytes = name.encode()
        adv = bytearray((2, 0x01, 0x06))  # flags: general discoverable, no BR/EDR
        adv += bytearray((len(name_bytes) + 1, 0x09)) + name_bytes  # complete name
        self._ble.gap_advertise(100000, adv_data=adv)

    def _irq(self, event, data):
        if event != _IRQ_GATTS_WRITE:
            return
        _conn_handle, value_handle = data
        if value_handle != self._config_handle:
            return

        self._buf += self._ble.gatts_read(self._config_handle)
        try:
            cfg = json.loads(self._buf.decode())
        except (ValueError, UnicodeError):
            return  # not a complete/valid JSON payload yet

        if isinstance(cfg, dict) and cfg.get("ssid") and cfg.get("seed"):
            self.result = {
                "ssid": cfg.get("ssid", ""),
                "password": cfg.get("password", ""),
                "seed": cfg.get("seed", ""),
                "account_name": cfg.get("account_name") or "TOTP",
            }

    def poll(self):
        return self.result

    def stop(self):
        try:
            self._ble.gap_advertise(None)
        finally:
            self._ble.active(False)
