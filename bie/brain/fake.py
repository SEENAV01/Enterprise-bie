"""A deterministic offline stand-in for the maker and reviewer AIs of the brain sections.

It answers from the prompt itself (block ids, item listings), so the whole chain (code checks,
reviewer, records, chapter map) runs offline and repeatably in CI. It proves execution, never
quality: its "understanding" only restates the book.
"""
from __future__ import annotations

import json
import re

from bie.model_gateway.live.messages import split_messages, text_of

BLOCK_LINE = re.compile(r"^(p\d{4}-b\d{4}) \| (.*)$", re.MULTILINE)
NOTES = {"about": "offline", "key_questions": ["offline?"], "decisions": [], "uncertain": []}


def _qa(text):
    return [{"depth": 1, "ask": "what", "question": "What does the book say here?", "answer": "Offline restatement: " + text[:80]},
            {"depth": 2, "ask": "why", "question": "Why does it matter?", "answer": "Offline answer for " + text[:40]}]


def _item(iid, text, *, source="text", block_ids=(), kind="paragraph", parent=""):
    return {"item_id": iid, "kind": kind, "parent_item_id": parent, "source": source, "block_ids": list(block_ids),
            "where_on_page": "offline", "content": text, "content_type": "fact", "teachable": True,
            "teacher_understanding": [dict(q, basis="book") for q in _qa(text)], "prerequisites": [],
            "exam_importance": "medium", "exam_note": "", "tests_item_ids": []}


def page_answer(user_text: str):
    blocks = BLOCK_LINE.findall(user_text.split("First lines of the next page")[-1])
    if blocks:
        items = [_item(f"i{n}", text, block_ids=[bid]) for n, (bid, text) in enumerate(blocks, 1)]
    else:
        items = [_item("i1", "Figure read from the image", source="image", kind="diagram"),
                 _item("i2", "First label of the figure", source="image", kind="diagram_label", parent="i1"),
                 _item("i3", "Second label of the figure", source="image", kind="diagram_label", parent="i1")]
    return {"notes": NOTES, "page_summary": "Offline page summary.", "items": items, "boilerplate_block_ids": [],
            "text_image_disagreements": []}


def connect_answer(user_text: str):
    start = user_text.index("[")
    items, _ = json.JSONDecoder().raw_decode(user_text[start:])
    pages = sorted({i["page"] for i in items})
    concepts = [{"concept_id": f"c{p}", "name": f"Page {p}", "item_ids": [i["id"] for i in items if i["page"] == p],
                 "content_type": "fact", "core_explanation": "Offline concept."} for p in pages]
    links = [{"question_item_id": i["id"], "tests_concepts": [f"c{i['page']}"]} for i in items if i["kind"] == "question"]
    return {"notes": NOTES, "chapter_title": "Offline", "chapter_summary": "Offline map.", "concepts": concepts,
            "relations": [], "prerequisites_to_teach": [], "cross_references": [], "question_links": links,
            "teaching_order": [c["concept_id"] for c in concepts], "exam_focus": []}


def _payload(user_text: str):
    start = user_text.index("{")
    value, _ = json.JSONDecoder().raw_decode(user_text[start:])
    return value


def plan_answer(user_text: str):
    data = _payload(user_text)
    names = [p["name"] for p in data.get("prerequisites_to_teach", [])]
    videos = [{"video_id": f"v{n}", "title": f"वीडियो {n}: {c['name']}", "goal": "Offline goal.", "concept_ids": [c["concept_id"]],
               "prerequisites_taught": names if n == 1 else [], "opening_hook": "Offline hook.", "story_or_analogy": "",
               "estimated_minutes": 5, "why_this_unit": "Offline."} for n, c in enumerate(data.get("concepts", []), 1)]
    return {"notes": NOTES, "videos": videos, "chapter_flow": "Offline flow."}


def script_answer(user_text: str):
    data = _payload(user_text)
    beats = [{"beat_id": "b0", "purpose": "hook", "say": "ज़रा सोचिए, ये offline hook है।", "covers_item_ids": [], "answers": [],
              "on_screen": "Offline.", "basis": "book"}]
    for n, item in enumerate(data.get("items", []), 1):
        beats.append({"beat_id": f"b{n}", "purpose": "explain", "say": "ये offline explanation है: " + item["content"][:60],
                      "covers_item_ids": [item["item_id"]], "answers": [q["id"] for q in item["teacher_questions"]],
                      "on_screen": "Offline.", "basis": "book"})
    beats.append({"beat_id": "b-end", "purpose": "recap", "say": "तो आज हमने offline recap किया।", "covers_item_ids": [],
                  "answers": [], "on_screen": "Offline.", "basis": "book"})
    return {"notes": NOTES, "title": data["video"]["title"], "beats": beats}


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
        props = (schema or {}).get("properties", {})
        if "verdict" in props:
            value = review_answer(schema)
            if self.fail_reviews > 0:
                self.fail_reviews -= 1
                value["verdict"] = "fail"
                key = "missing" if "missing" in props else "problems"
                value[key] = ([{"what": "offline missing row", "where_on_page": "offline"}] if key == "missing" else
                              [{"where": "offline", "problem": "offline problem", "fix": "offline fix"}])
        elif "items" in props:
            value = page_answer(user)
        elif "concepts" in props:
            value = connect_answer(user)
        elif "videos" in props:
            value = plan_answer(user)
        elif "beats" in props:
            value = script_answer(user)
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
