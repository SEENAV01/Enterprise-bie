"""A deterministic offline stand-in for the maker and reviewer AIs of the brain sections.

It answers from the prompt itself (block ids, item listings), so the whole chain (code checks,
reviewer, records, chapter map) runs offline and repeatably in CI. It proves execution, never
quality: its "understanding" only restates the book.
"""
from __future__ import annotations

import json
import re

from bie.model_gateway.live.messages import split_messages, text_of

from . import cards
from . import content_types as ct
from . import shots

BLOCK_LINE = re.compile(r"^(p\d{4}-b\d{4}) \| (.*)$", re.MULTILINE)
ITEM_LINE = re.compile(r"^(p\d{3}-[^ |]+) \| (\d+) \| (\w+) \| (\w+) \| (teach|no) \|", re.MULTILINE)
QUESTION_LINE = re.compile(r"^  (p\d{3}-[^ |#]+#q\d+) \|", re.MULTILINE)
NOTES = {"about": "offline", "key_questions": ["offline?"], "decisions": [], "uncertain": []}


def _qa(text, asks=("what",)):
    asks = list(dict.fromkeys(list(asks) + ["why"]))
    if len(asks) < 2:
        asks.insert(0, "what")
    return [{"depth": 1 if n == 0 else 2, "ask": ask, "question": f"Offline {ask} question?",
             "answer": f"Offline answer ({ask}) for " + text[:40]} for n, ask in enumerate(asks)]


# The offline real-world example (S1-16, Navin's sugar shop; test input, never lesson content): the same numbers the fake
# script speaks first (S2-08), so an offline economics chapter passes both checks on the first try.
STORY_NUMBERS = ("50", "65", "2", "12")
STORY_SAY = ("ज़रा सोचिए: दुकान में चीनी के 3 packet हैं, ₹50 का एक; कल 2 खरीदार आए और आज 12 आ गए, तो दाम का क्या होगा? "
             "दुकानदार दाम ₹65 कर देता है और सिर्फ 3 लोग खरीद पाते हैं।")


def _real_world(word: str) -> dict:
    return {"place": "kirana shop", "actors": ["shopkeeper", "buyers"], "goods": ["sugar"],
            "numbers": [{"what": "price", "before": "₹50", "after": "₹65"}, {"what": "buyers", "before": "2", "after": "12"}],
            "steps": [{"step": "दुकान में चीनी के 3 packet हैं, ₹50 का एक; कल 2 खरीदार आए", "mechanism_link": "supply fixed, demand low"},
                      {"step": "आज 12 खरीदार आ गए, दुकानदार दाम ₹65 कर देता है", "mechanism_link": "demand above supply, price up"}],
            "term_after": f"इसलिए इसे {word} कहते हैं", "real_life_link": "Diwali से पहले सब्ज़ी मंडी में यही दिखता है"}


def _unpack(text, *, with_terms=True, real_world=False):
    """An offline unpack (S1-15): one term opened in Devanagari, one why step with its basis, one example. One why step
    fits every level profile; the revision profile adds no terms, so the fake drops them when the prefix says so. An
    economics concept item also carries the offline real-world example (S1-16)."""
    word = next((w for w in re.findall(r"[A-Za-z][A-Za-z\-]{3,}", text)), "topic")
    return {"terms": [{"term": word, "plain_meaning": f"{word} यानी offline सरल अर्थ", "everyday_image": "घर की एक आम चीज़"}]
            if with_terms else [],
            "why_chain": [{"step": "ज़रूरत है, इसलिए यह offline वजह है", "basis": "book"}],
            "example_or_place": "offline example", "consequence": "offline consequence", "visual_verb": "show",
            "level_extra": "",
            "real_world_example": _real_world(word) if real_world else json.loads(json.dumps(soul_empty()))}


def soul_empty() -> dict:
    from .soul import EMPTY_REAL_WORLD
    return EMPTY_REAL_WORLD


def subject_family(system_text: str) -> str:
    """The subject family of the course line in a prefix ("· subject: Indian Economy ·")."""
    found = re.search(r"· subject: (.*?) · learners:", system_text or "")
    return shots.subject_family(found.group(1) if found else "")


def _item(iid, text, *, source="text", block_ids=(), kind="paragraph", parent="", content_type="definition", with_terms=True,
          family=""):
    types = ct.load()
    asks = types.required_asks(content_type)
    return {"item_id": iid, "kind": kind, "parent_item_id": parent, "source": source, "block_ids": list(block_ids),
            "where_on_page": "offline", "content": text, "content_type": content_type, "type_note": "", "teachable": True,
            "teacher_understanding": [dict(q, basis="book") for q in _qa(text, asks)], "prerequisites": [],
            "exam_importance": "medium", "exam_note": "", "tests_item_ids": [],
            "unpack": _unpack(text, with_terms=with_terms, real_world=types.needs_real_world(family, content_type))}


def page_answer(user_text: str, system_text: str = ""):
    """Agrees with BIE's proposed type for every block (definition where the code has none)."""
    card = cards.read_card(user_text)
    with_terms = "- Revision: one line per item, no new terms" not in system_text
    family = subject_family(system_text)
    types = ct.load()
    proposed = {i: p["type"] for p in card["parts"] for i in p["item_ids"]}
    skip = {s["item_id"] for s in card["coverage"]["may_skip"]}
    blocks = BLOCK_LINE.findall(user_text)
    items = []
    for bid, text in (b for b in blocks if b[0] not in skip):
        kind = proposed.get(bid, ct.NONE)
        items.append(_item(f"i{len(items) + 1}", text, block_ids=[bid], content_type=kind if kind in types.types else "definition",
                           with_terms=with_terms, family=family))
    if not items:
        items = [_item("i1", "Figure read from the image", source="image", kind="diagram", content_type="figure", with_terms=with_terms),
                 _item("i2", "First label of the figure", source="image", kind="diagram_label", parent="i1", content_type="figure",
                       with_terms=with_terms),
                 _item("i3", "Second label of the figure", source="image", kind="diagram_label", parent="i1", content_type="figure",
                       with_terms=with_terms)]
    return {"notes": NOTES, "page_summary": "Offline page summary.", "items": items,
            "boilerplate_block_ids": [bid for bid, _ in blocks if bid in skip], "text_image_disagreements": []}


def connect_answer(user_text: str):
    rows = ITEM_LINE.findall(user_text)
    pages = sorted({int(page) for _, page, _, _, _ in rows})
    concepts = []
    for page in pages:
        mine = [r for r in rows if int(r[1]) == page]
        kinds = [r[3] for r in mine if r[3] in ct.load().types]
        concepts.append({"concept_id": f"c{page}", "name": f"Page {page}", "item_ids": [r[0] for r in mine],
                         "content_type": max(set(kinds), key=kinds.count) if kinds else "facts_numbers",
                         "core_explanation": "Offline concept."})
    links = [{"question_item_id": r[0], "tests_concepts": [f"c{r[1]}"]} for r in rows if r[2] == "question"]
    return {"notes": NOTES, "chapter_title": "Offline", "chapter_summary": "Offline map.", "concepts": concepts,
            "relations": [], "prerequisites_to_teach": [], "prerequisite_note": "", "cross_references": [], "question_links": links,
            "teaching_order": [c["concept_id"] for c in concepts], "exam_focus": []}


def _payload(user_text: str):
    start = user_text.index("{")
    value, _ = json.JSONDecoder().raw_decode(user_text[start:])
    return value


BUDGET = re.compile(r"(\S+) (\d+\.\d)-(\d+\.\d)")
SCRIPT_TIME = re.compile(r"Narration time \(S2-01\): [\d.]+-[\d.]+ minutes, about (\d+)-(\d+) spoken words")
FILLER = "ये बात ध्यान से समझिए, क्योंकि आगे यही बात बार बार काम आएगी और exam में भी पूछी जा सकती है।"


def plan_answer(user_text: str):
    """A prerequisite video first when the map has prerequisites, then one topic video per concept, each in its budget."""
    card = cards.read_card(user_text)
    section = user_text.split("Prerequisites to teach", 1)[-1].split("BIE's teaching order", 1)[0]
    names = [line[2:].split(" · ")[0] for line in section.splitlines() if line.startswith("- ")]
    budget_text = user_text.split("Minutes per concept", 1)[-1]
    budget = {cid: (float(lo), float(hi)) for cid, lo, hi in BUDGET.findall(budget_text)}
    video = lambda vid, title, kind, cids, taught, minutes: {
        "video_id": vid, "title": title, "goal": "Offline goal.", "kind": kind, "concept_ids": cids, "prerequisites_taught": taught,
        "opening_hook": "Offline hook.", "story_or_analogy": "", "estimated_minutes": minutes, "length_note": "",
        "why_this_unit": "Offline."}
    videos = [video("v0", "पहले यह जान लो", "prerequisites", [], names, 6)] if names else []
    groups, low, high = [], 0.0, 0.0             # concepts in order, a new video once the last one has 6-8 minutes
    for cid in card["coverage"]["must_cover"]:
        if not groups or high >= 8:
            groups.append([[], 0.0, 0.0])
        lo, hi = budget.get(cid, (1.0, 1.0))
        groups[-1][0].append(cid)
        groups[-1][1] += lo
        groups[-1][2] += hi
        low, high = groups[-1][1], groups[-1][2]
    if len(groups) > 1 and groups[-1][2] < 3:     # a short tail joins the video before it
        tail = groups.pop()
        groups[-1] = [groups[-1][0] + tail[0], groups[-1][1] + tail[1], groups[-1][2] + tail[2]]
    for n, (cids, low, high) in enumerate(groups, 1):
        videos.append(video(f"v{n}", f"वीडियो {n}", "topic", cids, [], max(1, round((low + high) / 2))))
    return {"notes": NOTES, "videos": videos, "chapter_flow": "Offline flow."}


def script_answer(user_text: str, system_text: str = ""):
    """One beat per item for the first pattern step (several items per beat when the narration time is short), then one beat
    per further step; a frame for every part; filler transitions up to the narration time. In an economics chapter a
    concept part opens with the offline real-world example, numbers first (S2-08)."""
    time = SCRIPT_TIME.search(user_text)
    family = subject_family(system_text)
    for per_beat in range(1, 40):
        value = _script(user_text, per_beat, family)
        if not time or sum(len(b["say"].split()) for b in value["beats"]) <= int(time.group(2)):
            break
    if time:                                    # speak as long as the card's narration time asks (S2-01)
        beats = value["beats"]
        target = (int(time.group(1)) + int(time.group(2))) // 2
        while sum(len(b["say"].split()) for b in beats) + len(FILLER.split()) <= target:
            beats.insert(-1, {"beat_id": f"b{len(beats)}x", "part_id": "", "step": 0, "purpose": "transition", "say": FILLER,
                              "covers_item_ids": [], "answers": [], "on_screen": "Offline.", "basis": "book"})
    return value


def _script(user_text: str, per_beat: int, family: str = ""):
    card = cards.read_card(user_text)
    types = ct.load()
    questions = {}
    for qid in QUESTION_LINE.findall(user_text):
        questions.setdefault(qid.split("#")[0], []).append(qid)
    hook = {"beat_id": "b0", "part_id": "", "step": 0, "purpose": "hook", "say": "ज़रा सोचिए, ये offline hook है। आज हम इस topic को बहुत ध्यान से समझेंगे।",
            "covers_item_ids": [], "answers": [], "on_screen": "Offline.", "basis": "book"}
    beats, parts = [hook], []
    for part in card["parts"]:
        parts.append({"part_id": part["part_id"], "frame": {k: f"offline {k}" for k in ("process", "how", "when", "conditions",
                                                                                           "atmosphere")}, "skipped_steps": []})
        first_step = 1 if types.pattern(part["type"]) else 0
        ids = part["item_ids"]
        story = types.needs_real_world(family, part["type"])
        for group in (ids[n:n + per_beat] for n in range(0, len(ids), per_beat)):
            if story:                               # the real-world example runs first, with its numbers (S2-08)
                beats.append({"beat_id": f"b{len(beats)}", "part_id": part["part_id"], "step": first_step, "purpose": "story",
                              "say": STORY_SAY, "covers_item_ids": group, "answers": [], "on_screen": "Offline shop.", "basis": "outside"})
            say = (f"ये सामने क्या दिख रहा है? ये offline explanation है: {group[0]}। इसे ध्यान से समझिए, ये exam में बहुत काम आएगा।"
                   if per_beat == 1 else f"ये सामने क्या दिख रहा है? ये offline explanation है: {', '.join(group)}।")
            beats.append({"beat_id": f"b{len(beats)}", "part_id": part["part_id"], "step": first_step, "purpose": "explain",
                          "say": say, "covers_item_ids": group, "answers": [q for iid in group for q in questions.get(iid, [])],
                          "on_screen": "Offline.", "basis": "book"})
        for step in range(2, len(types.pattern(part["type"])) + 1):
            beats.append({"beat_id": f"b{len(beats)}", "part_id": part["part_id"], "step": step, "purpose": "explain",
                          "say": f"अब step {step} offline समझते हैं। सोचिए, ये पिछली बात से कैसे जुड़ता है?", "covers_item_ids": [], "answers": [],
                          "on_screen": "Offline.", "basis": "book"})
    beats.append({"beat_id": "b-end", "part_id": "", "step": 0, "purpose": "recap", "say": "तो आज हमने offline recap किया। अगली video में हम आगे की बात करेंगे।",
                  "covers_item_ids": [], "answers": [], "on_screen": "Offline.", "basis": "book"})
    return {"notes": NOTES, "title": card["unit"]["title"], "parts": parts, "beats": beats}


def trim_answer(user_text: str):
    """Keep the first 8 prerequisites (needed by the first concept of the map), drop the rest."""
    card = cards.read_card(user_text)
    rows = [line.split(" | ") for line in user_text.split("Current prerequisites", 1)[-1].splitlines() if line.startswith("pre")]
    concept = next((row[0] for row in card["context"]["map_slice"]), "c1")
    kept = [{"name": row[1], "why_needed": "Offline.", "needed_for": [concept], "basis": "outside", "from_ids": [row[0]]}
            for row in rows[:8]]
    return {"notes": NOTES, "prerequisites": kept, "dropped": [{"id": row[0], "reason": "offline: not needed directly"}
                                                                for row in rows[8:]], "prerequisite_note": ""}


def director_answer(user_text: str):
    data = _payload(user_text)
    scenes = []
    for n, beat in enumerate(data.get("beats", []), 1):
        word = (beat["say"].split() or ["x"])[0]
        scenes.append({"scene_id": f"s{n}", "beat_ids": [beat["beat_id"]],
                       "frame": {"process": "", "how_it_works": "", "when_or_sequence": "", "conditions_or_atmosphere": "",
                                 "who_or_what_changes": ""},
                       "style": "offline", "setting": "offline",
                       "elements": [{"element_id": "e1", "kind": "illustration", "shows": "Offline element.", "parts_to_label": [],
                                     "detail": "schematic", "source_item_ids": beat["covers_item_ids"]}],
                       "camera": [], "actions": [{"cue": {"beat_id": beat["beat_id"], "word": word}, "element_id": "e1",
                                                  "action": "appear", "detail": "offline"}],
                       "visual_math": [], "interaction": {"type": "none", "question_id": "", "prompt": "", "target_element_id": ""}})
    return {"notes": NOTES, "scenes": scenes}


def _first_word(say: str) -> str:
    words = [w for w in say.replace("।", " ").replace(",", " ").split() if w.strip("।,.!?")]
    return words[0].strip("।,.!?") if words else ""


def canvas_answer(user_text: str):
    """A plan the canvas compiler accepts: a title tag, then one short text box per beat on its first word, two columns of
    six rows; a 13th beat onward reuses a cell after its earlier box leaves (until_cue). Offline only."""
    data = _payload(user_text)
    beats = data.get("beats", [])
    part = (data.get("part") or {}).get("part_id") or (data.get("part") or {}).get("id") or "part"
    empty = {"cue_fraction": 0.0, "until_cue": [], "until_fraction": 0.0, "text": "", "style": "", "size": 0, "tone": "", "fill": "",
             "align": "", "icon": "", "label": "", "cols": 0, "steps": [], "from": "", "to": "", "from_side": "", "to_side": "", "elbow": "",
             "dashed": False, "curve": False, "target": "", "mark": "", "pos": "", "root": "", "children": [], "columns": [], "rows": [],
             "highlights": [], "marks": [], "flow": {"icon": "", "count": 0, "period": 0, "size": 0, "reverse": False, "cue": []}}
    nodes = []
    if beats:
        nodes.append(dict(empty, id="tag", kind="text", cell=[0, 0, 5, 1], cue=[beats[0]["beat_id"], ""], style="tag",
                          text=f"Part {part}"[:28]))
    slots = 12
    for n, beat in enumerate(beats):
        slot = n % slots
        cell = [(slot % 2) * 6, 1 + slot // 2, 6, 1]
        words = beat["say"].replace("।", " ").split()
        text = " ".join(words[:4])[:40] or "…"
        if n >= slots:
            nodes[1 + n - slots]["until_cue"] = [beat["beat_id"], ""]
        nodes.append(dict(empty, id=f"t{n + 1}", kind="text", cell=cell, cue=[beat["beat_id"], _first_word(beat["say"])],
                          style="box", size=28, text=text))
    graph = {"plot": {"x": 0, "y": 0, "w": 0, "h": 0}, "x_label": "", "y_label": "", "x_domain": [], "y_domain": [], "axes_cue": [],
             "curves": [], "dots": [], "shades": [], "guides": [], "notes": []}
    return {"notes": NOTES, "nodes": nodes, "camera": [], "focus": [], "graph_used": False, "graph": graph}


def world_answer(user_text: str):
    """A world the world compiler accepts: a shop, a price tag, a crowd that grows, a title, and one camera key per beat."""
    data = _payload(user_text)
    beats = data.get("beats", [])
    empty = {"x": 0, "y": 0, "sign": "", "text": "", "fill": "", "string": 0, "steps": [], "packets": [], "cue": [], "until_cue": [],
             "tilt_cue": [], "tilt": 0, "x0": 0, "x1": 0, "y0": 0, "y1": 0, "spacing": 0, "enter_x": 0, "exit_x": 0, "face": 0, "seed": 0,
             "count": 0, "lift_cue": [], "lift_dy": 0, "carry_cue": [], "carry_n": 0}
    first = beats[0]["beat_id"] if beats else "b1"
    els = [dict(empty, id="shop", kind="shop", x=2600, sign="दुकान", packets=[{"n": 3, "cue": [first, ""]}]),
           dict(empty, id="lamp1", kind="lamp", x=2050), dict(empty, id="fg1", kind="foreground", x=1750),
           dict(empty, id="tag", kind="price_tag", x=2870, y=560, string=60,
                steps=[{"text": "₹50", "n": 0, "dir": "", "cue": [first, _first_word(beats[0]["say"]) if beats else ""]}]),
           dict(empty, id="crowd", kind="crowd", x0=2330, spacing=120, enter_x=3950, exit_x=4300, face=-1, seed=4,
                steps=[{"text": "", "n": 2 + n, "dir": "", "cue": [b["beat_id"], _first_word(b["say"])]} for n, b in enumerate(beats)]),
           dict(empty, id="title", kind="title", text="Story", cue=[first, ""])]
    camera = [{"cue": [b["beat_id"], ""], "x": 2600 + 40 * n, "y": 560, "zoom": 1.0 + 0.05 * (n % 3), "frames": 30} for n, b in enumerate(beats)]
    return {"notes": NOTES, "elements": els, "camera": camera}


def notes_answer(user_text: str):
    data = _payload(user_text)
    slides = []
    teachable = [i for i in data.get("items", []) if i["teachable"]]
    for n, item in enumerate(teachable, 1):
        kind = ["flow", "difference_table", "tree", "labelled_list"][n % 4]
        visual = {"type": kind, "title": "Offline visual", "steps": [], "events": [], "columns": [], "rows": [], "series": [],
                  "nodes": [], "edges": []}
        if kind == "flow":
            visual["steps"] = [{"label": "Pehla", "detail": "offline"}, {"label": "Doosra", "detail": "offline"}]
        elif kind == "difference_table":
            visual["columns"] = ["A", "B"]
            visual["rows"] = [{"label": "Feature", "cells": ["x", "y"]}]
        else:
            visual["nodes"] = [{"id": "r", "label": "Root", "parent_id": "", "detail": ""},
                               {"id": "c", "label": "Child", "parent_id": "r", "detail": "offline"}]
        slides.append({"slide_id": f"n{n}", "ask": "what", "question": "ये क्या है? " + item["content"][:40],
                       "essence": "Offline essence.", "answer": "Offline answer.", "deep_dive": "Offline deep dive.", "visual": visual,
                       "source_item_ids": [item["item_id"]], "basis": "book", "not_in_book": "", "pyq_item_ids": []})
    return {"notes": NOTES, "slides": slides}


def game_answer(user_text: str):
    data = _payload(user_text)
    missions = []
    for n, concept in enumerate(data.get("concepts", []), 1):
        missions.append({"mission_id": f"m{n}", "title": f"मिशन {n}", "item_ids": concept["item_ids"], "content_type": "process",
                         "mechanic": "run_process", "player_role": "offline", "goal": "Offline goal.", "scene": "Offline scene.",
                         "interactions": ["drag"],
                         "steps": [{"step_id": "s1", "player_does": "Drag the part into place.", "correct_when": "offline",
                                    "wrong_moves": [{"move": "wrong part", "what_breaks": "the process stops", "why": "offline",
                                                     "item_ids": concept["item_ids"][:1]}]}],
                         "win": "offline", "feedback_on_win": "offline", "replay_twist": "offline", "assets_needed": []})
    return {"notes": NOTES, "game_title": "Offline game", "world": "Offline world.", "missions": missions,
            "revision_loop": "offline"}


def asset_plan_answer(user_text: str):
    start = user_text.index("[")
    rows, _ = json.JSONDecoder().raw_decode(user_text[start:])
    return {"notes": NOTES, "needs": [{"element_key": r["element_key"], "queries": ["offline " + r["kind"]], "must_show": []}
                                      for r in rows]}


def layout_answer(user_text: str):
    data = _payload(user_text)
    scene, beats = data["scene"], data["beats"]
    first = beats[0]
    word = (first["say"].split() or ["x"])[0]
    cue = {"beat_id": first["beat_id"], "word": word}
    empty_box = {"x": 0, "y": 0, "w": 0, "h": 0}
    blank = {"id": "", "type": "title", "cue": cue, "until": {"beat_id": "", "word": ""}, "box": empty_box, "element_id": "",
             "text": "", "subtitle": "", "tone": "accent", "anchor": {"layer": "", "x": 0, "y": 0}, "target_layer": "",
             "region": empty_box, "path": [], "entries": [], "columns": [], "rows": [], "focus": [],
             "from_ref": {"layer": "", "x": 0, "y": 0}, "to_ref": {"layer": "", "x": 0, "y": 0}}
    layers = []
    pictures = list(data.get("pictures", {}))
    if pictures:
        layers.append(dict(blank, id="img", type="image", box={"x": 0.05, "y": 0.1, "w": 0.5, "h": 0.75}, element_id=pictures[0]))
        layers.append(dict(blank, id="lab", type="label", box={"x": 0.62, "y": 0.2, "w": 0.3, "h": 0.1}, text="Offline label",
                           anchor={"layer": "img", "x": 0.5, "y": 0.5}))
    else:
        layers.append(dict(blank, id="t", type="title", box={"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.3}, text="Offline title"))
    return {"notes": NOTES, "layers": layers, "camera": []}


def review_answer(schema):
    value = {"notes": NOTES, "verdict": "pass", "checklist": []}
    for key in schema.get("properties", {}):
        value.setdefault(key, [])
    return value


class BrainFakeClient:
    def __init__(self, provider: str = "fake", *, usage=(2000, 1000), fail_reviews: int = 0):
        self.provider = provider
        self.via = "direct"
        self.usage = usage
        self.fail_reviews = fail_reviews   # the first N reviews fail, to exercise remakes
        self.calls = []
        self.last_model = None

    def _respond(self, model, messages, schema):
        split_messages(messages, provider=self.provider)
        user = text_of(messages[1]["content"])
        system = text_of(messages[0]["content"]) if messages[0].get("role") == "system" else ""
        props = (schema or {}).get("properties", {})
        if list(props) == ["status"]:                   # the cost guard's preflight call
            value = {"status": "ready"}
        elif list(props) == ["number"]:                 # the vision preflight: "reads" 47 only when an image was sent
            content = messages[1]["content"]
            sent = not isinstance(content, str) and any(part.get("type") == "image" for part in content)
            value = {"number": "47" if sent else "none"}
        elif "verdict" in props:
            value = review_answer(schema)
            if self.fail_reviews > 0:
                self.fail_reviews -= 1
                value["verdict"] = "fail"
                key = "missing" if "missing" in props else "problems"
                value[key] = ([{"what": "offline missing row", "where_on_page": "offline", "severity": "blocking"}]
                              if key == "missing" else
                              [{"where": "offline", "problem": "offline problem", "fix": "offline fix", "severity": "blocking"}])
        elif "needs" in props:
            value = asset_plan_answer(user)
        elif "choice" in props:
            value = {"notes": NOTES, "choice": 0, "reason": "offline", "parts": []}
        elif "replace_layers" in props:
            value = {"notes": NOTES, "replace_layers": [], "remove_layer_ids": [], "camera": []}
        elif "layers" in props:
            value = layout_answer(user)
        elif "replace_missions" in props:
            value = {"notes": NOTES, "replace_missions": [], "remove_mission_ids": []}
        elif "missions" in props:
            value = game_answer(user)
        elif "replace_slides" in props:
            value = {"notes": NOTES, "replace_slides": [], "remove_slide_ids": []}
        elif "slides" in props:
            value = notes_answer(user)
        elif "replace_scenes" in props:
            value = {"notes": NOTES, "replace_scenes": [], "remove_scene_ids": []}
        elif "nodes" in props and "graph_used" in props:
            value = canvas_answer(user)
        elif "elements" in props and "camera" in props and "notes" in props and len(props) == 3:
            value = world_answer(user)
        elif "scenes" in props:
            value = director_answer(user)
        elif "replace_beats" in props:
            value = {"notes": NOTES, "replace_parts": [], "replace_beats": [], "insert_beats": [], "remove_beat_ids": []}
        elif "replace_items" in props:
            value = {"notes": NOTES, "replace_items": [], "remove_item_ids": [], "boilerplate_block_ids": [],
                     "text_image_disagreements": []}
        elif "items" in props:
            value = page_answer(user, system)
        elif "concepts" in props:
            value = connect_answer(user)
        elif "videos" in props:
            value = plan_answer(user)
        elif "dropped" in props:
            value = trim_answer(user)
        elif "beats" in props:
            value = script_answer(user, system)
        else:
            raise ValueError("BrainFakeClient does not know this schema")
        self.calls.append({"model": model, "kind": next(iter(props), "")})
        self.last_model = f"fake-{model}"
        return {"content": json.dumps(value, ensure_ascii=False), "finish_reason": "stop", "model": self.last_model,
                "usage": {"input_tokens": self.usage[0], "output_tokens": self.usage[1], "cached_input_tokens": 0,
                          "reasoning_tokens": 0}}

    def messages_create(self, *, model, messages, schema=None):
        return self._respond(model, messages, schema)

    def responses_create(self, *, model, messages, response_schema=None):
        return self._respond(model, messages, response_schema)

    def generate(self, *, model, messages, schema=None):
        return self._respond(model, messages, schema)
