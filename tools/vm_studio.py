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

    python -B tools/vm_studio.py --stage pyq --source <chapter PDF> --pyqs <questions JSON: https URL or file> --out <folder>

Stage ``pyq`` (``bie.brain.studio_pyq``, Navin, 19 November 2026): the PYQ lab. Each question (a PYQ, a question-book
question or an exercise question: id, exam, question, options, answer index, origin) becomes a visual investigation of its
concept in five stages, driven by one science model (``bie.brain.pyq_models``) that code checks; ``PYQ.html`` plays all of
the chapter's investigations on a phone, with ``pyq/<qid>.json`` and ``PYQS.md`` (question-level evidence and the
chapter-level reach kept apart).

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

STAGES = ("questions", "films", "games", "book", "pyq")
MAX_IMAGES_PER_FILM = 12
PLAYER = ROOT / "bie" / "brain" / "studio_player.html"
GAME_PLAYER = ROOT / "bie" / "brain" / "studio_game_player.html"
BOOK_PLAYER = ROOT / "bie" / "brain" / "studio_book_player.html"
PYQ_PLAYER = ROOT / "bie" / "brain" / "studio_pyq_player.html"
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


def vision_part(path, width: int = 1280) -> dict:
    """The picture as an image message part for a vision call (JPEG, at most ``width`` px wide)."""
    import base64
    import io
    from PIL import Image
    image = Image.open(path).convert("RGB")
    if image.width > width:
        image = image.resize((width, round(image.height * width / image.width)))
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=88)
    return {"type": "image", "media_type": "image/jpeg", "data": base64.b64encode(buffer.getvalue()).decode("ascii")}


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


def kept_pictures(source: str) -> list:
    """The picture cupboard (almaari): ``library.json`` in the from-run folder lists kept pictures, each with an id, its
    scale, what it shows, its labelled places and its file under ``library/`` in the same folder."""
    found = maybe_json(source, "library.json") if source else None
    out = []
    for e in (found or {}).get("pictures") or [] if isinstance(found, dict) else []:
        file = str(e.get("file") or "") if isinstance(e, dict) else ""
        if e.get("id") and file.startswith("library/") and ".." not in file and file.endswith((".png", ".jpg", ".webp")):
            out.append({"id": str(e["id"]), "type": str(e.get("type") or "cutaway"), "scale": str(e.get("scale") or ""),
                        "shows": str(e.get("shows") or ""), "places": [p for p in e.get("places") or [] if isinstance(p, dict)][:8],
                        "file": file, "set": str(e.get("set") or "")})
    return out


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
    terms = frozenset(studio.chapter_terms(pages)) if pages else frozenset()
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
        if pages:                                   # every book line taught, checked sentence by sentence (20 Nov 2026)
            q["book_lines"] = studio.book_lines(pages, ids)
            q["chapter_terms"] = terms
        q["other_questions"] = [f"{o.get('id')}: {o.get('question')}" for o in plan.get("questions") or []
                                if o.get("id") != q.get("id")]
        # the teacher's own script (Navin, 20 November 2026): teacher/<qid>.json in the from-run folder holds his lines
        # (and notes) and the earlier film; the film is made again with his lines as its narration
        teacher = maybe_json(args.from_run, f"teacher/{q['id']}.json")
        if isinstance(teacher, dict) and teacher.get("lines"):
            q["teacher_lines"] = [{"roman": str(x.get("roman") or ""), "note": str(x.get("note") or "")}
                                  for x in teacher["lines"] if isinstance(x, dict)]
            q["earlier_film"] = teacher.get("film") if isinstance(teacher.get("film"), dict) else {}
        q["library"] = kept_pictures(args.from_run)
        record = studio_film.write(client, model, q, course=args.course, language=args.language,
                                   chapter=plan.get("chapter_title", ""), max_rounds=args.max_rounds)
        for key in usage:
            usage[key] += record["usage"].get(key, 0)
        film = record.get("film") if isinstance(record.get("film"), dict) else {}
        images, audio, made, files, placed, kept = {}, {}, 0, {}, {}, 0
        shots = film.get("shots") or []
        for number, shot in enumerate(shots):
            if (shot.get("visual") or {}).get("type") in ("photo", "cutaway") and made < MAX_IMAGES_PER_FILM \
                    and hasattr(client, "generate_image"):
                target = out / "films" / "img" / f"{q['id']}-{shot.get('id')}.png"
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    entry = {e["id"]: e for e in q.get("library") or []}.get(((shot.get("visual") or {}).get("library") or "").strip())
                    saved = None
                    if entry:                        # a kept picture from the cupboard (Navin, 21 November 2026)
                        try:
                            target.write_bytes(read_bytes(args.from_run, entry["file"]))
                            saved, kept = target, kept + 1
                        except Exception as exc:
                            record["problems"] = record["problems"] + [f"{shot.get('id')}: kept picture {entry['id']} not read "
                                                                       f"({str(exc)[:80]}); a new one was drawn"]
                    if saved is None:
                        done = client.generate_image(studio_film.image_prompt(shot, film.get("look", "")), target)
                        saved = target.with_name(done["file"]) if isinstance(done, dict) and done.get("file") else target
                        saved = saved if saved.exists() else target
                        made += 1
                    # the labels go where the picture really shows their structure (Navin's Q14 review, 20 Nov 2026)
                    nxt = shots[number + 1] if number + 1 < len(shots) else None
                    placed[shot.get("id")] = studio_film.place(client, model, shot, nxt, vision_part(saved))
                    for key in usage:
                        usage[key] += int((placed[shot.get("id")].get("usage") or {}).get(key) or 0)
                    images[shot.get("id")] = image_uri(saved)
                    files[shot.get("id")] = saved.name
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
        covered = studio_film.coverage(film, q)
        (out / "films" / f"{q['id']}.json").write_text(json.dumps({"film": film, "problems": record["problems"],
                                                                   "rounds": record["rounds"], "images": files,
                                                                   "book_lines": q.get("book_lines") or [],
                                                                   "placement": placed},
                                                                  ensure_ascii=False, indent=1),
                                                       encoding="utf-8")
        if q.get("book_lines"):                     # Navin's NCERT-to-film page (a review page, never the learner's)
            (out / "films" / f"{q['id']}-ncert.html").write_text(
                studio_film.coverage_page(film, q, chapter=plan.get("chapter_title", "")), encoding="utf-8")
        seconds = sum(s["dur"] for shot in data["shots"] for s in shot["sentences"])
        rows.append({"qid": q["id"], "question": q.get("question"), "shots": len(film.get("shots") or []), "images": made,
                     "minutes": round(seconds / 60, 1), "rounds": len(record["rounds"]), "problems": record["problems"],
                     "book_lines": f"{covered['taught']}/{covered['total']}", "beyond": len(covered["beyond"]),
                     "points_moved": sum(p.get("moved", 0) for p in placed.values()),
                     "teacher_lines": len(q.get("teacher_lines") or []),
                     "kept_pictures": kept,
                     "not_in_picture": [m for p in placed.values() for m in p.get("missing", [])]})
    lines = ["# Filmein", "", f"Awaaz: {summary['voice']}", ""]
    for row in rows:
        lines.append(f"- **{row['qid']}** {row['question']} · {row['shots']} shots · {row['images']} tasveerein · "
                     f"{row['minutes']} min · NCERT lines {row['book_lines']} · NCERT se bahar {row['beyond']} · "
                     f"tasveer dekhkar khiske points {row['points_moved']}"
                     + (f" · teacher ki {row['teacher_lines']} lines" if row.get("teacher_lines") else "")
                     + (f" · almaari se {row['kept_pictures']} tasveer" if row.get("kept_pictures") else "")
                     + (f" · kamiyan: {len(row['problems'])}" if row["problems"] else ""))
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


def read_pyqs(source: str) -> list:
    """The questions for the PYQ lab: a JSON list (or {"questions": [...]}) from an https URL or a file."""
    if source.startswith("https://"):
        import urllib.request
        with urllib.request.urlopen(urllib.request.Request(source, headers={"user-agent": "bie-studio/1"}), timeout=120) as r:
            data = json.loads(r.read(5 * 1024 * 1024).decode("utf-8"))
    else:
        data = json.loads(Path(source).read_text(encoding="utf-8"))
    items = data.get("questions") if isinstance(data, dict) else data
    out = []
    for n, item in enumerate(items or [], 1):
        if not isinstance(item, dict) or not item.get("question") or not isinstance(item.get("options") or [], list):
            raise ValueError(f"pyqs item {n}: needs question and options")
        answer = item.get("answer")
        out.append({"id": str(item.get("id") or f"pyq{n:02d}"), "exam": str(item.get("exam") or ""),
                    "origin": item.get("origin") if item.get("origin") in ("pyq", "practice", "exercise") else "pyq",
                    "question": str(item["question"]), "options": [str(o) for o in item.get("options") or []],
                    "answer": answer if isinstance(answer, int) and 0 <= answer < len(item.get("options") or []) else None})
    if not out:
        raise ValueError("the pyqs file has no questions")
    return out


def pyq(args, client, model, pages, out: Path, summary: dict, *, voice_maker=None):
    from bie.brain import studio_pyq, studio_voice
    questions = read_pyqs(args.pyqs)
    blocks, teach = studio.all_blocks(pages), studio.teachable(pages)
    text = studio.chapter_text(pages)
    voice, why = (voice_maker or studio_voice.make)()
    summary["voice"] = "kokoro hf_alpha" if voice else f"no voice ({why}); the player uses the browser's voice or captions"
    records, usage, audio = [], {"input_tokens": 0, "output_tokens": 0}, {}
    (out / "pyq").mkdir(exist_ok=True)
    for q in questions:
        record = studio_pyq.write(client, model, q, course=args.course, language=args.language, chapter_text=text,
                                  block_ids=set(blocks), max_rounds=args.max_rounds)
        for key in usage:
            usage[key] += record["usage"].get(key, 0)
        records.append(record)
        for stage in record["lesson"].get("stages") or []:
            for k, beat in enumerate(stage.get("beats") or []):
                if voice:
                    try:
                        audio[(q["id"], stage.get("key"), k)] = voice.say(beat.get("voice") or beat.get("say") or "")
                    except Exception:
                        pass
        saved = {k: v for k, v in record.items() if k != "model"}
        saved["model"] = {k: (sorted(v) if isinstance(v, set) else v) for k, v in record["model"].items() if k != "data"}
        (out / "pyq" / f"{q['id']}.json").write_text(json.dumps(saved, ensure_ascii=False, indent=1, default=str),
                                                     encoding="utf-8")
    title = args.course or "PYQ Lab"
    data = studio_pyq.player_data([r for r in records if r["lesson"]], title=title, tint=studio.subject_tint(args.course),
                                  audio=audio, voice=summary["voice"])
    (out / "PYQ.html").write_text(studio_pyq.html(data, PYQ_PLAYER.read_text(encoding="utf-8")), encoding="utf-8")
    cover = studio_pyq.coverage(records, set(teach))
    (out / "PYQS.md").write_text(studio_pyq.markdown(records, cover, title=title), encoding="utf-8")
    rows = [{"qid": r["question"]["id"], "kind": r["model"].get("kind"),
             "proved": (r["model"].get("answer_option") + 1) if r["model"].get("answer_option") is not None else None,
             "key": (r["question"]["answer"] + 1) if isinstance(r["question"].get("answer"), int) else None,
             "verified": r["model"].get("verified"), "rounds": len(r["rounds"]), "problems": r["problems"]} for r in records]
    summary.update(pyq=rows, coverage=cover["chapter"], usage=usage, model=model,
                   status="ok" if rows and not any(r["problems"] for r in rows) else ("needs_fix" if rows else "failed"))


def run(args, *, client=None, load=None, voice_maker=None, read=None) -> dict:
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
            source_hash, page_count, pages = load((read or read_pdf)(args.source), args.pages or None, with_images=False)
            summary.update(source_sha256=source_hash, page_count=page_count, pages_read=[p.number for p in pages])
        if args.stage in ("films", "games", "book", "pyq"):
            if args.stage == "pyq":
                pyq(args, client, model, pages, out, summary, voice_maker=voice_maker)
            elif args.stage == "films":
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
    parser.add_argument("--pyqs", default="", help="pyq: the questions JSON (https URL or file)")
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
    if args.stage == "pyq" and not (args.source and args.pyqs):
        parser.error("--source and --pyqs are needed for pyq")
    if args.stage in ("films", "games", "book") and not args.from_run:
        parser.error(f"--from-run is needed for {args.stage}")
    summary = run(args)
    print(json.dumps({k: summary.get(k) for k in ("status", "questions", "coverage", "voice", "error")}, ensure_ascii=False))
    return 0 if summary["status"] in ("ok", "needs_fix") else 1


if __name__ == "__main__":
    raise SystemExit(main())
