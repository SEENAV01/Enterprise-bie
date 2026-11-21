"""The studio's narrator voice, per language, with BIE's teacher pauses and (when it is set up) Navin's own tone colour.

Engines (all free, all on the machine's CPU):

- **Kokoro** (kokoro-onnx, MIT; Kokoro-82M weights, Apache-2.0) for Hindi/Hinglish and English. Hindi voice ``hf_alpha``
  is the voice Navin heard in the approved Monsoon film (18 November 2026); its known limit (weak aspirated sounds such as
  kh and gh) was told to him. Files are fetched once to ``$BIE_HOME/models/kokoro`` (or ``BIE_KOKORO_DIR``).
- **AI4Bharat Indic-TTS** (FastPitch + HiFi-GAN; code and checkpoints MIT, trained on the IIT Madras Indic TTS database,
  royalty-free licence) for Tamil, Telugu, Malayalam and Marathi, read through Coqui TTS (``coqui-tts``, MPL-2.0, used
  unmodified as a library). Autodub (Navin, 21 November 2026). Checkpoints in ``$BIE_HOME/models/indic-tts/<lang>/``
  (``fastpitch/`` and ``hifigan/``, as AI4Bharat releases them). These engines read only their own script.
- **Navin's tone colour** (Navin, 21 November 2026: "Kokoro + OpenVoice"): OpenVoice V2's tone-colour converter (MyShell,
  MIT) turns the base voice into his timbre in any language. Only his timbre is taken from his recording; how a line is
  said (pauses, pace) is BIE's teacher rule below, because his recording has slips he asked BIE not to learn. The tone
  file and every audio made with it are private: never in the repository or a public run folder
  (``docs/roadmap/VOICE_CLIP_METHOD.md``). Set ``BIE_NARRATOR=navin`` and ``BIE_VOICE_TONE=<tone .npy>``; the base voice
  is then a male one, which converts best to his.

When an engine or its files are missing the studio still makes the film, timed by text length and marked "no voice".
"""
from __future__ import annotations

import base64
import io
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

FILES = {"kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
         "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"}
VOICE, SPEED, LANG = "hf_alpha", 0.95, "hi"
# narrator -> language -> (Kokoro voice, Kokoro language). "navin" uses male base voices for his tone colour.
KOKORO_VOICES = {"female": {"hi": (VOICE, LANG), "en": ("bf_emma", "en-gb")},
                 "navin": {"hi": ("hm_omega", "hi"), "en": ("bm_george", "en-gb")}}
INDIC = ("ta", "te", "ml", "mr")                      # AI4Bharat Indic-TTS; speakers "female" and "male"
INDIC_SPEAKER = {"female": "female", "navin": "male"}

# BIE's teacher rules for saying a line (Navin, 20 and 21 November 2026), not taken from any recording:
QUESTION_PAUSE = 0.45     # seconds of silence after a question (question and answer sounded alike)
CLAUSE_PAUSE = 0.22       # a short breath at ";", ":" and "—" inside a statement (one long flow sounded like a paragraph)
QUESTION_SPEED = 0.92     # a question is asked a little slower than the answer is told
CLAUSE = re.compile(r"\s*(?:;|:|—|–)\s*")
CONVERT_TAU = 0.3         # OpenVoice's strength of the tone change (its default)


def folder() -> Path:
    return Path(os.environ.get("BIE_KOKORO_DIR") or Path(os.environ.get("BIE_HOME", "/var/lib/bie")) / "models" / "kokoro")


def indic_folder(language: str) -> Path:
    return Path(os.environ.get("BIE_INDIC_TTS_DIR") or Path(os.environ.get("BIE_HOME", "/var/lib/bie")) / "models" /
                "indic-tts") / language


def narrator() -> str:
    return "navin" if os.environ.get("BIE_NARRATOR", "").strip().lower() == "navin" else "female"


def parts(text: str) -> list:
    """The pieces a line is spoken in, with the silence after each: a question on its own with QUESTION_PAUSE after it;
    a statement in one flow, with a short breath (CLAUSE_PAUSE) at ";", ":" and "—".
    "Band membrane kyun chahiye? Iska seedha sa jawab hai: jamav." -> [("Band membrane kyun chahiye?", 0.45),
    ("Iska seedha sa jawab hai", 0.22), ("jamav.", 0.0)]."""
    out = []
    for piece in [p.strip() for p in re.split(r"(?<=\?)\s*", (text or "").strip()) if p.strip()]:
        if piece.endswith("?"):
            out.append((piece, QUESTION_PAUSE))
            continue
        bits = [b.strip() for b in CLAUSE.split(piece) if b.strip()]
        out.extend((b, CLAUSE_PAUSE if j < len(bits) - 1 else 0.0) for j, b in enumerate(bits))
    return out or [((text or "").strip() or ".", 0.0)]


def speed(part: str) -> float:
    return QUESTION_SPEED if part.endswith("?") else SPEED


class KokoroEngine:
    def __init__(self, language: str, who: str, *, fetch: bool = True, path: Path | None = None):
        if language not in KOKORO_VOICES[who]:
            raise LookupError(f"no Kokoro voice for {language!r}")
        self.voice, self.lang = KOKORO_VOICES[who][language]
        from kokoro_onnx import Kokoro            # optional: ImportError means "no voice"
        path = path or folder()
        path.mkdir(parents=True, exist_ok=True)
        for name, url in FILES.items():
            target = path / name
            if not target.exists():
                if not fetch:
                    raise FileNotFoundError(f"{target} is missing")
                with urllib.request.urlopen(url, timeout=600) as response, tempfile.NamedTemporaryFile(dir=path, delete=False) as tmp:
                    shutil.copyfileobj(response, tmp)
                Path(tmp.name).replace(target)
        self.engine = Kokoro(str(path / "kokoro-v1.0.onnx"), str(path / "voices-v1.0.bin"))
        self.label = f"kokoro {self.voice}"

    def speak(self, text: str, pace: float):
        import numpy as np
        made, rate = self.engine.create(text, voice=self.voice, speed=pace, lang=self.lang)
        return np.asarray(made, dtype="float32"), rate


def local_config(model: Path) -> Path:
    """AI4Bharat's configs name their speaker file by the path it had on their machine ("models/v1/ta/fastpitch/
    speakers.pth"); a copy beside the original names the file where it really is."""
    import json
    config = json.loads((model / "config.json").read_text(encoding="utf-8"))
    speakers = str((model / "speakers.pth").resolve())

    def fix(node):
        if isinstance(node, dict):
            return {k: (speakers if k == "speakers_file" and v else fix(v)) for k, v in node.items()}
        return [fix(x) for x in node] if isinstance(node, list) else node
    fixed = model / "config.bie.json"
    text = json.dumps(fix(config), ensure_ascii=False, indent=1)
    if not fixed.exists() or fixed.read_text(encoding="utf-8") != text:
        fixed.write_text(text, encoding="utf-8")
    return fixed


class IndicEngine:
    def __init__(self, language: str, who: str):
        base = indic_folder(language)
        model, vocoder = base / "fastpitch", base / "hifigan"
        for need in (model / "best_model.pth", model / "config.json", vocoder / "best_model.pth", vocoder / "config.json"):
            if not need.exists():
                raise FileNotFoundError(f"{need} is missing")
        from TTS.utils.synthesizer import Synthesizer     # optional: coqui-tts
        speakers = model / "speakers.pth"
        self.engine = Synthesizer(tts_checkpoint=str(model / "best_model.pth"), tts_config_path=str(local_config(model)),
                                  tts_speakers_file=str(speakers) if speakers.exists() else None,
                                  vocoder_checkpoint=str(vocoder / "best_model.pth"), vocoder_config=str(vocoder / "config.json"),
                                  use_cuda=False)
        self.speaker = INDIC_SPEAKER[who]
        self.label = f"indic-tts {language} {self.speaker}"

    def speak(self, text: str, pace: float):
        import numpy as np
        made = self.engine.tts(text, speaker_name=self.speaker, split_sentences=False)
        samples = np.asarray(made, dtype="float32")
        if abs(pace - 1.0) > 0.01:                          # FastPitch has no speed knob here: stretch without pitch change
            import librosa
            samples = librosa.effects.time_stretch(samples, rate=pace)
        return samples, self.engine.output_sample_rate


class Tone:
    """OpenVoice V2's tone-colour converter: the base voice's line in Navin's timbre (``BIE_VOICE_TONE``)."""

    def __init__(self, tone_file: Path | None = None, model_dir: Path | None = None):
        import numpy as np
        import torch
        from openvoice import utils
        from openvoice.models import SynthesizerTrn
        model_dir = model_dir or Path(os.environ.get("BIE_OPENVOICE_DIR") or
                                      Path(os.environ.get("BIE_HOME", "/var/lib/bie")) / "models" / "openvoice" / "converter")
        self.torch = torch
        self.hps = utils.get_hparams_from_file(str(model_dir / "config.json"))
        self.model = SynthesizerTrn(len(getattr(self.hps, "symbols", [])), self.hps.data.filter_length // 2 + 1,
                                    n_speakers=self.hps.data.n_speakers, **self.hps.model).eval()
        self.model.load_state_dict(torch.load(str(model_dir / "checkpoint.pth"), map_location="cpu")["model"], strict=False)
        self.rate = self.hps.data.sampling_rate
        self.target = torch.from_numpy(np.load(str(tone_file)).astype("float32")) if tone_file else None
        self.sources = {}

    def _spec(self, samples):
        from openvoice.mel_processing import spectrogram_torch
        d = self.hps.data
        return spectrogram_torch(self.torch.FloatTensor(samples).unsqueeze(0), d.filter_length, d.sampling_rate,
                                 d.hop_length, d.win_length, center=False)

    def tone_of(self, clips) -> "object":
        """The mean tone-colour vector of clips of one voice (each a few seconds of steady speech at ``self.rate``)."""
        with self.torch.no_grad():
            found = [self.model.ref_enc(self._spec(c).transpose(1, 2)).unsqueeze(-1) for c in clips if len(c) > self.rate]
        return self.torch.stack(found).mean(0)

    def convert(self, samples, rate: int, source_key: str, source_sample):
        """``source_sample`` () -> (samples, rate): a steady stretch of the base voice, asked for once per base voice."""
        import numpy as np
        samples = resample(samples, rate, self.rate)
        if source_key not in self.sources:                    # the base voice's own tone, once per base voice
            ref, ref_rate = source_sample()
            ref = resample(ref, ref_rate, self.rate)
            step = 8 * self.rate
            self.sources[source_key] = self.tone_of([ref[i:i + step] for i in range(0, len(ref), step)])
        with self.torch.no_grad():
            spec = self._spec(samples)
            out = self.model.voice_conversion(spec, self.torch.LongTensor([spec.size(-1)]), sid_src=self.sources[source_key],
                                              sid_tgt=self.target, tau=CONVERT_TAU)
        return np.asarray(out[0][0, 0].cpu().float().numpy(), dtype="float32"), self.rate


def resample(samples, rate: int, target: int):
    if rate == target:
        return samples
    import librosa
    return librosa.resample(samples, orig_sr=rate, target_sr=target)


# a steady stretch of each base voice for its own tone colour (said once per voice, never shown)
TONE_SAMPLE = {"hi": "Aaiye, aaj hum dekhte hain ki patte ke andar energy kaise banti hai, aur yeh kaam kaun karta hai.",
               "en": "Today we will see how a leaf turns sunlight into chemical energy, and which parts do the work.",
               "ta": "இன்று ஒரு இலை சூரிய ஒளியை எப்படி ஆற்றலாக மாற்றுகிறது என்று பார்ப்போம்.",
               "te": "ఈ రోజు ఒక ఆకు సూర్యకాంతిని ఎలా శక్తిగా మారుస్తుందో చూద్దాం.",
               "ml": "ഇന്ന് ഒരു ഇല സൂര്യപ്രകാശത്തെ എങ്ങനെ ഊർജമാക്കി മാറ്റുന്നു എന്ന് നോക്കാം.",
               "mr": "आज आपण पाहूया की एक पान सूर्यप्रकाशाचे ऊर्जेत कसे रूपांतर करते."}


def _tone_from_env() -> "Tone":
    tone_file = os.environ.get("BIE_VOICE_TONE", "")
    if not tone_file or not Path(tone_file).exists():
        raise FileNotFoundError("BIE_NARRATOR=navin needs BIE_VOICE_TONE (Navin's private tone file)")
    return Tone(Path(tone_file))


class Voice:
    def __init__(self, path: Path | None = None, *, fetch: bool = True, language: str = "hi", who: str | None = None,
                 tone: "Tone | None" = None, base_only: bool = False):
        who = who or narrator()
        if language in INDIC:
            self.engine = IndicEngine(language, who)
        elif language in KOKORO_VOICES[who]:
            self.engine = KokoroEngine(language, who, fetch=fetch, path=path)
        else:
            raise LookupError(f"no voice engine for {language!r} on this machine yet")
        self.language, self.who = language, who
        # base_only: the base voice alone (its timbre is changed later in one batch, ``tools/studio_revoice.py``)
        self.tone = None if base_only else (tone if tone is not None or who != "navin" else _tone_from_env())
        self.label = self.engine.label + (" · Navin ki tone" if self.tone else "")

    def say(self, text: str) -> dict:
        """{"uri": data URI (mp3 when ffmpeg is here, else wav), "dur": seconds}, said by BIE's teacher rules (``parts``)."""
        samples, rate = self.render(text)
        return clip(samples, rate)

    def render(self, text: str):
        """(samples, rate) of the line, said by BIE's teacher rules, in Navin's tone when a tone is set."""
        import numpy as np
        chunks, rate = [], 24000
        for part, pause in parts(text):
            made, rate = self.engine.speak(part, speed(part))
            chunks.append(made)
            if pause:
                chunks.append(np.zeros(int(rate * pause), dtype="float32"))
        samples = np.concatenate(chunks) if chunks else np.zeros(1, dtype="float32")
        if self.tone is not None and len(samples) > rate // 2:
            samples, rate = self.tone.convert(samples, rate, self.engine.label,
                                              lambda: self.engine.speak(TONE_SAMPLE.get(self.language, TONE_SAMPLE["en"]), SPEED))
        return samples, rate


def clip(samples, rate: int) -> dict:
    """{"uri": data URI (mp3 when ffmpeg is here, else wav), "dur": seconds} for the film player."""
    wav = wav_bytes(samples, rate)
    mp3 = to_mp3(wav)
    data, mime = (mp3, "audio/mpeg") if mp3 else (wav, "audio/wav")
    return {"uri": f"data:{mime};base64," + base64.b64encode(data).decode("ascii"), "dur": round(len(samples) / rate, 3)}


def wav_bytes(samples, rate: int) -> bytes:
    """16-bit mono WAV through the standard library (no audio library needed to write it)."""
    import wave
    import numpy as np
    pcm = (np.clip(np.asarray(samples, dtype="float32"), -1.0, 1.0) * 32767).astype("<i2").tobytes()
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(int(rate))
        out.writeframes(pcm)
    return buffer.getvalue()


def to_mp3(wav: bytes) -> bytes | None:
    if not shutil.which("ffmpeg"):
        return None
    done = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-b:a", "48k", "-f", "mp3", "pipe:1"],
                          input=wav, capture_output=True, timeout=120)
    return done.stdout if done.returncode == 0 and done.stdout else None


PLAYER_JS = Path(__file__).with_name("studio_voice_player.js")
VOICE_SLOT = "/*__VOICE__*/"


def with_player_voice(page: str) -> str:
    """The page with BIE's voice script (``studio_voice_player.js``) in its slot: the audio element with a data: URI first,
    Web Audio when the viewer refuses media loads, and a visible notice when neither can sound (Navin, 20 November 2026:
    the first films played silently)."""
    return page.replace(VOICE_SLOT, PLAYER_JS.read_text(encoding="utf-8"), 1)


def name(language: str = "hi") -> str:
    who = narrator()
    if language in INDIC:
        return f"indic-tts {language} {INDIC_SPEAKER[who]}"
    voice = KOKORO_VOICES[who].get(language)
    return f"kokoro {voice[0]}" if voice else "none"


def make(fetch: bool = True, language: str = "hi"):
    """A Voice, or None with the reason when this machine cannot speak yet (or not in this language)."""
    try:
        return Voice(fetch=fetch, language=language), None
    except Exception as exc:              # missing library, files or network: the film is still made, without voice
        return None, f"{type(exc).__name__}: {str(exc)[:200]}"
