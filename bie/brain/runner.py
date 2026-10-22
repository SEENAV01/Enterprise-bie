"""The section runner: how every BIE section works, the same way every time.

One step is one unit of work of one section (for example one page for "understand"). It runs:

1. The maker AI gets the section's instructions (role, course, the vision rules for this section,
   output format) and the source (text and page images). It writes brief notes (what the unit is
   about, its main decisions with reasons, what is uncertain) and its output.
2. BIE's code checks the output (``Step.check``). Problems go straight back to the maker.
3. An independent reviewer AI, on a different provider, checks the output against the source and
   the rulebook checklist (``Step.review_*``). Its findings go back to the maker.
4. The maker remakes the whole output with those findings, at most ``max_rounds`` rounds in all.
5. Every round is kept in the process record: the maker's notes and output, the code
   problems, the reviewer's findings, models, tokens and cost. A passed step is a candidate for
   locking; failed rounds are kept and marked "avoid".

Images are recorded by hash and size only, never by content. When the run's cost guard refuses a call
(rupee cap reached) or the provider says its balance is used up, the step ends as "stopped", not
"failed": nothing is wrong with the work, it simply was not paid for.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from bie.model_gateway.live.budget import STOP_KINDS
from bie.model_gateway.live.errors import ProviderError
from bie.model_gateway.live.pricing import estimate_cost
from bie.model_gateway.model_interface import ModelRequest

from .common import minor_findings

RECORD_SCHEMA = "bie.brain.process-record/1"

NOTES_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["about", "key_questions", "decisions", "uncertain"],
    "properties": {
        "about": {"type": "string", "description": "What this unit of work is about and how it fits the whole (one or two sentences)."},
        "key_questions": {"type": "array", "items": {"type": "string"},
                          "description": "The key questions a teacher must answer about this unit."},
        "decisions": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["decision", "reason"],
            "properties": {"decision": {"type": "string"}, "reason": {"type": "string"}}}},
        "uncertain": {"type": "array", "items": {"type": "string"}},
    },
}

REMAKE_INSTRUCTION = (
    "BIE's checks found problems with your output.\n{problems}\n\n"
    "Fix every problem and keep everything that was already right. Reply with the complete corrected JSON "
    "for the whole unit, not only the changes, and update your notes to say what you changed and why."
)
PATCH_INSTRUCTION = (
    "BIE's checks found problems with your output.\n{problems}\n\n"
    "Fix every problem and keep everything that was already right. {hint} Update your notes to say what you changed and why."
)


@dataclass
class Step:
    section: str
    unit: str
    instructions_version: str
    system: str
    user: Any
    schema: dict
    check: Callable[[dict], list] = lambda value: []
    review_system: str | None = None
    review_user: Callable[[dict], Any] | None = None
    review_schema: dict | None = None
    review_problems: Callable[[dict], list] | None = None
    patch_schema: dict | None = None          # remakes answer with a patch instead of the whole output
    apply_patch: Callable[[dict, dict], dict] | None = None
    patch_hint: str = ""
    max_rounds: int = 3


@dataclass
class StepResult:
    section: str
    unit: str
    status: str            # "passed", "failed" or "stopped" (cost cap or provider balance)
    output: dict | None
    rounds: list = field(default_factory=list)
    record_path: str | None = None
    cost_usd: float = 0.0
    seconds: float = 0.0

    @property
    def passed(self) -> bool:
        return self.status == "passed"


def safe_content(content):
    """Message content with images replaced by their hash and size."""
    if isinstance(content, str):
        return content
    out = []
    for part in content:
        if part.get("type") == "image":
            raw = part["data"].encode("ascii")
            out.append({"type": "image", "media_type": part["media_type"], "sha256": hashlib.sha256(raw).hexdigest(),
                        "base64_chars": len(raw)})
        else:
            out.append(dict(part))
    return out


def content_digest(*contents) -> str:
    return hashlib.sha256(json.dumps([safe_content(c) for c in contents], sort_keys=True, ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def _call_info(response, route):
    prov = response.provenance
    via = prov.get("via", "direct")
    cost = estimate_cost(prov.get("returned_model") or response.model, response.usage, None, via)
    if cost is None:
        cost = estimate_cost(response.model, response.usage, None, via)
    return {"route": route, "provider": response.provider, "model": response.model, "via": via,
            "returned_model": prov.get("returned_model"), "request_hash": prov.get("request_hash"),
            "cache_hit": bool(prov.get("cache_hit")), "attempts": prov.get("attempts"),
            "input_tokens": response.usage.get("input_tokens", 0), "output_tokens": response.usage.get("output_tokens", 0),
            "cost_usd": cost or 0.0}


def _problems_text(problems):
    return "\n".join(f"- {p}" for p in problems[:60]) + (f"\n- ... and {len(problems) - 60} more" if len(problems) > 60 else "")


def independence(gateway, maker: str, reviewer: str | None) -> str:
    """How independent the reviewer is: another company (the rule), or the same company with another model
    (a temporary exception while only one provider key is usable; marked in every record)."""
    if reviewer is None:
        return "none"
    company = lambda route: getattr(gateway.routes[route], "provider", route) if route in getattr(gateway, "routes", {}) else route
    return "same_company_temporary" if company(maker) == company(reviewer) else "other_company"


class SectionRunner:
    def __init__(self, gateway, *, maker: str, reviewer: str | None, rulebook, records_dir: str | Path | None = None,
                 clock=time.time):
        if reviewer is not None and reviewer == maker:
            raise ValueError("the reviewer must be a different route from the maker")
        self.gateway, self.maker, self.reviewer, self.rulebook = gateway, maker, reviewer, rulebook
        self.records_dir = Path(records_dir) if records_dir else None
        self._clock = clock
        self.independence = independence(gateway, maker, reviewer)

    def run(self, step: Step) -> StepResult:
        messages = [{"role": "system", "content": step.system}, {"role": "user", "content": step.user}]
        rounds, output, status = [], None, "failed"
        started = self._clock()
        schema, patching = step.schema, False
        for number in range(1, step.max_rounds + 1):
            entry = {"round": number, "started_at": self._clock(), "mode": "patch" if patching else "full"}
            request = ModelRequest(request_id=f"{step.section}:{step.unit}:r{number}", messages=tuple(messages),
                                   response_schema=schema)
            try:
                response = self.gateway.complete(self.maker, request, prompt_version=step.instructions_version)
            except ProviderError as exc:
                entry.update(maker_error={"kind": exc.kind, "message": str(exc)[:300]}, passed=False)
                rounds.append(entry)
                status = "stopped" if exc.kind in STOP_KINDS else status
                break
            value = response.content
            if patching:
                entry["patch"] = value
                value = step.apply_patch(output, value)
            entry["maker"] = _call_info(response, self.maker)
            entry["notes"] = value.get("notes")
            entry["output"] = value
            problems = [f"[code] {p}" for p in step.check(value)]
            entry["code_problems"] = problems
            if not problems and self.reviewer and step.review_system:
                review_messages = ({"role": "system", "content": step.review_system},
                                   {"role": "user", "content": step.review_user(value)})
                review_request = ModelRequest(request_id=f"{step.section}:{step.unit}:r{number}:review",
                                              messages=review_messages, response_schema=step.review_schema)
                try:
                    review = self.gateway.complete(self.reviewer, review_request,
                                                   prompt_version=step.instructions_version + "/review")
                except ProviderError as exc:
                    entry.update(review_error={"kind": exc.kind, "message": str(exc)[:300]}, passed=False)
                    rounds.append(entry)
                    output = value
                    status = "stopped" if exc.kind in STOP_KINDS else status
                    break
                entry["review"] = dict(_call_info(review, self.reviewer), value=review.content)
                problems = [f"[reviewer] {p}" for p in step.review_problems(review.content)]
                entry["review_problems"] = problems
                entry["review_minor"] = minor_findings(review.content)
            entry["passed"] = not problems
            entry["finished_at"] = self._clock()
            rounds.append(entry)
            output = value
            if not problems:
                status = "passed"
                break
            previous = json.dumps(value, ensure_ascii=False)
            patching = step.patch_schema is not None and step.apply_patch is not None
            schema = step.patch_schema if patching else step.schema
            instruction = (PATCH_INSTRUCTION.format(problems=_problems_text(problems), hint=step.patch_hint) if patching
                           else REMAKE_INSTRUCTION.format(problems=_problems_text(problems)))
            messages = [messages[0], messages[1], {"role": "assistant", "content": previous},
                        {"role": "user", "content": instruction}]
        cost = sum(r.get("maker", {}).get("cost_usd", 0.0) + r.get("review", {}).get("cost_usd", 0.0) for r in rounds)
        result = StepResult(step.section, step.unit, status, output, rounds, cost_usd=round(cost, 6),
                            seconds=round(self._clock() - started, 1))
        result.record_path = self._save(step, result)
        return result

    def _model(self, route):
        try:
            return self.gateway.model_of(route) if route else None
        except (AttributeError, KeyError):
            return None

    def _save(self, step: Step, result: StepResult):
        if self.records_dir is None:
            return None
        record = {
            "schema": RECORD_SCHEMA,
            "section": step.section,
            "unit": step.unit,
            "status": result.status,
            "instructions_version": step.instructions_version,
            "rulebook_version": self.rulebook.version,
            "rulebook_digest": self.rulebook.digest,
            "rules_used": [r.id for r in self.rulebook.for_section(step.section)],
            "maker_route": self.maker,
            "reviewer_route": self.reviewer,
            "maker_model": self._model(self.maker),
            "reviewer_model": self._model(self.reviewer),
            "reviewer_independence": self.independence,
            "inputs_digest": content_digest(step.system, step.user),
            "inputs": {"system": step.system, "user": safe_content(step.user)},
            "rounds": result.rounds,
            "avoid_rounds": [r["round"] for r in result.rounds if not r.get("passed")],
            "cost_usd": result.cost_usd,
            "seconds": result.seconds,
            "navin_verdict": None,
        }
        self.records_dir.mkdir(parents=True, exist_ok=True)
        path = self.records_dir / f"{step.section}--{step.unit}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        return str(path)
