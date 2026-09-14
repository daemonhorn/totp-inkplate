"""Unit tests for totp.py. Runs under plain CPython (or the MicroPython unix
port) -- no Inkplate hardware needed.

The 6-digit expected values below were generated independently with Python's
stdlib `hmac`/`hashlib` (not by reusing totp.py's own HMAC implementation) at
the timestamps from RFC 6238's SHA1 test vector table. Note RFC 6238's own
published table lists 8-digit codes -- those are NOT reused here directly.
"""

import base64
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import totp  # noqa: E402

# RFC 6238 SHA1 test seed: the ASCII string "12345678901234567890".
RFC6238_SECRET_B32 = base64.b32encode(b"12345678901234567890").decode()

# (unix_time, expected 6-digit code), independently computed via
# hmac.new(secret, struct.pack(">Q", unix_time // 30), hashlib.sha1).
RFC6238_VECTORS = [
    (59, "287082"),
    (1111111109, "081804"),
    (1111111111, "050471"),
    (1234567890, "005924"),
    (2000000000, "279037"),
    (20000000000, "353130"),
]


class TestBase32Decode(unittest.TestCase):
    def test_known_string(self):
        self.assertEqual(totp.b32decode("NBSWY3DP"), b"hello")

    def test_padding_optional(self):
        # "hello" base32-encodes to "NBSWY3DP" with no padding needed, so use
        # a value that normally requires '=' padding to check both accepted.
        padded = base64.b32encode(b"hi").decode()  # "NBUQ===="
        unpadded = padded.rstrip("=")
        self.assertEqual(totp.b32decode(padded), b"hi")
        self.assertEqual(totp.b32decode(unpadded), b"hi")

    def test_lowercase_and_whitespace_tolerated(self):
        self.assertEqual(totp.b32decode(" nbswy3dp \n"), b"hello")

    def test_invalid_character_raises(self):
        with self.assertRaises(ValueError):
            totp.b32decode("this is not base32!")


class TestHmacSha1(unittest.TestCase):
    def test_matches_stdlib(self):
        import hashlib
        import hmac

        key = b"key"
        msg = b"The quick brown fox jumps over the lazy dog"
        self.assertEqual(
            totp.hmac_sha1(key, msg), hmac.new(key, msg, hashlib.sha1).digest()
        )

    def test_matches_stdlib_long_key(self):
        # Exercises the >64-byte key path (key gets pre-hashed).
        import hashlib
        import hmac

        key = b"x" * 100
        msg = b"message"
        self.assertEqual(
            totp.hmac_sha1(key, msg), hmac.new(key, msg, hashlib.sha1).digest()
        )


class TestTotpRfc6238(unittest.TestCase):
    def test_vectors(self):
        for unix_time, expected in RFC6238_VECTORS:
            window = totp.current_window(unix_time, step=30)
            code = totp.generate(RFC6238_SECRET_B32, window, digits=6)
            self.assertEqual(
                code, expected, "mismatch at t=%d (window=%d)" % (unix_time, window)
            )

    def test_window_end(self):
        self.assertEqual(totp.window_end(0, step=30), 30)
        self.assertEqual(totp.current_window(29, step=30), 0)
        self.assertEqual(totp.current_window(30, step=30), 1)


if __name__ == "__main__":
    unittest.main()
