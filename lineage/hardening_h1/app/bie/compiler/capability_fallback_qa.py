"""QA-002: fail-closed fallback and emitted-capability checks.

The existing DSL resolver is exercised, but its booleans and semantic assertions
are not treated as evidence. Output binding, action support, and known lossy
emitter behavior are checked separately. This does not prove visual quality.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable
from .qa_common import CompilerQAError, QAFinding, digest, ordered_findings, token
from .artifact_hashing import require_sha256
from bie.scene_ir.compiler_capability_resolution import resolve_compiler_capabilities

@dataclass(frozen=True)
class FallbackApplication:
    fallback_id: str
    element_id: str
    capability_id: str
    action: str
    output_sha256: str
    source_refs: tuple[str, ...]
    reasoning_refs: tuple[str, ...]
    accessibility_sha256: str
    def __post_init__(self):
        for name in ("fallback_id", "element_id", "capability_id", "action"):
            token(getattr(self, name), name)
        for name in ("output_sha256", "accessibility_sha256"):
            require_sha256(getattr(self, name), name)
        for name in ("source_refs", "reasoning_refs"):
            vals = tuple(getattr(self, name))
            if not vals or len(vals) != len(set(vals)):
                raise CompilerQAError("fallback application requires unique provenance refs")
            for val in vals:
                token(val, name)
            object.__setattr__(self, name, vals)

@dataclass(frozen=True)
class FallbackApproval:
    fallback_id: str
    scene_fingerprint: str
    output_sha256: str
    reviewer_id: str
    evidence_ref: str
    def __post_init__(self):
        for name in ("fallback_id", "reviewer_id", "evidence_ref"):
            token(getattr(self, name), name)
        require_sha256(self.scene_fingerprint)
        require_sha256(self.output_sha256)

@dataclass(frozen=True)
class CapabilityFallbackQAReceipt:
    scene_id: str
    scene_fingerprint: str
    profile: str
    supported_requests: tuple[str, ...]
    verified_fallback_ids: tuple[str, ...]
    findings: tuple[QAFinding, ...]
    source_contract_passed: bool
    visual_semantic_validation: str = "NOT_RUN"
    acceptance_scope: str = "SOURCE_CONTRACT_ONLY"
    accepted: bool = False
    @property
    def passed(self) -> bool:
        return self.source_contract_passed


def inspect_emitted_semantics(document, results: Iterable) -> tuple[QAFinding, ...]:
    """Known compiler-specific loss checks. No generic 'warning means safe' rule."""
    results = tuple(results)
    findings: list[QAFinding] = []
    indexed = {}
    elements = document.to_dict()["elements"]
    expected = {e["element_id"]: e for e in elements}
    def add(code, message, eid, severity="ERROR"):
        findings.append(QAFinding(code, severity, message, f"$.elements[{eid}]"))
    for r in results:
        if r.element_id in indexed:
            add("DUPLICATE_COMPILED_ELEMENT", "Duplicate element output.", r.element_id)
        indexed[r.element_id] = r
        if r.element_id not in expected:
            add("UNEXPECTED_COMPILED_ELEMENT", "Output has no input element.", r.element_id)
            continue
        if r.source_sha256 != sha256(r.source_text.encode("utf-8")).hexdigest():
            add("COMPILED_SOURCE_HASH_MISMATCH", "Compiler output hash does not match its bytes.", r.element_id)
        if r.element_type != expected[r.element_id]["element_type"]:
            add("COMPILED_ELEMENT_TYPE_MISMATCH", "Output type differs from source element.", r.element_id)
    for e in elements:
        eid, kind, props = e["element_id"], e["element_type"], e["props"]
        result = indexed.get(eid)
        if result is None:
            add("MISSING_COMPILED_ELEMENT", "Input element disappeared from compiler output.", eid)
            continue
        # H1: metadata alone cannot certify fixed emitters. Recompute the governed
        # emitter deterministically and compare bytes plus dependencies/assets.
        from .text_compiler import compile_text_element
        from .annotation_callout_compiler import compile_annotation_callout_element
        from .chart_compiler import compile_chart_element
        from .vector_compiler import compile_vector_element
        from .model2d_compiler import compile_model2d_element
        from .element_compiler_common import ElementCompilerError
        hardened = {"text": compile_text_element, "annotation": compile_annotation_callout_element,
                    "callout": compile_annotation_callout_element, "chart": compile_chart_element,
                    "vector": compile_vector_element, "model2d": compile_model2d_element}
        if kind in hardened:
            try:
                canonical = hardened[kind](e)
                if canonical != result:
                    add("HARDENED_EMITTER_OUTPUT_MISMATCH", "Output does not match the governed emitter and input contracts.", eid)
            except ElementCompilerError as exc:
                import re
                code = str(exc).split(":", 1)[0]
                add(code if re.fullmatch(r"[A-Z][A-Z0-9_]+", code) else "ELEMENT_COMPILE_REJECTED", str(exc), eid)
        warnings_seen = set()
        if kind == "chart":
            if props.get("chart_kind") != "bar" and "values.map" in result.source_text:
                add("CHART_KIND_DOWNGRADE", "Non-bar chart is emitted as bars; this is not an equivalent fallback.", eid)
                warnings_seen.add("generic_chart_renderer_uses_bar_fallback_for_non_bar_kind")
            if any(isinstance(v, (float, int)) and v < 0 for v in props.get("values", ())):
                if "Math.abs(value)" in result.source_text:
                    add("CHART_SIGN_LOSS", "Magnitude-only bar height discards negative-value semantics.", eid)
        if kind == "equation":
            fmt = props.get("format", "latex")
            marker = "equation_renderer_dependency_may_be_required_for_typeset_output"
            if fmt != "plain" and "{expression}" in result.source_text:
                add("EQUATION_TYPESETTING_NOT_IMPLEMENTED", "Raw equation text is not a verified LaTeX/MathML renderer.", eid)
                warnings_seen.add(marker)
            elif fmt == "plain":
                # Plain text is explicitly requested; no typesetting obligation is inferred.
                warnings_seen.add(marker)
        if kind in {"text", "annotation", "callout"}:
            text = props.get("content") if kind == "callout" else props.get("text", "")
            escaped = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if ("{" in str(text) or "}" in str(text)) and ("\n      " + escaped + "\n") in result.source_text:
                add("TEXT_LITERAL_JSX_INJECTION", "Literal braces are inserted into executable JSX rather than a string binding.", eid)
        if kind == "vector" and len(props.get("components", ())) == 3:
            if float(props["components"][2]) != 0 and "viewBox=\"0 0 200 200\"" in result.source_text:
                add("VECTOR_Z_COMPONENT_DROPPED", "3D vector has been reduced to a 2D arrow without an explicit projection.", eid)
        if kind == "simulation" and "JSON.stringify(initialState" in result.source_text:
            add("SIMULATION_STATE_ONLY", "Initial-state JSON is not an executed simulation.", eid)
        if kind == "map":
            routes = [x for x in props.get("layers", ()) if x.get("kind") == "route"]
            if not routes:
                add("MAP_GEOMETRY_NOT_EMITTED", "No usable route geometry is emitted.", eid)
                warnings_seen.add("map_has_no_route_geometry; external/static-map provider may be required")
            if any(x.get("kind") != "route" for x in props.get("layers", ())):
                add("MAP_LAYER_DROPPED", "A non-route map layer is ignored by this emitter.", eid)
            if routes and (props.get("crs") not in {"normalized", "BIE:NORMALIZED"}):
                add("MAP_PROJECTION_UNVERIFIED", "The emitter expects normalized coordinates, not a geographic CRS.", eid)
        if kind == "model2d":
            vertices = props.get("vertices", ())
            for edge in props.get("edges", ()):
                if len(edge) != 2 or any(type(i) is not int or not 0 <= i < len(vertices) for i in edge):
                    add("MODEL2D_EDGE_INDEX_INVALID", "Generated edge reads a nonexistent vertex.", eid)
                    break
        if kind == "particle_system" and props.get("physical_claim"):
            add("PARTICLE_PHYSICS_NOT_EXECUTED", "A receipt reference does not make a static particle arrangement a physical simulation.", eid)
        for warning in result.warnings:
            if warning not in warnings_seen:
                add("UNREVIEWED_COMPILER_WARNING", str(warning), eid)
    return ordered_findings(findings)


def evaluate_capability_fallbacks(document, registry, element_results: Iterable, *,
                                  profile: str = "web", applications: Iterable[FallbackApplication] = (),
                                  approvals: Iterable[FallbackApproval] = ()) -> CapabilityFallbackQAReceipt:
    token(profile, "profile")
    raw_doc = document.to_dict()
    require_sha256(document.fingerprint)
    results = tuple(element_results)
    findings = list(inspect_emitted_semantics(document, results))
    def add(code, message, path="$", severity="ERROR"):
        findings.append(QAFinding(code, severity, message, path))
    elements = {e["element_id"]: e for e in raw_doc["elements"]}
    emitted = {r.element_id: r for r in results}
    fbs: dict[tuple[str, str], dict] = {}
    fb_ids: set[str] = set()
    for fb in raw_doc["planned_fallbacks"]:
        if not all(isinstance(fb.get(name), str) and fb[name].strip() for name in
                   ("fallback_id", "element_id", "missing_capability_id", "fallback_capability_id", "fallback_action")):
            add("MALFORMED_FALLBACK_IDENTIFIERS", "Fallback identifiers must be nonblank strings.")
            continue
        key = (fb.get("element_id"), fb.get("missing_capability_id"))
        if key in fbs or fb.get("fallback_id") in fb_ids:
            add("AMBIGUOUS_FALLBACK", "Duplicate fallback key or ID.")
        fbs[key] = fb
        fb_ids.add(fb.get("fallback_id"))
        for name in ("preserves_source_refs", "preserves_reasoning_refs", "preserves_accessibility", "required_review"):
            if type(fb.get(name, True if name == "required_review" else None)) is not bool:
                add("FALLBACK_NONBOOLEAN_CONTRACT", f"{name} must be a JSON boolean.")
        if fb.get("element_id") not in elements:
            add("FALLBACK_UNKNOWN_ELEMENT", "Fallback references an unknown element.")
    applications = tuple(applications)
    approvals = tuple(approvals)
    app_by = {}
    for app in applications:
        if app.fallback_id in app_by:
            add("DUPLICATE_FALLBACK_APPLICATION", "Multiple application receipts have the same ID.")
        app_by[app.fallback_id] = app
        if app.fallback_id not in fb_ids:
            add("ORPHAN_FALLBACK_APPLICATION", "Application has no planned fallback.")
    supported, verified, used_keys = [], [], set()
    requests_seen = set()
    registry_snapshot = {row[0]: row for row in registry.snapshot()}
    for req in raw_doc["capability_requests"]:
        eid, cid, action = req.get("element_id"), req.get("capability_id"), req.get("requested_action")
        if not all(isinstance(x, str) and x.strip() for x in (eid, cid, action)):
            add("MALFORMED_CAPABILITY_REQUEST", "Capability request identifiers must be nonblank strings.")
            continue
        key = (cid, eid, action)
        if key in requests_seen:
            add("DUPLICATE_CAPABILITY_REQUEST", "Duplicate capability request.")
        requests_seen.add(key)
        required = req.get("required", True)
        if type(required) is not bool:
            add("REQUEST_NONBOOLEAN_REQUIRED", "required must be a JSON boolean.")
        if eid not in elements:
            add("CAPABILITY_UNKNOWN_ELEMENT", "Capability request references an unknown element.")
            continue
        e = elements[eid]
        etype = e["element_type"]
        if req.get("element_type", etype) != etype:
            add("CAPABILITY_ELEMENT_TYPE_MISMATCH", "Request type differs from actual element type.")
        if not all(isinstance(x, str) and x.strip() for x in (cid, action)):
            add("MALFORMED_CAPABILITY_REQUEST", "Capability ID/action missing.")
            continue
        if registry.supports(cid, etype, action, profile):
            if registry_snapshot[cid][-1] is not True:
                add("NONDETERMINISTIC_CAPABILITY", "Native capability is not deterministic.")
            supported.append(":".join(key))
            continue
        fbkey = (eid, cid)
        fb = fbs.get(fbkey)
        if fb is None:
            add("UNSUPPORTED_REQUIRED_CAPABILITY" if required is not False else "UNSUPPORTED_OPTIONAL_CAPABILITY",
                f"No supported native capability/fallback for {cid}/{action}.",
                severity="ERROR" if required is not False else "WARNING")
            continue
        used_keys.add(fbkey)
        fallback_id = fb.get("fallback_id")
        target, fallback_action = fb.get("fallback_capability_id"), fb.get("fallback_action")
        valid = True
        if not registry.supports(target, etype, fallback_action, profile):
            add("FALLBACK_ACTION_UNSUPPORTED", "Fallback action/profile/type is not supported, even if capability ID exists.")
            valid = False
        elif registry_snapshot[target][-1] is not True:
            add("NONDETERMINISTIC_FALLBACK", "Fallback adapter is not deterministic.")
            valid = False
        if any(fb.get(n) is not True for n in ("preserves_source_refs", "preserves_reasoning_refs", "preserves_accessibility")):
            add("FALLBACK_LOSES_REQUIRED_CONTRACT", "Fallback must preserve source, reasoning, and accessibility.")
            valid = False
        semantic = fb.get("semantic_equivalence")
        if semantic not in {"equivalent", "degraded_but_safe", "illustrative_only"}:
            add("FALLBACK_SEMANTICS_INVALID", "Unknown semantic-equivalence claim.")
            valid = False
        if semantic == "illustrative_only" and required is not False:
            add("ILLUSTRATIVE_FALLBACK_FOR_REQUIRED_CAPABILITY", "Illustration cannot satisfy a required semantic capability.")
            valid = False
        app = app_by.get(fallback_id)
        result = emitted.get(eid)
        if app is None:
            add("FALLBACK_NOT_APPLIED", "A planned fallback is not evidence of generated fallback output.")
            valid = False
        elif (result is None or app.element_id != eid or app.capability_id != target
                or app.action != fallback_action or app.output_sha256 != result.source_sha256
                or set(app.source_refs) != set(e["source_refs"])
                or set(app.reasoning_refs) != set(e["reasoning_refs"])
                or app.accessibility_sha256 != digest(e["accessibility"])):
            add("FALLBACK_APPLICATION_MISMATCH", "Applied fallback does not bind to the emitted bytes and input contracts.")
            valid = False
        needs_review = fb.get("required_review", True) is not False or semantic != "equivalent"
        if needs_review and (app is None or not any(
                a.fallback_id == fallback_id and a.scene_fingerprint == document.fingerprint
                and a.output_sha256 == app.output_sha256 for a in approvals)):
            add("FALLBACK_REVIEW_REQUIRED", "A source/output-bound review reference is required; approval is never fabricated.")
            valid = False
        if valid:
            verified.append(fallback_id)
    for key in fbs.keys() - used_keys:
        add("UNUSED_PLANNED_FALLBACK", "Unused fallback declaration retained for review.", severity="WARNING")
    # Keep the old resolver as a compatibility gate without inheriting its weaker checks.
    try:
        legacy = resolve_compiler_capabilities(document, registry, profile)
        for blocker in legacy.blockers:
            add("DSL_CAPABILITY_BLOCKER", blocker)
    except (ValueError, TypeError, KeyError) as exc:
        add("DSL_CAPABILITY_RESOLUTION_FAILED", str(exc) or type(exc).__name__)
    ordered = ordered_findings(findings)
    return CapabilityFallbackQAReceipt(document.scene_id, document.fingerprint, profile,
             tuple(sorted(set(supported))), tuple(sorted(set(verified))), ordered,
             not any(f.severity == "ERROR" for f in ordered))
