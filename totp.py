"""Base32 decoding and TOTP (RFC 6238) / HOTP (RFC 4226) code generation.

Pure Python, no `machine`/`network` imports, so this module runs unmodified
under both MicroPython (on-device) and CPython (for `tests/test_totp.py`).

MicroPython's `hashlib` provides `sha1` but there is no `hmac` module, so
HMAC-SHA1 is implemented here directly (RFC 2104).
"""

import hashlib
import struct

_B32_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
_B32_LOOKUP = {c: i for i, c in enumerate(_B32_ALPHABET)}

_HMAC_BLOCK_SIZE = 64  # SHA-1's block size, in bytes


def b32decode(s):
    """Decode an RFC 4648 base32 string. Padding ('=') is optional."""
    s = "".join(s.split()).upper()
    s = s.rstrip("=")

    bits = 0
    value = 0
    out = bytearray()
    for ch in s:
        if ch not in _B32_LOOKUP:
            raise ValueError("invalid base32 character: %r" % ch)
        value = (value << 5) | _B32_LOOKUP[ch]
        bits += 5
        if bits >= 8:
            bits -= 8
            out.append((value >> bits) & 0xFF)
    return bytes(out)


def hmac_sha1(key, msg):
    """HMAC-SHA1(key, msg) -> 20-byte digest."""
    if len(key) > _HMAC_BLOCK_SIZE:
        key = hashlib.sha1(key).digest()
    key = key + b"\x00" * (_HMAC_BLOCK_SIZE - len(key))

    o_key_pad = bytes(b ^ 0x5C for b in key)
    i_key_pad = bytes(b ^ 0x36 for b in key)

    inner = hashlib.sha1(i_key_pad + msg).digest()
    return hashlib.sha1(o_key_pad + inner).digest()


def hotp(secret, counter, digits=6):
    """HOTP(secret, counter) per RFC 4226. `secret` is raw bytes."""
    msg = struct.pack(">Q", counter)
    h = hmac_sha1(secret, msg)

    offset = h[-1] & 0x0F
    code_int = (
        ((h[offset] & 0x7F) << 24)
        | ((h[offset + 1] & 0xFF) << 16)
        | ((h[offset + 2] & 0xFF) << 8)
        | (h[offset + 3] & 0xFF)
    )
    code = code_int % (10 ** digits)
    # str.zfill() isn't implemented in all MicroPython builds -- plain
    # %-formatting is universally supported, so use that instead.
    return ("%0" + str(digits) + "d") % code


def current_window(unix_time, step=30):
    return int(unix_time) // step


def generate(secret_b32, window, digits=6):
    """TOTP code for a given time-step `window` (see `current_window`)."""
    secret = b32decode(secret_b32)
    return hotp(secret, window, digits)


def window_end(window, step=30):
    """Unix time at which `window` expires (i.e. the next window begins)."""
    return (window + 1) * step
