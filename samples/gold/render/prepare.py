"""Build the frame timeline (and the narration track) for a gold-sample lesson.

Narration drives timing: each beat's audio length sets its duration, and every visual cue is bound to
the time its word is spoken (whisper word timestamps), falling back to a fraction of the beat's
speech when the word is not found. Without audio (--estimate) durations are estimated from text
length so the animation can be previewed before the voice exists.

Writes timeline.json and, with audio, narration.wav (all beats placed at their start times).
"""
from __future__ import annotations

import argparse
import array
import json
import re
import unicodedata
import wave
from pathlib import Path

FPS = 30
LEAD_IN = 0.5      # seconds before a scene's first beat
GAP = 0.35         # pause between beats
TAIL = 0.9         # seconds after a scene's last beat
CHARS_PER_SECOND = 14.0


def norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    text = text.replace("़", "")  # nukta: ग़ == ग
    return re.sub(r"[^\wऀ-ॿ]+", "", text)


def find_word(words, cue, after):
    target = norm(cue)
    if not target:
        return None
    probe = target[: max(3, min(len(target), 5))]
    for item in words:
        if item["start"] + 1e-6 < after:
            continue
        got = norm(item["w"])
        if got and (got == target or got.startswith(probe) or target.startswith(got) and len(got) >= 3):
            return item["start"]
    return None


def build(lesson, timings, fps=FPS):
    scenes, cursor = [], 0.0
    for scene in lesson["scenes"]:
        start = cursor
        t = LEAD_IN
        beats, marks = [], {}
        for beat in scene["beats"]:
            info = (timings or {}).get(beat["id"])
            if info:
                duration = info["duration"]
                words = info.get("words") or []
                speech0 = words[0]["start"] if words else 0.0
                speech1 = words[-1]["end"] if words else duration
            else:
                duration = max(1.2, len(beat["say"]) / CHARS_PER_SECOND)
                words, speech0, speech1 = [], 0.0, duration
            after = 0.0
            for cue in beat["cues"]:
                at = find_word(words, cue["word"], after) if words else None
                if at is None:
                    at = speech0 + cue["fallback"] * max(0.1, speech1 - speech0)
                after = at
                name = cue["mark"]
                key = name if name not in marks else f"{beat['id']}:{name}"
                marks[key] = round((t + at) * fps)
                marks.setdefault(f"{beat['id']}:{name}", marks[key])
            beats.append({"id": beat["id"], "start": round(t * fps), "end": round((t + duration) * fps),
                          "audio_start": round(start + t, 4)})
            t += duration + GAP
        t += TAIL - GAP
        total = round(t * fps)
        scenes.append({"id": scene["id"], "component": scene["component"], "zone": scene.get("zone"),
                       "start": round(start * fps), "duration": total, "beats": beats, "marks": marks})
        cursor = start + total / fps
    return {"fps": fps, "width": lesson["video"]["width"], "height": lesson["video"]["height"],
            "frames": round(cursor * fps), "seconds": round(cursor, 2), "title": lesson["video"]["title"],
            "scenes": scenes}


def narration(timeline, audio_dir: Path, out: Path):
    rate = None
    track = None
    for scene in timeline["scenes"]:
        for beat in scene["beats"]:
            with wave.open(str(audio_dir / f"{beat['id']}.wav"), "rb") as handle:
                if rate is None:
                    rate, width, channels = handle.getframerate(), handle.getsampwidth(), handle.getnchannels()
                    if width != 2 or channels != 1:
                        raise SystemExit("expected 16-bit mono WAV")
                    track = array.array("h", bytes(2 * int((timeline["seconds"] + 1) * rate)))
                samples = array.array("h", handle.readframes(handle.getnframes()))
            offset = int(beat["audio_start"] * rate)
            track[offset:offset + len(samples)] = samples
    with wave.open(str(out), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(track.tobytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lesson", required=True)
    parser.add_argument("--voice", help="folder with timings.json and audio/ (omit to estimate)")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    lesson = json.loads(Path(args.lesson).read_text(encoding="utf-8"))
    timings = None
    if args.voice:
        timings = json.loads((Path(args.voice) / "timings.json").read_text(encoding="utf-8"))["beats"]
    timeline = build(lesson, timings)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1), encoding="utf-8")
    if args.voice:
        narration(timeline, Path(args.voice) / "audio", out / "narration.wav")
    found = sum(1 for s in lesson["scenes"] for b in s["beats"] for c in b["cues"]
                if timings and find_word(timings.get(b["id"], {}).get("words", []), c["word"], 0) is not None)
    cues = sum(len(b["cues"]) for s in lesson["scenes"] for b in s["beats"])
    print(f"{timeline['seconds']:.1f} s, {timeline['frames']} frames, {len(timeline['scenes'])} scenes; "
          f"cues bound to spoken words: {found}/{cues}" + ("" if timings else " (estimated timing)"))


if __name__ == "__main__":
    main()
