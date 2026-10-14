"""Explicit Task036 policy and strict native document admission; no new schema."""
from contextlib import contextmanager
from contextvars import ContextVar
from importlib import import_module
from math import isfinite
from pathlib import Path
import uuid

from .contracts import require, canonical, strict_json, digest, sha, identifier
from .animation_contract import profile_config as animation_profile, code_identity_scope as animation_scope
from .scene_ir_m1_review import verified_m1_review
from .scene_ir_monitor_review import identities as monitor_review_identities
from bie.scene_ir.unified_scene_ir_codec import ROOT_FIELDS, ELEMENT_FIELDS, TRACK_FIELDS, decode_scene_ir

PROFILE = "source_grounded_di_knowledge_pr_math_reasoning_pedagogy_director_visual_animation_scene_ir_v1"
SCHEMA = "1.0.0"
POLICY = "current-complete-single-scene-native-ir/1"
MAPPING_POLICY = "source-grammar-native-elements/1"
INPUT_COMPOSITION_POLICY = "fresh-m1-entry-catalog-and-fresh-exit/1"
REVIEW_SHA256 = "33458799eaf58951aa474a08d412b6b56361ec2f08aebdc23f150976a92410a5"
_CODE_SCOPE = ContextVar("task036_scene_ir_code_identity", default=None)


@contextmanager
def code_identity_scope():
    with animation_scope():
        marker = _CODE_SCOPE.set({})
        try:
            yield
        finally:
            _CODE_SCOPE.reset(marker)


def engine_identity():
    cached = _CODE_SCOPE.get()
    if cached is not None and "identity" in cached:
        return dict(cached["identity"])
    root = Path(__file__).resolve().parents[2]
    review_identity = verified_m1_review(root)
    names = ["bie.productization.scene_ir_" + n for n in ("contract", "catalog", "plan", "slice", "m1_review", "monitor_review")]
    names += ["bie.productization.durable_slice", "apps.operator.scene_ir_producer", "apps.operator.scene_ir_worker_child"]
    result = {n: sha(Path(import_module(n).__file__).read_bytes().replace(b"\r\n", b"\n")) for n in names}
    for p in sorted((root / "bie/scene_ir").glob("*.py")):
        result["bie.scene_ir." + p.stem] = sha(p.read_bytes().replace(b"\r\n", b"\n"))
    result.update(review_identity)
    # Fixed identities are usable only after verified_m1_review authenticated
    # both actual review generations and the complete current source chain.
    result.update(monitor_review_identities())
    if cached is not None:
        cached["identity"] = result
    return dict(result)


def refresh_code_identity():
    cached = _CODE_SCOPE.get()
    if cached is not None:
        cached.clear()
    return engine_identity()


def scene_ir_config():
    return dict(schema=SCHEMA, policy=POLICY, mapping_policy=MAPPING_POLICY,
        input_composition_policy=INPUT_COMPOSITION_POLICY,
        scope="COMPLETE_SINGLE_SCENE", capability_profile="producer-motion-v1", fps=24,
        engines=engine_identity(), audio_complete=False, audio_reconciliation_open=True)


def profile_config(provider="technical_source_derived", model="lexical-extractive-v1", *,
                   director=None, visual=None, animation=None, scene_ir=None):
    expected = scene_ir_config()
    require(scene_ir == expected, "scene_ir_configuration_required")
    return dict(animation_profile(provider, model, director=director, visual=visual, animation=animation),
                profile=PROFILE, scene_ir=expected)


def run_identity(tenant, key):
    identifier(tenant); identifier(key)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, canonical(dict(tenant=tenant, key=key, profile=PROFILE)).decode()))


def finite_tree(value, depth=0):
    require(depth < 32, "scene_ir_json_depth")
    if type(value) is dict:
        require(len(value) <= 512 and all(type(k) is str for k in value), "scene_ir_json_shape")
        for v in value.values():
            finite_tree(v, depth + 1)
    elif type(value) is list:
        require(len(value) <= 512, "scene_ir_json_shape")
        for v in value:
            finite_tree(v, depth + 1)
    else:
        require(value is None or type(value) in (bool, str, int, float), "scene_ir_json_shape")
        if type(value) in (int, float):
            require(isfinite(value), "scene_ir_nonfinite")
        if type(value) is str:
            require(len(value) <= 16384, "scene_ir_text_budget")


def strict_document(raw):
    value = strict_json(raw)
    finite_tree(value)
    require(type(value) is dict and set(value) == ROOT_FIELDS, "scene_ir_root_fields")
    require(value["review_required"] is True and value["accepted"] is False, "scene_ir_review_boundary")
    for key in ("scene_id", "title", "fingerprint"):
        require(type(value[key]) is str and value[key] and value[key].strip() == value[key], "scene_ir_string")
    require(value["schema_version"] == SCHEMA, "scene_ir_schema")
    for key in ("duration_ms", "upstream_revision"):
        require(type(value[key]) is int and 0 < value[key] <= 3600000, "scene_ir_integer")
    for key in ("source_refs", "reasoning_refs", "compiler_capabilities"):
        _ids(value[key], key, nonempty=True)
    for key in ("layout", "metadata"):
        require(type(value[key]) is dict, "scene_ir_object")
    for key in ("events", "narration_cues", "interaction_cues", "interaction_bindings", "state_bindings",
                "simulation_controls", "accessibility_metadata", "capability_requests", "planned_fallbacks"):
        require(type(value[key]) is list and all(type(v) is dict for v in value[key]), "scene_ir_object_list")
    for cue in value["narration_cues"]:
        require(set(cue) == {"cue_id", "start_ms", "end_ms", "text_ref", "narration_revision", "target_ids"},
                "scene_ir_narration_fields")
        require(all(type(cue[k]) is int for k in ("start_ms", "end_ms", "narration_revision")) and
                0 <= cue["start_ms"] < cue["end_ms"] <= value["duration_ms"] and
                cue["narration_revision"] == value["upstream_revision"], "scene_ir_narration_time")
        for key in ("cue_id", "text_ref"):
            require(type(cue[key]) is str and cue[key] and cue[key].strip() == cue[key], "scene_ir_narration_identity")
        _ids(cue["target_ids"], "cue_targets")
    require(len({c["cue_id"] for c in value["narration_cues"]}) == len(value["narration_cues"]),
            "scene_ir_duplicate_cue")
    for name, fields, identity in (("elements", ELEMENT_FIELDS, "element_id"),
                                   ("tracks", TRACK_FIELDS, "track_id")):
        rows = value[name]
        require(type(rows) is list and bool(rows) and len(rows) <= 256, "scene_ir_inventory")
        require(all(type(r) is dict and set(r) == fields for r in rows), "scene_ir_member_fields")
        require(all(type(r[identity]) is str and r[identity] and r[identity].strip() == r[identity]
                    for r in rows) and len({r[identity] for r in rows}) == len(rows), "scene_ir_duplicate_identity")
    for key in ("duration_ms", "upstream_revision"):
        require(type(value[key]) is int and 0 < value[key] <= 3600000, "scene_ir_integer")
    for track in value["tracks"]:
        require(all(type(track[k]) is int for k in ("start_ms", "end_ms")) and
                0 <= track["start_ms"] < track["end_ms"] <= value["duration_ms"], "scene_ir_track_time")
        require(type(track["parameters"]) is dict, "scene_ir_parameters")
        for key in ("element_id", "action"):
            require(type(track[key]) is str and track[key] and track[key].strip() == track[key], "scene_ir_string")
        _ids(track["source_refs"], "source_refs", True); _ids(track["reasoning_refs"], "reasoning_refs", True)
    for element in value["elements"]:
        require(type(element["element_type"]) is str and element["element_type"] in ("chart", "diagram", "shape", "text"),
                "scene_ir_element_scope")
        require(type(element["props"]) is dict and type(element["accessibility"]) is dict, "scene_ir_element_object")
        _ids(element["source_refs"], "source_refs", True); _ids(element["reasoning_refs"], "reasoning_refs", True)
        box = element["normalized_box"]
        require(type(box) is dict and set(box) == {"x", "y", "width", "height"} and
                all(type(v) in (int, float) and isfinite(v) for v in box.values()), "scene_ir_box")
        # Strict property admission precedes the codec, whose generic Mapping
        # freeze is not a domain validator and must not bless ignored fields.
        props = element["props"]
        if element["element_type"] == "chart":
            from bie.compiler.chart_geometry import chart_geometry
            chart_geometry(props)
        elif element["element_type"] == "shape":
            from bie.compiler.shape_compiler import shape_geometry
            shape_geometry(props)
        elif element["element_type"] == "diagram":
            from bie.compiler.diagram_compiler import diagram_geometry
            diagram_geometry(props, element["source_refs"], element["reasoning_refs"])
        else:
            require({"text", "role"} <= set(props) <= {"text", "role", "language"} and
                all(type(v) is str and v and v.strip() == v for v in props.values()), "scene_ir_text_fields")
    targets = {e["element_id"] for e in value["elements"]}
    require(all(set(c["target_ids"]) <= targets for c in value["narration_cues"]), "scene_ir_foreign_cue_target")
    for request in value["capability_requests"]:
        require(set(request) == {"element_id", "element_type", "capability_id", "requested_action", "required"} and
                request["required"] is True and request["element_id"] in targets,
                "scene_ir_capability_fields")
    doc = decode_scene_ir(value)
    require(canonical(doc.to_dict()) == canonical(value), "scene_ir_codec_field_loss")
    return doc


def _ids(value, name, nonempty=False):
    require(type(value) is list and (bool(value) or not nonempty) and
            all(type(v) is str and v and v.strip() == v for v in value) and
            len(value) == len(set(value)), "scene_ir_" + name)
