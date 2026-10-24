"""The section runner: how every BIE section works, the same way every time.

One step is one unit of work of one section (for example one page for "understand"). It runs:

1. The maker AI gets the section's instructions (role, course, the vision rules for this section,
   output format) and the source (text and page images). It writes brief notes (what the unit is
   about, its main decisions with reasons, what is uncertain) and its output.
2. BIE's code checks the output (``Step.check``). Problems go straight back to the maker.
3. An independent reviewer AI, on a different provider, checks the output against the source and
   the rulebook checklist (``Step.review_*``). Its findings go back to the maker.
4. The maker remakes the whole output with those findings, at most ``max_rounds`` rounds in all; a converging answer
   (code alone sends it back with ever fewer problems, at most ``CONVERGING_MAX``) gets up to ``extra_rounds`` more patch
   rounds, which cost no reviewer call (Task 045d).
5. Every round is kept in the process record: the maker's notes and output, the code
   problems, the reviewer's findings, models, tokens and cost. A passed step is a candidate for
   locking; failed rounds are kept and marked "avoid".

Since Task 045 a step can carry its task card (``bie/brain/cards.py``): the system message is then the card's
fixed prefix, whose hash must match the card before anything is sent, and the record keeps the card, the
prefix hash and what BIE's code observed about each round (``Step.observe``, for example the type comparison).

Since Task 045d (job B2) a step can continue from an earlier answer (``Step.start``, for example a script that failed
an earlier run by one or two words): round 0 makes no maker call; BIE's code checks that answer with today's checks and,
when it is clean, the reviewer reads it; otherwise the first maker round is a patch of exactly today's problems (and round
0's count is the "round before" for converging rounds). A failed unit is then finished, not written again from scratch (a
fresh rewrite brings new problems of its own).

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


CONVERGING_MAX = 4           # a code-only rejection with at most this many problems, fewer than the round before, converges


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
    patch_hint: str | Callable[[dict], str] = ""     # text, or (current answer) -> text for the next patch round
    max_rounds: int = 3
    extra_rounds: int = 3        # converging rounds past max_rounds: only while code alone sends the answer back with ever fewer
                                 # problems, at most CONVERGING_MAX of them (Task 045d, job B: 1-4 small residues after 3 rounds)
    card: dict | None = None                  # the task card sent with this step (Task 045)
    observe: Callable[[dict], dict] | None = None   # code findings to record per round, never sent back
    normalize: Callable[[dict], tuple] | None = None  # (value, changes): code tidies the answer before checks and review
    start: dict | None = None                 # an earlier answer to continue from (round 0: no maker call, Task 045d B2)


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


def merge_notes(previous: dict | None, patch: dict | None) -> dict | None:
    """The notes of a patched answer: the whole unit's notes stay (about, key questions); the patch's decisions are added
    and its uncertainties replace the old ones. A patch round's notes alone describe only the patch (job 2, v11: the
    reviewer failed a passed script for notes that read "local correction to beat b34")."""
    if not previous or not patch:
        return patch or previous
    return {"about": previous.get("about") or patch.get("about", ""),
            "key_questions": previous.get("key_questions") or patch.get("key_questions") or [],
            "decisions": list(previous.get("decisions") or []) + list(patch.get("decisions") or []),
            "uncertain": patch.get("uncertain") if patch.get("uncertain") is not None else previous.get("uncertain", [])}


def _problems_text(problems):
    return "\n".join(f"- {p}" for p in problems[:60]) + (f"\n- ... and {len(problems) - 60} more" if len(problems) > 60 else "")


def independence(gateway, maker: str, reviewer: str | None) -> str:
    """How independent the reviewer is: another company (the rule); the same company with another model (a temporary
    exception while only one provider key is usable); or the same model in a fresh call when the key allows only one
    model (kamzor jaanch, the weakest check). Marked in every record; nothing it passes is ever locked as accepted."""
    if reviewer is None:
        return "none"
    company = lambda route: getattr(gateway.routes[route], "provider", route) if route in getattr(gateway, "routes", {}) else route
    if company(maker) != company(reviewer):
        return "other_company"
    try:
        same_model = gateway.model_of(maker) == gateway.model_of(reviewer)
    except (AttributeError, KeyError):
        same_model = False
    return "same_model_temporary" if same_model else "same_company_temporary"


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
        if step.card is not None and step.card["prefix"]["sha256"] != hashlib.sha256(step.system.encode("utf-8")).hexdigest():
            raise ValueError(f"{step.section}:{step.unit}: the card's prefix hash is not the system message that would be sent")
        messages = [{"role": "system", "content": step.system}, {"role": "user", "content": step.user}]
        rounds, output, status = [], None, "failed"
        started = self._clock()
        schema, patching = step.schema, False
        number, extra_used, last_code, converging = 0, 0, None, False
        if step.start is not None:
            status, output, last_code, messages, schema, patching = self._resume(step, rounds, messages)
        while status == "failed" and not (rounds and rounds[-1].get("review_error")):
            number += 1
            if number > step.max_rounds:
                # A converging answer (code alone sent it back, with fewer problems than the round before, at most
                # CONVERGING_MAX) gets up to extra_rounds more patch rounds; these cost no reviewer call.
                if not (converging and extra_used < step.extra_rounds):
                    break
                extra_used += 1
            entry = {"round": number, "started_at": self._clock(), "mode": "patch" if patching else "full"}
            if number > step.max_rounds:
                entry["extra_round"] = True
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
            if step.normalize is not None:
                value, changes = step.normalize(value)
                if changes:
                    entry["normalized"] = changes
            entry["maker"] = _call_info(response, self.maker)
            entry["notes"] = value.get("notes")
            entry["output"] = value
            problems = [f"[code] {p}" for p in step.check(value)]
            entry["code_problems"] = problems
            converging = (bool(problems) and len(problems) <= CONVERGING_MAX
                          and last_code is not None and len(problems) < last_code)     # one round shows no trend
            if problems:
                last_code = len(problems)
            if step.observe is not None:
                entry["observed"] = step.observe(value)
            if not problems and self.reviewer and step.review_system:
                problems = self._review(step, value, entry, number)
                if problems is None:                    # the reviewer call failed
                    rounds.append(entry)
                    output = value
                    status = "stopped" if entry["review_error"]["kind"] in STOP_KINDS else status
                    break
                converging = False                      # a reviewer's rejection never extends the rounds
            entry["passed"] = not problems
            entry["finished_at"] = self._clock()
            rounds.append(entry)
            output = value
            if not problems:
                status = "passed"
                break
            messages, schema, patching = self._next(step, messages, value, problems)
        cost = sum(r.get("maker", {}).get("cost_usd", 0.0) + r.get("review", {}).get("cost_usd", 0.0) for r in rounds)
        result = StepResult(step.section, step.unit, status, output, rounds, cost_usd=round(cost, 6),
                            seconds=round(self._clock() - started, 1))
        result.record_path = self._save(step, result)
        return result

    def _resume(self, step: Step, rounds: list, messages: list) -> tuple:
        """Round 0 (Task 045d B2): the earlier answer in ``step.start`` is checked by code and, when clean, reviewed; no
        maker call. Returns (status, output, problem count, messages, schema, patching) for the rounds that follow."""
        value = json.loads(json.dumps(step.start))
        entry = {"round": 0, "started_at": self._clock(), "mode": "resume"}
        if step.normalize is not None:
            value, changes = step.normalize(value)
            if changes:
                entry["normalized"] = changes
        entry["notes"] = value.get("notes")
        entry["output"] = value
        problems = [f"[code] {p}" for p in step.check(value)]
        entry["code_problems"] = problems
        if step.observe is not None:
            entry["observed"] = step.observe(value)
        count = len(problems) or None
        if not problems and self.reviewer and step.review_system:
            problems = self._review(step, value, entry, 0)
            if problems is None:
                rounds.append(entry)
                status = "stopped" if entry["review_error"]["kind"] in STOP_KINDS else "failed"
                return status, value, count, messages, step.schema, False
        entry["passed"] = not problems
        entry["finished_at"] = self._clock()
        rounds.append(entry)
        if not problems:
            return "passed", value, count, messages, step.schema, False
        return ("failed", value, count) + self._next(step, messages, value, problems)

    def _review(self, step: Step, value: dict, entry: dict, number: int):
        """The reviewer's problems for a clean answer, recorded in ``entry``; None when the reviewer call failed."""
        review_messages = ({"role": "system", "content": step.review_system},
                           {"role": "user", "content": step.review_user(value)})
        review_request = ModelRequest(request_id=f"{step.section}:{step.unit}:r{number}:review",
                                      messages=review_messages, response_schema=step.review_schema)
        try:
            review = self.gateway.complete(self.reviewer, review_request, prompt_version=step.instructions_version + "/review")
        except ProviderError as exc:
            entry.update(review_error={"kind": exc.kind, "message": str(exc)[:300]}, passed=False)
            return None
        entry["review"] = dict(_call_info(review, self.reviewer), value=review.content)
        problems = [f"[reviewer] {p}" for p in step.review_problems(review.content)]
        entry["review_problems"] = problems
        entry["review_minor"] = minor_findings(review.content)
        return problems

    @staticmethod
    def _next(step: Step, messages: list, value: dict, problems: list) -> tuple:
        """(messages, schema, patching) for the next maker round: the answer so far and the problems to fix."""
        previous = json.dumps(value, ensure_ascii=False, separators=(",", ":"))     # compact: the maker reads it again
        patching = step.patch_schema is not None and step.apply_patch is not None
        schema = step.patch_schema if patching else step.schema
        hint = step.patch_hint(value) if callable(step.patch_hint) else step.patch_hint
        instruction = (PATCH_INSTRUCTION.format(problems=_problems_text(problems), hint=hint) if patching
                       else REMAKE_INSTRUCTION.format(problems=_problems_text(problems)))
        return ([messages[0], messages[1], {"role": "assistant", "content": previous},
                 {"role": "user", "content": instruction}], schema, patching)

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
            "card": step.card,
            "prefix_sha256": hashlib.sha256(step.system.encode("utf-8")).hexdigest(),
            "review_prefix_sha256": hashlib.sha256(step.review_system.encode("utf-8")).hexdigest() if step.review_system else None,
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
