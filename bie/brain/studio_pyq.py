"""The course studio's PYQ lab (Navin, 19 November 2026): a question becomes a visual investigation of its concept.

A PYQ, a question-book question or a chapter's exercise question is the doorway into the book's concept. The maker writes
one investigation per question in five teaching stages (see the question, understand the mistake, open the concept, watch
it solve, apply it to a new question). The science lives in one model (``bie.brain.pyq_models``): the main scene and the
enlarged detail view are both driven by it, and code takes every answer, intermediate value, bond change, charge and
chromosome count from it, never from the maker's prose. Code checks the whole lesson and sends the exact problems back
(``studio.ask``): stages, beats and their cues, prediction gates with a reason for every wrong action, one diagnosis per
option, question families recomputed by the model, book evidence that really is in the chapter, and no number in the
narration that the model did not produce. The player is ``bie/brain/studio_pyq_player.html``; the lesson is data.

Coverage is kept apart on purpose: a question's own evidence blocks (question level) and the share of the chapter's
teachable blocks that all the chapter's PYQs reach (chapter level). One solved PYQ never claims the chapter is taught.
"""
from __future__ import annotations

import json
import re

from . import pyq_models
from .studio import SOURCE_WORDS, ask
from .studio_book import CAUTION

N = {"type": "number"}
S = {"type": "string"}
I = {"type": "integer"}
B = {"type": "boolean"}
STAGES = ("see", "trap", "concept", "solve", "transfer")
STAGE_NAMES = {"see": "Sawal ko visualise karo", "trap": "Galti ko samjho", "concept": "Concept ko kholo",
               "solve": "Problem ko solve hote dekho", "transfer": "Naye sawal par lagao"}
MECHANICS = ("number", "choose", "tap_part", "pair", "order")
VIEWS = ("main", "detail", "both")
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
END = re.compile(r"[.?!।]\s*$")


def _obj(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def _arr(items: dict) -> dict:
    return {"type": "array", "items": items}


BEAT = _obj({"say": S, "voice": S, "view": {"type": "string", "enum": list(VIEWS)}, "focus": _arr(S), "labels": _arr(S),
             "moment": S, "play": B, "board": S, "detail": S, "gate": S})
SCHEMA = _obj({
    "title": S, "concept": S, "scene_title": S,
    "given": _arr(_obj({"name": S, "value": S})), "asked": S, "unknowns": _arr(S), "assumptions": _arr(S),
    "objectives": _arr(S), "prerequisites": _arr(_obj({"idea": S, "why": S})),
    "evidence": _arr(_obj({"block_ids": _arr(S), "idea": S, "parts": _arr(S), "moment": S})),
    "model": _obj({"kind": {"type": "string", "enum": list(pyq_models.KINDS)}, "lines": _arr(S), "svg": S}),
    "stages": _arr(_obj({"key": {"type": "string", "enum": list(STAGES)}, "title": S, "text": S, "beats": _arr(BEAT)})),
    "details": _arr(_obj({"id": S, "title": S, "text": S, "chain": _arr(S), "focus": _arr(S), "moment": S})),
    "gates": _arr(_obj({"id": S, "mechanic": {"type": "string", "enum": list(MECHANICS)}, "prompt": S, "choices": _arr(S),
                        "answer": S, "tolerance": N, "wrong": _arr(_obj({"match": S, "why": S})), "reveal": S, "why": S})),
    "board": _arr(_obj({"step": S, "note": S})),
    "diagnoses": _arr(_obj({"option": I, "title": S, "why": S, "shows": S})),
    "families": _arr(_obj({"id": S, "title": S, "question": S, "changes": _arr(S), "choices": _arr(S), "correct": I,
                           "why": S, "transfer": B})),
    "recap": S, "limitations": _arr(S),
})

INSTRUCTIONS = """You are BIE's PYQ teacher for {course}. Turn ONE exam question into a visual investigation that teaches the
book concept behind it. Learner-facing language: {language} (natural spoken Hinglish in Roman script for "say", the same
sentence in Devanagari for "voice", which the narrator speaks). A correct option alone is not understanding.

THE MODEL (the single source of truth; code computes every number, structure and count from it)
- model.kind "projectile": lines like "u = 280 m/s", "theta = 30 deg", "g = 9.8 m/s2", "sin = 0.5" (only if the question
  gives it), "asked = max_height|time_to_peak|flight_time|range", optional 'ref = 828 m "Burj Khalifa"'. Code works out
  u, theta, g, s, c, uy, ux, uy2, two_g, H (or t_up, T, R) and traps H_one_sin, H_whole_u (or t_whole_u, T_half,
  R_up_only). Parts: launcher projectile path v vx vy gravity height peak ground range ref ghost. Moments: launch rise
  peak descent land.
- model.kind "numeric": any other numerical question. lines: 'given <name> = <number> <unit> "<meaning>"',
  'step <name> = <expression> : <unit> "<meaning>"', 'trap <name> = <expression> : <unit> "<the mistake>"',
  'answer <name>'. Expressions use + - * / ^, sqrt, sin(deg), cos(deg). Units are checked.
- model.kind "mechanism": atom-mapped SMILES and electron-pair arrows. 'reactant <mapped SMILES>' (map EVERY atom an
  arrow touches, including a hydrogen that moves, e.g. [C:3]([H:9])), 'label <map> <tag>' for atom tracking tags like
  C2, 'step <id> <what happens>: <arrow>; <arrow>' with arrows 'lp D -> A' (lone pair of D makes the D-A bond),
  'bond A-B -> B' (the pair goes to B), 'shift G A -> B' (group G moves from A to the next atom B WITH its bond pair),
  'pi A-B -> B-C'; 'trap <id> after <step id|start> <the student's wrong idea>: <arrows>'; 'option <n> <SMILES>' for
  each structure option. Code applies the arrows, checks lone pairs, valence and charge, finds every carbocation and
  whether a 1,2-shift would make it more stable, and decides which option is the product. Never force a shift that
  does not make a more stable carbocation; never miss one that does. Parts: atom ids a<map> and bonds a1-a2. Moments:
  start, each step id, each trap id. In the acid step show both arrows: the O lone pair takes H, the H-Br pair goes to Br.
- model.kind "fusion": 'diploid <2n>' (if counts matter), 'entity <id> "<label>" <cell|nucleus|gamete|structure>
  sets=<n count> origin=<maternal|paternal|none> in=<cell id> at=<x>,<y> nuclei=<count>' (at in percent of the scene),
  'fuse <id> "<name>": a + b [+ c] -> <product id> "<label>" fate="<what it becomes>"', 'asked sequence 1 2 3' or
  'asked count|sets|ratio <id>' or 'asked cells|nuclei', and for a sequence question 'option <n> = id, id, id'. Code adds
  the sets, keeps maternal and paternal shares, counts cells and nuclei apart. Parts: the entity and product ids.
  Moments: start, entry (gametes travel in), each fuse id, end.
- model.kind "scene": every other subject. svg: one labelled SVG (viewBox, gradients, depth, an id on every part you
  will point at; no script, no images, no style element); lines: 'moment <id> "<label>"' and 'key <moment> <part id>
  x=<dx> y=<dy> scale=<s> opacity=<o>' to move parts at a moment. Code checks its structure only.

THE LESSON
- stages: exactly five, in this order: see (show the scenario; what is given, what is asked; let the learner tell the
  relevant quantity from the tempting one before any formula), trap (show the plausible wrong idea and exactly which
  assumption or operation fails), concept (the book concept and its prerequisites, using the detail view for the
  mechanism), solve (every operation tied to the scene: why the equation applies before substituting, signs, the square,
  the decimal, units; or each bond and charge change; or each set added), transfer (change ONE meaningful feature and
  apply the same concept). Scene count and length follow the concept, not a template.
- beats: what the teacher says while the scene shows it. say: complete, natural sentences (8+ words), terms explained in
  everyday words, never a formula read aloud without its meaning ("Is arrow ko dekho. Yeh poori speed nahi, upar wali
  speed hai."). view main|detail|both; focus and labels: part ids; moment: a model moment ("" to hold); play: animate
  through the moment; board: the solving-board step this beat explains (a model step name, mechanism step id or fusion
  id; "" if none); detail: a detail id to open ("" if none); gate: a gate id that waits after this beat ("" if none).
- details: the enlarged causal views (at least 2): id, title, text, chain = exactly three short lines [source/given,
  operation/event, result/meaning], focus parts, moment.
- gates (at least 3; one in concept, one in solve): prediction before the action is shown. mechanic: number (answer = a
  model value name such as uy, or a literal number; tolerance relative, e.g. 0.01), choose (choices; answer = the right
  index as text, "0"), tap_part (answer = a part id), pair (answer = "source>target", e.g. the electron-pair donor and
  acceptor "a8>a3", or a gamete and its target), order (choices; answer = the right order of indexes "2,0,1"). wrong:
  for each tempting wrong action, match (the wrong index / part / pair / a model value name such as u, or "other") and
  why = the exact misconception behind it, in a full sentence. reveal: the moment played when the learner is right.
  why: the teacher's reason after the action is seen. No timers anywhere.
- board: the solving-board rows in order, each a model step (code writes the numbers) with a note on why it follows.
- diagnoses: one per option (option is 1-based): title and why, the reasoning behind choosing it; shows: the trap id
  that produces it, or "".
- families: at least 2 question types this concept makes (height / time to peak / flight time / range / ratio;
  chromosome numbers / maternal:paternal; shift / no shift...). changes: model lines that change (e.g. "u = 140 m/s",
  "asked = range", "diploid 20"); choices; correct (1-based; code recomputes it for projectile, numeric and fusion);
  why. Mark exactly one transfer true: the new question the learner solves alone at the end.
- evidence: the book ideas this lesson uses: block_ids (from the chapter text below), idea (a short paraphrase, never an
  invented quotation, page or figure number), parts and moment that show it.
- given, asked, unknowns, assumptions (scientific simplifications such as no air drag), objectives, prerequisites,
  recap. limitations: model limits for the review page only (never shown to the learner).
- Never name the source or the book on the learner's screen; no caution lines ("illustrative", "assume") in say.
- Every number you write in say, text, details, gates, diagnoses or families must be one the model produces, one the
  question gives, or a small count. Code checks this.

The question:
{question}

Answer with the JSON object only."""

PROBLEMS_PROMPT = ("BIE's code checked the investigation and found these problems. Send the whole corrected JSON object "
                   "again:\n- ")


def messages(question: dict, *, course: str, language: str, chapter_text: str) -> list:
    shown = {k: question.get(k) for k in ("id", "exam", "question", "options", "origin")}
    shown["key"] = (f"option {question['answer'] + 1}" if isinstance(question.get("answer"), int) else "not given")
    return [{"role": "system", "content": INSTRUCTIONS.format(course=course or "exam learners",
                                                              language=language or "Hinglish",
                                                              question=json.dumps(shown, ensure_ascii=False, indent=1))},
            {"role": "user", "content": "The chapter's text blocks (cite their ids as evidence):\n\n" + chapter_text}]


def learner_texts(lesson: dict):
    for stage in lesson.get("stages") or []:
        yield f"stage {stage.get('key')}", stage.get("text") or ""
        for k, beat in enumerate(stage.get("beats") or [], 1):
            yield f"stage {stage.get('key')} beat {k}", beat.get("say") or ""
    for d in lesson.get("details") or []:
        yield f"detail {d.get('id')}", " ".join([d.get("text") or ""] + list(d.get("chain") or []))
    for g in lesson.get("gates") or []:
        yield f"gate {g.get('id')}", " ".join([g.get("prompt") or "", g.get("why") or ""] + list(g.get("choices") or []) +
                                              [w.get("why") or "" for w in g.get("wrong") or []])
    for d in lesson.get("diagnoses") or []:
        yield f"diagnosis {d.get('option')}", (d.get("title") or "") + " " + (d.get("why") or "")
    yield "recap", lesson.get("recap") or ""


def problems(lesson, question: dict, model_result: dict, block_ids: set) -> list:
    if not isinstance(lesson, dict):
        return ["the answer is not a JSON object"]
    out = list(model_result.get("problems") or [])
    options = question.get("options") or []
    parts, moments = set(model_result.get("parts") or []), set(model_result.get("moments") or []) | {""}
    board_keys = set((model_result.get("board") or {}).keys()) | {""}
    details = {d.get("id") for d in lesson.get("details") or []}
    gates = {g.get("id"): g for g in lesson.get("gates") or []}
    keys = [s.get("key") for s in lesson.get("stages") or []]
    if keys != list(STAGES):
        out.append(f"stages must be exactly {', '.join(STAGES)} in that order (got {', '.join(map(str, keys))})")
    gate_uses, gate_stage = {}, {}
    for stage in lesson.get("stages") or []:
        beats = stage.get("beats") or []
        need = 3 if stage.get("key") == "solve" else 2
        if len(beats) < need:
            out.append(f"stage {stage.get('key')}: {len(beats)} beats; it needs at least {need}")
        for k, beat in enumerate(beats, 1):
            where = f"stage {stage.get('key')} beat {k}"
            say = (beat.get("say") or "").strip()
            if len(say.split()) < 8 or not END.search(say):
                out.append(f"{where}: say must be complete sentences (8+ words, ending with . ? or !)")
            if not DEVANAGARI.search(beat.get("voice") or ""):
                out.append(f"{where}: voice must be the same sentence in Devanagari")
            for field in ("focus", "labels"):
                bad = [p for p in beat.get(field) or [] if p not in parts]
                if bad:
                    out.append(f"{where}: {field} {', '.join(bad[:4])} are not parts of the model "
                               f"({', '.join(sorted(parts)[:12])}...)")
            if beat.get("moment", "") not in moments:
                out.append(f"{where}: moment {beat.get('moment')!r} is not one of {', '.join(sorted(m for m in moments if m))}")
            if beat.get("board", "") not in board_keys:
                out.append(f"{where}: board {beat.get('board')!r} is not a model step ({', '.join(sorted(k for k in board_keys if k))})")
            if beat.get("detail") and beat["detail"] not in details:
                out.append(f"{where}: detail {beat['detail']!r} is not defined")
            if beat.get("gate"):
                if beat["gate"] not in gates:
                    out.append(f"{where}: gate {beat['gate']!r} is not defined")
                gate_uses[beat["gate"]] = gate_uses.get(beat["gate"], 0) + 1
                gate_stage[beat["gate"]] = stage.get("key")
    if len(gates) < 3:
        out.append(f"{len(gates)} gates; write at least 3 prediction gates")
    for stage_key in ("concept", "solve"):
        if stage_key not in gate_stage.values():
            out.append(f"stage {stage_key} needs at least one gate")
    values = model_result.get("values") or {}
    for gid, gate in gates.items():
        where = f"gate {gid}"
        if gate_uses.get(gid) != 1:
            out.append(f"{where}: must be used by exactly one beat (used {gate_uses.get(gid, 0)} times)")
        mech, answer, choices = gate.get("mechanic"), str(gate.get("answer") or "").strip(), gate.get("choices") or []
        if mech == "number":
            if answer not in values and not re.fullmatch(r"-?\d[\d,]*(\.\d+)?", answer):
                out.append(f"{where}: a number gate's answer is a model value name ({', '.join(list(values)[:10])}) or a number")
        elif mech in ("choose", "order"):
            if len(choices) < 2:
                out.append(f"{where}: {mech} needs at least 2 choices")
            idx = answer.split(",") if mech == "order" else [answer]
            if not all(i.strip().isdigit() and int(i) < len(choices) for i in idx) or \
                    (mech == "order" and sorted(int(i) for i in idx) != list(range(len(choices)))):
                out.append(f"{where}: answer {answer!r} is not a valid {'order of indexes' if mech == 'order' else 'choice index'}")
        elif mech == "tap_part":
            if answer not in parts:
                out.append(f"{where}: tap_part answer {answer!r} is not a model part")
        elif mech == "pair":
            src, _, dst = answer.partition(">")
            if src not in parts or dst not in parts:
                out.append(f"{where}: pair answer must be 'source>target' with model parts (got {answer!r})")
        wrong = gate.get("wrong") or []
        if not wrong or any(len((w.get("why") or "").split()) < 6 for w in wrong):
            out.append(f"{where}: every gate needs wrong branches whose why names the misconception in a full sentence")
        if gate.get("reveal", "") not in moments:
            out.append(f"{where}: reveal {gate.get('reveal')!r} is not a model moment")
        if len((gate.get("why") or "").split()) < 6:
            out.append(f"{where}: why (the teacher's reason after the action) is missing")
    for d in lesson.get("details") or []:
        if len(d.get("chain") or []) != 3:
            out.append(f"detail {d.get('id')}: chain must be exactly three lines (source, operation, result)")
        bad = [p for p in d.get("focus") or [] if p not in parts]
        if bad:
            out.append(f"detail {d.get('id')}: focus {', '.join(bad[:4])} are not model parts")
        if d.get("moment", "") not in moments:
            out.append(f"detail {d.get('id')}: moment {d.get('moment')!r} is not a model moment")
    if len(details) < 2:
        out.append("write at least 2 details (enlarged causal views)")
    board = lesson.get("board") or []
    if len(board) < 2 or any(r.get("step") not in board_keys - {""} for r in board):
        out.append(f"board: at least 2 rows, each a model step ({', '.join(sorted(k for k in board_keys if k))})")
    diag = {d.get("option") for d in lesson.get("diagnoses") or []}
    if options and diag != set(range(1, len(options) + 1)):
        out.append(f"diagnoses: one for each option 1..{len(options)}")
    for trap, opt in (model_result.get("trap_options") or {}).items():
        if opt is None:
            continue
        hit = next((d for d in lesson.get("diagnoses") or [] if d.get("option") == opt + 1), None)
        if hit and hit.get("shows") != trap:
            out.append(f"diagnosis for option {opt + 1}: the model's trap {trap} produces this option; set shows to {trap!r}")
    proved = model_result.get("answer_option")
    key = question.get("answer")
    if model_result.get("verified") and proved is not None and isinstance(key, int) and proved != key:
        out.append(f"the model proves option {proved + 1}, but the question's key says option {key + 1}: check the model")
    families = lesson.get("families") or []
    if len(families) < 2 or sum(1 for f in families if f.get("transfer")) != 1:
        out.append("families: at least 2 question types, exactly one marked transfer")
    allowed = set(model_result.get("numbers") or set())
    for text in [question.get("question") or ""] + list(options):
        allowed |= set(pyq_models.spoken_numbers(text))
    for item in lesson.get("given") or []:
        allowed |= set(pyq_models.spoken_numbers(item.get("value") or ""))
    model = lesson.get("model") or {}
    for fam in families:
        checked = pyq_models.family(model, fam.get("changes") or [], fam.get("choices") or [])
        allowed |= set(checked.get("numbers") or set())
        for text in [fam.get("question") or ""] + list(fam.get("choices") or []) + list(fam.get("changes") or []):
            allowed |= set(pyq_models.spoken_numbers(text))
        if checked["checked"]:
            out += [f"family {fam.get('id')}: {p}" for p in checked["problems"]]
            if checked["correct"] is None:
                out.append(f"family {fam.get('id')}: the model's answer ({checked.get('value')}) matches none of its choices")
            elif fam.get("correct") != checked["correct"] + 1:
                out.append(f"family {fam.get('id')}: the model says choice {checked['correct'] + 1} is right, not "
                           f"{fam.get('correct')}")
    for where, text in learner_texts(lesson):
        stray = pyq_models.stray_numbers(text, allowed)
        if stray:
            out.append(f"{where}: the numbers {', '.join(stray[:4])} come from nowhere in the model or the question")
        if SOURCE_WORDS.search(text):
            out.append(f"{where}: names the source; remove it")
        if CAUTION.search(text):
            out.append(f"{where}: a caution line belongs in limitations (review page), not on the learner's screen")
    evidence = lesson.get("evidence") or []
    if not evidence:
        out.append("evidence: name at least one book idea with its block ids")
    for k, ev in enumerate(evidence, 1):
        bad = [b for b in ev.get("block_ids") or [] if b not in block_ids]
        if bad or not ev.get("block_ids"):
            out.append(f"evidence {k}: block ids {', '.join(bad) or '(none)'} are not in the chapter")
        badp = [p for p in ev.get("parts") or [] if p not in parts]
        if badp:
            out.append(f"evidence {k}: parts {', '.join(badp[:4])} are not model parts")
    return out


def write(client, model_name: str, question: dict, *, course: str, language: str, chapter_text: str, block_ids: set,
          max_rounds: int = 3) -> dict:
    convo = messages(question, course=course, language=language, chapter_text=chapter_text)
    cache = {}

    def check(answer):
        if not isinstance(answer, dict):
            return ["the answer is not a JSON object"]
        key = json.dumps(answer.get("model"), sort_keys=True)
        if key not in cache:
            cache[key] = pyq_models.build(answer.get("model") or {}, question.get("options") or [])
        return problems(answer, question, cache[key], block_ids)

    result = ask(client, model_name, convo, SCHEMA, check, max_rounds=max_rounds, problems_prompt=PROBLEMS_PROMPT)
    lesson = result["answer"] if isinstance(result["answer"], dict) else {}
    built = pyq_models.build(lesson.get("model") or {}, question.get("options") or []) if lesson else {}
    return {"question": question, "lesson": lesson, "model": built, "problems": result["problems"],
            "rounds": result["rounds"], "usage": result["usage"]}


def _jsonable(model: dict) -> dict:
    return {k: (sorted(v) if isinstance(v, set) else v) for k, v in (model or {}).items()}


def player_data(records: list, *, title: str, tint: str, audio: dict | None = None, voice: str = "") -> dict:
    """The JSON the PYQ player reads: one investigation per question, the model's data and computed answers."""
    audio = audio or {}
    items = []
    for rec in records:
        lesson, model, q = rec["lesson"], rec["model"], rec["question"]
        values = model.get("values") or {}
        gates = []
        for g in lesson.get("gates") or []:
            gate = dict(g)
            if g.get("mechanic") == "number":
                raw = str(g.get("answer") or "")
                gate["value"] = float(str(values.get(raw, raw)).replace(",", "")) if (raw in values or raw) else None
                gate["wrong_values"] = {w["match"]: float(str(values[w["match"]]).replace(",", ""))
                                        for w in g.get("wrong") or [] if w.get("match") in values}
            gates.append(gate)
        families = []
        for f in lesson.get("families") or []:
            checked = pyq_models.family(lesson.get("model") or {}, f.get("changes") or [], f.get("choices") or [])
            families.append({**f, "right": (checked["correct"] if checked["checked"] and checked["correct"] is not None
                                            else max(0, (f.get("correct") or 1) - 1)),
                             "model_checked": bool(checked["checked"] and checked["correct"] is not None),
                             "value": checked.get("value")})
        stages = []
        for stage in lesson.get("stages") or []:
            beats = []
            for k, beat in enumerate(stage.get("beats") or []):
                clip = audio.get((q.get("id"), stage.get("key"), k)) or {}
                beats.append({**beat, "audio": clip.get("uri", ""), "dur": clip.get("dur") or 0})
            stages.append({**stage, "name": STAGE_NAMES.get(stage.get("key"), ""), "beats": beats})
        board = []
        for row in lesson.get("board") or []:
            step = (model.get("board") or {}).get(row.get("step"), {})
            board.append({"step": row.get("step"), "note": row.get("note"), **step})
        items.append({"id": q.get("id"), "exam": q.get("exam", ""), "origin": q.get("origin", "pyq"),
                      "question": q.get("question"), "options": q.get("options") or [], "key": q.get("answer"),
                      "proved": model.get("answer_option"), "verified": model.get("verified"),
                      "title": lesson.get("title"), "concept": lesson.get("concept"), "scene_title": lesson.get("scene_title"),
                      "given": lesson.get("given") or [], "asked": lesson.get("asked"), "assumptions": lesson.get("assumptions") or [],
                      "objectives": lesson.get("objectives") or [], "prerequisites": lesson.get("prerequisites") or [],
                      "evidence": [{k: v for k, v in e.items() if k != "block_ids"} for e in lesson.get("evidence") or []],
                      "model": {"kind": model.get("kind"), "data": model.get("data") or {}, "values": values,
                                "trap_options": model.get("trap_options") or {}},
                      "stages": stages, "details": lesson.get("details") or [], "gates": gates, "board": board,
                      "diagnoses": lesson.get("diagnoses") or [], "families": families, "recap": lesson.get("recap")})
    return {"title": title, "tint": tint, "voice": voice, "items": items}


def html(data: dict, template: str) -> str:
    blob = json.dumps(data, ensure_ascii=False, default=lambda v: sorted(v) if isinstance(v, set) else str(v))
    return template.replace("/*__PYQ__*/null", blob.replace("</", "<\\/"), 1)


def coverage(records: list, teachable_ids: set) -> dict:
    """Question-level evidence and chapter-level reach, kept apart."""
    per_q = {r["question"].get("id"): sorted({b for e in (r["lesson"].get("evidence") or []) for b in e.get("block_ids") or []})
             for r in records}
    reached = {b for ids in per_q.values() for b in ids} & set(teachable_ids)
    return {"questions": per_q, "chapter": {"teachable_blocks": len(teachable_ids), "reached_by_pyqs": len(reached),
                                            "percent": round(100 * len(reached) / max(1, len(teachable_ids)), 1),
                                            "note": "PYQ evidence only; the chapter is taught by the films and notes"}}


def markdown(records: list, cover: dict, *, title: str) -> str:
    lines = [f"# PYQ Lab · {title}", "",
             f"Chapter ki baatein jin tak yeh sawaal pahunche: {cover['chapter']['reached_by_pyqs']} / "
             f"{cover['chapter']['teachable_blocks']} ({cover['chapter']['percent']}%) — yeh chapter padhana nahi, sirf "
             f"sawaalon ka saboot hai.", ""]
    for rec in records:
        q, model, lesson = rec["question"], rec["model"], rec["lesson"]
        proved = model.get("answer_option")
        key = q.get("answer")
        verdict = ("model se jaancha: sahi" if proved is not None and proved == key else
                   "model se jaancha: key se alag!" if proved is not None and key is not None else
                   "model ne jawab nahi jaancha" if not model.get("verified") else "jawab nahi mila")
        lines += [f"## {q.get('id')} · {lesson.get('title') or q.get('question')}", "",
                  f"- Sawaal: {q.get('question')}", f"- Model: {model.get('kind')} · {verdict}"
                  + (f" (option {proved + 1})" if proved is not None else ""),
                  f"- Concept: {lesson.get('concept', '')}",
                  f"- Gates: {len(lesson.get('gates') or [])} · families: {len(lesson.get('families') or [])} · rounds: "
                  f"{len(rec.get('rounds') or [])}" + (f" · kamiyan: {len(rec['problems'])}" if rec.get("problems") else ""),
                  "- Review ke liye (learner ko nahi dikhta): " + "; ".join(lesson.get("limitations") or ["—"]), ""]
    return "\n".join(lines) + "\n"
