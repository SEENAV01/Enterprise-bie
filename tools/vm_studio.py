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

    python -B tools/vm_studio.py --stage dub --from-run <films run> --source <same PDF> --language ta,te,ml,mr,en --out <folder>

Stage ``dub`` (``bie.brain.studio_dub``, Navin, 21 November 2026): autodub. Each finished film of the from-run is said
again in each language (the screen lines, title and everyday labels in that language, technical terms in English), checked
by code line by line; ``dub/<lang>/<qid>.html`` plays it with the same pictures and motion, voiced when the machine has
that language's voice engine, with ``dub/<lang>/<qid>.json`` and ``DUB.md``.

    python -B tools/vm_studio.py --stage script --from-run <naksha run (or understand run)> --out <folder>

Stage ``script`` (``bie.brain.studio_script``, Navin, 22 November 2026): the whole chapter's script in one teacher's words,
heading by heading, each heading checked by code before the next (``script.json``, ``SCRIPT.md``, ``SCRIPT.html``).

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

STAGES = ("questions", "naksha", "script", "films", "games", "book", "pyq", "dub")
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


def cupboard(args) -> list:
    """The pictures a film may take again: the cupboard named by the job (``--library``) first, then any cupboard kept in
    the from-run folder; one id once. Navin, 24 November 2026: the first 11.6.3b film's real dam "almari mein bhi thi
    hamare paas", yet the remake drew a new one, because the cupboard lived only beside the script run it came from."""
    out, seen = [], set()
    for source in (getattr(args, "library", "") or "", args.from_run):
        for entry in kept_pictures(source) if source else []:
            if entry["id"] not in seen:
                seen.add(entry["id"])
                out.append(dict(entry, source=source))
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


def naksha(args, client, model, out: Path, summary: dict):
    """Stage ``naksha`` (Navin, 21 November 2026): from Section 1's chapter map (``from_run``: an understand run) BIE
    writes the chapter file and asks for the two naksha, shape A (films by student question inside each heading) and
    shape B (one heading, one film), each checked by code; their films become this run's questions (a01..., b01...)."""
    from bie.brain import chapter_file, studio_naksha
    chapter = read_json(args.from_run, "chapter_map.json")
    course = dict(chapter.get("course") or {})
    for pair in filter(None, (part.strip() for part in (args.course or "").split(";"))):
        if "=" in pair:
            key, value = pair.split("=", 1)
            course[key.strip()] = value.strip()
    (out / "chapter_map.json").write_text(json.dumps(chapter, ensure_ascii=False), encoding="utf-8")   # for the script stage
    (out / "CHAPTER.md").write_text(chapter_file.markdown(chapter), encoding="utf-8")
    (out / "SAMAJH.html").write_text(chapter_file.html(chapter), encoding="utf-8")
    (out / "chapter_file.json").write_text(json.dumps(chapter_file.build(chapter), ensure_ascii=False, indent=1), encoding="utf-8")
    records, usage = [], {"input_tokens": 0, "output_tokens": 0}
    for shape in studio_naksha.SHAPES:
        record = studio_naksha.plan(client, model, chapter, shape, course=course, language=args.language,
                                    max_rounds=args.max_rounds)
        records.append(record)
        for key in usage:
            usage[key] += record["usage"].get(key, 0)
    (out / "naksha.json").write_text(studio_naksha.dump({r["shape"]: r["answer"] for r in records}), encoding="utf-8")
    (out / "record.json").write_text(studio_naksha.dump(records), encoding="utf-8")
    questions = [q for r in records if isinstance(r.get("answer"), dict) for q in studio_naksha.questions(chapter, r["answer"])]
    plan = {"chapter_title": (chapter.get("map") or {}).get("chapter_title") or course.get("title", ""), "naksha": True,
            "questions": questions}
    (out / "questions.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "NAKSHA.md").write_text(studio_naksha.markdown(chapter, records), encoding="utf-8")
    (out / "NAKSHA.html").write_text(studio_naksha.html(chapter, records), encoding="utf-8")
    left = [p for r in records for p in r["problems"]]
    summary.update(status="ok" if not left else "needs_fix", usage=usage, model=model,
                   shapes={r["shape"]: {"films": len((r.get("answer") or {}).get("films") or []), "rounds": len(r["rounds"]),
                                        "problems": r["problems"][:10],
                                        "minutes": sum(f.get("minutes") or 0 for f in (r.get("answer") or {}).get("films") or [])}
                           for r in records},
                   coverable=len(studio_naksha.coverable(chapter)))


def script(args, client, model, out: Path, summary: dict):
    """Stage ``script`` (Navin, 22 November 2026: "poore chapter ki ek script, phir video ke tukde"): from a naksha run (its
    ``chapter_map.json`` and, as ideas, its ``naksha.json``) or an understand run, the whole chapter's script, heading by
    heading, each heading checked by code before the next; saved after every heading so a stopped run keeps its work."""
    from bie.brain import studio_script
    chapter = read_json(args.from_run, "chapter_map.json")
    plans = maybe_json(args.from_run, "naksha.json")
    course = dict(chapter.get("course") or {})
    for pair in filter(None, (part.strip() for part in (args.course or "").split(";"))):
        if "=" in pair:
            key, value = pair.split("=", 1)
            course[key.strip()] = value.strip()

    (out / "chapter_map.json").write_text(json.dumps(chapter, ensure_ascii=False), encoding="utf-8")   # for the films
    if isinstance(plans, dict):
        (out / "naksha.json").write_text(json.dumps(plans, ensure_ascii=False), encoding="utf-8")

    def save(record):
        (out / "script.json").write_text(studio_script.dump({"chapter_title": (chapter.get("map") or {}).get("chapter_title", ""),
                                                             "parts": record["parts"]}), encoding="utf-8")
        (out / "record.json").write_text(studio_script.dump({"rounds": record["rounds"], "problems": record["problems"],
                                                             "usage": record["usage"]}), encoding="utf-8")
        (out / "SCRIPT.md").write_text(studio_script.markdown(chapter, record), encoding="utf-8")
        (out / "SCRIPT.html").write_text(studio_script.html(chapter, record), encoding="utf-8")

    record = studio_script.write(client, model, chapter, course=course, naksha=plans if isinstance(plans, dict) else None,
                                 language=args.language, max_rounds=args.max_rounds, on_part=save)
    save(record)
    summary.update(status="ok" if not record["problems"] else "needs_fix", usage=record["usage"], model=model,
                   script=studio_script.counts(chapter, record["parts"]),
                   rounds={r["section"] or "opening": len(r["rounds"]) for r in record["rounds"]},
                   problems={k: v[:5] for k, v in record["problems"].items()})


PARTS_WORKER = ROOT / "tools" / "picture_parts_worker.py"
PARTS_TIMEOUT = 900


def parts_python():
    """The python that can cut parts: BIE_PARTS_PYTHON, else the studio machine's voice environment (torch and
    transformers at tools/vm_voice.py's pinned versions; the first voice job made it). None when neither is here: the film
    then plays uncut and its report says so; it never installs torch by itself."""
    import os
    named = os.environ.get("BIE_PARTS_PYTHON")
    if named:
        return named if Path(named).exists() else None
    python = Path(os.environ.get("BIE_HOME") or "/var/lib/bie") / "voice-venv" / "bin" / "python"
    return str(python) if python.exists() else None


def layer_uri(path, scale: float = 1.0) -> str:
    """A cut part as a data URI that keeps its transparency (WEBP with alpha), at the scale its picture is shown."""
    import base64
    import io
    from PIL import Image
    image = Image.open(path).convert("RGBA")
    if scale < 1:
        image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))))
    buffer = io.BytesIO()
    image.save(buffer, "WEBP", quality=85)
    return "data:image/webp;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def image_width(path, default: int = 1600) -> int:
    """A picture's width, the file closed after reading it."""
    if not path:
        return default
    from PIL import Image
    with Image.open(path) as image:
        return image.width


def spin_of(path, scale: float = 1.0) -> dict | None:
    """A spinning part seen from the side, drawn turning (bie/brain/part_spin.py); None for a wheel facing us (the player
    turns it in the picture's plane) or if the frames could not be drawn (the part keeps its old way)."""
    from bie.brain import part_spin
    try:
        return part_spin.spin_layer(path, scale)
    except Exception:                                   # a part that cannot be drawn turning still plays
        return None


def cut_parts(film: dict, placed: dict, paths: dict, folder: Path, *, python=None, run=None):
    """Cut every acted part of the film's pictures (bie/brain/picture_parts.py, in the voice environment, the model loaded
    once per film). Returns ({shot id: [{id, img, box, centre}]}, {shot id: plate path}, report); a part that was not
    found or not cut cleanly is named in the report's problems and plays uncut."""
    import os
    import subprocess
    from PIL import Image
    from bie.brain import studio_film
    report = {"wanted": 0, "cut": 0, "problems": [], "parts": {}}
    shots = []
    for shot in film.get("shots") or []:
        sid = shot.get("id")
        acted = studio_film.acted_parts(shot)
        if not acted:
            continue
        report["wanted"] += len(acted)
        wanted = studio_film.part_requests(shot, (placed.get(sid) or {}).get("parts") or {})
        missing = [p.get("id") for p in acted if p.get("id") not in {w["id"] for w in wanted}]
        if missing:
            report["problems"].append(f"{sid}: parts not found in the picture: {', '.join(map(str, missing))}")
        if wanted and paths.get(sid):
            shots.append({"id": sid, "image": str(paths[sid]), "parts": wanted})
    if not shots:
        return {}, {}, report
    python = python or parts_python()
    if not python:
        report["problems"].append("parts not cut: the cutting environment (torch and transformers) is not on this machine")
        return {}, {}, report
    folder.mkdir(parents=True, exist_ok=True)
    request, result_path = folder / "request.json", folder / "result.json"
    request.write_text(json.dumps({"threads": os.cpu_count(), "out": str(folder), "shots": shots}, indent=1), encoding="utf-8")
    env = dict(os.environ, HF_HOME=str(Path(os.environ.get("BIE_HOME") or "/var/lib/bie") / "parts-models"),
               HF_HUB_DISABLE_TELEMETRY="1")
    try:
        (run or subprocess.run)([python, "-B", str(PARTS_WORKER), "--request", str(request), "--result", str(result_path)],
                                env=env, timeout=PARTS_TIMEOUT, check=False)
    except subprocess.TimeoutExpired:
        pass
    result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {"error": "the cutter wrote no result"}
    if result.get("error"):
        report["problems"].append(f"parts not cut: {str(result['error'])[:160]}")
    layers, plates = {}, {}
    spinning = {(shot.get("id"), a.get("part")) for shot in film.get("shots") or [] for s in shot.get("sentences") or []
                for a in s.get("acts") or [] if a.get("do") == "spin"}
    for row in result.get("shots") or []:
        sid = row.get("id")
        if row.get("error"):
            report["problems"].append(f"{sid}: parts not cut ({str(row['error'])[:120]})")
            continue
        width = image_width(paths.get(sid))
        scale = min(1.0, 1600 / max(1, width))
        for got in row.get("layers") or []:
            report["parts"][f"{sid}.{got.get('id')}"] = {k: got.get(k) for k in ("area", "score", "box", "problems")}
            if got.get("problems"):
                report["problems"].append(f"{sid}: part {got.get('id')} not cut cleanly ({'; '.join(got['problems'])})")
            elif got.get("file") and Path(got["file"]).exists():
                layer = {"id": got["id"], "img": layer_uri(got["file"], scale), "box": got["box"], "centre": got.get("centre")}
                if (sid, got["id"]) in spinning:
                    spin = spin_of(got["file"], scale)
                    if spin:
                        layer["spin"] = spin
                    report["parts"][f"{sid}.{got['id']}"]["turns"] = spin["axis"] if spin else "facing"
                layers.setdefault(sid, []).append(layer)
                report["cut"] += 1
        if row.get("plate") and Path(row["plate"]).exists():
            plates[sid] = Path(row["plate"])
    return layers, plates, report


def films(args, client, model, pages, out: Path, summary: dict, *, voice_maker=None):
    from bie.brain import studio_film, studio_voice
    wanted = [q.strip() for q in (args.videos or "").split(",") if q.strip()]
    script = maybe_json(args.from_run, "script.json")
    if isinstance(script, dict) and script.get("parts"):
        # a script run (Navin, 22 November 2026): one film per heading, its narration the script's lines; the chapter map
        # and the plan come from the script run, else from --chapter-map (the naksha run the script was written from)
        base = args.chapter_map or args.from_run
        from bie.brain import studio_script
        plans = maybe_json(base, "naksha.json")
        plan = studio_script.film_questions(script, read_json(base, "chapter_map.json"),
                                            plans if isinstance(plans, dict) else None, wanted)
    else:
        plan = read_json(args.from_run, "questions.json")
    if pages and not plan.get("naksha"):            # an older question list: the unit's opening page moves to its overview
        plan = studio.with_unit_overview(plan, pages)
    questions = [q for q in plan.get("questions") or [] if not wanted or q.get("id") in wanted]
    blocks = studio.all_blocks(pages) if pages else {}
    terms = frozenset(studio.chapter_terms(pages)) if pages else frozenset()
    voice, why = (voice_maker or studio_voice.make)()
    summary["voice"] = studio_voice.name() if voice else f"no voice ({why})"
    template = PLAYER.read_text(encoding="utf-8")
    (out / "films").mkdir(exist_ok=True)
    (out / "questions.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    rows, usage = [], {"input_tokens": 0, "output_tokens": 0}
    def one(q):
        q = dict(q)
        ids = [i for p in q.get("points") or [] for i in p.get("block_ids") or []]
        q["source_text"] = "\n".join(f"[{i}] {blocks[i]}" for i in dict.fromkeys(ids) if i in blocks)
        if pages:                                   # every book line taught, checked sentence by sentence (20 Nov 2026)
            q["book_lines"] = studio.book_lines(pages, ids)
            q["chapter_terms"] = terms
        q["other_questions"] = [] if q.get("naksha") else [f"{o.get('id')}: {o.get('question')}" for o in plan.get("questions") or []
                                                           if o.get("id") != q.get("id")]
        # the teacher's own script (Navin, 20 November 2026): teacher/<qid>.json in the from-run folder holds his lines
        # (and notes) and the earlier film; the film is made again with his lines as its narration
        teacher = None if q.get("script_lines") else maybe_json(args.from_run, f"teacher/{q['id']}.json")
        if isinstance(teacher, dict) and teacher.get("lines"):
            q["teacher_lines"] = [{"roman": str(x.get("roman") or ""), "note": str(x.get("note") or "")}
                                  for x in teacher["lines"] if isinstance(x, dict)]
            q["earlier_film"] = teacher.get("film") if isinstance(teacher.get("film"), dict) else {}
        q["library"] = cupboard(args)
        record = studio_film.write(client, model, q, course=args.course, language=args.language,
                                   chapter=plan.get("chapter_title", ""), max_rounds=args.max_rounds, look=getattr(args, "look", "") or None)
        for key in usage:
            usage[key] += record["usage"].get(key, 0)
        film = record.get("film") if isinstance(record.get("film"), dict) else {}
        images, audio, made, files, placed, kept, paths = {}, {}, 0, {}, {}, 0, {}
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
                            target.write_bytes(read_bytes(entry.get("source") or args.from_run, entry["file"]))
                            saved, kept = target, kept + 1
                        except Exception as exc:
                            record["problems"] = record["problems"] + [f"{shot.get('id')}: kept picture {entry['id']} not read "
                                                                       f"({str(exc)[:80]}); a new one was drawn"]
                    if saved is None:
                        done = client.generate_image(studio_film.image_prompt(shot, film.get("look", ""),
                                                                                 getattr(args, "look", "") or None),
                                                     target)
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
                    paths[shot.get("id")] = saved
                except Exception as exc:             # one failed picture does not stop the film; the report names it
                    record["problems"] = record["problems"] + [f"{shot.get('id')}: image not made ({str(exc)[:120]})"]
            for k, sentence in enumerate(shot.get("sentences") or []):
                if voice:
                    try:
                        audio[(shot.get("id"), k)] = voice.say(sentence.get("voice") or sentence.get("roman") or "")
                    except Exception as exc:         # a line left unvoiced is timed by its text; the report names it
                        record["problems"] = record["problems"] + [f"{shot.get('id')} sentence {k + 1}: not voiced "
                                                                   f"({type(exc).__name__}: {str(exc)[:80]})"]
        # the parts that move, cut out of their pictures (Navin's routeS choice, 23 November 2026)
        layers, plates, cut_report = cut_parts(film, placed, paths, out / "films" / "parts" / q["id"])
        record["problems"] = record["problems"] + cut_report["problems"]
        images.update({sid: image_uri(path) for sid, path in plates.items()})
        data = studio_film.player_data(film, images=images, audio=audio, chapter=plan.get("chapter_title", ""), question=q,
                                       tint=studio.subject_tint(args.course), parts=layers)
        (out / "films" / f"{q['id']}.html").write_text(studio_film.html(data, template), encoding="utf-8")
        covered = studio_film.coverage(film, q)
        (out / "films" / f"{q['id']}.json").write_text(json.dumps({"film": film, "problems": record["problems"],
                                                                   "rounds": record["rounds"], "images": files,
                                                                   "book_lines": q.get("book_lines") or [],
                                                                   "placement": placed, "parts": cut_report},
                                                                  ensure_ascii=False, indent=1),
                                                       encoding="utf-8")
        if cut_report["wanted"]:                    # Navin's page of the parts that move (a review page)
            (out / "films" / f"{q['id']}-hisse.html").write_text(
                studio_film.acts_page(film, cut_report, question=q, chapter=plan.get("chapter_title", "")), encoding="utf-8")
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
                     "parts_cut": cut_report["cut"], "parts_wanted": cut_report["wanted"],
                     "not_in_picture": [m for p in placed.values() for m in p.get("missing", [])]})

    for q in questions:
        try:
            one(q)
        except Exception as exc:                    # one film that fails does not stop the others; its row says why
            if getattr(exc, "kind", None) == "plan_limit":
                raise
            rows.append({"qid": q.get("id"), "question": q.get("question"), "shots": 0, "images": 0, "minutes": 0, "rounds": 0,
                         "problems": [f"the film was not made: {type(exc).__name__}: {str(exc)[:200]}"], "book_lines": "0/0",
                         "beyond": 0, "points_moved": 0, "teacher_lines": 0, "kept_pictures": 0, "not_in_picture": [],
                         "failed": True})
    lines = ["# Filmein", "", f"Awaaz: {summary['voice']}", ""]
    for row in rows:
        lines.append(f"- **{row['qid']}** {row['question']} · {row['shots']} shots · {row['images']} tasveerein · "
                     f"{row['minutes']} min · NCERT lines {row['book_lines']} · NCERT se bahar {row['beyond']} · "
                     f"tasveer dekhkar khiske points {row['points_moved']}"
                     + (f" · hilte hisse {row['parts_cut']}/{row['parts_wanted']}" if row.get("parts_wanted") else "")
                     + (f" · teacher ki {row['teacher_lines']} lines" if row.get("teacher_lines") else "")
                     + (f" · almaari se {row['kept_pictures']} tasveer" if row.get("kept_pictures") else "")
                     + (f" · kamiyan: {len(row['problems'])}" if row["problems"] else ""))
    (out / "FILMS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary.update(films=rows, usage=usage, model=model,
                   status="ok" if rows and not any(r["problems"] for r in rows) else ("needs_fix" if any(not r.get("failed") for r in rows) else "failed"))


def games(args, client, model, pages, out: Path, summary: dict):
    from bie.brain import studio_game
    plan = read_json(args.from_run, "questions.json")
    if pages:
        plan = studio.with_unit_overview(plan, pages)
    wanted = [q.strip() for q in (args.videos or "").split(",") if q.strip()]
    # the unit's overview is seen, not revised: no game stage of its own
    questions = [q for q in plan.get("questions") or [] if (not wanted or q.get("id") in wanted) and not q.get("overview")]
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
    if pages:
        plan = studio.with_unit_overview(plan, pages)
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


def dub(args, client, model, pages, out: Path, summary: dict, *, voice_maker=None):
    """Stage ``dub`` (Navin, 21 November 2026): the from-run's finished films said again in each language of
    ``--language`` (codes: ta, te, ml, mr, en; comma-separated), the screen lines and labels in that language with the
    technical terms in English, and the voice from the language's engine when this machine has one."""
    from bie.brain import studio_dub, studio_film, studio_voice
    # codes separated by commas or spaces (the VM's job check allows letters and spaces in "language": "ta te ml")
    languages = [x for x in (args.language or "").replace(",", " ").split() if x]
    unknown = [x for x in languages if x not in studio_dub.LANGUAGES]
    if not languages or unknown:
        raise ValueError(f"--language for dub: codes from {', '.join(studio_dub.LANGUAGES)} (got {args.language!r})")
    plan = read_json(args.from_run, "questions.json")
    wanted = [q.strip() for q in (args.videos or "").split(",") if q.strip()]
    questions = [q for q in plan.get("questions") or [] if not wanted or q.get("id") in wanted]
    known = frozenset(studio.chapter_terms(pages)) if pages else frozenset()
    template = PLAYER.read_text(encoding="utf-8")
    rows, usage = [], {"input_tokens": 0, "output_tokens": 0}
    voices = {}
    for language in languages:
        voices[language] = (voice_maker or studio_voice.make)(language=language)
    summary["voice"] = {x: (studio_voice.name(x) if v[0] else f"no voice ({v[1]})") for x, v in voices.items()}
    for q in questions:
        made = maybe_json(args.from_run, f"films/{q['id']}.json") or {}
        film = made.get("film") if isinstance(made.get("film"), dict) else None
        if not film:
            rows.append({"qid": q["id"], "language": "-", "lines": 0, "rounds": 0, "voice": "-",
                         "problems": ["the from-run has no film for this question"]})
            continue
        images = {}
        for shot_id, name in (made.get("images") or {}).items():
            try:
                images[shot_id] = image_uri(read_bytes(args.from_run, f"films/img/{name}"))
            except Exception:
                pass
        for language in languages:
            record = studio_dub.dub(client, model, film, q, language, course=args.course, known=known,
                                    max_rounds=args.max_rounds)
            for key in usage:
                usage[key] += record["usage"].get(key, 0)
            folder = out / "dub" / language
            folder.mkdir(parents=True, exist_ok=True)
            voice = voices[language][0]
            audio = {}
            if record["film"] and voice:
                for shot in record["film"].get("shots") or []:
                    for k, sentence in enumerate(shot.get("sentences") or []):
                        try:
                            audio[(shot.get("id"), k)] = voice.say(sentence.get("voice") or sentence.get("roman") or "")
                        except Exception as exc:     # timed by its text; the record names it
                            record["problems"] = list(record.get("problems") or []) + [
                                f"{shot.get('id')} sentence {k + 1}: not voiced ({type(exc).__name__}: {str(exc)[:80]})"]
            if record["film"]:
                data = studio_film.player_data(record["film"], images=images, audio=audio, chapter=plan.get("chapter_title", ""),
                                               question=record["question"], tint=studio.subject_tint(args.course))
                (folder / f"{q['id']}.html").write_text(studio_film.html(data, template), encoding="utf-8")
            (folder / f"{q['id']}.json").write_text(studio_dub.to_json({k: v for k, v in record.items() if k != "usage"}),
                                                    encoding="utf-8")
            rows.append({"qid": q["id"], "language": language, "lines": len(studio_dub.line_ids(film)),
                         "rounds": len(record["rounds"]), "problems": record["problems"],
                         "voice": studio_voice.name(language) if voice else "nahi (text se samay)",
                         "voiced_lines": len(audio)})
    (out / "DUB.md").write_text(studio_dub.markdown(rows), encoding="utf-8")
    (out / "questions.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    summary.update(dubs=rows, usage=usage, model=model,
                   status="ok" if rows and not any(r["problems"] for r in rows) else ("needs_fix" if any(not r.get("failed") for r in rows) else "failed"))


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
                    except Exception as exc:         # timed by its text; the record names it
                        record["problems"] = list(record.get("problems") or []) + [
                            f"{stage.get('key')} beat {k + 1}: not voiced ({type(exc).__name__}: {str(exc)[:80]})"]
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
                   status="ok" if rows and not any(r["problems"] for r in rows) else ("needs_fix" if any(not r.get("failed") for r in rows) else "failed"))


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
        if args.stage in ("naksha", "script", "films", "games", "book", "pyq", "dub"):
            if args.stage == "naksha":
                naksha(args, client, model, out, summary)
            elif args.stage == "script":
                script(args, client, model, out, summary)
            elif args.stage == "dub":
                dub(args, client, model, pages, out, summary, voice_maker=voice_maker)
            elif args.stage == "pyq":
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
    parser.add_argument("--chapter-map", default="", help="films from a script run: the run whose chapter_map.json and "
                        "naksha.json the script was written from (when the script run does not keep them)")
    parser.add_argument("--from-run", default="", help="naksha: an understand run (chapter_map.json); films, games, book: the "
                        "earlier run (folder or https URL) with questions.json")
    parser.add_argument("--videos", default="", help="films, games, book: only these question ids, for example q01,q02")
    parser.add_argument("--library", default="", help="films: a picture cupboard (folder or https URL with library.json and "
                        "library/) whose kept pictures the film may take again")
    parser.add_argument("--look", default="", help="films: how the pictures are drawn (glossy, mixed, matte, structure, "
                        "close_up, overview; studio_film.FILM_STYLE when not given)")
    parser.add_argument("--pyqs", default="", help="pyq: the questions JSON (https URL or file)")
    parser.add_argument("--out", required=True)
    parser.add_argument("--pages", default="")
    parser.add_argument("--course", default="")
    parser.add_argument("--language", default="Hinglish", help="dub: the target language codes, for example 'ta te ml mr en'")
    parser.add_argument("--model", default="")
    parser.add_argument("--max-rounds", type=int, default=3)
    args = parser.parse_args(argv)
    args.max_rounds = max(1, min(6, args.max_rounds))
    if args.stage == "questions" and not args.source:
        parser.error("--source is needed for questions")
    if args.stage == "pyq" and not (args.source and args.pyqs):
        parser.error("--source and --pyqs are needed for pyq")
    if args.stage in ("naksha", "script", "films", "games", "book", "dub") and not args.from_run:
        parser.error(f"--from-run is needed for {args.stage}")
    summary = run(args)
    print(json.dumps({k: summary.get(k) for k in ("status", "questions", "coverage", "voice", "error")}, ensure_ascii=False))
    return 0 if summary["status"] in ("ok", "needs_fix") else 1


if __name__ == "__main__":
    raise SystemExit(main())
