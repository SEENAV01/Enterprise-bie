"""After assemble.py clean: speech-to-text on every clean part. Cuts the noise the voice model sometimes adds after the
sentence (cut at the last word + 0.15 s), updates durations.json, and lists parts whose words do not match the text
(those are regenerated with another seed)."""
import difflib, json, os, re, sys
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
import librosa

script = json.load(open("script.json"))
want = {f"{l['id']}_{i}": p for sc in script for l in sc["lines"] for i, p in enumerate(l["say_parts"])}
durs = json.load(open("tts/clean/durations.json"))
done = json.load(open("tts/clean/aligned.json")) if os.path.exists("tts/clean/aligned.json") else {}
m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=int(sys.argv[1]) if len(sys.argv) > 1 else 2)
norm = lambda s: re.sub(r"[^ऀ-ॿ]", "", s)
bad = []
for k in sorted(durs):
    if k in done:
        continue
    f = f"tts/clean/{k}.wav"
    a, sr = sf.read(f)
    a16 = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=16000)
    segs, _ = m.transcribe(a16, language="hi", beam_size=3, temperature=0.0, condition_on_previous_text=False, word_timestamps=True)
    words = [(w.start, w.end, w.word) for s in segs for w in s.words]
    heard = "".join(w for _, _, w in words)
    sim = difflib.SequenceMatcher(None, norm(heard), norm(want[k])).ratio()
    if words:
        end = words[-1][1] + 0.15
        if len(a) / sr - end > 0.35:
            a = a[: int(end * sr)]
            sf.write(f, a, sr)
    durs[k] = round(len(a) / sr, 3)
    done[k] = {"sim": round(sim, 2), "heard": heard.strip(), "dur": durs[k]}
    if sim < 0.45:
        bad.append(k)
    print(k, round(sim, 2), durs[k], flush=True)
json.dump(durs, open("tts/clean/durations.json", "w"), indent=0)
json.dump(done, open("tts/clean/aligned.json", "w"), ensure_ascii=False, indent=0)
print("BAD", bad)
