#!/usr/bin/env python3
"""Navin's tone colour from his own recording: only the clean stretches, never a slip (Navin, 21 November 2026).

    python3 tools/voice_tone.py --recording <his recording> --out <private folder>

His words: "bahut galtiyan hai us voice mein par clone karne ke liye kaam mein laa sakte ho ... bolne ka niyam isse mat
lena". So the recording gives only his timbre. Whisper (faster-whisper, large-v3-turbo, MIT) writes down every word with
its time; a clean stretch is a run of words 3 to 10 seconds long with no gap over GAP seconds inside it, no word said
twice in a row (a restart) and every word heard with probability at least MIN_P. OpenVoice V2's tone-colour encoder
(``bie.brain.studio_voice.Tone``) turns the clean stretches into one tone vector, saved as ``tone.npy``.

Everything this writes is private: the output folder must be outside the repository (the tool refuses a folder inside
it), and its ``report.json`` holds numbers only (pauses, restarts, how many clean seconds), which may be quoted in docs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GAP, MIN_P, LO, HI = 0.45, 0.55, 3.0, 10.0


def _bare(word: str) -> str:
    return word.strip().strip("?.,।!—-").casefold()


def stretches(words: list) -> list:
    """Clean runs of [{"w", "s", "e", "p"}] words: [{"s", "e", "text"}], each LO to HI seconds."""
    runs, cur = [], []
    for w in words:
        restart = bool(cur) and _bare(w["w"]) == _bare(cur[-1]["w"])
        if w["p"] < MIN_P or restart:
            if cur:
                runs.append(cur)
            cur = []
            continue
        if cur and w["s"] - cur[-1]["e"] > GAP:
            runs.append(cur)
            cur = []
        cur.append(w)
        if cur[-1]["e"] - cur[0]["s"] >= HI:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [{"s": r[0]["s"], "e": r[-1]["e"], "text": " ".join(x["w"].strip() for x in r)} for r in runs
            if LO <= r[-1]["e"] - r[0]["s"] <= HI + 1]


def report(words: list, seconds: float, clean: list) -> dict:
    gaps = sorted((round(b["s"] - a["e"], 2) for a, b in zip(words, words[1:]) if b["s"] - a["e"] > 0.8), reverse=True)
    return {"seconds": round(seconds, 1), "words": len(words),
            "words_per_minute": round(len(words) / max(seconds / 60, 1e-6), 1),
            "speech_share": round(sum(w["e"] - w["s"] for w in words) / max(seconds, 1e-6), 2),
            "pauses_over_0_8s": len(gaps), "longest_pauses_s": gaps[:5],
            "restarts": sum(1 for a, b in zip(words, words[1:]) if _bare(a["w"]) == _bare(b["w"])),
            "unsure_words": sum(1 for w in words if w["p"] < MIN_P),
            "clean_stretches": len(clean), "clean_seconds": round(sum(c["e"] - c["s"] for c in clean), 1)}


def transcribe(samples, language: str = "hi") -> list:
    from faster_whisper import WhisperModel
    model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(samples, language=language, beam_size=1, word_timestamps=True, vad_filter=False,
                                   condition_on_previous_text=False)
    return [{"w": w.word, "s": float(w.start), "e": float(w.end), "p": float(w.probability)}
            for seg in segments for w in seg.words if w.word.strip()]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--recording", required=True)
    parser.add_argument("--out", required=True, help="a private folder outside the repository")
    parser.add_argument("--language", default="hi")
    args = parser.parse_args(argv)
    out = Path(args.out).resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error("the tone and its stretches are private: --out must be outside the repository")
    out.mkdir(parents=True, exist_ok=True)
    out.chmod(0o700)
    import librosa
    import numpy as np
    from bie.brain.studio_voice import Tone
    samples16 = librosa.load(args.recording, sr=16000, mono=True)[0]
    words = transcribe(samples16, args.language)
    clean = stretches(words)
    tone = Tone()
    audio = librosa.load(args.recording, sr=tone.rate, mono=True)[0]
    vector = tone.tone_of([audio[int(c["s"] * tone.rate):int(c["e"] * tone.rate)] for c in clean])
    np.save(out / "tone.npy", vector.cpu().numpy())
    (out / "tone.npy").chmod(0o600)
    found = report(words, len(samples16) / 16000, clean)
    (out / "report.json").write_text(json.dumps(found, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "clean.json").write_text(json.dumps(clean, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(found, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
