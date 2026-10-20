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
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from bie.model_gateway.live.errors import redact  # noqa: E402

API = "https://api.openai.com/v1"


def post(path, body: bytes, content_type: str, key: str, timeout=300) -> bytes:
    request = urllib.request.Request(API + path, data=body, method="POST")
    request.add_header("authorization", "Bearer " + key)
    request.add_header("content-type", content_type)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read(2000).decode("utf-8", "replace")
        raise SystemExit(f"OPENAI_HTTP_{exc.code}: {redact(detail, (key,))[:400]}") from None


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
    beats, made, reused = {}, 0, 0
    for scene in lesson["scenes"]:
        for beat in scene["beats"]:
            digest = hashlib.sha256(json.dumps([beat["say"], voice], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            wav_path = out / "audio" / f"{beat['id']}.wav"
            old = previous.get(beat["id"])
            if old and old.get("hash") == digest and wav_path.is_file():
                beats[beat["id"]] = old
                reused += 1
                continue
            wav_path.write_bytes(speech(beat["say"], voice, key))
            text, timed = words(wav_path.read_bytes(), beat["say"], key)
            beats[beat["id"]] = {"hash": digest, "duration": round(duration(wav_path), 3), "transcript": text, "words": timed}
            made += 1
            print(f"{beat['id']}: {beats[beat['id']]['duration']:.2f}s, {len(timed)} words", flush=True)
    keep = {f"{b}.wav" for b in beats}
    for stale in (out / "audio").glob("*.wav"):
        if stale.name not in keep:
            stale.unlink()
    total = sum(b["duration"] for b in beats.values())
    (out / "timings.json").write_text(json.dumps({"lesson_id": lesson["lesson_id"], "voice": {k: voice[k] for k in ("model", "voice")},
                                                   "total_seconds": round(total, 2), "beats": beats}, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    print(f"::notice title=gold voice::{made} beats generated, {reused} reused, {total:.1f} s of narration")


if __name__ == "__main__":
    main()
