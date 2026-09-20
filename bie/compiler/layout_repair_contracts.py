"""H4-001: explicit layout authority and content-preserving candidate generation.

A bounded local search is not a teaching-plan rewrite. It changes only declared
owner rectangles and the supported, literal-only presentation contract. The
upstream visual owner must explicitly grant space; defaults invent no new space.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from typing import Any, Iterator

from .artifact_hashing import canonical_json
from .frame_layout import finite, layout_policy, layer_box
from .qa_common import CompilerQAError, digest
from .scene_ir_loader import load_scene_ir_payload

SCHEMA = "bie.layout-repair-policy.v1"
LAYOUT_KEY = "compiler_layout"
SUPPORTED = frozenset({"text", "map", "equation"})
MAX_CANDIDATES = 32
MAX_OWNERS = 8


def fail(code: str, message: str) -> None:
    raise CompilerQAError(code + ": " + message)


def canonical_scene(payload: dict) -> dict:
    """Validate original fingerprint before omitting it from a mutable derivative."""
    result = load_scene_ir_payload(payload).document.to_dict()
    result.pop("fingerprint", None)
    return result


def box(value: Any) -> dict[str, float]:
    if not isinstance(value, dict) or set(value) != {"x", "y", "width", "height"}:
        fail("REPAIR_BOX_INVALID", "exact x,y,width,height object required")
    b = {key: finite(value[key], key) for key in ("x", "y", "width", "height")}
    if b["x"] < 0 or b["y"] < 0 or b["width"] <= 0 or b["height"] <= 0 or b["x"] + b["width"] > 1 + 1e-12 or b["y"] + b["height"] > 1 + 1e-12:
        fail("REPAIR_BOX_INVALID", "rectangle must be positive and inside viewport")
    return b


def contains(outer: dict, inner: dict) -> bool:
    return (inner["x"] >= outer["x"] - 1e-12 and inner["y"] >= outer["y"] - 1e-12
            and inner["x"] + inner["width"] <= outer["x"] + outer["width"] + 1e-12
            and inner["y"] + inner["height"] <= outer["y"] + outer["height"] + 1e-12)


def presentation(kind: str, value: Any) -> dict:
    if kind not in {"text", "map"}:
        fail("REPAIR_PRESENTATION_UNSUPPORTED", "only text and map have presentation adapters")
    common = {"font_px", "line_height", "padding_px"}
    allowed = common | ({"legend_columns", "plot_height_px"} if kind == "map" else set())
    if not isinstance(value, dict) or set(value) != allowed:
        fail("REPAIR_PRESENTATION_INVALID", "supported presentation fields must be explicit and exact")
    result = {k: finite(value[k], k) for k in common}
    if not 12 <= result["font_px"] <= 96 or not 1.25 <= result["line_height"] <= 2.5 or not 0 <= result["padding_px"] <= 32:
        fail("REPAIR_PRESENTATION_INVALID", "font, line spacing or padding outside technical contract")
    if kind == "map":
        cols = value["legend_columns"]
        if type(cols) is not int or not 1 <= cols <= 3:
            fail("REPAIR_PRESENTATION_INVALID", "legend columns must be integer 1..3")
        height = finite(value["plot_height_px"], "plot_height_px")
        if not 120 <= height <= 1024:
            fail("REPAIR_PRESENTATION_INVALID", "plot height must be 120..1024 CSS pixels")
        result.update(legend_columns=cols, plot_height_px=height)
    return result


def default_policy(payload: dict) -> dict:
    """No geometry expansion by default. Intended for upstream policy construction."""
    raw = canonical_scene(payload)
    floor = max(16., layout_policy(raw)["min_text_px"])
    owners = {}
    for e in raw["elements"]:
        kind = e["element_type"]
        if kind not in SUPPORTED:
            continue
        style = None
        if kind in {"text", "map"}:
            style = {"font_px": floor, "line_height": 1.4, "padding_px": 0.}
            if kind == "map":
                style.update(legend_columns=1, plot_height_px=180.)
            if LAYOUT_KEY in e["props"]:
                style = presentation(kind, e["props"][LAYOUT_KEY])
        owners[e["element_id"]] = {"region": deepcopy(e["normalized_box"]), "presentation": style}
    if not owners:
        fail("REPAIR_NO_SUPPORTED_OWNERS", "this bounded repair adapter has no eligible elements")
    return {"schema_version": SCHEMA, "scene_identity": digest(raw), "max_candidates": 16,
            "owners": owners, "reason": "Reflow inside existing owned boxes only; no new layout space granted.",
            "source_refs": list(raw["source_refs"]), "reasoning_refs": list(raw["reasoning_refs"])}


def validate_policy(payload: dict, policy: Any) -> tuple[dict, dict]:
    raw = canonical_scene(payload)
    expected = {"schema_version", "scene_identity", "max_candidates", "owners", "reason", "source_refs", "reasoning_refs"}
    if not isinstance(policy, dict) or set(policy) != expected or policy["schema_version"] != SCHEMA:
        fail("REPAIR_POLICY_INVALID", "unknown or missing policy fields")
    if policy["scene_identity"] != digest(raw):
        fail("REPAIR_POLICY_SOURCE_MISMATCH", "policy must identify the exact original Scene IR")
    budget = policy["max_candidates"]
    if type(budget) is not int or not 1 <= budget <= MAX_CANDIDATES:
        fail("REPAIR_BUDGET_INVALID", "candidate budget must be integer 1..32")
    reason = policy["reason"]
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
        fail("REPAIR_POLICY_INVALID", "a bounded upstream justification is required")
    for field in ("source_refs", "reasoning_refs"):
        allowed = set(raw[field]) | {v for e in raw["elements"] for v in e[field]}
        refs = policy[field]
        if not isinstance(refs, list) or not refs or any(not isinstance(v, str) or v not in allowed for v in refs) or len(set(refs)) != len(refs):
            fail("REPAIR_PROVENANCE_UNBOUND", field + " must reference existing provenance")
    owner_data = policy["owners"]
    if not isinstance(owner_data, dict) or not 1 <= len(owner_data) <= MAX_OWNERS:
        fail("REPAIR_POLICY_INVALID", "one to eight explicitly permitted owners required")
    by_id = {e["element_id"]: e for e in raw["elements"]}
    checked = {}
    for eid, grant in sorted(owner_data.items()):
        if eid not in by_id or by_id[eid]["element_type"] not in SUPPORTED:
            fail("REPAIR_OWNER_UNSUPPORTED", "unknown or unsupported owner")
        if not isinstance(grant, dict) or set(grant) != {"region", "presentation"}:
            fail("REPAIR_POLICY_INVALID", "exact owner region and presentation required")
        e = by_id[eid]
        region = box(grant["region"])
        if not contains(region, box(e["normalized_box"])):
            fail("REPAIR_PERMISSION_EXCLUDES_ORIGINAL", "allowed region must contain original geometry")
        if e["element_type"] == "equation":
            if grant["presentation"] is not None:
                fail("REPAIR_PRESENTATION_UNSUPPORTED", "equations may gain space, not change math or type size")
            style = None
        else:
            style = presentation(e["element_type"], grant["presentation"])
            original_size = e["props"].get(LAYOUT_KEY, {}).get("font_px", 16.)
            if style["font_px"] < max(original_size, layout_policy(raw)["min_text_px"]):
                fail("REPAIR_FONT_REDUCTION_FORBIDDEN", "do not reduce type to fit")
        checked[eid] = {"region": region, "presentation": style}
    return raw, {**deepcopy(policy), "owners": checked}


def semantic_identity(payload: dict, owner_ids: set[str]) -> str:
    raw = canonical_scene(payload)
    for e in raw["elements"]:
        if e["element_id"] in owner_ids:
            e.pop("normalized_box", None)
            e["props"].pop(LAYOUT_KEY, None)
    return digest(raw)


def verify_repair(original: dict, candidate: dict, policy: dict) -> dict:
    raw, grant = validate_policy(original, policy)
    effective = canonical_scene(candidate)
    owners = set(grant["owners"])
    if semantic_identity(raw, owners) != semantic_identity(effective, owners):
        fail("REPAIR_SEMANTIC_CHANGE_FORBIDDEN", "non-layout content or contracts changed")
    before = {e["element_id"]: e for e in raw["elements"]}
    changes = []
    for e in effective["elements"]:
        eid = e["element_id"]
        if eid not in owners:
            continue
        permission = grant["owners"][eid]
        b = box(e["normalized_box"])
        if not contains(permission["region"], b):
            fail("REPAIR_OUTSIDE_PERMISSION", eid + " exceeds its authorized rectangle")
        old_box = box(before[eid]["normalized_box"])
        if b["width"] < old_box["width"] - 1e-12 or b["height"] < old_box["height"] - 1e-12:
            fail("REPAIR_SHRINK_FORBIDDEN", "repair must not make the original owner smaller")
        actual_style = e["props"].get(LAYOUT_KEY)
        original_style = before[eid]["props"].get(LAYOUT_KEY)
        if actual_style != original_style and actual_style != permission["presentation"]:
            fail("REPAIR_PRESENTATION_OUTSIDE_PERMISSION", "style differs from the explicit grant")
        if actual_style is not None:
            presentation(e["element_type"], actual_style)
        if before[eid]["normalized_box"] != e["normalized_box"] or original_style != actual_style:
            changes.append({"element_id": eid, "before_box": old_box, "after_box": b,
                            "before_presentation": original_style, "after_presentation": actual_style})
    return {"schema_version": "bie.layout-repair-invariants.v1", "original_identity": digest(raw),
            "effective_identity": digest(effective), "semantic_identity": semantic_identity(raw, owners),
            "policy_identity": digest(grant), "changes": changes, "content_preserved": True,
            "learning_equivalence_verified": False, "accepted": False}


@dataclass(frozen=True)
class RepairCandidate:
    index: int
    document: dict
    invariants: dict


def candidates(payload: dict, policy: dict) -> Iterator[RepairCandidate]:
    """Breadth-ranked finite Cartesian search; explicit budget, no hidden sampling."""
    original, grant = validate_policy(payload, policy)
    ids = sorted(grant["owners"])
    by_id = {e["element_id"]: e for e in original["elements"]}
    options = []
    for eid in ids:
        e = by_id[eid]; b = box(e["normalized_box"]); region = grant["owners"][eid]["region"]
        styles = [deepcopy(e["props"].get(LAYOUT_KEY)), grant["owners"][eid]["presentation"]]
        rectangles = [b, {**b, "width": region["x"] + region["width"] - b["x"]},
                      {**b, "height": region["y"] + region["height"] - b["y"]},
                      {**b, "width": region["x"] + region["width"] - b["x"],
                       "height": region["y"] + region["height"] - b["y"]}, region,
                      {**b, "x": region["x"] + region["width"] - b["width"]},
                      {**b, "y": region["y"] + region["height"] - b["height"]},
                      {**b, "x": region["x"] + region["width"] - b["width"], "y": region["y"] + region["height"] - b["height"]}]
        rows = [(b, styles[0])] + [(r, styles[1]) for r in rectangles]
        unique = []; seen = set()
        for r, style in rows:
            # Floating-point boundary arithmetic must not create extra candidates
            # when the permission is exactly the original rectangle.
            r = {k: b[k] if abs(v - b[k]) <= 1e-12 else v for k, v in r.items()}
            key = digest([r, style])
            if key not in seen:
                seen.add(key); unique.append((r, style))
        options.append(unique)
    initial = (0,) * len(ids)
    heap = [(0, initial)]; seen_states = {initial}; number = 0
    while heap and number < grant["max_candidates"]:
        _, state = heappop(heap)
        p = deepcopy(original)
        for eid, choice in zip(ids, state):
            e = next(v for v in p["elements"] if v["element_id"] == eid)
            rect, style = options[ids.index(eid)][choice]
            e["normalized_box"] = deepcopy(rect)
            if style is not None: e["props"][LAYOUT_KEY] = deepcopy(style)
            else: e["props"].pop(LAYOUT_KEY, None)
        proof = verify_repair(original, p, grant)
        yield RepairCandidate(number, p, proof)
        number += 1
        for i in range(len(ids)):
            if state[i] + 1 >= len(options[i]): continue
            nxt = state[:i] + (state[i] + 1,) + state[i + 1:]
            if nxt not in seen_states:
                seen_states.add(nxt); heappush(heap, (sum(nxt), nxt))
