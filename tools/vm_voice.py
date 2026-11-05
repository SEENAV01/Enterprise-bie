"""Navin's voice clip on his private machine (P1-D voice; decision cards of 5 November 2026).

Navin's answers: the clip may be kept "sirf VM par private" (docs/roadmap/VOICE_CLIP_METHOD.md), and it reaches the
machine through "Ek-baar ka upload page": a private page on the VM, opened by a secret link, that takes one audio file
and switches itself off. He switches it on himself, from the Hostinger browser terminal:

  sudo bash /var/lib/bie/repo/deployment/codex-vm/bie-voice-upload

which makes the folder and runs, as the ``bie`` user,

  python tools/vm_voice.py upload --folder /etc/bie/voice

What the page does and does not do:

- It listens on one port (8443) over HTTPS with a certificate the machine makes for this one run (the browser warns
  once, because no outside authority signed it; the data is still encrypted on the way). The certificate and its key
  live in a temporary folder that is deleted when the page closes.
- The only address that answers is ``/<secret>``, a random 32-character secret made for this run and printed only in
  Navin's terminal. Every other address gets a bare 404. Nothing about the secret is written to a log.
- It takes one audio file (wav, mp3, m4a/aac, ogg/opus, webm, flac), at most 25 MB, checked by its first bytes, and
  stores it as ``navin_ref.<ext>`` (file mode 600) in the voice folder (mode 700, owner ``bie``). Then it closes.
- It closes by itself after 20 minutes if nothing came. It never overwrites a clip already there unless run with
  ``--replace``.
- It sends nothing anywhere: no copy to GitHub, no log line with the audio, no outside resource in the page.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import ipaddress
import os
import secrets
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8443
MAX_BYTES = 25 * 1024 * 1024
MIN_BYTES = 8 * 1024             # a few seconds of compressed speech at least
OPEN_SECONDS = 20 * 60
CLIP = "navin_ref"
# first bytes of the audio kinds a tablet or phone records or exports
KINDS = (
    (".wav", lambda b: b[:4] == b"RIFF" and b[8:12] == b"WAVE"),
    (".flac", lambda b: b[:4] == b"fLaC"),
    (".ogg", lambda b: b[:4] == b"OggS"),
    (".webm", lambda b: b[:4] == b"\x1a\x45\xdf\xa3"),
    (".m4a", lambda b: b[4:8] == b"ftyp"),
    (".mp3", lambda b: b[:3] == b"ID3" or (len(b) > 1 and b[0] == 0xFF and (b[1] & 0xE0) == 0xE0)),
    (".aac", lambda b: len(b) > 1 and b[0] == 0xFF and (b[1] & 0xF6) == 0xF0),
)


def kind_of(head: bytes) -> str | None:
    """The file extension for these first bytes, or None when they are not a known audio file."""
    for ext, test in KINDS:
        try:
            if test(head):
                return ext
        except IndexError:
            continue
    return None


def existing(folder: Path) -> list:
    return sorted(p for p in folder.glob(CLIP + ".*") if p.is_file()) if folder.is_dir() else []


PAGE = """<!doctype html>
<html lang="hi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>BIE: awaaz ki clip</title>
<style>
:root {{ --bg: #f6f3ee; --fg: #1f1d1a; --muted: #5d5850; --line: #d8d1c6; --accent: #1f6f5c; --bad: #a3322a; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg: #191816; --fg: #efebe4; --muted: #b3ab9f; --line: #3a3732;
  --accent: #5cc2a6; --bad: #f08a80; color-scheme: dark; }} }}
body {{ margin: 0; background: var(--bg); color: var(--fg); font: 18px/1.5 system-ui, sans-serif; }}
main {{ max-width: 34rem; margin: 0 auto; padding: 2rem max(16px, env(safe-area-inset-left, 0px)) 3rem; }}
h1 {{ font-size: 1.5rem; margin: 0 0 .25rem; }}
p, li {{ color: var(--muted); }}
ul {{ padding-left: 1.2rem; }}
.box {{ border: 1px solid var(--line); border-radius: 12px; padding: 1rem; display: grid; gap: .9rem; }}
input[type=file] {{ font: inherit; width: 100%; }}
button {{ font: inherit; font-weight: 600; padding: .7rem 1rem; border-radius: 10px; border: 0; background: var(--accent);
  color: var(--bg); }}
button:disabled {{ opacity: .5; }}
#say {{ min-height: 1.5em; color: var(--fg); }}
#say.bad {{ color: var(--bad); }}
small {{ color: var(--muted); }}
</style></head>
<body><main>
<h1>Awaaz ki clip &mdash; ek baar</h1>
<p>Yeh page sirf aapke liye hai aur ek file lekar band ho jayega.</p>
<ul>
<li>10 se 30 second ki clip, shaant kamre mein, apni normal awaaz mein.</li>
<li>Koi bhi audio file: m4a, mp3, wav, ogg, webm, flac (25 MB tak).</li>
<li>Clip sirf aapki machine par rahegi (<code>/etc/bie/voice</code>), GitHub par kabhi nahi.</li>
</ul>
<div class="box">
<input id="f" type="file" accept="audio/*,.m4a,.mp3,.wav,.ogg,.opus,.webm,.flac,.aac">
<button id="b" disabled>Bhejiye</button>
<div id="say" role="status"></div>
</div>
<p><small>Page {minutes} minute mein khud band ho jayega.</small></p>
</main>
<script>
const f = document.getElementById("f"), b = document.getElementById("b"), say = document.getElementById("say");
f.addEventListener("change", () => {{ b.disabled = !f.files.length; say.textContent = ""; say.className = ""; }});
b.addEventListener("click", async () => {{
  const file = f.files[0]; if (!file) return;
  if (file.size > {max_mb} * 1024 * 1024) {{ say.className = "bad"; say.textContent = "File {max_mb} MB se badi hai: chhoti clip bhejiye."; return; }}
  b.disabled = true; say.className = ""; say.textContent = "Bhej rahe hain…";
  try {{
    const r = await fetch(location.pathname, {{ method: "POST", body: file,
      headers: {{ "Content-Type": "application/octet-stream", "X-Bie-Voice": "1" }} }});
    const t = await r.text();
    say.textContent = t; if (!r.ok) {{ say.className = "bad"; b.disabled = false; }}
    else {{ f.disabled = true; }}
  }} catch (e) {{ say.className = "bad"; say.textContent = "Nahi gaya: " + e; b.disabled = false; }}
}});
</script>
</body></html>
"""


class Upload(ThreadingHTTPServer):
    """The one-time page: answers only ``/<secret>``, keeps one audio file, then stops."""

    daemon_threads = True

    def __init__(self, address, *, folder: Path, secret: str, max_bytes: int = MAX_BYTES, minutes: int = 20,
                 replace: bool = False, say=print):
        super().__init__(address, Handler)
        self.folder, self.secret, self.max_bytes, self.minutes = Path(folder), secret, max_bytes, minutes
        self.replace, self.say = replace, say
        self.lock = threading.Lock()
        self.saved: dict | None = None
        self.refused = 0

    def handle_error(self, request, client_address):
        # a browser that stops at the certificate warning, or a scanner, drops its connection: not worth a traceback
        # in Navin's terminal
        self.refused += 1

    def keep(self, data: bytes) -> tuple[int, str]:
        with self.lock:
            if self.saved is not None:
                return 410, "Clip pehle hi mil chuki hai; yeh page band hai."
            if len(data) < MIN_BYTES:
                return 400, "File bahut chhoti hai: 10 se 30 second ki clip bhejiye."
            ext = kind_of(data[:16])
            if ext is None:
                return 415, "Yeh audio file nahi lagti: m4a, mp3, wav, ogg, webm ya flac bhejiye."
            self.folder.mkdir(mode=0o700, parents=True, exist_ok=True)
            if self.replace:
                for old in existing(self.folder):
                    old.unlink()
            elif existing(self.folder):
                return 409, "Ek clip pehle se rakhi hai; nayi ke liye page --replace ke saath chalaiye."
            path = self.folder / (CLIP + ext)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as out:
                out.write(data)
            os.chmod(path, 0o600)
            self.saved = {"file": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        self.say(f"Mil gaya: {path.name}, {len(data) // 1024} KB, sha256 {self.saved['sha256'][:16]}...")
        threading.Thread(target=self.shutdown, daemon=True).start()
        return 200, f"Shukriya, clip mil gayi ({len(data) // 1024} KB). Yeh page ab band hai."


class Handler(BaseHTTPRequestHandler):
    server: Upload
    timeout = 60                 # a slow or silent visitor cannot hold the page
    server_version = "bie"
    sys_version = ""

    def log_message(self, *args):        # never write paths (the secret) to a log
        return

    def _send(self, code: int, body: str, kind: str = "text/plain; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Robots-Tag", "noindex")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; "
                         "script-src 'unsafe-inline'; connect-src 'self'; form-action 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def _ours(self) -> bool:
        ok = secrets.compare_digest(self.path.split("?", 1)[0].encode(), ("/" + self.server.secret).encode())
        if not ok:
            self.server.refused += 1
            self._send(404, "")
        return ok

    def do_GET(self):
        if self._ours():
            self._send(200, PAGE.format(minutes=self.server.minutes, max_mb=self.server.max_bytes // (1024 * 1024)),
                       "text/html; charset=utf-8")

    def do_POST(self):
        if not self._ours():
            return
        if self.headers.get("X-Bie-Voice") != "1":
            return self._send(400, "Is page se hi bhejiye.")
        try:
            size = int(self.headers.get("Content-Length") or "")
        except ValueError:
            return self._send(411, "File ka size nahi aaya; dobara bhejiye.")
        if size > self.server.max_bytes:
            return self._send(413, f"File {self.server.max_bytes // (1024 * 1024)} MB se badi hai: chhoti clip bhejiye.")
        data = self.rfile.read(size)
        if len(data) != size:
            return self._send(400, "File poori nahi aayi; dobara bhejiye.")
        code, text = self.server.keep(data)
        self._send(code, text)

    def do_HEAD(self):
        self._send(404, "")

    do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_HEAD


def public_ip() -> str:
    """The machine's public IPv4 address as its own network card reports it (Hostinger gives the VM one)."""
    try:
        out = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=5).stdout.split()
    except (OSError, subprocess.SubprocessError):
        out = []
    for word in out:
        try:
            ip = ipaddress.ip_address(word)
        except ValueError:
            continue
        if ip.version == 4 and ip.is_global:
            return word
    for word in out:
        if ":" not in word:
            return word
    return socket.gethostname()


def certificate(folder: Path, name: str) -> tuple[Path, Path, str]:
    """A certificate for this one run (2 days, ECDSA P-256), made with the system's openssl; returns cert, key and
    its SHA-256 fingerprint."""
    cert, key = folder / "cert.pem", folder / "key.pem"
    try:
        ipaddress.ip_address(name)
        alt = f"subjectAltName=IP:{name}"
    except ValueError:
        alt = f"subjectAltName=DNS:{name}"
    subprocess.run(["openssl", "req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes",
                    "-keyout", str(key), "-out", str(cert), "-days", "2", "-subj", "/CN=bie-voice-upload", "-addext", alt],
                   check=True, capture_output=True, timeout=60)
    os.chmod(key, 0o600)
    der = ssl.PEM_cert_to_DER_cert(cert.read_text(encoding="ascii"))
    return cert, key, hashlib.sha256(der).hexdigest()


def tls(server: Upload, cert: Path, key: Path) -> None:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(str(cert), str(key))
    # the handshake runs in each visitor's own thread, so a stuck visitor cannot hold the page
    server.socket = ctx.wrap_socket(server.socket, server_side=True, do_handshake_on_connect=False)


def run(server: Upload, seconds: float) -> dict:
    """Serve until the clip is kept or the time is up; returns what happened."""
    timer = threading.Timer(seconds, server.shutdown)
    timer.daemon = True
    timer.start()
    started = time.monotonic()
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        timer.cancel()
        server.server_close()
    return {"saved": server.saved, "open_s": round(time.monotonic() - started, 1), "refused_requests": server.refused}


def upload(argv=None) -> int:
    p = argparse.ArgumentParser(prog="vm_voice.py upload")
    p.add_argument("--folder", type=Path, default=Path("/etc/bie/voice"))
    p.add_argument("--port", type=int, default=PORT)
    p.add_argument("--minutes", type=int, default=OPEN_SECONDS // 60)
    p.add_argument("--host-name", default="", help="the address printed in the link (default: the machine's public IPv4)")
    p.add_argument("--replace", action="store_true", help="replace a clip that is already there")
    args = p.parse_args(argv)
    if existing(args.folder) and not args.replace:
        print("Ek clip pehle se rakhi hai: " + ", ".join(x.name for x in existing(args.folder)))
        print("Nayi clip daalni ho to isi command ke aakhir mein --replace likhiye.")
        return 2
    if not shutil.which("openssl"):
        print("openssl nahi mila; page nahi khula.")
        return 1
    name = args.host_name or public_ip()
    secret = secrets.token_urlsafe(24)
    with tempfile.TemporaryDirectory(prefix="bie-voice-") as tmp:
        cert, key, finger = certificate(Path(tmp), name)
        server = Upload(("0.0.0.0", args.port), folder=args.folder, secret=secret, minutes=args.minutes,
                        replace=args.replace)
        tls(server, cert, key)
        print()
        print("Upload page khul gaya. Yeh link tablet ke browser mein kholiye (kisi aur ko mat bhejiye):")
        print()
        print(f"   https://{name}:{args.port}/{secret}")
        print()
        print("Browser ek baar 'connection private nahi' jaisi chetavni dikhayega, kyunki certificate is machine ne")
        print("khud banaya hai. 'Advanced' / 'Details' -> 'Proceed' / 'Visit' dabaiye; data phir bhi encrypted jaata hai.")
        print(f"Certificate ka fingerprint (SHA-256): {finger[:32]}...")
        print(f"Page {args.minutes} minute mein ya ek file milte hi band ho jayega. Abhi band karna ho: Ctrl+C")
        print()
        try:
            result = run(server, args.minutes * 60)
        except KeyboardInterrupt:
            server.server_close()
            print("Band kar diya. Koi clip nahi aayi.")
            return 1
    if result["saved"]:
        print("Ho gaya. Clip yahan hai: " + str(args.folder / result["saved"]["file"]))
        return 0
    print("Samay khatam, koi clip nahi aayi. Page band hai; dobara chahiye to wahi command phir chalaiye.")
    return 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] != "upload":
        print("usage: vm_voice.py upload [--folder DIR] [--port N] [--minutes N] [--replace]")
        return 2
    return upload(argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
