"""The clone voice's worker on the private machine (P1-D voice; run by ``tools/vm_voice.py speak``, never by hand).

It runs inside the voice environment (``$BIE_HOME/voice-venv``: torch CPU, Chatterbox Multilingual, pinned by
``vm_voice.PINS``), so it imports nothing from BIE. It reads a request (sentences, language, reference, pitch, the
private audio folder), speaks each sentence with Chatterbox Multilingual on the CPU, writes each sentence's WAV into the
private folder only, and writes a result of numbers (seconds of audio, seconds of compute, characters) for the public
run folder. Chatterbox marks its audio with its Perth watermark (an inaudible mark that says the audio is generated).

Request (JSON): {"sentences": [{"key", "text"}], "language": "hi", "reference": path or null, "pitch_semitones": float,
"audio_dir": path, "model_revision": sha, "threads": int or null, "seed": int}

Convert request (Navin, 21 November 2026, card "6: Kokoro + Chatterbox badlaav"): {"convert": [{"key", "wav"}],
"target": path of his clip, "audio_dir", "model_revision", "threads"}. Chatterbox's voice conversion (S3Gen, MIT) turns
each base-voice WAV (Kokoro, Indic-TTS) into his timbre; the words and their timing stay the base voice's. Each WAV goes
to the private folder only; the result holds numbers.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time
import wave
from pathlib import Path


def to_wav(path: Path, folder: Path) -> Path:
    """The reference as a WAV the model can read: wav, flac, ogg and mp3 as they are; m4a, aac, webm and others through
    PyAV (its wheels carry their own FFmpeg libraries, so the machine needs no system ffmpeg)."""
    if path.suffix.lower() in (".wav", ".flac", ".ogg", ".mp3"):
        return path
    import av
    import numpy as np
    out = folder / "reference.wav"
    with av.open(str(path)) as box:
        stream = box.streams.audio[0]
        resampler = av.AudioResampler(format="s16", layout="mono", rate=24000)
        chunks = []
        for frame in box.decode(stream):
            for piece in resampler.resample(frame):
                chunks.append(piece.to_ndarray().reshape(-1))
        for piece in resampler.resample(None):
            chunks.append(piece.to_ndarray().reshape(-1))
    write_wav(out, np.concatenate(chunks).astype("int16"), 24000)
    return out


def write_wav(path: Path, samples, rate: int) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples.tobytes())
    os.chmod(path, 0o600)


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--request", type=Path, required=True)
    p.add_argument("--result", type=Path, required=True)
    args = p.parse_args(argv)
    req = json.loads(args.request.read_text(encoding="utf-8"))
    audio_dir = Path(req["audio_dir"])
    audio_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    if req.get("convert"):
        return convert(req, audio_dir, args.result)
    result = {"status": "failed", "sentences": [], "error": None}

    def save():
        args.result.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    try:
        import numpy as np
        import torch
        from huggingface_hub import snapshot_download
        from chatterbox.mtl_tts import REPO_ID, ChatterboxMultilingualTTS
        if req.get("threads"):
            torch.set_num_threads(int(req["threads"]))
        torch.manual_seed(int(req.get("seed", 7)))
        t0 = time.perf_counter()
        ckpt = snapshot_download(repo_id=REPO_ID, repo_type="model", revision=req["model_revision"],
                                 allow_patterns=["ve.pt", "t3_mtl23ls_v2.safetensors", "s3gen.pt",
                                                 "grapheme_mtl_merged_expanded_v1.json", "conds.pt", "Cangjie5_TC.json"])
        result["download_s"] = round(time.perf_counter() - t0, 1)
        t0 = time.perf_counter()
        model = ChatterboxMultilingualTTS.from_local(Path(ckpt), "cpu")
        result["load_s"] = round(time.perf_counter() - t0, 1)
        reference = req.get("reference")
        if reference:
            t0 = time.perf_counter()
            model.prepare_conditionals(str(to_wav(Path(reference), audio_dir)))
            result["reference_s"] = round(time.perf_counter() - t0, 1)
        result.update(sample_rate=model.sr, threads=torch.get_num_threads(), torch=torch.__version__)
        pitch = float(req.get("pitch_semitones") or 0.0)
        for item in req["sentences"]:
            t0 = time.perf_counter()
            wav = model.generate(item["text"], language_id=req.get("language", "hi")).squeeze(0).numpy()
            if pitch:
                import librosa
                wav = librosa.effects.pitch_shift(wav, sr=model.sr, n_steps=pitch)
            compute = time.perf_counter() - t0
            samples = (np.clip(wav, -1.0, 1.0) * 32767).astype("int16")
            write_wav(audio_dir / f"{item['key']}.wav", samples, model.sr)
            audio_s = len(samples) / model.sr
            result["sentences"].append({"key": item["key"], "chars": len(item["text"]), "audio_s": round(audio_s, 2),
                                        "compute_s": round(compute, 2),
                                        "rtf": round(compute / audio_s, 2) if audio_s else None})
            save()                                   # a long run that stops still leaves the sentences it made
        result["status"] = "ok"
    except Exception as exc:                         # the error goes to the result; the audio folder keeps what was made
        import traceback
        result["error"] = f"{type(exc).__name__}: {str(exc)[:400]}"
        result["trace"] = traceback.format_exc()[-1500:]       # where it died, for the next fix (file paths only, no audio)
    result["peak_ram_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    save()
    return 0 if result["status"] == "ok" else 1


def convert(req: dict, audio_dir: Path, result_path: Path) -> int:
    """Each base-voice WAV of ``req["convert"]`` in the voice of ``req["target"]`` (Chatterbox voice conversion)."""
    result = {"status": "failed", "converted": [], "error": None}

    def save():
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    try:
        import numpy as np
        import torch
        from huggingface_hub import hf_hub_download
        from chatterbox.vc import ChatterboxVC
        if req.get("threads"):
            torch.set_num_threads(int(req["threads"]))
        t0 = time.perf_counter()
        folder = Path(hf_hub_download(repo_id="ResembleAI/chatterbox", filename="s3gen.safetensors",
                                      revision=req["model_revision"])).parent
        result["download_s"] = round(time.perf_counter() - t0, 1)
        t0 = time.perf_counter()
        model = ChatterboxVC.from_local(folder, "cpu")
        model.set_target_voice(str(to_wav(Path(req["target"]), audio_dir)))
        result["load_s"] = round(time.perf_counter() - t0, 1)
        result.update(sample_rate=model.sr, threads=torch.get_num_threads(), torch=torch.__version__)
        for item in req["convert"]:
            t0 = time.perf_counter()
            wav = model.generate(str(item["wav"])).squeeze(0).numpy()
            compute = time.perf_counter() - t0
            samples = (np.clip(wav, -1.0, 1.0) * 32767).astype("int16")
            write_wav(audio_dir / f"{item['key']}.wav", samples, model.sr)
            audio_s = len(samples) / model.sr
            result["converted"].append({"key": item["key"], "audio_s": round(audio_s, 2), "compute_s": round(compute, 2),
                                        "rtf": round(compute / audio_s, 2) if audio_s else None})
            save()
        result["status"] = "ok"
    except Exception as exc:                         # the error goes to the result; the folder keeps what was made
        import traceback
        result["error"] = f"{type(exc).__name__}: {str(exc)[:400]}"
        result["trace"] = traceback.format_exc()[-1500:]
    result["peak_ram_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    save()
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
