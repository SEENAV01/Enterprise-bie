"""The narration timeline of the showing engine (Phase 1, part C; the Money v2 gold example's Timeline, now BIE's).

A script is scenes of lines: each line an id, its subtitle (``sub``), its spoken sentences (``say_parts``) and the
book items it covers. ``Timeline`` places every line and sentence in the final audio — real seconds when the voice
step gives durations (per sentence key ``"<line>_<i>"``), estimated from length otherwise — and ``cue()`` finds the
moment a word is spoken, which is what every time in a scene plan means. ``script_of`` writes the script from a
lesson plan's beats, so BIE's own videos speak the same shape the gold example speaks.
"""
from __future__ import annotations

import re

GAP_PART, GAP_LINE, GAP_SCENE, LEAD = 0.28, 0.45, 0.9, 0.5
EST = 0.10   # seconds per character for sentences whose voice is not generated yet


def split_sub(sub: str) -> list:
    return [p for p in re.split(r"(?<=[।?!.])\s+", sub.strip()) if p]


class Timeline:
    def __init__(self, script: list, durations: dict | None = None):
        self.script = script
        self.lines, self.parts, t = {}, [], LEAD
        durs = durations or {}
        self.estimated = 0
        for si, sc in enumerate(self.script):
            if si:
                t += GAP_SCENE - GAP_LINE
            sc["t0"] = t
            for line in sc["lines"]:
                subs = split_sub(line["sub"])
                if len(subs) != len(line["say_parts"]):
                    subs = [line["sub"]] if len(line["say_parts"]) == 1 else subs
                assert len(subs) == len(line["say_parts"]), line["id"]
                lt0, parts = t, []
                for i, (say, sub) in enumerate(zip(line["say_parts"], subs)):
                    key = f"{line['id']}_{i}"
                    d = durs.get(key)
                    if d is None:
                        d = len(say) * EST
                        self.estimated += 1
                    parts.append({"key": key, "t0": t, "t1": t + d, "sub": sub, "say": say})
                    self.parts.append(parts[-1])
                    t += d + GAP_PART
                t += GAP_LINE - GAP_PART
                line.update(t0=lt0, t1=parts[-1]["t1"], parts=parts, scene=sc["id"])
                self.lines[line["id"]] = line
            sc["t1"] = t
        self.duration = t + 1.0

    def L(self, lid: str) -> dict:
        if lid not in self.lines:
            raise KeyError(f"no narration line {lid!r}")
        return self.lines[lid]

    def has(self, lid: str) -> bool:
        return lid in self.lines

    def line_ids(self) -> list:
        return list(self.lines)

    def cue(self, lid: str, word: str | None = None, frac: float = 0.0, nth: int = 1) -> float:
        """Time of a word in a line (its start), found in the subtitle text; ``frac`` moves along the line instead."""
        line = self.L(lid)
        if word is None:
            return line["t0"] + (line["t1"] - line["t0"]) * frac
        seen = 0
        for p in line["parts"]:
            start = 0
            while True:
                i = p["sub"].lower().find(word.lower(), start)
                if i < 0:
                    break
                seen += 1
                if seen == nth:
                    return p["t0"] + (p["t1"] - p["t0"]) * (i / max(1, len(p["sub"])))
                start = i + 1
        raise KeyError(f"cue word not found: {lid} {word!r}")

    def subs(self) -> list:
        out = []
        for i, p in enumerate(self.parts):
            nxt = self.parts[i + 1]["t0"] if i + 1 < len(self.parts) else p["t1"] + 0.8
            out.append({"t0": round(p["t0"], 3), "t1": round(min(nxt, p["t1"] + 0.6), 3), "text": p["sub"]})
        return out


def script_of(video: dict) -> list:
    """A lesson-plan video's beats as the narration script: one scene per run of beats of one card part, one line
    per beat, in the beats' own order.

    ``sub`` is the beat's subtitle (what the strip shows); when its sentences do not match the spoken sentences,
    the spoken text is the subtitle too, so every spoken sentence has its strip text. A part that comes back later
    (a closing recap with part "" after the hook's "", or p1 again after p2) is a new scene "<part>-2" at its own
    place: the spoken order is never changed (Sloman chapter 18: the closing recap played right after the hook).
    """
    scenes, seen, prev = [], {}, None
    for beat in video.get("beats") or []:
        say = (beat.get("say") or "").strip()
        if not say:
            continue
        sub = (beat.get("subtitle") or "").strip() or say
        say_parts = split_sub(say)
        if len(split_sub(sub)) != len(say_parts) and len(say_parts) != 1:
            sub = say
        line = {"id": beat["beat_id"], "sub": sub, "say_parts": say_parts,
                "covers": list(beat.get("covers_item_ids") or [])}
        pid = beat.get("part_id") or "part"
        if pid != prev:
            seen[pid] = seen.get(pid, 0) + 1
            scenes.append({"id": pid if seen[pid] == 1 else f"{pid}-{seen[pid]}", "lines": []})
            prev = pid
        scenes[-1]["lines"].append(line)
    return scenes
