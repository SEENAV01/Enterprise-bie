"""Task033 configuration and admission, not a second Director implementation."""
from dataclasses import asdict, dataclass
import re
import uuid

from bie.director.director_model import DirectingPolicy, model_identity
from bie.director.semantic_execution import SemanticExecutionPolicy
from bie.director.annotated_directing import AnnotationRuntime
from bie.director.hierarchical_annotations import HierarchicalAnnotationPolicy
from bie.director.hierarchical_annotation_review import HierarchicalAnnotationReviewPolicy
from .pedagogy_plan import profile_config as pedagogy_config
from .contracts import require, digest, canonical, identifier, strict_json

PROFILE = "source_grounded_di_knowledge_pr_math_reasoning_pedagogy_director_v1"
SCHEMA = "bie.dir.annotated_plan/1.0.0"
POLICY = "canonical-director-production-admission-v1"
ROLES = ("generator", "critic", "annotator", "reviewer")


@dataclass(frozen=True)
class DirectorProviderStack:
    generator: object
    generator_identity: object
    critic: object
    critic_identity: object
    annotations: AnnotationRuntime
    evidence_kind: str

    def descriptor(self):
        for provider, identity in ((self.generator, self.generator_identity),
                                   (self.critic, self.critic_identity)):
            require(callable(getattr(provider, "invoke", None)), "director_provider_unavailable")
            model_identity(identity)
        require(isinstance(self.annotations, AnnotationRuntime) and
                isinstance(self.annotations.policy, HierarchicalAnnotationPolicy) and
                isinstance(self.annotations.review_policy, HierarchicalAnnotationReviewPolicy),
                "director_hierarchical_runtime_required")
        self.annotations.validate()
        require(self.evidence_kind in ("SYNTHETIC_TEST", "CONFIGURED_PROVIDER_UNACCEPTED"),
                "director_provider_evidence_kind")
        return dict(generator=asdict(self.generator_identity), critic=asdict(self.critic_identity),
                    annotator=asdict(self.annotations.annotator_identity),
                    reviewer=asdict(self.annotations.reviewer_identity))


def director_config(*, title, language, providers, evidence_kind, revision=1,
                    previous_key=None, scene_corrections=()):
    require(type(title) is str and title.strip() == title and 0 < len(title) <= 256,
            "director_title_required")
    require(type(language) is str and re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", language),
            "director_language_required")
    require(type(providers) is dict and set(providers) == set(ROLES), "director_provider_identity")
    for identity in providers.values():
        require(type(identity) is dict and set(identity) == {"provider", "model", "adapter_version"},
                "director_provider_identity")
        require(all(type(v) is str and 0 < len(v) <= 128 and re.fullmatch(r"[A-Za-z0-9_.:/-]+", v)
                    for v in identity.values()), "director_provider_identity")
    require(evidence_kind in ("SYNTHETIC_TEST", "CONFIGURED_PROVIDER_UNACCEPTED"),
            "director_provider_evidence_kind")
    require(type(revision) is int and 1 <= revision <= 3, "director_revision_invalid")
    require((revision == 1 and previous_key is None and not scene_corrections) or
            (revision > 1 and type(previous_key) is str and previous_key.strip()),
            "director_revision_invalid")
    return strict_json(canonical(dict(title=title, language=language, providers=providers, evidence_kind=evidence_kind,
                revision=revision, previous_key=previous_key,
                scene_corrections=list(scene_corrections), policy=POLICY,
                directing_policy=asdict(DirectingPolicy()),
                semantic_policy=asdict(SemanticExecutionPolicy()),
                annotation_policy=asdict(HierarchicalAnnotationPolicy()),
                annotation_review_policy=asdict(HierarchicalAnnotationReviewPolicy()))))


def profile_config(provider="technical_source_derived", model="lexical-extractive-v1", *, director=None):
    require(type(director) is dict, "director_configuration_required")
    expected = director_config(**{k: director[k] for k in
        ("title", "language", "providers", "evidence_kind", "revision", "previous_key", "scene_corrections")})
    require(director == expected, "director_policy_conflict")
    return dict(pedagogy_config(provider, model), profile=PROFILE, director=expected)


def run_identity(tenant, key):
    identifier(tenant); identifier(key)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, canonical(dict(tenant=tenant, key=key, profile=PROFILE)).decode()))


def native_key(run_id, reasoning_ref, pedagogy_ref, config):
    return "director:" + digest(dict(run=run_id, reasoning=asdict(reasoning_ref),
                                   pedagogy=asdict(pedagogy_ref), config=config))
