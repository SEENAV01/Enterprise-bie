"""Small shared helpers for the brain sections: JSON-schema builders, prompt formatting, reviewer findings."""
from __future__ import annotations

S = {"type": "string"}


def obj(properties: dict, **extra):
    """A strict object schema: every property required, nothing extra (what OpenAI strict mode and Anthropic need)."""
    return {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties, **extra}


def arr(items):
    return {"type": "array", "items": items}


def fmt(template, course, **extra):
    return template.format(title=course.title, subject=course.subject, learners=course.learners, exam=course.exam,
                           language=course.language, **extra)


def checklist_text(rulebook, section):
    return "\n".join(f"[{rule_id}] {question}" for rule_id, question in rulebook.checklist(section))


def review_problems(review: dict) -> list:
    """A reviewer's findings as remake instructions; empty means pass."""
    problems = [f"missing: {m['what']} ({m['where_on_page']})" for m in review.get("missing") or []]
    problems += [f"wrong in {w['item_id']}: {w['problem']} -> fix: {w['fix']}" for w in review.get("wrong") or []]
    problems += [f"shallow {s['item_id']}: {s['what_is_missing']}" for s in review.get("shallow") or []]
    problems += [f"{p['where']}: {p['problem']} -> fix: {p['fix']}" for p in review.get("problems") or []]
    problems += [f"rule {c['rule_id']} not met: {c['note']}" for c in review.get("checklist") or [] if not c.get("met")]
    if review.get("verdict") != "pass" and not problems:
        problems.append("the reviewer did not pass this work but gave no detail; check the work again completely")
    return problems
