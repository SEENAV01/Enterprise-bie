"""Voice ↔ picture timing from voice activity only (fast; no speech-to-text needed).

Speech phrases come from Silero VAD (bundled with faster-whisper); visual changes from events/<ID>.json.
For each video: phrase and pause lengths, how often the picture changes, where changes land (inside a phrase and
how far into it, or in a pause), how many phrases get a change, and what happens in long pauses.
Usage: vad_sync.py ID [ID ...]
"""
import json
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from faster_whisper.vad import VadOptions, get_speech_timestamps

B = os.path.dirname(os.path.abspath(__file__))


def pct(xs, p):
    if not xs:
        return None
    xs = sorted(xs)
    return round(float(xs[min(len(xs) - 1, int(p / 100 * len(xs)))]), 2)


def audio(vid):
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "a.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(B, "vids", vid + ".mp4"), "-ac", "1", "-ar", "16000", p],
                       check=True, stdin=subprocess.DEVNULL)
        w = wave.open(p)
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def analyse(vid):
    a = audio(vid)
    ts = get_speech_timestamps(a, VadOptions(min_silence_duration_ms=int(os.environ.get("MINSIL", "150")), speech_pad_ms=60, threshold=0.5))
    ph = [{"start": t["start"] / 16000, "end": t["end"] / 16000} for t in ts]
    ev = json.load(open(os.path.join(B, "events", vid + ".json")))
    speech_end = ph[-1]["end"] if ph else 0
    events = [e for e in ev["events"] if e["start"] <= speech_end + 1.0]
    starts = [e["start"] for e in events]
    pauses = [b["start"] - a_["end"] for a_, b in zip(ph, ph[1:])]
    inside, in_pause, frac, after, lead = 0, 0, [], [], []
    for t in starts:
        hit = next((p for p in ph if p["start"] - 0.05 <= t <= p["end"] + 0.05), None)
        if hit:
            inside += 1
            frac.append((t - hit["start"]) / max(0.3, hit["end"] - hit["start"]))
            after.append(t - hit["start"])
        else:
            in_pause += 1
            nxt = next((p for p in ph if p["start"] > t), None)
            if nxt:
                lead.append(nxt["start"] - t)
    long_p = [(a_["end"], b["start"]) for a_, b in zip(ph, ph[1:]) if b["start"] - a_["end"] > 1.0]
    gaps = [b - a_ for a_, b in zip(starts, starts[1:])]
    talk = sum(p["end"] - p["start"] for p in ph)
    res = {"id": vid, "duration": ev["duration"], "phrases": len(ph), "phrase_median_s": pct([p["end"] - p["start"] for p in ph], 50),
           "pause_median_s": pct(pauses, 50), "pause_p90_s": pct(pauses, 90), "speech_share": round(talk / max(1.0, speech_end), 2),
           "changes": len(events), "change_gap_median_s": pct(gaps, 50), "change_gap_p90_s": pct(gaps, 90),
           "longest_still_s": round(max(gaps), 1) if gaps else None,
           "changes_inside_phrase": round(inside / max(1, len(events)), 2), "changes_in_pause": round(in_pause / max(1, len(events)), 2),
           "position_in_phrase_median": pct(frac, 50), "seconds_into_phrase_median": pct(after, 50),
           "pause_change_before_next_phrase_s": pct(lead, 50),
           "phrases_with_change": round(sum(any(p["start"] - 0.3 <= t <= p["end"] + 0.3 for t in starts) for p in ph) / max(1, len(ph)), 2),
           "long_pauses": len(long_p), "long_pauses_with_change": sum(any(s - 0.2 <= t <= e + 0.2 for t in starts) for s, e in long_p),
           "kinds": {k: sum(e["kind"] == k for e in events) for k in ("add", "big", "reset")}}
    os.makedirs(os.path.join(B, "sync"), exist_ok=True)
    json.dump({**res, "phrase_times": [[round(p["start"], 2), round(p["end"], 2)] for p in ph]},
              open(os.path.join(B, "sync", vid + ".vad.json"), "w"), indent=0)
    return res


if __name__ == "__main__":
    rows = []
    for v in sys.argv[1:]:
        r = analyse(v)
        rows.append(r)
        print(json.dumps(r), flush=True)
    json.dump(rows, open(os.path.join(B, "sync", "vad_summary.json"), "w"), indent=1)
