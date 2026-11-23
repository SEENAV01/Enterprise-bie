#!/usr/bin/env python3
"""Say a finished studio film again with another voice: a language's own engine, or Navin's voice.

    python3 tools/studio_revoice.py --page <film .html> --film <film .json> --language hi|en|ta|te|ml|mr --out <page .html>
           [--narrator navin --converter chatterbox --target <his clip> --voice-python <voice venv python>
            --private <folder>]
           [--narrator navin --converter openvoice --tone <his tone.npy>] [--pace 1.05]
           [--narrator navin --converter chatterbox ... --base female]

The page gives the pictures and the film's frame (title, question, colours); the film JSON (a ``films/<qid>.json`` or
``dub/<lang>/<qid>.json`` record) gives every sentence's voice line. Each sentence is said by ``bie.brain.studio_voice``
(BIE's teacher pauses), and the page is built again by ``studio_film.player_data``, so the motion's timing follows the new
voice.

Navin's voice (cards of 21 November 2026, "6: Kokoro + Chatterbox badlaav"): the base voice (Kokoro, or Indic-TTS for
Tamil, Telugu, Malayalam and Marathi) says every line, then Chatterbox's voice conversion turns all lines into his voice
in one batch, inside the private voice environment (``tools/vm_voice_worker.py``, convert request), with ``--target`` a
clean clip of his reading. OpenVoice (``--converter openvoice``) stays as the faster, less close way. A page in his
voice is private: it and its working files are written outside the repository and shared only with him
(``docs/roadmap/VOICE_CLIP_METHOD.md``).

``--base female`` (Chatterbox only) lets the female voice say every line and turns it into his timbre, so his copy keeps
the female voice's way of speaking: its pauses and its rise and fall (Navin, 23 November 2026, after the two 11.6.3b
films: "sara kamal aawaj ka hai aur screen ke sath uske talmel ka ... female voice ... uske pattern ko pakdo wo meri
aawaj par lagao"); the default male base keeps the male voice's.

``--pace`` says the film at another base pace (Navin, 22 November 2026: 1.00 now, and a 1.05 copy of the next films for his
ear before he chooses); the pictures and motion stay, only the voice and its timing change.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MARK = "const F="
WORKER = ROOT / "tools" / "vm_voice_worker.py"


def page_data(page: str) -> dict:
    """The film data a player page carries (``const F=<json>;``)."""
    at = page.find(MARK)
    if at < 0:
        raise ValueError("not a BIE film page (no film data)")
    data, _ = json.JSONDecoder().raw_decode(page, at + len(MARK))
    return data


def film_of(record: dict) -> dict:
    film = record.get("film") if isinstance(record.get("film"), dict) else record
    if not isinstance(film, dict) or not film.get("shots"):
        raise ValueError("the film JSON has no shots")
    return film


def lines_of(film: dict) -> list:
    """[(key "s1-0", (shot id, k), voice line)] in film order."""
    return [(f"{shot.get('id')}-{k}", (shot.get("id"), k), sentence.get("voice") or sentence.get("roman") or "")
            for shot in film.get("shots") or [] for k, sentence in enumerate(shot.get("sentences") or [])]


def read_wav(path: Path):
    import numpy as np
    with wave.open(str(path), "rb") as w:
        rate, frames = w.getframerate(), w.readframes(w.getnframes())
    return np.frombuffer(frames, dtype="<i2").astype("float32") / 32767.0, rate


def chatterbox_convert(base: dict, *, target: Path, private: Path, python: str, worker: Path = WORKER,
                       revision: str = "", threads: int | None = None) -> tuple[dict, dict]:
    """{key: base WAV path} in Navin's voice through one worker run: ({key: (samples, rate)}, worker result)."""
    if not revision:
        from vm_voice import MODEL_REVISION as revision        # the pinned Chatterbox model (tools/vm_voice.py)
    out = private / "converted"
    request = {"convert": [{"key": k, "wav": str(v)} for k, v in base.items()], "target": str(target),
               "audio_dir": str(out), "model_revision": revision, "threads": threads}
    (private / "request.json").write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
    subprocess.run([python, str(worker), "--request", str(private / "request.json"), "--result", str(private / "result.json")],
                   check=False, timeout=6 * 3600)
    result = json.loads((private / "result.json").read_text(encoding="utf-8"))
    made = {k: read_wav(out / f"{k}.wav") for k in base if (out / f"{k}.wav").exists()}
    return made, result


def revoice(page: str, record: dict, voice, *, template: str, convert=None, private: Path | None = None) -> tuple[str, dict]:
    """The page said again by ``voice``; with ``convert`` ({key: wav path} -> ({key: (samples, rate)}, result)) every
    line is first said by the base voice into ``private`` and then turned to the new voice in one batch."""
    from bie.brain import studio_film, studio_voice
    data = page_data(page)
    film = film_of(record)
    images = {s.get("id"): s.get("img") for s in data.get("shots") or [] if s.get("img")}
    audio, rows, started, worker = {}, [], time.process_time(), {}
    todo = lines_of(film)
    refused = [key for key, _, line in todo if studio_voice.unsaid(line, getattr(voice, "language", "hi"))]
    todo = [row for row in todo if row[0] not in refused]       # a sign the voice cannot say: timed by text, reported
    if convert is None:
        for key, where, line in todo:
            audio[where] = voice.say(line)
    else:
        base = private / "base"
        base.mkdir(parents=True, exist_ok=True)
        files = {}
        for key, where, line in todo:
            samples, rate = voice.render(line)
            files[key] = base / f"{key}.wav"
            files[key].write_bytes(studio_voice.wav_bytes(samples, rate))
        made, worker = convert(files)
        for key, where, line in todo:
            if key in made:
                audio[where] = studio_voice.clip(*made[key])
            else:                                    # a line the converter did not make keeps the base voice; reported
                audio[where] = studio_voice.clip(*read_wav(files[key]))
                rows.append({"line": key, "not_converted": True})
    for key, where, _ in todo:
        rows.append({"line": key, "seconds": audio[where]["dur"]})
    question = {"id": data.get("qid"), "question": data.get("question")}
    rebuilt = studio_film.player_data(film, images=images, audio=audio, chapter=data.get("chapter") or "", question=question,
                                      tint=data.get("tint") or "#2c6e87")
    seconds = sum(r.get("seconds", 0) for r in rows)
    cpu = time.process_time() - started
    report = {"lines": len(todo), "voice_seconds": round(seconds, 1), "cpu_seconds": round(cpu, 1),
              "voice": getattr(voice, "label", ""), "not_converted": [r["line"] for r in rows if r.get("not_converted")],
              "not_voiced": refused,
              "converter": {k: v for k, v in worker.items() if k in ("status", "error", "load_s", "threads")} if worker else None,
              "convert_seconds": round(sum(x.get("compute_s", 0) for x in worker.get("converted", [])), 1) if worker else None,
              "per_line": [r for r in rows if "seconds" in r]}
    return studio_film.html(rebuilt, template), report


def studio_pace_range() -> tuple:
    from bie.brain import studio_voice
    return studio_voice.PACE_RANGE


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--page", required=True)
    parser.add_argument("--film", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--narrator", choices=("female", "navin"), default="female")
    parser.add_argument("--converter", choices=("chatterbox", "openvoice"), default="chatterbox")
    parser.add_argument("--tone", default="", help="openvoice: his private tone .npy (tools/voice_tone.py)")
    parser.add_argument("--target", default="", help="chatterbox: a clean clip of his reading (private)")
    parser.add_argument("--voice-python", default="", help="chatterbox: the voice environment's python")
    parser.add_argument("--private", default="", help="chatterbox: a private working folder outside the repository")
    parser.add_argument("--pace", type=float, default=None, help="the base pace (1.00 by default; 1.05 for Navin's ear)")
    parser.add_argument("--base", choices=("male", "female"), default="male",
                        help="chatterbox: the base voice his timbre is put on; female keeps the female voice's way of "
                             "speaking (Navin, 23 November 2026: \"female voice ... uske pattern ko pakdo wo meri aawaj par lagao\")")
    args = parser.parse_args(argv)
    if args.pace is not None and not (studio_pace_range()[0] <= args.pace <= studio_pace_range()[1]):
        parser.error(f"--pace must be between {studio_pace_range()[0]} and {studio_pace_range()[1]}")
    out = Path(args.out).resolve()
    private = Path(args.private).resolve() if args.private else None
    if args.narrator == "navin":
        for where in (out, private):
            if where is not None and (where == ROOT or ROOT in where.parents):
                parser.error("Navin's voice is private: --out and --private must be outside the repository")
        if args.converter == "openvoice" and (not args.tone or not Path(args.tone).exists()):
            parser.error("--converter openvoice needs --tone (his private tone file)")
        if args.converter == "chatterbox" and not (args.target and Path(args.target).exists() and args.voice_python and private):
            parser.error("--converter chatterbox needs --target, --voice-python and --private")
    from bie.brain import studio_voice
    convert = None
    if args.narrator == "navin" and args.converter == "chatterbox":
        private.mkdir(mode=0o700, parents=True, exist_ok=True)
        sys.path.insert(0, str(ROOT / "tools"))
        voice = studio_voice.Voice(language=args.language, who="female" if args.base == "female" else "navin",
                                   base_only=True, pace=args.pace)

        def convert(files):
            return chatterbox_convert(files, target=Path(args.target), private=private, python=args.voice_python)
    else:
        tone = studio_voice.Tone(Path(args.tone)) if args.narrator == "navin" else None
        voice = studio_voice.Voice(language=args.language, who=args.narrator, tone=tone, pace=args.pace)
    template = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
    page, report = revoice(Path(args.page).read_text(encoding="utf-8"),
                           json.loads(Path(args.film).read_text(encoding="utf-8")), voice, template=template,
                           convert=convert, private=private)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    if args.narrator == "navin":
        out.chmod(0o600)
    out.with_suffix(".voice.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "per_line"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
