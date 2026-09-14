"""Minimal captive-portal config UI: a DNS server that answers every query
with the AP's own IP, plus a tiny HTTP server serving a config form and
handling its POST. No frameworks -- just `socket`, since MicroPython doesn't
ship one and this needs to run on the AP interface only.
"""

import socket

_FORM_HTML = """<!doctype html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>TOTP Inkplate setup</title></head>
<body style="font-family: sans-serif; max-width: 400px; margin: 2em auto;">
<h3>TOTP Inkplate setup</h3>
<form method="POST" action="/save">
  <label>WiFi SSID<br><input name="ssid" required></label><br><br>
  <label>WiFi password<br><input name="password" type="password"></label><br><br>
  <label>Account name<br><input name="account_name" value="TOTP"></label><br><br>
  <label>Base32 TOTP seed<br><input name="seed" required></label><br><br>
  <input type="submit" value="Save">
</form>
</body></html>
"""


def _urldecode(s):
    s = s.replace("+", " ")
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "%" and i + 2 < len(s):
            try:
                out.append(chr(int(s[i + 1 : i + 3], 16)))
                i += 3
                continue
            except ValueError:
                pass
        out.append(c)
        i += 1
    return "".join(out)


def _parse_form(body):
    fields = {}
    try:
        text = body.decode()
    except UnicodeError:
        return fields
    for pair in text.split("&"):
        if "=" not in pair:
            continue
        key, _, value = pair.partition("=")
        fields[_urldecode(key)] = _urldecode(value)
    return fields


def _dns_response(query, ip):
    """Build a minimal DNS A-record response pointing every query at `ip`."""
    transaction_id = query[:2]
    flags = b"\x81\x80"
    qdcount = query[4:6]
    ancount = b"\x00\x01"
    nscount = b"\x00\x00"
    arcount = b"\x00\x00"
    header = transaction_id + flags + qdcount + ancount + nscount + arcount

    qname_end = query.index(b"\x00", 12)
    question = query[12 : qname_end + 5]  # QNAME + QTYPE(2) + QCLASS(2)

    answer = (
        b"\xc0\x0c"  # name: pointer to offset 12 (the question's QNAME)
        + b"\x00\x01"  # TYPE A
        + b"\x00\x01"  # CLASS IN
        + b"\x00\x00\x00\x3c"  # TTL 60s
        + b"\x00\x04"  # RDLENGTH
        + bytes(int(p) for p in ip.split("."))
    )
    return header + question + answer


class _DnsRedirector:
    def __init__(self, ip):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setblocking(False)
        self._sock.bind(("0.0.0.0", 53))
        self._ip = ip

    def poll(self):
        try:
            query, addr = self._sock.recvfrom(512)
        except OSError:
            return
        try:
            self._sock.sendto(_dns_response(query, self._ip), addr)
        except Exception:
            pass

    def close(self):
        self._sock.close()


class _ConfigHttpServer:
    def __init__(self, port=80):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("0.0.0.0", port))
        self._sock.listen(2)
        self._sock.setblocking(False)
        self.result = None

    def poll(self):
        try:
            conn, _addr = self._sock.accept()
        except OSError:
            return
        conn.settimeout(3)
        try:
            self._handle(conn)
        except Exception:
            pass
        finally:
            conn.close()

    def _handle(self, conn):
        request = b""
        while b"\r\n\r\n" not in request:
            chunk = conn.recv(512)
            if not chunk:
                break
            request += chunk
        if not request:
            return

        request_line = request.split(b"\r\n", 1)[0].decode()
        method = request_line.split(" ", 1)[0]

        if method == "POST":
            header, _, rest = request.partition(b"\r\n\r\n")
            content_length = 0
            for h in header.split(b"\r\n"):
                if h.lower().startswith(b"content-length:"):
                    content_length = int(h.split(b":", 1)[1].strip())
            body = rest
            while len(body) < content_length:
                chunk = conn.recv(512)
                if not chunk:
                    break
                body += chunk

            fields = _parse_form(body)
            if fields.get("ssid") and fields.get("seed"):
                self.result = {
                    "ssid": fields.get("ssid", ""),
                    "password": fields.get("password", ""),
                    "seed": fields.get("seed", ""),
                    "account_name": fields.get("account_name") or "TOTP",
                }
                conn.send(
                    b"HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n"
                    b"<h3>Saved. Rebooting...</h3>"
                )
            else:
                conn.send(b"HTTP/1.0 400 Bad Request\r\n\r\nMissing ssid/seed")
            return

        # GET (or any captive-portal probe path) -> serve the form.
        body = _FORM_HTML.encode()
        conn.send(
            (
                "HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nContent-Length: %d\r\n\r\n"
                % len(body)
            ).encode()
        )
        conn.send(body)

    def close(self):
        self._sock.close()


class CaptivePortal:
    """Owns both the DNS redirector and the HTTP form server. `result` is
    set to the submitted config dict once the form has been POSTed.
    """

    def __init__(self, ip="192.168.4.1"):
        self._dns = _DnsRedirector(ip)
        self._http = _ConfigHttpServer()
        self.result = None

    def poll(self):
        self._dns.poll()
        self._http.poll()
        if self._http.result and not self.result:
            self.result = self._http.result

    def close(self):
        self._dns.close()
        self._http.close()
