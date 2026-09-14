"""Best-effort NTP time sync with a small fallback server list.

Must be called while WiFi STA is connected. Sets the device RTC on success.
"""

import ntptime

_SERVERS = (
    "pool.ntp.org",
    "time.google.com",
    "time.cloudflare.com",
)


def sync(timeout_s=5):
    """Try each server in turn. Returns True on the first success."""
    ntptime.timeout = timeout_s
    for host in _SERVERS:
        ntptime.host = host
        try:
            ntptime.settime()
            return True
        except OSError:
            continue
    return False
