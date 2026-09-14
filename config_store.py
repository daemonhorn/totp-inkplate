"""Load/save the on-device config (WiFi credentials + TOTP seed) as JSON.

Kept intentionally tiny: this is the one file that touches secrets, so it's
easy to audit. Runs on MicroPython (ujson/uos are aliased to json/os there).
"""

try:
    import ujson as json
except ImportError:
    import json

try:
    import uos as os
except ImportError:
    import os

CONFIG_PATH = "config.json"

REQUIRED_FIELDS = ("ssid", "password", "seed")


class ConfigError(Exception):
    pass


def exists():
    try:
        os.stat(CONFIG_PATH)
        return True
    except OSError:
        return False


def load():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    validate(cfg)
    return cfg


def validate(cfg):
    missing = [f for f in REQUIRED_FIELDS if not cfg.get(f)]
    if missing:
        raise ConfigError("missing required config field(s): %s" % ", ".join(missing))


def save(cfg):
    validate(cfg)
    cfg = {
        "ssid": cfg["ssid"],
        "password": cfg["password"],
        "seed": cfg["seed"],
        "account_name": cfg.get("account_name", "TOTP"),
    }
    tmp_path = CONFIG_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(cfg, f)
    os.rename(tmp_path, CONFIG_PATH)
    return cfg
