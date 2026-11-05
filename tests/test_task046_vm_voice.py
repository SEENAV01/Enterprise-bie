"""The one-time voice upload page (Navin, 5 November 2026: "Ek-baar ka upload page"; tools/vm_voice.py).

Offline: the page runs on 127.0.0.1 in a thread; one test also runs it over HTTPS with a certificate made by the
system's openssl (skipped where openssl is missing).
"""
from __future__ import annotations

import contextlib
import http.client
import io
import os
import shutil
import ssl
import stat
import struct
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import vm_voice  # noqa: E402

SECRET = "s3cret-link-for-this-run-only-xyz"


def wav(seconds: float = 1.0, rate: int = 16000) -> bytes:
    frames = int(seconds * rate)
    data = b"\x00\x00" * frames
    return (b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVE" + b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate,
            rate * 2, 2, 16) + b"data" + struct.pack("<I", len(data)) + data)


class Page:
    """The page on a free local port, served in a thread until it closes."""

    def __init__(self, folder: Path, *, seconds: float = 30, use_tls: bool = False, **kw):
        self.server = vm_voice.Upload(("127.0.0.1", 0), folder=folder, secret=SECRET, say=lambda *_: None, **kw)
        self.port = self.server.server_address[1]
        self.tls = self.tmp = None
        if use_tls:
            self.tmp = tempfile.TemporaryDirectory()
            cert, key, self.finger = vm_voice.certificate(Path(self.tmp.name), "127.0.0.1")
            vm_voice.tls(self.server, cert, key)
            self.tls = ssl._create_unverified_context()    # the test trusts the run's own certificate
        self.result = None
        self.thread = threading.Thread(target=self._run, args=(seconds,), daemon=True)
        self.thread.start()

    def _run(self, seconds):
        self.result = vm_voice.run(self.server, seconds)

    def ask(self, method: str, path: str, body: bytes | None = None, headers=None):
        if self.tls:
            conn = http.client.HTTPSConnection("127.0.0.1", self.port, timeout=10, context=self.tls)
        else:
            conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            r = conn.getresponse()
            return r.status, r.read().decode("utf-8"), dict(r.getheaders())
        finally:
            conn.close()

    def send(self, data: bytes, path: str = "/" + SECRET):
        return self.ask("POST", path, data, {"X-Bie-Voice": "1", "Content-Type": "application/octet-stream"})

    def wait(self):
        self.thread.join(15)
        if self.tmp is not None:
            self.tmp.cleanup()
        return self.result


class OnePage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name) / "voice"

    def tearDown(self):
        self.tmp.cleanup()

    def test_only_the_secret_address_answers(self):
        page = Page(self.folder)
        try:
            for path in ("/", "/index.html", "/" + SECRET[:-1], "/" + SECRET + "x", "/../etc/passwd"):
                status, body, _ = page.ask("GET", path)
                self.assertEqual((status, body), (404, ""), path)
            status, body, headers = page.ask("GET", "/" + SECRET)
            self.assertEqual(status, 200)
            self.assertIn("ek baar", body)
            self.assertIn("no-store", headers["Cache-Control"])
            self.assertIn("default-src 'none'", headers["Content-Security-Policy"])
            self.assertNotIn("http://", body)
            self.assertNotIn("https://", body)            # no outside resource in the page
        finally:
            page.server.shutdown()
            page.wait()
        self.assertFalse(self.folder.exists() and any(self.folder.iterdir()))

    def test_a_wrong_or_too_big_file_is_refused_and_the_page_stays_open(self):
        page = Page(self.folder, max_bytes=200_000)
        try:
            self.assertEqual(page.send(b"<html>" + b"x" * 20000)[0], 415)
            self.assertEqual(page.send(wav(0.1))[0], 400)                  # too short to be a clip
            self.assertEqual(page.send(wav(10.0))[0], 413)
            self.assertEqual(page.ask("POST", "/" + SECRET, wav(1.0))[0], 400)     # not from the page
            self.assertEqual(page.send(wav(1.0), "/elsewhere")[0], 404)
            status, body, _ = page.send(wav(1.0))
            self.assertEqual(status, 200, body)
        finally:
            result = page.wait()
        self.assertEqual(result["saved"]["file"], "navin_ref.wav")

    def test_one_clip_is_kept_privately_and_the_page_closes(self):
        page = Page(self.folder)
        status, body, _ = page.send(wav(1.0))
        self.assertEqual(status, 200, body)
        self.assertIn("band", body)
        result = page.wait()
        self.assertFalse(page.thread.is_alive())
        clip = self.folder / "navin_ref.wav"
        self.assertEqual(clip.read_bytes(), wav(1.0))
        self.assertEqual(stat.S_IMODE(clip.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.folder.stat().st_mode) & 0o077, 0)
        self.assertEqual(result["saved"]["bytes"], len(wav(1.0)))
        with self.assertRaises(OSError):
            Page.ask(page, "GET", "/" + SECRET)

    def test_it_closes_by_itself_when_nothing_comes(self):
        page = Page(self.folder, seconds=0.6)
        result = page.wait()
        self.assertIsNone(result["saved"])
        self.assertLess(result["open_s"], 10)

    def test_a_clip_already_there_is_never_overwritten_without_replace(self):
        self.folder.mkdir(mode=0o700)
        (self.folder / "navin_ref.m4a").write_bytes(b"old")
        said = io.StringIO()
        with contextlib.redirect_stdout(said):
            self.assertEqual(vm_voice.upload(["--folder", str(self.folder), "--minutes", "1"]), 2)
        self.assertIn("--replace", said.getvalue())
        page = Page(self.folder)
        try:
            self.assertEqual(page.send(wav(1.0))[0], 409)
        finally:
            page.server.shutdown()
            page.wait()
        self.assertEqual((self.folder / "navin_ref.m4a").read_bytes(), b"old")
        page = Page(self.folder, replace=True)
        self.assertEqual(page.send(wav(1.0))[0], 200)
        page.wait()
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()), ["navin_ref.wav"])

    @unittest.skipUnless(shutil.which("openssl"), "openssl not installed")
    def test_over_https_with_the_runs_own_certificate(self):
        page = Page(self.folder, use_tls=True)
        self.assertEqual(len(page.finger), 64)
        status, body, _ = page.ask("GET", "/" + SECRET)
        self.assertEqual(status, 200)
        self.assertEqual(page.send(wav(1.0))[0], 200)
        page.wait()
        self.assertTrue((self.folder / "navin_ref.wav").is_file())


class Kinds(unittest.TestCase):
    def test_audio_kinds_by_their_first_bytes(self):
        self.assertEqual(vm_voice.kind_of(wav(0.01)[:16]), ".wav")
        self.assertEqual(vm_voice.kind_of(b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00"), ".m4a")
        self.assertEqual(vm_voice.kind_of(b"ID3\x04\x00" + b"\x00" * 11), ".mp3")
        self.assertEqual(vm_voice.kind_of(b"OggS" + b"\x00" * 12), ".ogg")
        self.assertEqual(vm_voice.kind_of(b"\x1a\x45\xdf\xa3" + b"\x00" * 12), ".webm")
        self.assertEqual(vm_voice.kind_of(b"fLaC" + b"\x00" * 12), ".flac")
        for other in (b"%PDF-1.7", b"<html>", b"\x89PNG\r\n\x1a\n", b"#!/bin/sh\n", b""):
            self.assertIsNone(vm_voice.kind_of(other), other)


class Wrapper(unittest.TestCase):
    def test_the_command_navin_runs_makes_a_private_folder_and_runs_as_bie(self):
        text = (ROOT / "deployment" / "codex-vm" / "bie-voice-upload").read_text(encoding="utf-8")
        self.assertIn('install -d -o bie -g bie -m 700 "$VOICE"', text)
        self.assertIn("runuser -u bie --", text)
        self.assertIn("tools/vm_voice.py\" upload", text)
        self.assertIn('ufw delete allow "$PORT/tcp"', text)
        self.assertTrue(os.access(ROOT / "deployment" / "codex-vm" / "bie-voice-upload", os.X_OK))


if __name__ == "__main__":
    unittest.main()
