#!/usr/bin/env python3
"""Say a finished studio film again with another voice: a language's own engine, or Navin's tone colour.

    python3 tools/studio_revoice.py --page <film .html> --film <film .json> --language hi|en|ta|te|ml|mr --out <page .html>
           [--narrator navin --tone <private tone.npy>]

The page gives the pictures and the film's frame (title, question, colours); the film JSON (a ``films/<qid>.json`` or
``dub/<lang>/<qid>.json`` record) gives every sentence's voice line. Each sentence is said by ``bie.brain.studio_voice``
(BIE's teacher pauses), and the page is built again by ``studio_film.player_data``, so the motion's timing follows the new
voice. With ``--narrator navin`` the voice is in Navin's timbre and the page is private: it must be written outside the
repository and is shared only with him (``docs/roadmap/VOICE_CLIP_METHOD.md``).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MARK = "const F="


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


def revoice(page: str, record: dict, voice, *, template: str) -> tuple[str, dict]:
    from bie.brain import studio_film
    data = page_data(page)
    film = film_of(record)
    images = {s.get("id"): s.get("img") for s in data.get("shots") or [] if s.get("img")}
    audio, rows, started = {}, [], time.process_time()
    for shot in film.get("shots") or []:
        for k, sentence in enumerate(shot.get("sentences") or []):
            line = sentence.get("voice") or sentence.get("roman") or ""
            clip = voice.say(line)
            audio[(shot.get("id"), k)] = clip
            rows.append({"line": f"{shot.get('id')}.{k}", "seconds": clip["dur"]})
    question = {"id": data.get("qid"), "question": data.get("question")}
    rebuilt = studio_film.player_data(film, images=images, audio=audio, chapter=data.get("chapter") or "", question=question,
                                      tint=data.get("tint") or "#2c6e87")
    seconds = sum(r["seconds"] for r in rows)
    cpu = time.process_time() - started
    return studio_film.html(rebuilt, template), {"lines": len(rows), "voice_seconds": round(seconds, 1),
                                                 "cpu_seconds": round(cpu, 1), "cpu_per_voice_second": round(cpu / max(seconds, 1e-6), 2),
                                                 "voice": getattr(voice, "label", ""), "per_line": rows}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--page", required=True)
    parser.add_argument("--film", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--narrator", choices=("female", "navin"), default="female")
    parser.add_argument("--tone", default="", help="navin: his private tone .npy (tools/voice_tone.py)")
    args = parser.parse_args(argv)
    out = Path(args.out).resolve()
    if args.narrator == "navin":
        if out == ROOT or ROOT in out.parents:
            parser.error("a page in Navin's voice is private: --out must be outside the repository")
        if not args.tone or not Path(args.tone).exists():
            parser.error("--narrator navin needs --tone (his private tone file)")
    from bie.brain import studio_voice
    tone = studio_voice.Tone(Path(args.tone)) if args.narrator == "navin" else None
    voice = studio_voice.Voice(language=args.language, who=args.narrator, tone=tone)
    template = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
    page, report = revoice(Path(args.page).read_text(encoding="utf-8"),
                           json.loads(Path(args.film).read_text(encoding="utf-8")), voice, template=template)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    if args.narrator == "navin":
        out.chmod(0o600)
    out.with_suffix(".voice.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "per_line"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
