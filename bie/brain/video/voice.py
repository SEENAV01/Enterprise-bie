"""A placeholder narration for Task 046's benchmark render: eSpeak NG, offline, one WAV per beat and one mixed track.

The real voice is Task 047 (natural voices, word timestamps through ``bie/audio``'s contracts). Here the voice only has to
drive the timing honestly: every beat's spoken seconds come from the real waveform, so ``timing.build(voice=...)`` places
every shot on a sound that exists, and the mixed track lines up with the frames. Hindi is read by the ``hi`` voice,
the English terms in Roman by ``en`` through an SSML language switch, as ``bie/audio/espeak_provider.py`` does for
VO-009. When eSpeak NG is not installed, ``available()`` is False and the caller uses the silent timeline with captions.
"""
from __future__ import annotations

import re
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path
from xml.sax.saxutils import escape

from . import timing

PROVIDER = "espeak-ng-placeholder/1"
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
RUN = re.compile(r"[A-Za-z][A-Za-z0-9’'\-]*(?:\s+[A-Za-z][A-Za-z0-9’'\-]*)*|[^A-Za-z]+")


def executable() -> str:
    return shutil.which("espeak-ng") or shutil.which("espeak") or ""


def available() -> bool:
    return bool(executable())


def ssml(text: str, *, hindi: str = "hi", english: str = "en") -> str:
    """The beat's words as SSML: Devanagari runs in the Hindi voice, Roman runs in the English voice (one switch per run)."""
    parts = []
    for run in RUN.findall(text):
        if not run.strip():
            continue
        voice = english if re.match(r"[A-Za-z]", run) else hindi
        parts.append(f'<voice name="{voice}">{escape(run)}</voice>')
    return '<speak version="1.0" xml:lang="hi">' + "".join(parts) + "</speak>"


def speak(text: str, out: str | Path, *, wpm: int = 150, pitch: int = 50, amplitude: int = 110, timeout: int = 60) -> dict:
    """One beat → one WAV (22050 Hz, mono, 16-bit); returns {"seconds", "bytes"}."""
    exe = executable()
    if not exe:
        raise RuntimeError("eSpeak NG is not installed (apt-get install espeak-ng)")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bie-voice-") as td:
        src = Path(td) / "beat.ssml"
        src.write_text(ssml(text), encoding="utf-8")
        done = subprocess.run([exe, "-m", "-s", str(wpm), "-p", str(pitch), "-a", str(amplitude), "-f", str(src), "-w", str(out)],
                              capture_output=True, text=True, timeout=timeout)
    if done.returncode != 0 or not out.exists():
        raise RuntimeError("eSpeak NG failed: " + (done.stderr or done.stdout)[-400:])
    return {"seconds": seconds_of(out), "bytes": out.stat().st_size}


def seconds_of(path: str | Path) -> float:
    with wave.open(str(path), "rb") as w:
        return round(w.getnframes() / float(w.getframerate()), 3)


def narrate(beats: list, out_dir: str | Path, *, wpm: int = 150) -> dict:
    """Every beat's ``voice`` text spoken to ``<out_dir>/beats/<beat_id>.wav``; returns the ``voice`` map ``timing.build`` takes:
    {beat_id: {"duration": seconds, "words": [], "file": path}} (no word stamps from the placeholder: cue words fall back to
    the character estimate; Task 047 brings real stamps)."""
    out = Path(out_dir) / "beats"
    out.mkdir(parents=True, exist_ok=True)
    voice = {}
    for beat in beats:
        text = beat.get("voice") or beat.get("say") or ""
        path = out / f"{beat['beat_id']}.wav"
        info = speak(text, path, wpm=wpm)
        voice[beat["beat_id"]] = {"duration": max(0.6, info["seconds"]), "words": [], "file": str(path), "provider": PROVIDER}
    return voice


def mix(voice: dict, scenes: list, timeline: dict, out: str | Path, *, fps: int = timing.FPS) -> dict:
    """One narration track for the whole video: each beat's WAV placed at its frame (scenes one after another), silence
    between; returns {"seconds", "beats"}."""
    rate, width, channels = 22050, 2, 1
    chunks = []
    cursor = 0.0
    total_frames = sum(timeline[s["scene_id"]]["duration"] for s in scenes)
    buffer = bytearray(b"\x00" * int(total_frames / fps * rate) * width)
    placed = 0
    scene_start = 0
    for scene in scenes:
        tl = timeline[scene["scene_id"]]
        for bid in scene["beat_ids"]:
            info = voice.get(bid)
            if not info or not info.get("file") or not Path(info["file"]).exists():
                continue
            start_frame, _ = tl["beats"][bid]
            offset = int((scene_start + start_frame) / fps * rate) * width
            with wave.open(info["file"], "rb") as w:
                if (w.getframerate(), w.getsampwidth(), w.getnchannels()) != (rate, width, channels):
                    raise RuntimeError(f"{info['file']}: expected {rate} Hz mono 16-bit")
                data = w.readframes(w.getnframes())
            end = min(len(buffer), offset + len(data))
            buffer[offset:end] = data[: end - offset]
            placed += 1
        scene_start += tl["duration"]
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(bytes(buffer))
    return {"seconds": round(len(buffer) / width / rate, 3), "beats": placed, "file": str(out), "provider": PROVIDER}
