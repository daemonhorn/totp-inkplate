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

# Fields the setup UI (BLE/captive portal) doesn't ask for, but that can be
# set by hand-editing config.json on the device (see install.md). Defaults
# below apply both to a freshly-saved config and to reading an older
# config.json that predates one of these settings.
OPTIONAL_DEFAULTS = {
    "account_name": "TOTP",
    "show_labels": False,  # account name + "valid until" line; off by
    # default since drawing them costs extra text_size changes and pushes
    # the on-device full-refresh time up further on an already-slow panel.
    "tz_offset_hours": -5,  # US Eastern Standard Time baseline
    "tz_dst": True,  # auto-adjust for US daylight saving on top of the above
}


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
    for key, default in OPTIONAL_DEFAULTS.items():
        cfg.setdefault(key, default)
    return cfg


def validate(cfg):
    missing = [f for f in REQUIRED_FIELDS if not cfg.get(f)]
    if missing:
        raise ConfigError("missing required config field(s): %s" % ", ".join(missing))


def save(cfg):
    """Write `cfg`'s required fields, plus any of OPTIONAL_DEFAULTS it
    supplies. Merges onto the existing config.json (if any) first, so
    hand-set optional fields (show_labels, tz_*) survive a WiFi/seed
    reconfigure through the setup UI, which never sends them.
    """
    validate(cfg)

    merged = {}
    if exists():
        try:
            with open(CONFIG_PATH) as f:
                merged = json.load(f)
        except (OSError, ValueError):
            merged = {}

    merged["ssid"] = cfg["ssid"]
    merged["password"] = cfg["password"]
    merged["seed"] = cfg["seed"]
    for key, default in OPTIONAL_DEFAULTS.items():
        merged[key] = cfg[key] if key in cfg else merged.get(key, default)

    tmp_path = CONFIG_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(merged, f)
    os.rename(tmp_path, CONFIG_PATH)
    return merged
