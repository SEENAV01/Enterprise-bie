"""The studio's narrator voice: Kokoro (kokoro-onnx, MIT; Kokoro-82M weights, Apache-2.0), Hindi voice ``hf_alpha``.

This is the voice Navin heard in the approved Monsoon film (18 November 2026); its known limit (weak aspirated sounds such as
kh and gh) was told to him. The voice stays replaceable: his own cloned voice comes in later through ``bie/audio``.
The model files are fetched once to ``$BIE_HOME/models/kokoro`` (or ``BIE_KOKORO_DIR``). When the library or the files are
missing the studio still makes the film, timed by text length and marked "no voice".
"""
from __future__ import annotations

import base64
import io
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

FILES = {"kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
         "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"}
VOICE, SPEED, LANG = "hf_alpha", 0.95, "hi"
QUESTION_PAUSE = 0.45     # seconds of silence after a question (Navin, 20 November 2026: question and answer sounded alike)


def folder() -> Path:
    return Path(os.environ.get("BIE_KOKORO_DIR") or Path(os.environ.get("BIE_HOME", "/var/lib/bie")) / "models" / "kokoro")


class Voice:
    def __init__(self, path: Path | None = None, *, fetch: bool = True):
        from kokoro_onnx import Kokoro            # optional: ImportError means "no voice"
        path = path or folder()
        path.mkdir(parents=True, exist_ok=True)
        for name, url in FILES.items():
            target = path / name
            if not target.exists():
                if not fetch:
                    raise FileNotFoundError(f"{target} is missing")
                with urllib.request.urlopen(url, timeout=600) as response, tempfile.NamedTemporaryFile(dir=path, delete=False) as tmp:
                    shutil.copyfileobj(response, tmp)
                Path(tmp.name).replace(target)
        self.engine = Kokoro(str(path / "kokoro-v1.0.onnx"), str(path / "voices-v1.0.bin"))

    def say(self, text: str) -> dict:
        """{"uri": data URI (mp3 when ffmpeg is here, else wav), "dur": seconds}. A question is spoken on its own and
        followed by a short silence, so the answer after it sounds like an answer (``parts``)."""
        import numpy as np
        import soundfile as sf
        chunks, rate = [], 24000
        for part, pause in parts(text):
            made, rate = self.engine.create(part, voice=VOICE, speed=SPEED, lang=LANG)
            chunks.append(np.asarray(made, dtype="float32"))
            if pause:
                chunks.append(np.zeros(int(rate * pause), dtype="float32"))
        samples = np.concatenate(chunks) if chunks else np.zeros(1, dtype="float32")
        buffer = io.BytesIO()
        sf.write(buffer, np.asarray(samples, dtype="float32"), rate, format="WAV")
        wav = buffer.getvalue()
        mp3 = to_mp3(wav)
        data, mime = (mp3, "audio/mpeg") if mp3 else (wav, "audio/wav")
        return {"uri": f"data:{mime};base64," + base64.b64encode(data).decode("ascii"), "dur": round(len(samples) / rate, 3)}


def parts(text: str) -> list:
    """The pieces a line is spoken in: each question on its own, with QUESTION_PAUSE seconds after it, then the rest.
    "Band membrane kyun chahiye? Iska seedha sa jawab hai ..." -> [("Band membrane kyun chahiye?", 0.45),
    ("Iska seedha sa jawab hai ...", 0.0)]."""
    pieces = [p.strip() for p in re.split(r"(?<=\?)\s*", (text or "").strip()) if p.strip()]
    return [(p, QUESTION_PAUSE if p.endswith("?") else 0.0) for p in pieces] or [((text or "").strip() or ".", 0.0)]


def to_mp3(wav: bytes) -> bytes | None:
    if not shutil.which("ffmpeg"):
        return None
    done = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-b:a", "48k", "-f", "mp3", "pipe:1"],
                          input=wav, capture_output=True, timeout=120)
    return done.stdout if done.returncode == 0 and done.stdout else None


PLAYER_JS = Path(__file__).with_name("studio_voice_player.js")
VOICE_SLOT = "/*__VOICE__*/"


def with_player_voice(page: str) -> str:
    """The page with BIE's voice script (``studio_voice_player.js``) in its slot: the audio element with a data: URI first,
    Web Audio when the viewer refuses media loads, and a visible notice when neither can sound (Navin, 20 November 2026:
    the first films played silently)."""
    return page.replace(VOICE_SLOT, PLAYER_JS.read_text(encoding="utf-8"), 1)


def make(fetch: bool = True):
    """A Voice, or None with the reason when this machine cannot speak yet."""
    try:
        return Voice(fetch=fetch), None
    except Exception as exc:              # missing library, files or network: the film is still made, without voice
        return None, f"{type(exc).__name__}: {str(exc)[:200]}"
