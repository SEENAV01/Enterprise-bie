"""Frame timing for a video: beats → frames, and cue words → frames.

Until the narration exists, a beat lasts as long as its text takes to say (Hinglish at about 14 characters
a second, the pace measured on the tissue sample); a cue word lands at its position inside the beat. When
the voice section has word timestamps, ``build`` takes them instead and every cue lands on its real word.
"""
from __future__ import annotations

import re
import unicodedata

FPS = 30
CHARS_PER_SECOND = 14.0
LEAD_IN = 0.4
GAP = 0.35
TAIL = 0.8


def _norm(text: str) -> str:
    return re.sub(r"[^\wऀ-ॿ]+", " ", unicodedata.normalize("NFC", text).lower())


def word_fraction(say: str, word: str) -> float:
    """Where ``word`` starts inside ``say`` as a fraction of the text (0 when it is not found)."""
    text, target = _norm(say), _norm(word).strip()
    if not target:
        return 0.0
    i = f" {text} ".find(f" {target} ")
    return 0.0 if i < 0 else max(0.0, (i - 1) / max(1, len(text)))


def beat_seconds(say: str) -> float:
    return max(1.5, len(say.strip()) / CHARS_PER_SECOND)


def build(beats: list, scenes: list, *, fps: int = FPS, voice: dict | None = None) -> dict:
    """Per scene: duration in frames, each beat's local start and length, and a cue(beat_id, word) → local frame map.

    ``voice`` (optional): beat_id → {"duration": seconds, "words": [{"w", "start", "end"}]} from the voice section.
    """
    says = {b["beat_id"]: b["say"] for b in beats}
    out = {}
    for scene in scenes:
        t = LEAD_IN
        beat_frames, cues = {}, {}
        for bid in scene["beat_ids"]:
            info = (voice or {}).get(bid)
            seconds = info["duration"] if info else beat_seconds(says.get(bid, ""))
            beat_frames[bid] = (round(t * fps), round(seconds * fps))
            cues[bid] = (t, seconds, info)
            t += seconds + GAP
        total = round((t - GAP + TAIL) * fps)
        out[scene["scene_id"]] = {"duration": max(total, fps), "beats": beat_frames, "_cues": cues, "fps": fps}
    return out


def cue_frame(timeline: dict, scene_id: str, beat_id: str, word: str, says: dict) -> int:
    scene = timeline[scene_id]
    if beat_id not in scene["_cues"]:
        return 0
    start, seconds, info = scene["_cues"][beat_id]
    fps = scene["fps"]
    if info and info.get("words"):
        target = _norm(word).strip()
        for w in info["words"]:
            if _norm(w.get("w", "")).strip() == target:
                return round((start + float(w["start"])) * fps)
    return round((start + word_fraction(says.get(beat_id, ""), word) * seconds) * fps)
