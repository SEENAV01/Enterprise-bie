"""Transcribe each video (Hindi/Hinglish) with word timings. Usage: stt_run.py OUTDIR ID1 ID2 ..."""
import json, os, subprocess, sys, tempfile, time, wave
import numpy as np
from faster_whisper import WhisperModel
S = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=2)
for vid in sys.argv[2:]:
    dst = os.path.join(out, vid + ".json")
    if os.path.exists(dst):
        continue
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(S, "vids", vid + ".mp4"), "-ac", "1", "-ar",
                        "16000", wav], check=True, stdin=subprocess.DEVNULL)
        w = wave.open(wav)
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    t = time.time()
    segs, info = m.transcribe(a, language="hi", task="transcribe", word_timestamps=True, beam_size=1,
                              temperature=0.0, condition_on_previous_text=False, vad_filter=True,
                              vad_parameters={"min_silence_duration_ms": 300})
    rows = []
    for s in segs:
        rows.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
                     "words": [[round(x.start, 2), round(x.end, 2), x.word.strip(), round(x.probability, 2)]
                               for x in (s.words or [])]})
    json.dump({"id": vid, "duration": round(info.duration, 1), "took_s": round(time.time() - t), "segments": rows},
              open(dst, "w"), ensure_ascii=False, indent=0)
    print(vid, "segments", len(rows), "took", round(time.time() - t), flush=True)
