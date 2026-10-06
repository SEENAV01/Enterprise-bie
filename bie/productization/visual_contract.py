"""Explicit current Visual configuration, not a historical DIR/REP receipt."""
from dataclasses import asdict
from contextlib import contextmanager
from contextvars import ContextVar
from importlib import import_module
from pathlib import Path
import uuid

from .contracts import require, canonical, digest, sha, identifier
from .director_contract import profile_config as director_config
from bie.visual_intelligence.representation_core import TargetProfile

PROFILE = "source_grounded_di_knowledge_pr_math_reasoning_pedagogy_director_visual_v1"
SCHEMA = "1.0.0"
POLICY = "current-source-declarations-visual-v1"
MODULES = ("bie.productization.visual_intents", "bie.productization.visual_plan",
    "bie.productization.visual_contract", "bie.productization.visual_slice",
    "apps.operator.visual_producer", "apps.operator.visual_worker_child",
    "bie.animation_intelligence.vis_ani_adoption",
    "bie.visual_intelligence.visual_orchestrator", "bie.visual_intelligence.visual_plan_contract",
    "bie.visual_intelligence.director_handoff_adoption", "bie.director.director_consumers",
    "bie.director.narration_visual_sync", "bie.director.sync_contract")
_CODE_SCOPE = ContextVar("task034_visual_code_identity", default=None)


@contextmanager
def code_identity_scope():
    """Memoize only source-code hashing within one control-plane operation.

    Config, CAS, source, state, currentness and QA reads are never memoized.
    The full code identity is freshly recomputed before terminal ACK validation.
    Direct service calls outside this scope retain uncached code validation.
    """
    token = _CODE_SCOPE.set({})
    try:
        yield
    finally:
        _CODE_SCOPE.reset(token)


def refresh_code_identity():
    scope = _CODE_SCOPE.get()
    if scope is not None:
        scope.clear()
    return engine_identity()


def engine_identity():
    # Native implementation identity is not a claim of historical ZIP execution.
    scope = _CODE_SCOPE.get()
    if scope is not None and "identity" in scope:
        return dict(scope["identity"])
    names = set(MODULES)
    folder = Path(import_module("bie.visual_intelligence").__file__).parent
    names.update("bie.visual_intelligence." + p.stem for p in folder.glob("*.py"))
    identity = {name: sha(Path(import_module(name).__file__).read_bytes().replace(b"\r\n", b"\n"))
                for name in sorted(names)}
    if scope is not None:
        scope["identity"] = identity
    return dict(identity)


def visual_config(target):
    require(type(target) is dict and set(target) == {
        "profile_id", "capabilities", "max_complexity", "supports_interaction", "supports_3d",
        "supports_simulation", "viewport_width", "viewport_height", "font_px", "foreground", "background"},
        "visual_target_profile_required")
    require(all(type(target[k]) is bool for k in
                ("supports_interaction", "supports_3d", "supports_simulation")), "visual_target_invalid")
    require(type(target["capabilities"]) is list and len(set(target["capabilities"])) == len(target["capabilities"]),
            "visual_target_invalid")
    for key, low, high in (("viewport_width", 320, 4096), ("viewport_height", 240, 2160), ("font_px", 16, 96)):
        require(type(target[key]) is int and low <= target[key] <= high, "visual_target_invalid")
    import re
    require(all(type(target[k]) is str and re.fullmatch(r"#[0-9A-Fa-f]{6}", target[k])
                for k in ("foreground", "background")), "visual_target_invalid")
    native = TargetProfile(**{k: tuple(v) if k == "capabilities" else v for k, v in target.items()
                              if k in TargetProfile.__dataclass_fields__})
    require(canonical(asdict(native)) == canonical({k: target[k] for k in TargetProfile.__dataclass_fields__}),
            "visual_target_invalid")
    return dict(target=target, schema=SCHEMA, policy=POLICY, engines=engine_identity(),
                extraction="complete-declared-source-and-current-narration-v1",
                historical_dir_runtime_claimed=False, historical_rep_archive_runtime_claimed=False)


def profile_config(provider="technical_source_derived", model="lexical-extractive-v1", *, director=None, visual=None):
    require(type(visual) is dict and "target" in visual, "visual_configuration_required")
    require(visual == visual_config(visual["target"]), "visual_policy_conflict")
    return dict(director_config(provider, model, director=director), profile=PROFILE, visual=visual)


def run_identity(tenant, key):
    identifier(tenant); identifier(key)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, canonical(dict(tenant=tenant, key=key, profile=PROFILE)).decode()))
