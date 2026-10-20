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


def tokens(text):
    return [w for w in re.split(r"[^\w\u0900-\u097f]+", norm_keep(text)) if w]


def norm_keep(text):
    return unicodedata.normalize("NFC", text).lower().replace("\u093c", "")


def coverage(say, transcript):
    want, got = tokens(say), set(tokens(transcript))
    return sum(1 for w in want if w in got) / max(1, len(want))


def activity_map(wav_path: Path):
    """Function fraction-of-spoken-text -> seconds, using where the audio is actually voiced."""
    with wave.open(str(wav_path), "rb") as h:
        rate = h.getframerate()
        x = array.array("h", h.readframes(h.getnframes()))
    hop = max(1, rate // 100)
    rms = [(sum(v * v for v in x[i:i + hop]) / hop) ** 0.5 for i in range(0, len(x) - hop, hop)]
    if not rms:
        return lambda f: 0.0
    thr = max(rms) * 0.08
    active = [1 if r > thr else 0 for r in rms]
    total = sum(active) or 1
    cum, acc = [], 0
    for a in active:
        acc += a
        cum.append(acc)

    def at(fraction):
        target = fraction * total
        for i, c in enumerate(cum):
            if c >= target:
                return i * hop / rate
        return len(cum) * hop / rate
    return at


def char_fraction(say, word, after_fraction):
    text = norm_keep(say)
    target = norm_keep(word)
    start = int(after_fraction * len(text))
    i = text.find(target, start)
    if i < 0:
        i = text.find(target)
    return None if i < 0 else i / max(1, len(text))


def build(lesson, timings, fps=FPS, audio_dir=None):
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
            reliable = bool(words) and coverage(beat["say"], (info or {}).get("transcript", "")) >= 0.8
            amap = activity_map(audio_dir / f"{beat['id']}.wav") if (info and not reliable and audio_dir) else None
            after_frac = 0.0
            for cue in beat["cues"]:
                at = find_word(words, cue["word"], after) if reliable else None
                if at is None and amap is not None:
                    frac = char_fraction(beat["say"], cue["word"], after_frac)
                    frac = cue["fallback"] if frac is None else frac
                    after_frac = frac
                    at = amap(frac)
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
    timeline = build(lesson, timings, audio_dir=Path(args.voice) / "audio" if args.voice else None)
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
