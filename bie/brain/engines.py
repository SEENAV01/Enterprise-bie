"""The old BIE engines inside the brain (Task 045, docs/roadmap/TARAZU.md rows KI, PR, RE and PED).

One BIE: the brain sections make the understanding and the lesson; the old engines' algorithms check them.

- KI knowledge: replaced and retired. The lexical producer (``bie/productization/candidates.py``) is not BIE's
  understanding any more; Section 1 is. Its QA functions are used: concept coverage (``ki_coverage_qa``),
  orphan concepts (``knowledge_graph_orphans``) and definition consistency (``definition_consistency``).
- PR prerequisites: the lexical producer (``bie/productization/pr_reasoning.py``) is replaced and retired; the
  graph algorithms check the map's prerequisite graph: cycles (``cycle_resolution.find_cycle``), the teaching
  order (``teaching_order``) and redundant links (``transitive_reduction``).
- RE reasoning: extended. Cause cycles (``graph_cycles.find_cycles``) and time order of dated concepts
  (``chronology_reasoning.year`` and ``relation``) check the map's cause-effect and sequence links.
- PED pedagogy: the template planner (``bie/productization/pedagogy_plan.py``) is replaced and retired by
  Section 2; its QA checks the lesson: objective coverage (``objective_coverage_qa``), cognitive load per beat
  (``cognitive_load_qa``), prerequisite coverage (``prerequisite_coverage_qa``) and duration
  (``lesson_duration_estimation``, recorded beside the script's spoken length).

Retired means: no brain section, no brain tool and no new BIE work calls these producers (a test enforces it).
Their files stay, because the evidence ledgers fail on a deleted working file and the 11-stage technical
pipeline still runs them as regression fixtures for Scene IR and the compiler until Task 051 moves that durable
run onto the brain sections; their outputs are already labelled TECHNICAL_SOURCE_DERIVED and never accepted.
"""
from __future__ import annotations

import re

from bie.knowledge_intelligence.definition_consistency import compare as definitions_compare
from bie.knowledge_intelligence.ki_coverage_qa import evaluate as ki_coverage
from bie.knowledge_intelligence.knowledge_graph_orphans import find as find_orphans
from bie.pedagogy.cognitive_load_qa import cognitive_load_qa
from bie.pedagogy.lesson_duration_estimation import estimate_duration
from bie.pedagogy.objective_coverage_qa import objective_coverage_qa
from bie.pedagogy.prerequisite_coverage_qa import prerequisite_coverage_qa
from bie.prerequisite_intelligence.cycle_resolution import WeightedEdge, find_cycle
from bie.prerequisite_intelligence.teaching_order import teaching_order
from bie.prerequisite_intelligence.transitive_reduction import transitive_reduction
from bie.reasoning.chronology_reasoning import relation as time_relation, year as parse_year
from bie.reasoning.graph_cycles import find_cycles

DECISIONS = (
    {"engine": "KI", "path": "bie/knowledge_intelligence/", "decision": "replace and retire",
     "retired": ["bie.productization.candidates"], "replaced_by": "bie.brain.understanding (Section 1)",
     "used_as_checks": ["ki_coverage_qa.evaluate", "knowledge_graph_orphans.find", "definition_consistency.compare"],
     "reason": "Lexical candidates (capitalised words and verbatim sentences) are not understanding; Section 1 reads "
               "both eyes and questions every item like a teacher. The KI QA functions still check the result."},
    {"engine": "PR", "path": "bie/prerequisite_intelligence/", "decision": "replace and retire the producer; use the graph",
     "retired": ["bie.productization.pr_reasoning"], "replaced_by": "the chapter map's depends_on links and prerequisites_to_teach",
     "used_as_checks": ["cycle_resolution.find_cycle", "teaching_order.teaching_order", "transitive_reduction.transitive_reduction"],
     "reason": "The producer accepted only literal 'X requires Y' sentences, so real books gave almost no prerequisites; "
               "the AI names them and the PR graph algorithms check them: no circles, order before use, no redundant links."},
    {"engine": "RE", "path": "bie/reasoning/", "decision": "extend",
     "retired": [], "replaced_by": "",
     "used_as_checks": ["graph_cycles.find_cycles", "chronology_reasoning.year", "chronology_reasoning.relation"],
     "reason": "Its graph and time reasoning is sound and deterministic; it now checks the AI's cause-effect links for "
               "circles and its sequence and cause links between dated concepts for going back in time."},
    {"engine": "PED", "path": "bie/pedagogy/", "decision": "replace and retire the planner; use the QA",
     "retired": ["bie.productization.pedagogy_plan", "bie.productization.pedagogy_slice"],
     "replaced_by": "bie.brain.lesson (Section 2)",
     "used_as_checks": ["objective_coverage_qa.objective_coverage_qa", "cognitive_load_qa.cognitive_load_qa",
                        "prerequisite_coverage_qa.prerequisite_coverage_qa", "lesson_duration_estimation.estimate_duration"],
     "reason": "The planner composed records from templates and wrote no narration; Section 2 writes the lesson on its "
               "task card, and the PED QA functions check coverage, load per beat, prerequisites and length."},
)
RETIRED_MODULES = tuple(m for d in DECISIONS for m in d["retired"])

YEAR = re.compile(r"\b(\d{1,4})\s*(BCE|BC|CE|AD)\b|\b(1[0-9]{3}|20[0-9]{2})\b")


# ---------------------------------------------------------------- chapter map (Section 1, connect step)

def _concept_edges(value, relation):
    """(from, to) pairs of one relation between known concepts."""
    known = {c["concept_id"] for c in value.get("concepts") or []}
    return [(r["from_concept"], r["to_concept"]) for r in value.get("relations") or []
            if r["relation"] == relation and r["from_concept"] in known and r["to_concept"] in known
            and r["from_concept"] != r["to_concept"]]


def _years(concept, items):
    found = []
    for iid in concept.get("item_ids") or []:
        for era_number, era, plain in YEAR.findall((items.get(iid) or {}).get("content", "")):
            label = f"{era_number} {era}" if era else plain
            try:
                found.append((parse_year(label), label))
            except ValueError:
                continue
    return min(found, key=lambda pair: pair[0].earliest) if found else None


def map_checks(value: dict, items: dict) -> tuple:
    """(problems, observed) for a chapter map, from the PR, RE and KI engines."""
    problems, observed = [], {}
    concepts = {c["concept_id"]: c for c in value.get("concepts") or []}
    nodes = set(concepts)
    # PR: "A depends_on B" means B is taught first: an edge B -> A.
    prereq = [(b, a) for a, b in _concept_edges(value, "depends_on")]
    cycle = find_cycle(nodes, [WeightedEdge(a, b, 1.0) for a, b in prereq])
    if cycle:
        circle = " -> ".join([cycle[0].source] + [e.target for e in cycle])
        problems.append(f"prerequisites go in a circle ({circle}); a concept cannot be needed by what it needs (PR cycle check)")
    else:
        order = [c for c in value.get("teaching_order") or [] if c in nodes]
        position = {c: n for n, c in enumerate(order)}
        late = [(a, b) for a, b in prereq if a in position and b in position and position[a] > position[b]]
        if late:
            priority = {c: -n for n, c in enumerate(order)}
            valid = teaching_order(nodes, prereq, priority) if len(order) == len(nodes) else []
            shown = ", ".join(f"{b} before its prerequisite {a}" for a, b in late[:8])
            problems.append(f"teaching_order teaches {shown} (PR teaching-order check)"
                            + (f"; an order that keeps yours where it can: {', '.join(valid)}" if valid else ""))
        kept = set(transitive_reduction(nodes, prereq)) if prereq else set()
        redundant = sorted(set(prereq) - kept)
        if redundant:
            observed["redundant_prerequisite_links"] = [f"{b} depends_on {a}" for a, b in redundant]
    # RE: cause and effect must not go in a circle; dated sequence and cause links must not go back in time.
    causes = _concept_edges(value, "causes")
    if causes:
        for circle in find_cycles(sorted(nodes), causes)[:3]:
            problems.append(f"cause and effect go in a circle ({' -> '.join(circle)}) (RE cause-graph check)")
    for relation in ("sequence_next", "causes"):
        for a, b in _concept_edges(value, relation):
            first, then = _years(concepts[a], items), _years(concepts[b], items)
            if first and then and time_relation(first[0], then[0]) == "after":
                problems.append(f"{a} {relation} {b}, but {a} is dated {first[1]} and {b} {then[1]}: the link goes back in "
                                f"time (RE chronology check)")
    # KI: coverage of teachable items (high exam items are critical), orphan concepts, consistent definitions.
    teachable = [i for i, it in items.items() if it.get("teachable")]
    grouped = {i for c in concepts.values() for i in c.get("item_ids") or []}
    critical = [i for i in teachable if items[i].get("exam_importance") == "high"]
    report = ki_coverage(teachable, grouped & set(teachable), critical) if teachable else {"coverage": 1, "missing": (), "passed": True}
    observed["ki_coverage"] = {"coverage": round(report["coverage"], 4), "passed": report["passed"],
                               "missing_critical": sorted(set(report["missing"]) & set(critical))[:30]}
    graph = {"nodes": sorted(nodes), "edges": [{"source": r["from_concept"], "target": r["to_concept"]}
                                                for r in value.get("relations") or []]}
    lonely = [c for c in find_orphans(graph) if len(nodes) > 2]
    if lonely:
        observed["orphan_concepts"] = lonely
    uneven = []
    for cid, concept in concepts.items():
        definitions = [{"text": items[i]["content"]} for i in concept.get("item_ids") or []
                       if items.get(i, {}).get("content_type") == "definition" and items[i].get("content", "").strip()]
        if len(definitions) > 1:
            try:
                result = definitions_compare(definitions)
            except ValueError:
                continue
            if not result["consistent"]:
                uneven.append({"concept": cid, "min_similarity": round(result["min_similarity"], 3)})
    if uneven:
        observed["definitions_to_reconcile"] = uneven
    return problems, observed


# ---------------------------------------------------------------- lesson (Section 2)

MAX_LOAD = 1.8           # cognitive_load_qa's default threshold
ITEM_LOAD = 0.4          # one new item in a beat
WORD_LOAD = 1 / 50       # one spoken word


def beat_loads(beats, must_cover) -> list:
    """(beat id, load) per beat: new items introduced and spoken words, on cognitive_load_qa's scale."""
    seen, loads = set(), []
    wanted = set(must_cover)
    for beat in beats:
        new = [i for i in beat.get("covers_item_ids") or [] if i in wanted and i not in seen]
        seen.update(new)
        loads.append((beat["beat_id"], round(ITEM_LOAD * len(new) + WORD_LOAD * len(beat.get("say", "").split()), 3)))
    return loads


def script_checks(beats, must_cover, *, planned_minutes: int | None, minutes_range: tuple | None = None) -> tuple:
    """(problems, observed) for one script, from the PED engine. With ``minutes_range`` the lesson's time rule (S2-01)
    replaces PED's "not under half the planned minutes" check; the lesson section checks the range itself."""
    problems, observed = [], {}
    by_item = {}
    for beat in beats:
        for iid in beat.get("covers_item_ids") or []:
            by_item.setdefault(iid, []).append(beat["beat_id"])
    if must_cover:
        report = objective_coverage_qa(by_item, must_cover)
        observed["objective_coverage"] = {"coverage": round(report.coverage, 4), "uncovered": list(report.uncovered_objectives)[:40]}
    loads = beat_loads(beats, must_cover)
    if loads:
        report = cognitive_load_qa(loads, max_load=MAX_LOAD)
        heavy = {sid: load for sid, load in loads if sid in report.overload_segments}
        for sid, load in heavy.items():
            beat = next(b for b in beats if b["beat_id"] == sid)
            problems.append(f"beat {sid} is too heavy for one breath (load {load} over {MAX_LOAD}: "
                            f"{len(beat.get('covers_item_ids') or [])} items, {len(beat.get('say', '').split())} words); "
                            f"split it into smaller beats (PED cognitive-load check)")
        observed["cognitive_load"] = {"max": max(load for _, load in loads), "abrupt_jumps": list(report.abrupt_jumps)[:20]}
    words = sum(len(b.get("say", "").split()) for b in beats)
    spoken = round(words / 130, 1)
    observed["duration"] = {"spoken_minutes_at_130_wpm": spoken, "planned_minutes": planned_minutes}
    if minutes_range is not None:
        observed["duration"]["range"] = list(minutes_range)
    elif planned_minutes and spoken < 0.5 * planned_minutes:
        problems.append(f"the script speaks about {spoken} minutes but the plan gives this video {planned_minutes}; "
                        f"nothing may be compressed away (G-05, PED duration check)")
    return problems, observed


def plan_checks(videos, concepts, prerequisites) -> tuple:
    """(problems, observed) for a lesson plan: every prerequisite bridged before use (PED), and PED's duration model."""
    problems, observed = [], {}
    names = {p["name"].strip().lower(): p["name"] for p in prerequisites}
    taught = {name.strip().lower() for v in videos for name in v.get("prerequisites_taught") or []}
    if names:
        report = prerequisite_coverage_qa(list(names), {n: 0.0 for n in names}, taught)
        for name in report.unbridged_prerequisites:
            problems.append(f"prerequisite {names[name]!r} is taught in no video (S2-03, PED prerequisite-coverage check); "
                            "use the exact name from the list")
    observed["ped_minutes"] = {v["video_id"]: round(estimate_duration(max(1, len(v.get("concept_ids") or [])), 1.0, 0), 1)
                               for v in videos}
    return problems, observed
