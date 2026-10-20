"""Final soundtrack: narration + a quiet synthesized music bed (ducked under the voice) + a few
sound effects bound to the same visual cues (scene whoosh, stamp thud, answer chime).

Everything is synthesized here (no third-party audio, no licences to track).
"""
from __future__ import annotations

import argparse
import json
import wave
from pathlib import Path

import numpy as np

SR = 48000
THUD = {"overload", "novac", "active", "meristem", "wrong", "trap"}
DING = {"regrow", "answer", "organisation", "recite", "fix", "game", "permanent"}


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as h:
        rate, n = h.getframerate(), h.getnframes()
        x = np.frombuffer(h.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    if rate != SR:
        t_old = np.arange(len(x)) / rate
        t_new = np.arange(int(len(x) * SR / rate)) / SR
        x = np.interp(t_new, t_old, x).astype(np.float32)
    return x


def env(n, attack, release):
    e = np.ones(n, dtype=np.float32)
    a, r = int(attack * SR), int(release * SR)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def pad(seconds: float) -> np.ndarray:
    chords = [[261.63, 329.63, 392.00, 493.88], [220.00, 261.63, 329.63, 392.00],
              [174.61, 220.00, 261.63, 329.63], [196.00, 246.94, 293.66, 392.00]]
    seg = 8.0
    out = np.zeros(int(seconds * SR) + SR, dtype=np.float32)
    t = np.arange(int(seg * SR * 1.25)) / SR
    k = 0
    pos = 0.0
    while pos < seconds:
        notes = chords[k % len(chords)]
        tone = np.zeros_like(t)
        for f in notes:
            for h, amp in ((1, 1.0), (2, 0.25), (3, 0.08)):
                tone += amp * np.sin(2 * np.pi * f * h * 0.5 * t + h)
        tone += 0.5 * np.sin(2 * np.pi * notes[0] * 0.25 * t)
        tone *= env(len(t), 2.0, 2.5) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.2 * t))
        start = int(pos * SR)
        end = min(len(out), start + len(tone))
        out[start:end] += tone[: end - start]
        pos += seg
        k += 1
    out /= np.max(np.abs(out)) + 1e-9
    return out[: int(seconds * SR)]


def whoosh():
    n = int(0.7 * SR)
    noise = np.random.default_rng(1).standard_normal(n).astype(np.float32)
    # moving one-pole low-pass: brighter in the middle
    cut = np.concatenate([np.linspace(0.02, 0.35, n // 2), np.linspace(0.35, 0.02, n - n // 2)])
    y = np.zeros(n, dtype=np.float32)
    acc = 0.0
    for i in range(n):
        acc += cut[i] * (noise[i] - acc)
        y[i] = acc
    return y * env(n, 0.25, 0.35) * 0.9


def thud():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (90 - 40 * t) * t) * np.exp(-t * 9)
    click = np.random.default_rng(2).standard_normal(n) * np.exp(-t * 60) * 0.3
    return (body + click).astype(np.float32)


def ding():
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    y = 0.6 * np.sin(2 * np.pi * 1318.5 * t) + 0.4 * np.sin(2 * np.pi * 1975.5 * t)
    return (y * np.exp(-t * 5) * env(n, 0.005, 0.1)).astype(np.float32)


def place(track, clip, at, gain):
    start = int(at * SR)
    if start >= len(track):
        return
    end = min(len(track), start + len(clip))
    track[start:end] += gain * clip[: end - start]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--timeline", required=True)
    p.add_argument("--narration", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    tl = json.loads(Path(a.timeline).read_text(encoding="utf-8"))
    fps = tl["fps"]
    voice = read_wav(Path(a.narration))
    n = int(tl["seconds"] * SR)
    voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]
    # duck the bed under speech (smoothed voice envelope)
    win = int(0.25 * SR)
    level = np.convolve(np.abs(voice), np.ones(win) / win, mode="same")
    duck = 1.0 - 0.55 * np.clip(level / 0.04, 0, 1)
    bed = pad(tl["seconds"]) * 0.085 * duck
    fx = np.zeros(n, dtype=np.float32)
    w, th, dg = whoosh(), thud(), ding()
    for s in tl["scenes"]:
        t0 = s["start"] / fps
        if s["start"] > 0:
            place(fx, w, t0 - 0.2, 0.18)
        seen = set()
        for key, frame in s["marks"].items():
            name = key.split(":")[-1]
            if frame in seen:
                continue
            if name in THUD:
                place(fx, th, t0 + frame / fps, 0.35)
                seen.add(frame)
            elif name in DING:
                place(fx, dg, t0 + frame / fps, 0.12)
                seen.add(frame)
    mix = voice * 1.0 + bed + fx
    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix *= 0.98 / peak
    with wave.open(a.out, "wb") as h:
        h.setnchannels(1)
        h.setsampwidth(2)
        h.setframerate(SR)
        h.writeframes((mix * 32767).astype(np.int16).tobytes())
    print(f"mixed {tl['seconds']:.1f} s -> {a.out}")


if __name__ == "__main__":
    main()
