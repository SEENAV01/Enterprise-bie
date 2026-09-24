"""H9-002: exact media/source/voice/model binding for modern evaluator reports.

The report format can carry multilingual/accent/IPA/OOV evidence and explicit
uncertainty. It never authorizes acceptance by itself.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import re
from .common import AudioError, digest, fingerprint, integer, refs, text
from .evaluator_capability import EvaluatorProfile, EvaluationRequirements, negotiate

_HEX64=re.compile(r"[0-9a-f]{64}")
_STATUSES={"MEASURED","UNSUPPORTED","NO_SIGNAL","INCOMPLETE","ERROR"}


def _sha64(value, code="EVALUATOR_MEDIA_SHA"):
    if type(value) is not str or _HEX64.fullmatch(value) is None: raise AudioError(code)
    return value


@dataclass(frozen=True)
class EvaluationTarget:
    target_fingerprint: str
    segment_id: str
    span_index: int
    language: str
    accent: str | None
    expected_spoken: str
    expected_ipa: str | None
    is_oov: bool
    start_sample: int | None
    end_sample: int | None
    source_refs: tuple[str,...]
    voice_fingerprint: str
    def __post_init__(self):
        digest(self.target_fingerprint); text(self.segment_id,"segment",2048); integer(self.span_index,"span index",0,100000)
        from .common import locale
        locale(self.language)
        if self.accent is not None: text(self.accent,"accent",128)
        text(self.expected_spoken,"expected spoken",65536)
        if self.expected_ipa is not None: text(self.expected_ipa,"expected ipa",4096)
        if type(self.is_oov) is not bool: raise AudioError("EVALUATOR_TARGET_OOV_TYPE")
        if (self.start_sample is None)!=(self.end_sample is None): raise AudioError("EVALUATOR_TARGET_SAMPLE_PAIR")
        if self.start_sample is not None:
            integer(self.start_sample,"target start",0,10**9); integer(self.end_sample,"target end",self.start_sample+1,10**9)
        refs(self.source_refs,"target source refs"); digest(self.voice_fingerprint)

    def fingerprint(self): return fingerprint(self)


@dataclass(frozen=True)
class EvaluationRequest:
    media_sha256: str
    sample_rate: int
    total_samples: int
    plan_fingerprint: str
    clock_fingerprint: str
    profile_fingerprint: str
    requirements_fingerprint: str
    capability_decision_fingerprint: str
    targets: tuple[EvaluationTarget,...]
    purpose: str = "PRONUNCIATION_AND_ALIGNMENT"
    schema_version: str = "bie.audio.evaluator-request/1"
    def __post_init__(self):
        if self.schema_version!="bie.audio.evaluator-request/1" or self.purpose!="PRONUNCIATION_AND_ALIGNMENT": raise AudioError("EVALUATOR_REQUEST_VERSION")
        _sha64(self.media_sha256); integer(self.sample_rate,"sample rate",8000,192000); integer(self.total_samples,"samples",1,self.sample_rate*7200)
        for value in (self.plan_fingerprint,self.clock_fingerprint,self.profile_fingerprint,self.requirements_fingerprint,self.capability_decision_fingerprint): digest(value)
        if type(self.targets) is not tuple or not self.targets or len(self.targets)>100000 or any(type(x) is not EvaluationTarget for x in self.targets): raise AudioError("EVALUATOR_REQUEST_TARGETS")
        if len({x.target_fingerprint for x in self.targets}) != len(self.targets): raise AudioError("EVALUATOR_REQUEST_DUPLICATE_TARGET")
        for x in self.targets:
            if x.end_sample is not None and x.end_sample>self.total_samples: raise AudioError("EVALUATOR_TARGET_OUT_OF_MEDIA")
    def fingerprint(self): return fingerprint(self)


@dataclass(frozen=True)
class EvaluatedTarget:
    target_fingerprint: str
    status: str
    deviation_score_ppm: int | None
    uncertainty_ppm: int | None
    observed_phones: tuple[str,...]
    word_start_sample: int | None
    word_end_sample: int | None
    oov_handled: bool
    diagnostic_codes: tuple[str,...]
    def __post_init__(self):
        digest(self.target_fingerprint)
        if self.status not in _STATUSES: raise AudioError("EVALUATOR_REPORT_STATUS")
        if (self.deviation_score_ppm is None)!=(self.uncertainty_ppm is None): raise AudioError("EVALUATOR_REPORT_SCORE_PAIR")
        if self.deviation_score_ppm is not None:
            integer(self.deviation_score_ppm,"deviation score",0,1_000_000); integer(self.uncertainty_ppm,"uncertainty",0,1_000_000)
        if type(self.observed_phones) is not tuple or len(self.observed_phones)>4096: raise AudioError("EVALUATOR_REPORT_PHONES")
        for p in self.observed_phones: text(p,"observed phone",64)
        if (self.word_start_sample is None)!=(self.word_end_sample is None): raise AudioError("EVALUATOR_REPORT_WORD_PAIR")
        if self.word_start_sample is not None:
            integer(self.word_start_sample,"word start",0,10**9); integer(self.word_end_sample,"word end",self.word_start_sample+1,10**9)
        if type(self.oov_handled) is not bool: raise AudioError("EVALUATOR_REPORT_OOV_TYPE")
        if type(self.diagnostic_codes) is not tuple or len(self.diagnostic_codes)>128: raise AudioError("EVALUATOR_REPORT_DIAGNOSTICS")
        for d in self.diagnostic_codes: text(d,"diagnostic",128)
        if self.status=="MEASURED" and (self.deviation_score_ppm is None or self.word_start_sample is None): raise AudioError("EVALUATOR_MEASURED_INCOMPLETE")
        if self.status!="MEASURED" and self.deviation_score_ppm is not None: raise AudioError("EVALUATOR_UNMEASURED_SCORE")

    def fingerprint(self): return fingerprint(self)


@dataclass(frozen=True)
class EvaluationReport:
    request_fingerprint: str
    evaluator_id: str
    provider_id: str
    model_id: str
    model_revision: str
    runtime_fingerprint: str
    profile_fingerprint: str
    media_sha256: str
    targets: tuple[EvaluatedTarget,...]
    report_scope: str = "MEASUREMENT_NOT_ACCEPTANCE"
    schema_version: str = "bie.audio.evaluator-report/1"
    def __post_init__(self):
        if self.schema_version!="bie.audio.evaluator-report/1" or self.report_scope!="MEASUREMENT_NOT_ACCEPTANCE": raise AudioError("EVALUATOR_REPORT_VERSION")
        for value in (self.request_fingerprint,self.runtime_fingerprint,self.profile_fingerprint): digest(value)
        for key in ("evaluator_id","provider_id","model_id","model_revision"): text(getattr(self,key),key,512)
        _sha64(self.media_sha256)
        if type(self.targets) is not tuple or not self.targets or len(self.targets)>100000 or any(type(x) is not EvaluatedTarget for x in self.targets): raise AudioError("EVALUATOR_REPORT_TARGETS")
        if len({x.target_fingerprint for x in self.targets})!=len(self.targets): raise AudioError("EVALUATOR_REPORT_DUPLICATE_TARGET")
    def fingerprint(self): return fingerprint(self)


def request_from_targets(*, media_sha256:str, sample_rate:int, total_samples:int, plan_fingerprint:str,
                         clock_fingerprint:str, profile:EvaluatorProfile, targets:tuple[EvaluationTarget,...],
                         requirements:EvaluationRequirements) -> EvaluationRequest:
    decision=negotiate(profile,requirements)
    if not decision.supported: raise AudioError("EVALUATOR_CAPABILITY_BLOCKED",";".join(decision.blockers)[:500])
    if len(targets)!=requirements.target_count: raise AudioError("EVALUATOR_REQUIREMENT_TARGET_COUNT")
    return EvaluationRequest(media_sha256,sample_rate,total_samples,plan_fingerprint,clock_fingerprint,
        profile.fingerprint(),requirements.fingerprint(),decision.fingerprint(),targets)


def validate_report(report:EvaluationReport, request:EvaluationRequest, profile:EvaluatorProfile):
    if type(report) is not EvaluationReport or type(request) is not EvaluationRequest or type(profile) is not EvaluatorProfile:
        raise AudioError("EVALUATOR_REPORT_INPUT")
    if report.request_fingerprint!=request.fingerprint() or report.profile_fingerprint!=profile.fingerprint() or request.profile_fingerprint!=profile.fingerprint():
        raise AudioError("EVALUATOR_REPORT_BINDING")
    if report.media_sha256!=request.media_sha256: raise AudioError("EVALUATOR_REPORT_MEDIA_CHANGED")
    if (report.evaluator_id,report.provider_id,report.model_id,report.model_revision,report.runtime_fingerprint)!=(profile.evaluator_id,profile.provider_id,profile.model_id,profile.model_revision,profile.runtime_fingerprint):
        raise AudioError("EVALUATOR_REPORT_IDENTITY")
    expected={x.target_fingerprint:x for x in request.targets}
    if set(expected)!={x.target_fingerprint for x in report.targets}: raise AudioError("EVALUATOR_REPORT_COVERAGE")
    for row in report.targets:
        target=expected[row.target_fingerprint]
        if row.word_end_sample is not None and row.word_end_sample>request.total_samples: raise AudioError("EVALUATOR_REPORT_WORD_OUT_OF_MEDIA")
        if target.is_oov and row.status=="MEASURED" and not row.oov_handled: raise AudioError("EVALUATOR_REPORT_OOV_UNHANDLED")
        if target.expected_ipa is not None and row.status=="MEASURED" and not row.observed_phones: raise AudioError("EVALUATOR_REPORT_IPA_EVIDENCE_MISSING")
    return report
