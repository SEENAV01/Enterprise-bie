"""Explicit Task035 configuration; native engines and existing storage only."""
from contextlib import contextmanager
from contextvars import ContextVar
from importlib import import_module
from math import isfinite
from pathlib import Path
import uuid

from .contracts import require, canonical, digest, sha, identifier
from .visual_contract import profile_config as visual_profile, code_identity_scope as visual_scope

PROFILE = "source_grounded_di_knowledge_pr_math_reasoning_pedagogy_director_visual_animation_v1"
SCHEMA = "1.0.0"
POLICY = "current-source-semantic-animation-v1"
POLICY_REVISION = 1
DOMAIN_REGISTRY_VERSION = "task035-bounded-domains/1"
_CODE_SCOPE = ContextVar("task035_animation_code_identity", default=None)


@contextmanager
def code_identity_scope():
    with visual_scope():
        token = _CODE_SCOPE.set({})
        try:
            yield
        finally:
            _CODE_SCOPE.reset(token)


def engine_identity():
    scope = _CODE_SCOPE.get()
    if scope is not None and "identity" in scope:
        return dict(scope["identity"])
    names = {"bie.productization.animation_" + n for n in ("contract", "intents", "plan", "slice")}
    names.update(("apps.operator.animation_producer", "apps.operator.animation_worker_child",
                  "bie.director.director_consumers", "bie.director.narration_animation_sync",
                  "bie.director.sync_contract"))
    folder = Path(import_module("bie.animation_intelligence").__file__).parent
    names.update("bie.animation_intelligence." + p.stem for p in folder.glob("*.py"))
    result = {n: sha(Path(import_module(n).__file__).read_bytes().replace(b"\r\n", b"\n"))
              for n in sorted(names)}
    if scope is not None:
        scope["identity"] = result
    return dict(result)


def refresh_code_identity():
    scope = _CODE_SCOPE.get()
    if scope is not None:
        scope.clear()
    return engine_identity()


def animation_config(*, reduced_motion_required, budget):
    require(type(reduced_motion_required) is bool, "animation_reduced_motion_policy_required")
    require(type(budget) is dict and set(budget) == {"profile_id", "max_score", "split_score",
        "max_particles", "max_3d_objects", "max_asset_bytes"}, "animation_budget_required")
    identifier(budget["profile_id"])
    for k in ("max_score", "split_score"):
        require(type(budget[k]) in (float, int) and isfinite(budget[k]) and 0 < budget[k] <= 35,
                "animation_budget_invalid")
    require(budget["max_score"] <= budget["split_score"], "animation_budget_invalid")
    for k in ("max_particles", "max_3d_objects", "max_asset_bytes"):
        require(type(budget[k]) is int and 0 <= budget[k] <= 10_000_000, "animation_budget_invalid")
    return dict(schema=SCHEMA, policy=POLICY, policy_revision=POLICY_REVISION,
        domain_registry_version=DOMAIN_REGISTRY_VERSION, reduced_motion_required=reduced_motion_required,
        budget=dict(budget), engines=engine_identity(), allow_scene_extension=False,
        audio_complete=False, audio_reconciliation_open=True)


def profile_config(provider="technical_source_derived", model="lexical-extractive-v1", *,
                   director=None, visual=None, animation=None):
    require(type(animation) is dict and "budget" in animation and "reduced_motion_required" in animation,
            "animation_configuration_required")
    expected = animation_config(reduced_motion_required=animation["reduced_motion_required"],
                                budget=animation["budget"])
    require(animation == expected, "animation_policy_conflict")
    base = visual_profile(provider, model, director=director, visual=visual)
    require(expected["budget"]["profile_id"] == visual["target"]["profile_id"], "animation_target_mismatch")
    return dict(base, profile=PROFILE, animation=expected)


def run_identity(tenant, key):
    identifier(tenant); identifier(key)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, canonical(dict(tenant=tenant, key=key, profile=PROFILE)).decode()))
