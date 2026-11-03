"""Voice parts -> clean parts (silence trimmed) + durations.json; then the narration track placed on the timeline,
pitched down two semitones (Navin's chosen interim voice) and loudness-normalised.
  python3 assemble.py clean      # trim parts, write durations, list suspicious parts
  python3 assemble.py track      # build narration.wav from the timeline (after builder.py)"""
import json, os, subprocess, sys
import numpy as np
import soundfile as sf

SR = 24000


def trim(a, sr, db=-42):
    e = np.abs(a)
    thr = 10 ** (db / 20) * (e.max() + 1e-9)
    idx = np.where(e > thr)[0]
    if not len(idx):
        return a
    s, t = max(0, idx[0] - int(0.03 * sr)), min(len(a), idx[-1] + int(0.06 * sr))
    return a[s:t]


def clean():
    os.makedirs("tts/clean", exist_ok=True)
    script = json.load(open("script.json"))
    durs, odd = {}, []
    aligned = json.load(open("tts/clean/aligned.json")) if os.path.exists("tts/clean/aligned.json") else {}
    old = json.load(open("tts/clean/durations.json")) if os.path.exists("tts/clean/durations.json") else {}
    for sc in script:
        for l in sc["lines"]:
            for i, say in enumerate(l["say_parts"]):
                k = f"{l['id']}_{i}"
                src = f"tts/parts/{k}.wav"
                if not os.path.exists(src):
                    continue
                if k in aligned and k in old and os.path.exists(f"tts/clean/{k}.wav"):
                    durs[k] = old[k]
                    continue
                a, sr = sf.read(src)
                a = trim(a, sr)
                # long inner pauses (> 0.6 s) are shortened to 0.35 s
                e = np.convolve(np.abs(a), np.ones(int(0.02 * sr)) / int(0.02 * sr), mode="same")
                quiet = e < 10 ** (-38 / 20) * e.max()
                out, j, n = [], 0, len(a)
                while j < n:
                    if quiet[j]:
                        k2 = j
                        while k2 < n and quiet[k2]:
                            k2 += 1
                        seg = a[j:k2]
                        out.append(seg if len(seg) < 0.6 * sr else seg[: int(0.35 * sr)])
                        j = k2
                    else:
                        k2 = j
                        while k2 < n and not quiet[k2]:
                            k2 += 1
                        out.append(a[j:k2]); j = k2
                a = np.concatenate(out) if out else a
                sf.write(f"tts/clean/{k}.wav", a, sr)
                d = len(a) / sr
                durs[k] = round(d, 3)
                rate = d / max(1, len(say))
                if rate > 0.15 or rate < 0.055:
                    odd.append((k, round(d, 2), len(say), round(rate, 3)))
    json.dump(durs, open("tts/clean/durations.json", "w"), indent=0)
    json.dump(odd, open("tts/clean/odd.json", "w"))
    print("clean parts", len(durs), "odd", odd)


def track():
    sys.path.insert(0, ".")
    from timeline import Timeline
    T = Timeline()
    buf = np.zeros(int((T.duration + 0.5) * SR), dtype=np.float32)
    missing = 0
    for p in T.parts:
        f = f"tts/clean/{p['key']}.wav"
        if not os.path.exists(f):
            missing += 1
            continue
        a, sr = sf.read(f, dtype="float32")
        s = int(p["t0"] * SR)
        buf[s:s + len(a)] += a[: len(buf) - s]
    sf.write("narration_raw.wav", buf, SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "narration_raw.wav", "-af",
                    "rubberband=pitch=0.8909,loudnorm=I=-16:TP=-1.5:LRA=7", "-ar", "48000", "narration.wav"], check=True)
    print("narration.wav", round(T.duration, 1), "s, missing parts", missing)


if __name__ == "__main__":
    {"clean": clean, "track": track}[sys.argv[1]]()
