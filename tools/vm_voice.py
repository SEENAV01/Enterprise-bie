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

``speak`` (the VM job section "voice", tools/codex_vm.py) speaks a video's narration sentences with Chatterbox
Multilingual on this machine's CPU (Rs 0): the built-in voice, or Navin's clip with pitch -2 semitones (agreement of
3 November 2026, section 5). The first run makes the voice environment ``$BIE_HOME/voice-venv`` with the pinned
versions below; ``tools/vm_voice_worker.py`` runs inside it. The audio goes only to the private folder
(``$BIE_HOME/private/voice/<job id>/``, mode 700); the public run folder gets numbers only: seconds of audio and of
compute per sentence, the totals and ``durations.json`` (sentence key -> seconds, the shape ``narration.Timeline`` takes).
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
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

ROOT = Path(__file__).resolve().parents[1]

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


# The voice environment (licences checked 5 November 2026; every one allows BIE's use on its own machine):
# chatterbox-tts 0.1.7 (MIT, Resemble AI), its model ResembleAI/chatterbox at a fixed revision (MIT), torch and torchaudio
# 2.6.0 CPU builds (BSD-3), av 18.0.0 (PyAV, BSD-3, its wheel carries LGPL FFmpeg libraries) to read an m4a clip. Their
# own dependencies (transformers, diffusers, librosa, s3tokenizer, resemble-perth ...) are Apache-2.0, MIT, BSD or ISC;
# pykakasi (GPL-3.0, Japanese only) is installed with chatterbox but never shipped in apps/. Move a pin only in a PR.
PINS = ("torch==2.6.0+cpu", "torchaudio==2.6.0+cpu", "chatterbox-tts==0.1.7", "av==18.0.0")
TORCH_INDEX = "https://download.pytorch.org/whl/cpu"
MODEL_REVISION = "5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18"     # ResembleAI/chatterbox on Hugging Face, 10 June 2026
NAVIN_PITCH = -2.0                                               # agreement of 3 November 2026, section 5
WORKER_TIMEOUT = 4 * 3600


def bie_home() -> Path:
    return Path(os.environ.get("BIE_HOME") or "/var/lib/bie")


def read(source: str) -> str:
    if source.startswith("https://"):
        import urllib.request
        with urllib.request.urlopen(urllib.request.Request(source, headers={"user-agent": "bie-voice/1"}), timeout=120) as r:
            return r.read(50 * 1024 * 1024).decode("utf-8")
    return Path(source).read_text(encoding="utf-8")


def sentences_of(from_run: str, video_id: str) -> tuple[list, int]:
    """The video's spoken sentences in narration order, keyed "<line>_<i>" as ``narration.Timeline`` keys real
    durations, each as the voice says it (``hinglish.voice_text``: "सतह (surface)" is said "सतह, यानी surface"); and the
    characters of the whole video."""
    sys.path.insert(0, str(ROOT))
    from bie.brain import formats, hinglish
    from bie.brain.video import narration
    base = from_run.rstrip("/") + "/"
    lesson = formats.accept("lesson_plan", json.loads(read(base + "lesson_plan.json")), where=base + "lesson_plan.json")
    videos = [v for v in lesson.get("videos") or [] if v.get("video_id") == video_id]
    if not videos:
        raise SystemExit(f"VIDEO_NOT_IN_LESSON: {video_id}")
    out = []
    for scene in narration.script_of(videos[0]):
        for line in scene["lines"]:
            for i, part in enumerate(line["say_parts"]):
                out.append({"key": f"{line['id']}_{i}", "text": hinglish.voice_text(part)})
    return out, sum(len(x["text"]) for x in out)


def ensure_venv(venv: Path, run=subprocess.run) -> dict:
    """The voice environment with exactly ``PINS``; made once (several minutes), then reused while the pins stay."""
    marker = venv / ".bie-pins"
    want = json.dumps({"pins": PINS, "index": TORCH_INDEX})
    if marker.exists() and marker.read_text(encoding="utf-8") == want and (venv / "bin" / "python").exists():
        return {"installed": False, "install_s": 0.0}
    t0 = time.monotonic()
    shutil.rmtree(venv, ignore_errors=True)
    py = str(venv / "bin" / "python")
    for cmd in ([sys.executable, "-m", "venv", str(venv)],
                [py, "-m", "pip", "install", "-q", "--upgrade", "pip"],
                [py, "-m", "pip", "install", "-q", "--extra-index-url", TORCH_INDEX, *PINS[:2]],
                [py, "-m", "pip", "install", "-q", *PINS[2:]]):
        run(cmd, check=True, timeout=3600)
    marker.write_text(want, encoding="utf-8")
    return {"installed": True, "install_s": round(time.monotonic() - t0, 1)}


def machine() -> dict:
    ram = None
    try:
        for row in Path("/proc/meminfo").read_text().splitlines():
            if row.startswith("MemTotal:"):
                ram = round(int(row.split()[1]) / 1024 / 1024, 1)
    except OSError:
        pass
    return {"cpus": os.cpu_count(), "ram_gb": ram}


def summarize(result: dict, *, video: str, reference: str, sentences: list, video_chars: int, setup: dict) -> dict:
    rows = result.get("sentences") or []
    audio = sum(r["audio_s"] for r in rows)
    compute = sum(r["compute_s"] for r in rows)
    chars = sum(r["chars"] for r in rows)
    totals = {"sentences_asked": len(sentences), "sentences_made": len(rows), "audio_s": round(audio, 1),
              "compute_s": round(compute, 1), "rtf": round(compute / audio, 2) if audio else None,
              "chars_per_audio_s": round(chars / audio, 1) if audio else None}
    if audio and chars:
        # the whole video at the same speed: its characters at the measured speaking rate, times the compute factor
        whole_audio = video_chars / (chars / audio)
        totals.update(video_chars=video_chars, video_audio_min_est=round(whole_audio / 60, 1),
                      video_compute_min_est=round(whole_audio * compute / audio / 60, 1))
    return {"section": "voice", "status": "ok" if result.get("status") == "ok" and rows else "failed",
            "video": video, "reference": reference, "error": result.get("error"),
            "engine": {"pins": list(PINS), "model": "ResembleAI/chatterbox", "model_revision": MODEL_REVISION,
                       "torch": result.get("torch"), "threads": result.get("threads"), "sample_rate": result.get("sample_rate"),
                       "watermark": "Perth (Chatterbox's own, inaudible)"},
            "machine": machine(), "setup": setup,
            "timing_s": {k: result.get(k) for k in ("download_s", "load_s", "reference_s")},
            "peak_ram_mb": result.get("peak_ram_mb"), "totals": totals, "sentences": rows,
            "cost": {"total_inr": 0, "note": "CPU of Navin's own machine"},
            "audio": "kept on the machine only (private folder); never published"}


def speak(argv=None) -> int:
    p = argparse.ArgumentParser(prog="vm_voice.py speak")
    p.add_argument("--from-run", required=True, help="a lesson run folder (its lesson_plan.json)")
    p.add_argument("--video", required=True)
    p.add_argument("--out", type=Path, required=True, help="the public run folder: numbers only")
    p.add_argument("--private", type=Path, required=True, help="where the audio is kept (never published)")
    p.add_argument("--max-lines", type=int, default=8, help="speak the first N sentences")
    p.add_argument("--reference", choices=("default", "navin"), default="default")
    p.add_argument("--voice-folder", type=Path, default=Path("/etc/bie/voice"))
    p.add_argument("--venv", type=Path, default=None)
    p.add_argument("--worker", type=Path, default=ROOT / "tools" / "vm_voice_worker.py")
    args = p.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.private.resolve().is_relative_to(args.out.resolve()):
        raise SystemExit("PRIVATE_INSIDE_PUBLIC: the audio folder must not be inside the published run folder")
    args.private.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(args.private, 0o700)
    sentences, video_chars = sentences_of(args.from_run, args.video)
    chosen = sentences[:args.max_lines]
    reference, pitch, kind = None, 0.0, "Chatterbox built-in voice"
    if args.reference == "navin":
        clips = existing(args.voice_folder)
        if not clips:
            summary = {"section": "voice", "status": "failed", "video": args.video, "reference": "Navin's clip",
                       "error": "NO_CLIP: the voice folder holds no clip yet (the one-time upload page puts it there)",
                       "cost": {"total_inr": 0}}
            (args.out / "SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
            return 1
        reference, pitch, kind = str(clips[0]), NAVIN_PITCH, "Navin's clip, pitch -2 semitones"
    venv = args.venv or bie_home() / "voice-venv"
    setup = ensure_venv(venv)
    request = {"sentences": chosen, "language": "hi", "reference": reference, "pitch_semitones": pitch,
               "audio_dir": str(args.private / "audio"), "model_revision": MODEL_REVISION, "threads": os.cpu_count(), "seed": 7}
    req_path, res_path = args.private / "request.json", args.private / "result.json"
    req_path.write_text(json.dumps(request, ensure_ascii=False, indent=1), encoding="utf-8")
    env = dict(os.environ, HF_HOME=str(bie_home() / "voice-models"), HF_HUB_DISABLE_TELEMETRY="1")
    try:
        subprocess.run([str(venv / "bin" / "python"), "-B", str(args.worker), "--request", str(req_path),
                        "--result", str(res_path)], env=env, timeout=WORKER_TIMEOUT, check=False)
    except subprocess.TimeoutExpired:
        pass
    result = json.loads(res_path.read_text(encoding="utf-8")) if res_path.exists() else {"error": "the worker wrote no result"}
    summary = summarize(result, video=args.video, reference=kind, sentences=chosen, video_chars=video_chars, setup=setup)
    (args.out / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (args.out / "durations.json").write_text(json.dumps({r["key"]: r["audio_s"] for r in summary["sentences"]}, indent=1)
                                             + "\n", encoding="utf-8")
    lines = [f"# Voice measure: {args.video} ({kind})", "",
             f"- {summary['totals']['sentences_made']} of {len(chosen)} sentences, {summary['totals']['audio_s']} s of audio "
             f"in {summary['totals']['compute_s']} s of CPU (real-time factor {summary['totals']['rtf']}).",
             f"- Machine: {summary['machine']['cpus']} CPUs, {summary['machine']['ram_gb']} GB; peak RAM "
             f"{summary.get('peak_ram_mb')} MB; model load {summary['timing_s']['load_s']} s.",
             "- The audio stays on the machine; this folder holds numbers only.", "",
             "| sentence | characters | audio s | compute s | factor |", "| --- | --- | --- | --- | --- |"]
    lines += [f"| {r['key']} | {r['chars']} | {r['audio_s']} | {r['compute_s']} | {r['rtf']} |" for r in summary["sentences"]]
    (args.out / "VOICE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], **summary["totals"]}))
    return 0 if summary["status"] == "ok" else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "upload":
        return upload(argv[1:])
    if argv and argv[0] == "speak":
        return speak(argv[1:])
    print("usage: vm_voice.py upload [--folder DIR] [--port N] [--minutes N] [--replace]\n"
          "       vm_voice.py speak --from-run URL --video ID --out DIR --private DIR [--max-lines N] [--reference default|navin]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
