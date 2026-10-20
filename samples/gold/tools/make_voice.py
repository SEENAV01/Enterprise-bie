"""Narration audio and word timings for a gold-sample lesson (runs in GitHub Actions).

For every beat in lesson.json: OpenAI text-to-speech → WAV, then whisper-1 word timestamps (the
beat's own text is passed as the prompt so the transcript keeps the script's spelling). Writes
<out>/audio/<beat>.wav and <out>/timings.json. Beats whose text and voice settings did not change
since the previous run (same hash in an existing timings.json) are reused, so edits cost only the
changed beats. The key comes only from OPENAI_API_KEY and is never written or printed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import urllib.error
import urllib.request
import time
import uuid
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from bie.model_gateway.live.errors import redact  # noqa: E402

API = "https://api.openai.com/v1"


class CallError(Exception):
    def __init__(self, message, retry):
        super().__init__(message)
        self.retry = retry


def post(path, body: bytes, content_type: str, key: str, timeout=120) -> bytes:
    """POST with up to 4 attempts for rate limits, server errors and timeouts."""
    last = None
    for attempt in range(4):
        request = urllib.request.Request(API + path, data=body, method="POST")
        request.add_header("authorization", "Bearer " + key)
        request.add_header("content-type", content_type)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read(2000).decode("utf-8", "replace")
            last = CallError(f"OPENAI_HTTP_{exc.code} {path}: {redact(detail, (key,))[:300]}", exc.code in (408, 409, 429) or exc.code >= 500)
        except (TimeoutError, OSError) as exc:
            last = CallError(f"OPENAI_NETWORK {path}: {redact(exc, (key,))[:200]}", True)
        if not last.retry:
            break
        time.sleep(3 * (2 ** attempt))
    raise last


def speech(text, voice, key) -> bytes:
    body = json.dumps({"model": voice["model"], "voice": voice["voice"], "input": text,
                       "instructions": voice["instructions"], "response_format": "wav"}, ensure_ascii=False).encode()
    return post("/audio/speech", body, "application/json", key)


def words(wav: bytes, prompt: str, key: str):
    boundary = "bie" + uuid.uuid4().hex
    fields = [("model", "whisper-1"), ("response_format", "verbose_json"), ("timestamp_granularities[]", "word"),
              ("prompt", prompt[:800])]
    parts = []
    for name, value in fields:
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="beat.wav"\r\n'
                 f'Content-Type: audio/wav\r\n\r\n'.encode() + wav + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    raw = post("/audio/transcriptions", b"".join(parts), f"multipart/form-data; boundary={boundary}", key)
    data = json.loads(raw)
    return data.get("text", ""), [{"w": w.get("word", ""), "start": float(w.get("start", 0)), "end": float(w.get("end", 0))}
                                  for w in data.get("words", [])]


def fix_wav(data: bytes) -> bytes:
    """OpenAI streams WAV with unknown (0xFFFFFFFF) sizes; rewrite the header with the real sizes."""
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise CallError("speech response is not WAV", False)
    pos, fmt = 12, None
    while pos + 8 <= len(data):
        cid, size = data[pos:pos + 4], int.from_bytes(data[pos + 4:pos + 8], "little")
        if cid == b"fmt ":
            fmt = data[pos + 8:pos + 8 + size]
        if cid == b"data":
            pcm = data[pos + 8:] if size in (0, 0xFFFFFFFF) or pos + 8 + size > len(data) else data[pos + 8:pos + 8 + size]
            channels, rate = int.from_bytes(fmt[2:4], "little"), int.from_bytes(fmt[4:8], "little")
            width = int.from_bytes(fmt[14:16], "little") // 8
            pcm = pcm[: len(pcm) - len(pcm) % (channels * width)]
            buf = io.BytesIO()
            with wave.open(buf, "wb") as handle:
                handle.setnchannels(channels)
                handle.setsampwidth(width)
                handle.setframerate(rate)
                handle.writeframes(pcm)
            return buf.getvalue()
        pos += 8 + size + (size % 2)
    raise CallError("speech WAV has no data chunk", False)


def duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lesson", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise SystemExit("OPENAI_API_KEY is not set")
    lesson = json.loads(Path(args.lesson).read_text(encoding="utf-8"))
    out = Path(args.out)
    (out / "audio").mkdir(parents=True, exist_ok=True)
    previous = {}
    if (out / "timings.json").is_file():
        previous = json.loads((out / "timings.json").read_text(encoding="utf-8")).get("beats", {})
    voice = lesson["voice"]
    beats, todo, reused = {}, [], 0
    for scene in lesson["scenes"]:
        for beat in scene["beats"]:
            digest = hashlib.sha256(json.dumps([beat["say"], voice], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            old = previous.get(beat["id"])
            wav_path = out / "audio" / f"{beat['id']}.wav"
            if old and old.get("hash") == digest and wav_path.is_file():
                wav_path.write_bytes(fix_wav(wav_path.read_bytes()))
                beats[beat["id"]] = dict(old, duration=round(duration(wav_path), 3))
                reused += 1
            else:
                todo.append((beat, digest))

    def make(item):
        beat, digest = item
        t0 = time.monotonic()
        wav_path = out / "audio" / f"{beat['id']}.wav"
        wav_path.write_bytes(fix_wav(speech(beat["say"], voice, key)))
        t1 = time.monotonic()
        text, timed = words(wav_path.read_bytes(), beat["say"], key)
        info = {"hash": digest, "duration": round(duration(wav_path), 3), "transcript": text, "words": timed,
                "seconds_tts": round(t1 - t0, 1), "seconds_words": round(time.monotonic() - t1, 1)}
        print(f"{beat['id']}: {info['duration']:.2f}s audio, tts {info['seconds_tts']}s, words {info['seconds_words']}s", flush=True)
        return beat["id"], info

    failures = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(make, item) for item in todo]
        for (beat, _), future in zip(todo, futures):
            try:
                beat_id, info = future.result()
                beats[beat_id] = info
            except Exception as exc:  # keep finished beats; report the rest
                failures.append(f"{beat['id']}: {redact(exc, (key,))[:200]}")
    made = len(todo) - len(failures)
    keep = {f"{b}.wav" for b in beats}
    for stale in (out / "audio").glob("*.wav"):
        if stale.name not in keep:
            stale.unlink()
    order = [b["id"] for sc in lesson["scenes"] for b in sc["beats"]]
    beats = {b: beats[b] for b in order if b in beats}
    total = sum(b["duration"] for b in beats.values())
    (out / "timings.json").write_text(json.dumps({"lesson_id": lesson["lesson_id"], "voice": {k: voice[k] for k in ("model", "voice")},
                                                   "total_seconds": round(total, 2), "beats": beats}, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    slow = sorted(((b.get("seconds_tts", 0) + b.get("seconds_words", 0), k) for k, b in beats.items()), reverse=True)[:3]
    print(f"::notice title=gold voice::{made} generated, {reused} reused, {len(failures)} failed, {total:.1f} s of narration; slowest calls {slow}")
    for failure in failures[:10]:
        print(f"::error title=gold voice beat::{failure}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except CallError as exc:
        print(f"::error title=gold voice::{exc}")
        raise SystemExit(1)
