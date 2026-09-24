"""H9-001: provider-neutral pronunciation/acoustic evaluator capability contracts.

Capability negotiation is descriptive only. A profile cannot self-certify accuracy,
calibration, authority, listening acceptance, or product acceptance.
"""
from __future__ import annotations
from dataclasses import dataclass
from .common import AudioError, digest, fingerprint, integer, locale, refs, text

_REQUIRED_OUTPUTS = ("word_boundaries", "phone_sequence", "deviation_score", "uncertainty")
_ALLOWED_INVENTORIES = {"IPA", "ARPABET", "X-SAMPA", "PROVIDER_NATIVE"}


@dataclass(frozen=True)
class AccentBinding:
    language: str
    accent: str
    evidence_refs: tuple[str, ...]
    def __post_init__(self):
        locale(self.language); text(self.accent, "accent", 128); refs(self.evidence_refs, "accent evidence")


@dataclass(frozen=True)
class EvaluatorProfile:
    evaluator_id: str
    provider_id: str
    model_id: str
    model_revision: str
    runtime_fingerprint: str
    supported_languages: tuple[str, ...]
    accent_bindings: tuple[AccentBinding, ...]
    phone_inventory: str
    outputs: tuple[str, ...]
    supports_ipa_targets: bool
    supports_oov_targets: bool
    supports_code_switching: bool
    max_targets: int
    max_audio_seconds: int
    evidence_refs: tuple[str, ...]
    quality_scope: str = "CAPABILITY_DECLARATION_ONLY"
    schema_version: str = "bie.audio.evaluator-profile/1"

    def __post_init__(self):
        if self.schema_version != "bie.audio.evaluator-profile/1" or self.quality_scope != "CAPABILITY_DECLARATION_ONLY":
            raise AudioError("EVALUATOR_PROFILE_VERSION")
        for key in ("evaluator_id", "provider_id", "model_id", "model_revision"):
            text(getattr(self, key), key, 512)
        digest(self.runtime_fingerprint)
        if type(self.supported_languages) is not tuple or not self.supported_languages or len(self.supported_languages) > 128:
            raise AudioError("EVALUATOR_LANGUAGES")
        for lang in self.supported_languages: locale(lang)
        if len(set(self.supported_languages)) != len(self.supported_languages): raise AudioError("EVALUATOR_LANGUAGE_DUPLICATE")
        if type(self.accent_bindings) is not tuple or len(self.accent_bindings) > 512 or any(type(x) is not AccentBinding for x in self.accent_bindings):
            raise AudioError("EVALUATOR_ACCENTS")
        if len({(x.language, x.accent) for x in self.accent_bindings}) != len(self.accent_bindings):
            raise AudioError("EVALUATOR_ACCENT_DUPLICATE")
        if any(x.language not in self.supported_languages for x in self.accent_bindings): raise AudioError("EVALUATOR_ACCENT_LANGUAGE")
        if self.phone_inventory not in _ALLOWED_INVENTORIES: raise AudioError("EVALUATOR_PHONE_INVENTORY")
        if type(self.outputs) is not tuple or len(set(self.outputs)) != len(self.outputs) or not set(_REQUIRED_OUTPUTS) <= set(self.outputs):
            raise AudioError("EVALUATOR_OUTPUTS")
        for out in self.outputs: text(out, "evaluator output", 128)
        for value in (self.supports_ipa_targets, self.supports_oov_targets, self.supports_code_switching):
            if type(value) is not bool: raise AudioError("EVALUATOR_BOOLEAN")
        integer(self.max_targets, "max targets", 1, 100000)
        integer(self.max_audio_seconds, "max audio seconds", 1, 7200)
        refs(self.evidence_refs, "evaluator profile evidence")

    def fingerprint(self): return fingerprint(self)


@dataclass(frozen=True)
class EvaluationRequirements:
    languages: tuple[str, ...]
    accents: tuple[tuple[str, str], ...]
    target_count: int
    audio_seconds: int
    requires_ipa: bool
    contains_oov: bool
    code_switched: bool
    def __post_init__(self):
        if type(self.languages) is not tuple or not self.languages: raise AudioError("EVALUATION_REQUIREMENT_LANGUAGES")
        for lang in self.languages: locale(lang)
        if len(set(self.languages)) != len(self.languages): raise AudioError("EVALUATION_REQUIREMENT_DUPLICATE_LANGUAGE")
        if type(self.accents) is not tuple or len(self.accents) > 512: raise AudioError("EVALUATION_REQUIREMENT_ACCENTS")
        for row in self.accents:
            if type(row) is not tuple or len(row) != 2: raise AudioError("EVALUATION_REQUIREMENT_ACCENT")
            locale(row[0]); text(row[1], "accent", 128)
        integer(self.target_count, "target count", 1, 100000)
        integer(self.audio_seconds, "audio seconds", 1, 7200)
        for value in (self.requires_ipa, self.contains_oov, self.code_switched):
            if type(value) is not bool: raise AudioError("EVALUATION_REQUIREMENT_BOOLEAN")

    def fingerprint(self): return fingerprint(self)


@dataclass(frozen=True)
class CapabilityDecision:
    profile_fingerprint: str
    requirements_fingerprint: str
    supported: bool
    blockers: tuple[str, ...]
    scope: str = "CAPABILITY_NEGOTIATION_NOT_ACCURACY"
    def __post_init__(self):
        digest(self.profile_fingerprint); digest(self.requirements_fingerprint)
        if type(self.supported) is not bool or type(self.blockers) is not tuple: raise AudioError("EVALUATOR_DECISION_TYPE")
        for x in self.blockers: text(x, "capability blocker", 256)
        if self.supported == bool(self.blockers): raise AudioError("EVALUATOR_DECISION_CONTRADICTION")
        if self.scope != "CAPABILITY_NEGOTIATION_NOT_ACCURACY": raise AudioError("EVALUATOR_DECISION_SCOPE")

    def fingerprint(self): return fingerprint(self)


def negotiate(profile: EvaluatorProfile, req: EvaluationRequirements) -> CapabilityDecision:
    if type(profile) is not EvaluatorProfile or type(req) is not EvaluationRequirements:
        raise AudioError("EVALUATOR_NEGOTIATION_INPUT")
    blockers=[]
    supported=set(profile.supported_languages)
    for lang in req.languages:
        if lang not in supported: blockers.append(f"UNSUPPORTED_LANGUAGE:{lang}")
    accent_set={(a.language,a.accent) for a in profile.accent_bindings}
    for pair in req.accents:
        if pair not in accent_set: blockers.append(f"UNSUPPORTED_ACCENT:{pair[0]}:{pair[1]}")
    if req.requires_ipa and not profile.supports_ipa_targets: blockers.append("IPA_TARGETS_UNSUPPORTED")
    if req.contains_oov and not profile.supports_oov_targets: blockers.append("OOV_TARGETS_UNSUPPORTED")
    if req.code_switched and not profile.supports_code_switching: blockers.append("CODE_SWITCHING_UNSUPPORTED")
    if req.target_count > profile.max_targets: blockers.append("TARGET_BUDGET_EXCEEDED")
    if req.audio_seconds > profile.max_audio_seconds: blockers.append("AUDIO_BUDGET_EXCEEDED")
    blockers=tuple(sorted(set(blockers)))
    return CapabilityDecision(profile.fingerprint(), req.fingerprint(), not blockers, blockers)
