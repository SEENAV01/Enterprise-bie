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


SEVERITY = {"type": "string", "enum": ["blocking", "minor"]}


def blocking(findings):
    return [f for f in findings or [] if f.get("severity", "blocking") == "blocking"]


def review_problems(review: dict) -> list:
    """A reviewer's blocking findings as remake instructions; empty means pass. Minor findings never block."""
    problems = [f"missing: {m['what']} ({m['where_on_page']})" for m in blocking(review.get("missing"))]
    problems += [f"wrong in {w['item_id']}: {w['problem']} -> fix: {w['fix']}" for w in blocking(review.get("wrong"))]
    problems += [f"shallow {s['item_id']}: {s['what_is_missing']}" for s in blocking(review.get("shallow"))]
    problems += [f"{p['where']}: {p['problem']} -> fix: {p['fix']}" for p in blocking(review.get("problems"))]
    if review.get("verdict") != "pass" and not problems:
        problems.append("the reviewer did not pass this work but named no blocking finding; check the work again completely")
    return problems


def minor_findings(review: dict) -> list:
    found = []
    for key in ("missing", "wrong", "shallow", "problems"):
        for f in review.get(key) or []:
            if f.get("severity") == "minor":
                found.append({k: v for k, v in f.items() if k != "severity"} | {"kind": key})
    return found
