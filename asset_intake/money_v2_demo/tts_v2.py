import json, os, sys, time, torch, torchaudio as ta
torch.set_num_threads(2)
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
s = json.load(open("script.json"))
os.makedirs("tts/parts", exist_ok=True)
jobs = [(l["id"], i, p) for sc in s for l in sc["lines"] for i, p in enumerate(l["say_parts"])]
todo = [j for j in jobs if not os.path.exists(f"tts/parts/{j[0]}_{j[1]}.wav")]
print("parts", len(jobs), "todo", len(todo), flush=True)
if not todo: sys.exit(0)
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
m.prepare_conditionals("ref_navin_12s.wav")
CAP = [1000]
_orig = m.t3.inference
def _capped(*a, **k):
    k["max_new_tokens"] = CAP[0]
    return _orig(*a, **k)
m.t3.inference = _capped
for lid, i, text in todo:
    t = time.time()
    torch.manual_seed(int(os.environ.get("SEED", "7")))
    CAP[0] = min(1000, int(len(text) * 4.2) + 40)
    wav = m.generate(text, language_id="hi")
    ta.save(f"tts/parts/{lid}_{i}.wav.tmp.wav", wav, m.sr)
    os.replace(f"tts/parts/{lid}_{i}.wav.tmp.wav", f"tts/parts/{lid}_{i}.wav")
    print(lid, i, round(time.time() - t), "s", round(wav.shape[-1] / m.sr, 1), flush=True)
print("DONE", flush=True)
