"""Timeline of the Money v2 narration (Claude's demo, not BIE output; the gold example): where every line and spoken
sentence sits in the final audio, and the cue time of any word. Real durations come from the voice step (seconds per
sentence key "<line>_<i>"); a sentence without a duration is estimated from its length, and ``estimated`` counts them."""
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
        return self.lines[lid]

    def cue(self, lid: str, word: str | None = None, frac: float = 0.0, nth: int = 1) -> float:
        """Time of a word in a line (its start), found in the subtitle text; ``frac`` moves along the line instead."""
        line = self.lines[lid]
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
