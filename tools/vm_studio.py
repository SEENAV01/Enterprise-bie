"""The course studio on Navin's Codex machine (VM job section ``studio``; Navin, 18 November 2026).

    python -B tools/vm_studio.py --stage questions --source <chapter PDF: https URL or file> --out <folder>
           [--pages 1-30] [--course "Class 11 Geography, NCERT level"] [--language Hinglish] [--max-rounds 3]

Stage ``questions`` (``bie.brain.studio``): the chapter's student questions, pillars and per-question film and game plan,
checked by code against every teachable block of the chapter; Navin says yes to the list before the films are made.
The maker is Codex on the ChatGPT plan (read-only, no shell, no files: the chapter text goes in the message), so no
rupees are billed; the plan's usage is read before and after.

Writes ``questions.json``, ``QUESTIONS.md`` (the list for Navin), ``record.json`` (rounds and problems) and
``SUMMARY.json`` (what the job runner reports).

    python -B tools/vm_studio.py --stage films --from-run <questions run: folder or https URL> --source <same PDF> --out <folder>
           [--videos q01,q02]

Stage ``films`` (``bie.brain.studio_film``), after Navin's yes to the question list: per question the maker writes the film
(shots, sentences, pins, arrows, effects, diagram SVG), Codex image_gen makes each photo shot's picture through the plan,
Kokoro speaks every sentence (``bie.brain.studio_voice``), and ``bie/brain/studio_player.html`` turns it into one film that
plays in a phone browser (``films/<qid>.html``), with ``films/<qid>.json`` (the film without media) and ``FILMS.md``.
The films run keeps a copy of ``questions.json``, so the later stages read one run.

    python -B tools/vm_studio.py --stage games --from-run <films run (or questions run)> --source <same PDF> --out <folder>
           [--videos q01,q02]

Stage ``games`` (``bie.brain.studio_game``): one game stage per question (an SVG scene and one to five rounds whose every
choice visibly does something), checked by code; ``GAME.html`` is the whole chapter's game for a phone browser (pillars
as worlds), with ``games/<qid>.json`` and ``GAMES.md``. When the from-run has films, each stage gets the film's takeaway
lines and its first picture as the stage's banner.

    python -B tools/vm_studio.py --stage book --from-run <films run> --source <same PDF> --out <folder> [--videos q01,q02]

Stage ``book`` (``bie.brain.studio_book``): the Living Book. Per question the maker writes the note cards (together they
cover every point), a class moment with Asha, Dev and the Teacher, a "yaad rakho" line and a check question; code adds
the film's picture with its pins, its diagram and its takeaway lines. ``BOOK.html`` is the chapter's notes for a phone
browser, linking each question to ``films/<qid>.html`` and ``GAME.html#<qid>`` of the same course folder.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import studio  # noqa: E402

STAGES = ("questions", "films", "games", "book")
MAX_IMAGES_PER_FILM = 12
PLAYER = ROOT / "bie" / "brain" / "studio_player.html"
GAME_PLAYER = ROOT / "bie" / "brain" / "studio_game_player.html"
BOOK_PLAYER = ROOT / "bie" / "brain" / "studio_book_player.html"
MAX_PDF_BYTES = 120 * 1024 * 1024


def read_pdf(source: str) -> bytes:
    if source.startswith("https://"):
        import urllib.request
        request = urllib.request.Request(source, headers={"user-agent": "bie-studio/1"})
        with urllib.request.urlopen(request, timeout=180) as response:
            data = response.read(MAX_PDF_BYTES + 1)
    else:
        data = Path(source).read_bytes()
    if len(data) > MAX_PDF_BYTES:
        raise ValueError("the PDF is larger than 120 MB")
    if not data.startswith(b"%PDF"):
        raise ValueError("the source is not a PDF")
    return data


def read_bytes(source: str, name: str, limit: int = 40 * 1024 * 1024) -> bytes:
    if source.startswith("https://"):
        import urllib.request
        url = source.rstrip("/") + "/" + name
        with urllib.request.urlopen(urllib.request.Request(url, headers={"user-agent": "bie-studio/1"}), timeout=120) as r:
            return r.read(limit)
    return (Path(source) / name).read_bytes()


def read_json(source: str, name: str) -> dict:
    return json.loads(read_bytes(source, name, 20 * 1024 * 1024).decode("utf-8"))


def maybe_json(source: str, name: str):
    try:
        return read_json(source, name)
    except Exception:                                # a film that was not made: the later stage works without it
        return None


def image_uri(path, width: int = 1600) -> str:
    """The picture as a WebP data URI, at most ``width`` px wide (the film is one file that works offline)."""
    import base64
    import io
    from PIL import Image
    image = Image.open(path if not isinstance(path, (bytes, bytearray)) else io.BytesIO(path)).convert("RGB")
    if image.width > width:
        image = image.resize((width, round(image.height * width / image.width)))
    buffer = io.BytesIO()
    image.save(buffer, "WEBP", quality=82)
    return "data:image/webp;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def films(args, client, model, pages, out: Path, summary: dict, *, voice_maker=None):
    from bie.brain import studio_film, studio_voice
    plan = read_json(args.from_run, "questions.json")
    wanted = [q.strip() for q in (args.videos or "").split(",") if q.strip()]
    questions = [q for q in plan.get("questions") or [] if not wanted or q.get("id") in wanted]
    blocks = studio.all_blocks(pages) if pages else {}
    voice, why = (voice_maker or studio_voice.make)()
    summary["voice"] = "kokoro hf_alpha" if voice else f"no voice ({why})"
    template = PLAYER.read_text(encoding="utf-8")
    (out / "films").mkdir(exist_ok=True)
    (out / "questions.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    rows, usage = [], {"input_tokens": 0, "output_tokens": 0}
    for q in questions:
        q = dict(q)
        ids = [i for p in q.get("points") or [] for i in p.get("block_ids") or []]
        q["source_text"] = "\n".join(f"[{i}] {blocks[i]}" for i in dict.fromkeys(ids) if i in blocks)
        record = studio_film.write(client, model, q, course=args.course, language=args.language,
                                   chapter=plan.get("chapter_title", ""), max_rounds=args.max_rounds)
        for key in usage:
            usage[key] += record["usage"].get(key, 0)
        film = record.get("film") if isinstance(record.get("film"), dict) else {}
        images, audio, made, files = {}, {}, 0, {}
        for shot in film.get("shots") or []:
            if (shot.get("visual") or {}).get("type") == "photo" and made < MAX_IMAGES_PER_FILM and hasattr(client, "generate_image"):
                target = out / "films" / "img" / f"{q['id']}-{shot.get('id')}.png"
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    done = client.generate_image(studio_film.image_prompt(shot), target)
                    saved = target.with_name(done["file"]) if isinstance(done, dict) and done.get("file") else target
                    saved = saved if saved.exists() else target
                    images[shot.get("id")] = image_uri(saved)
                    files[shot.get("id")] = saved.name
                    made += 1
                except Exception as exc:             # one failed picture does not stop the film; the report names it
                    record["problems"] = record["problems"] + [f"{shot.get('id')}: image not made ({str(exc)[:120]})"]
            for k, sentence in enumerate(shot.get("sentences") or []):
                if voice:
                    try:
                        audio[(shot.get("id"), k)] = voice.say(sentence.get("voice") or sentence.get("roman") or "")
                    except Exception:
                        pass
        data = studio_film.player_data(film, images=images, audio=audio, chapter=plan.get("chapter_title", ""), question=q,
                                       tint=studio.subject_tint(args.course))
        (out / "films" / f"{q['id']}.html").write_text(studio_film.html(data, template), encoding="utf-8")
        (out / "films" / f"{q['id']}.json").write_text(json.dumps({"film": film, "problems": record["problems"],
                                                                   "rounds": record["rounds"], "images": files},
                                                                  ensure_ascii=False, indent=1),
                                                       encoding="utf-8")
        seconds = sum(s["dur"] for shot in data["shots"] for s in shot["sentences"])
        rows.append({"qid": q["id"], "question": q.get("question"), "shots": len(film.get("shots") or []), "images": made,
                     "minutes": round(seconds / 60, 1), "rounds": len(record["rounds"]), "problems": record["problems"]})
    lines = ["# Filmein", "", f"Awaaz: {summary['voice']}", ""]
    for row in rows:
        lines.append(f"- **{row['qid']}** {row['question']} · {row['shots']} shots · {row['images']} tasveerein · "
                     f"{row['minutes']} min" + (f" · kamiyan: {len(row['problems'])}" if row["problems"] else ""))
    (out / "FILMS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary.update(films=rows, usage=usage, model=model,
                   status="ok" if rows and not any(r["problems"] for r in rows) else ("needs_fix" if rows else "failed"))


def games(args, client, model, pages, out: Path, summary: dict):
    from bie.brain import studio_game
    plan = read_json(args.from_run, "questions.json")
    wanted = [q.strip() for q in (args.videos or "").split(",") if q.strip()]
    questions = [q for q in plan.get("questions") or [] if not wanted or q.get("id") in wanted]
    blocks = studio.all_blocks(pages) if pages else {}
    (out / "games").mkdir(exist_ok=True)
    (out / "questions.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    stages, heroes, photos, rows, usage = [], {}, {}, [], {"input_tokens": 0, "output_tokens": 0}
    for q in questions:
        q = dict(q)
        ids = [i for p in q.get("points") or [] for i in p.get("block_ids") or []]
        q["source_text"] = "\n".join(f"[{i}] {blocks[i]}" for i in dict.fromkeys(ids) if i in blocks)
        made = maybe_json(args.from_run, f"films/{q['id']}.json") or {}
        film = made.get("film") if isinstance(made.get("film"), dict) else {}
        q["film_keys"] = "\n".join(f"- {s.get('key')}" for s in film.get("shots") or [] if s.get("key"))
        files = made.get("images") or {}
        q["film_photos"] = [studio_game.film_photo(shot) for shot in film.get("shots") or [] if shot.get("id") in files]
        for name in files.values():
            try:
                heroes[q["id"]] = image_uri(read_bytes(args.from_run, f"films/img/{name}"), 1200)
                break
            except Exception:
                continue
        record = studio_game.write(client, model, q, course=args.course, language=args.language,
                                   chapter=plan.get("chapter_title", ""), max_rounds=args.max_rounds)
        shot = (record.get("stage") or {}).get("photo_shot") if isinstance(record.get("stage"), dict) else None
        if shot in files:
            try:
                photos[(q["id"], shot)] = image_uri(read_bytes(args.from_run, f"films/img/{files[shot]}"), 1600)
            except Exception as exc:              # the stage still plays; the report says the photo is missing
                record["problems"] = record["problems"] + [f"film photo {shot} not read ({str(exc)[:80]})"]
        for key in usage:
            usage[key] += record["usage"].get(key, 0)
        stage = record.get("stage") if isinstance(record.get("stage"), dict) else None
        (out / "games" / f"{q['id']}.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        if stage and not record["problems"]:
            stages.append({"qid": q["id"], "stage": stage})
        rows.append({"qid": q["id"], "question": q.get("question"), "rounds": len((stage or {}).get("rounds") or []),
                     "look": (stage or {}).get("backdrop"),
                     "mechanics": sorted({r.get("mechanic") for r in (stage or {}).get("rounds") or []}),
                     "maker_rounds": len(record["rounds"]), "problems": record["problems"]})
    data = studio_game.player_data(stages, plan=plan, tint=studio.subject_tint(args.course), heroes=heroes, photos=photos)
    (out / "GAME.html").write_text(studio_game.html(data, GAME_PLAYER.read_text(encoding="utf-8")), encoding="utf-8")
    lines = ["# Game", "", f"{len(stages)} / {len(rows)} sawaalon ke stage bane (GAME.html).", ""]
    for row in rows:
        look = {"film_photo": "film ki photo par", "illustration": "illustration"}.get(row["look"], "")
        lines.append(f"- **{row['qid']}** {row['question']} · {row['rounds']} round · {', '.join(row['mechanics'])} · {look}"
                     + (f" · kamiyan: {len(row['problems'])}" if row["problems"] else ""))
    (out / "GAMES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary.update(games=rows, stages=len(stages), usage=usage, model=model,
                   status="ok" if rows and len(stages) == len(rows) else ("needs_fix" if stages else "failed"))


def book(args, client, model, pages, out: Path, summary: dict):
    from bie.brain import studio_book
    plan = read_json(args.from_run, "questions.json")
    wanted = [q.strip() for q in (args.videos or "").split(",") if q.strip()]
    questions = [q for q in plan.get("questions") or [] if not wanted or q.get("id") in wanted]
    blocks = studio.all_blocks(pages) if pages else {}
    (out / "book").mkdir(exist_ok=True)
    (out / "questions.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    sections, rows, usage = [], [], {"input_tokens": 0, "output_tokens": 0}
    for q in questions:
        q = dict(q)
        ids = [i for p in q.get("points") or [] for i in p.get("block_ids") or []]
        q["source_text"] = "\n".join(f"[{i}] {blocks[i]}" for i in dict.fromkeys(ids) if i in blocks)
        made = maybe_json(args.from_run, f"films/{q['id']}.json") or {}
        film = made.get("film") if isinstance(made.get("film"), dict) else {}
        q["film_text"] = "\n".join(s.get("roman", "") for shot in film.get("shots") or [] for s in shot.get("sentences") or [])
        images = {}
        for sid, name in (made.get("images") or {}).items():
            try:
                images[sid] = image_uri(read_bytes(args.from_run, f"films/img/{name}"), 1200)
            except Exception:
                continue
        record = studio_book.write(client, model, q, course=args.course, language=args.language,
                                   chapter=plan.get("chapter_title", ""), max_rounds=args.max_rounds)
        for key in usage:
            usage[key] += record["usage"].get(key, 0)
        (out / "book" / f"{q['id']}.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        notes = record.get("notes") if isinstance(record.get("notes"), dict) else None
        if notes:
            sections.append({"qid": q["id"], "notes": notes, "figures": studio_book.film_figures(film, images),
                             "film_link": f"films/{q['id']}.html" if film else "", "game_link": f"GAME.html#{q['id']}"})
        rows.append({"qid": q["id"], "question": q.get("question"), "cards": len((notes or {}).get("cards") or []),
                     "picture": bool(images), "maker_rounds": len(record["rounds"]), "problems": record["problems"]})
    data = studio_book.player_data(sections, plan=plan, tint=studio.subject_tint(args.course))
    (out / "BOOK.html").write_text(studio_book.html(data, BOOK_PLAYER.read_text(encoding="utf-8")), encoding="utf-8")
    lines = ["# Living Book", "", f"{len(sections)} / {len(rows)} sawaalon ke notes bane (BOOK.html).", ""]
    for row in rows:
        lines.append(f"- **{row['qid']}** {row['question']} · {row['cards']} cards" + (" · film ki tasveer" if row["picture"] else "")
                     + (f" · kamiyan: {len(row['problems'])}" if row["problems"] else ""))
    (out / "BOOK.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    clean = sum(1 for r in rows if not r["problems"])
    summary.update(book=rows, sections=len(sections), usage=usage, model=model,
                   status="ok" if rows and clean == len(rows) else ("needs_fix" if sections else "failed"))


def run(args, *, client=None, load=None, voice_maker=None) -> dict:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    summary = {"schema": "bie.studio-run/1", "section": "studio", "stage": args.stage, "status": "failed",
               "maker": "codex on the ChatGPT plan (read-only, no shell)", "cost": {"total_inr": 0.0}, "error": None}
    try:
        if client is None:
            from bie.model_gateway.live.codex_client import DEFAULT_MODEL, CodexExecClient
            client = CodexExecClient()
            model = args.model or DEFAULT_MODEL
        else:
            model = args.model or "fake"
        if load is None:
            from bie.brain.pages import load_pages
            load = load_pages
        summary["plan_usage_before"] = _usage(client)
        pages = []
        if args.source:
            source_hash, page_count, pages = load(read_pdf(args.source), args.pages or None, with_images=False)
            summary.update(source_sha256=source_hash, page_count=page_count, pages_read=[p.number for p in pages])
        if args.stage in ("films", "games", "book"):
            if args.stage == "films":
                films(args, client, model, pages, out, summary, voice_maker=voice_maker)
            elif args.stage == "games":
                games(args, client, model, pages, out, summary)
            else:
                book(args, client, model, pages, out, summary)
            summary["plan_usage_after"] = _usage(client)
            raise _Done()
        record = studio.plan(client, model, pages, course=args.course, language=args.language,
                             max_rounds=args.max_rounds)
        (out / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        if isinstance(record.get("answer"), dict):
            (out / "questions.json").write_text(json.dumps(record["answer"], ensure_ascii=False, indent=1), encoding="utf-8")
        (out / "QUESTIONS.md").write_text(studio.markdown(record), encoding="utf-8")
        answer = record.get("answer") or {}
        summary.update(status="ok" if not record["problems"] else "needs_fix", rounds=len(record["rounds"]),
                       problems=record["problems"], coverage={k: v for k, v in (record.get("coverage") or {}).items()
                                                              if k != "missing"},
                       questions=len(answer.get("questions") or []), pillars=len(answer.get("pillars") or []),
                       usage=record["usage"], model=model)
        summary["plan_usage_after"] = _usage(client)
    except _Done:
        pass
    except Exception as exc:                        # the runner publishes the folder either way; the error says why
        summary["error"] = f"{type(exc).__name__}: {str(exc)[:400]}"
        kind = getattr(exc, "kind", None)
        if kind == "plan_limit":
            summary["stop_reason"] = "plan_limit"
    summary["minutes"] = round((time.time() - started) / 60, 1)
    (out / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


class _Done(Exception):
    pass


def _usage(client):
    reader = getattr(client, "plan_usage", None)
    return reader() if callable(reader) else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", choices=STAGES, default="questions")
    parser.add_argument("--source", default="")
    parser.add_argument("--from-run", default="", help="films, games, book: the earlier run (folder or https URL) with questions.json")
    parser.add_argument("--videos", default="", help="films, games, book: only these question ids, for example q01,q02")
    parser.add_argument("--out", required=True)
    parser.add_argument("--pages", default="")
    parser.add_argument("--course", default="")
    parser.add_argument("--language", default="Hinglish")
    parser.add_argument("--model", default="")
    parser.add_argument("--max-rounds", type=int, default=3)
    args = parser.parse_args(argv)
    args.max_rounds = max(1, min(6, args.max_rounds))
    if args.stage == "questions" and not args.source:
        parser.error("--source is needed for questions")
    if args.stage in ("films", "games", "book") and not args.from_run:
        parser.error(f"--from-run is needed for {args.stage}")
    summary = run(args)
    print(json.dumps({k: summary.get(k) for k in ("status", "questions", "coverage", "voice", "error")}, ensure_ascii=False))
    return 0 if summary["status"] in ("ok", "needs_fix") else 1


if __name__ == "__main__":
    raise SystemExit(main())
