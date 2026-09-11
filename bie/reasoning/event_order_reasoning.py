"""RE-TEMP-002: evidence-grounded partial orders, date consistency and cycle refusal."""
from __future__ import annotations
from collections import deque
from dataclasses import asdict, dataclass
from datetime import date
import heapq

from bie.reasoning.chronology_reasoning import chronology, validate_events
from bie.reasoning.decision_graph import build
from bie.reasoning.grounded_result import identifier, inference, require_refs

TASK_ID = "BIE-RE-TEMP-002"


@dataclass(frozen=True)
class Before:
    before: str
    after: str
    evidence_ids: tuple[str, ...]


def _effective_bounds(span):
    """Missing evidence does not remove the declared calendar's limits."""
    if span.axis == "gregorian_day":
        return (1 if span.earliest is None else span.earliest,
                date.max.toordinal() if span.latest is None else span.latest)
    return span.earliest, span.latest


def _cycle(adjacency, remaining):
    """Iterative DFS returns an actual cycle witness, not all blocked descendants."""
    finished = set()
    for start in sorted(remaining):
        if start in finished: continue
        path, active = [start], {start: 0}
        stack = [(start, iter(sorted(adjacency[start])))]
        while stack:
            node, children = stack[-1]
            child = next(children, None)
            if child is None:
                stack.pop(); finished.add(node); active.pop(node); path.pop()
            elif child in active:
                return path[active[child]:] + [child]
            elif child not in finished:
                active[child] = len(path); path.append(child)
                stack.append((child, iter(sorted(adjacency[child]))))
    return []


def event_order(events, constraints, refs):
    events, refs = validate_events(events, refs)
    constraints = tuple(sorted(constraints, key=lambda c: (c.before, c.after)))
    by_id = {x.event_id: x for x in events}
    bounds = {x.event_id: _effective_bounds(x.time) for x in events}
    temporal = chronology(events, refs)
    edges = {tuple(x) for x in temporal.value["proven_before"]}
    provenance = {edge: {"kind": "date_bounds", "evidence_ids": sorted(set(by_id[edge[0]].evidence_ids + by_id[edge[1]].evidence_ids))} for edge in edges}
    seen, violations = set(), []
    for c in constraints:
        identifier(c.before); identifier(c.after); require_refs(c.evidence_ids, refs)
        if c.before not in by_id or c.after not in by_id or c.before == c.after:
            raise ValueError("Constraint endpoints must be known distinct events")
        edge = (c.before, c.after)
        if edge in seen:
            raise ValueError("Duplicate explicit order constraint")
        seen.add(edge)
        lower, upper = bounds[c.before][0], bounds[c.after][1]
        if lower is not None and upper is not None and lower >= upper:
            violations.append({"before": c.before, "after": c.after, "reason": "Strict before relation contradicts date bounds", "evidence_ids": sorted(set(c.evidence_ids + by_id[c.before].evidence_ids + by_id[c.after].evidence_ids))})
        edges.add(edge)
        prior = provenance.get(edge)
        provenance[edge] = {"kind": "explicit_and_date_bounds" if prior else "explicit", "evidence_ids": sorted(set(c.evidence_ids) | set(prior["evidence_ids"] if prior else []))}
    graph = build(sorted(by_id), sorted(edges))
    adjacency, indegree = {k: set() for k in by_id}, {k: 0 for k in by_id}
    for a, b in graph.edges:
        adjacency[a].add(b); indegree[b] += 1
    ready = sorted(k for k in by_id if indegree[k] == 0)
    heapq.heapify(ready)
    order, unique = [], True
    while ready:
        if len(ready) > 1: unique = False
        node = heapq.heappop(ready); order.append(node)
        for child in sorted(adjacency[node]):
            indegree[child] -= 1
            if indegree[child] == 0: heapq.heappush(ready, child)
    remaining = set(by_id) - set(order)
    cycle = _cycle(adjacency, remaining) if remaining else []
    # Propagate all strict constraints through interval lower bounds. This catches
    # contradictions caused by a chain even when every individual edge is feasible.
    effective_lower = {k: bounds[k][0] for k in by_id}
    if not cycle:
        for node in order:
            lower = effective_lower[node]
            upper = bounds[node][1]
            if lower is not None and upper is not None and lower > upper:
                violations.append({"event_id": node, "reason": "Order chain is infeasible within date bounds", "earliest_required": lower, "latest_allowed": upper})
            if lower is not None:
                for child in adjacency[node]:
                    old = effective_lower[child]
                    effective_lower[child] = lower + 1 if old is None else max(old, lower + 1)
    conflict = bool(violations or cycle)
    inputs = {"events": [asdict(x) for x in events], "constraints": [asdict(x) for x in sorted(constraints, key=lambda c: (c.before, c.after))]}
    value = {"axis": events[0].time.axis, "linear_extension": [] if conflict else order, "unique_order": unique and not conflict, "edges": [{"before": a, "after": b, **provenance[(a, b)]} for a, b in sorted(edges)], "cycle_witness": cycle, "violations": violations, "blocked_event_ids": sorted(remaining)}
    status = "CONFLICT" if conflict else "RESOLVED" if unique else "AMBIGUOUS"
    uncertainty = ("Contradictory ordering evidence requires review; no valid order emitted",) if conflict else ("Multiple valid linear extensions exist; lexical tie-breaking does not imply chronology",) if not unique else ()
    return inference(TASK_ID, "temporal.event_order", inputs, value, refs, status=status, assumptions=("Before is strict at the declared year/day resolution", "Explicit temporal precedence does not imply causation"), uncertainty=uncertainty)
