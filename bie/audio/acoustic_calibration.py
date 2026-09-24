"""H9-003: deterministic held-out calibration and error-rate accounting.

Calibration evidence is explicitly scoped. Synthetic/unit-test fixtures can validate
mechanics but can never be promoted to production calibration.
"""
from __future__ import annotations
from dataclasses import dataclass
from .common import AudioError, digest, fingerprint, integer, locale, refs, text

_LABELS={"CORRECT","PRONUNCIATION_ERROR"}
_SCOPES={"TEST_FIXTURE_ONLY","HELD_OUT_INDEPENDENT"}


@dataclass(frozen=True)
class CalibrationCase:
    case_id: str
    target_fingerprint: str
    media_sha256: str
    language: str
    accent: str
    label: str
    deviation_score_ppm: int
    uncertainty_ppm: int
    evaluator_profile_fingerprint: str
    evidence_refs: tuple[str,...]
    def __post_init__(self):
        text(self.case_id,"calibration case",256); digest(self.target_fingerprint); digest(self.evaluator_profile_fingerprint)
        if type(self.media_sha256) is not str or len(self.media_sha256)!=64 or any(c not in "0123456789abcdef" for c in self.media_sha256): raise AudioError("CALIBRATION_MEDIA_SHA")
        locale(self.language); text(self.accent,"accent",128)
        if self.label not in _LABELS: raise AudioError("CALIBRATION_LABEL")
        integer(self.deviation_score_ppm,"deviation score",0,1_000_000); integer(self.uncertainty_ppm,"uncertainty",0,1_000_000)
        refs(self.evidence_refs,"calibration evidence")

    def fingerprint(self): return fingerprint(self)


@dataclass(frozen=True)
class CalibrationDataset:
    dataset_id: str
    revision: str
    evaluator_profile_fingerprint: str
    cases: tuple[CalibrationCase,...]
    held_out: bool
    independent_labels: bool
    scope: str
    evidence_refs: tuple[str,...]
    schema_version: str = "bie.audio.calibration-dataset/1"
    def __post_init__(self):
        if self.schema_version!="bie.audio.calibration-dataset/1" or self.scope not in _SCOPES: raise AudioError("CALIBRATION_DATASET_VERSION")
        text(self.dataset_id,"dataset id",256); text(self.revision,"dataset revision",256); digest(self.evaluator_profile_fingerprint)
        if type(self.cases) is not tuple or not self.cases or len(self.cases)>100000 or any(type(x) is not CalibrationCase for x in self.cases): raise AudioError("CALIBRATION_CASES")
        if len({x.case_id for x in self.cases})!=len(self.cases): raise AudioError("CALIBRATION_DUPLICATE_CASE")
        if any(x.evaluator_profile_fingerprint!=self.evaluator_profile_fingerprint for x in self.cases): raise AudioError("CALIBRATION_PROFILE_MIX")
        if type(self.held_out) is not bool or type(self.independent_labels) is not bool: raise AudioError("CALIBRATION_DATASET_BOOLEAN")
        if self.scope=="HELD_OUT_INDEPENDENT" and not (self.held_out and self.independent_labels): raise AudioError("CALIBRATION_SCOPE_CONTRADICTION")
        refs(self.evidence_refs,"dataset evidence")
    def fingerprint(self): return fingerprint(self)


@dataclass(frozen=True)
class CalibrationPolicy:
    min_correct: int = 20
    min_error: int = 20
    max_false_positive_ppm: int = 100_000
    max_false_negative_ppm: int = 100_000
    max_case_uncertainty_ppm: int = 250_000
    require_each_language_both_labels: bool = True
    revision: str = "audio-h9-calibration-v1"
    def __post_init__(self):
        integer(self.min_correct,"min correct",1,100000); integer(self.min_error,"min error",1,100000)
        integer(self.max_false_positive_ppm,"max fp",0,1_000_000); integer(self.max_false_negative_ppm,"max fn",0,1_000_000)
        integer(self.max_case_uncertainty_ppm,"max uncertainty",0,1_000_000)
        if type(self.require_each_language_both_labels) is not bool: raise AudioError("CALIBRATION_POLICY_BOOLEAN")
        text(self.revision,"calibration revision",256)
    def fingerprint(self): return fingerprint(self)


@dataclass(frozen=True)
class CalibrationResult:
    dataset_fingerprint: str
    evaluator_profile_fingerprint: str
    policy_fingerprint: str
    status: str
    threshold_ppm: int | None
    correct_count: int
    error_count: int
    false_positive_count: int
    false_negative_count: int
    false_positive_ppm: int | None
    false_negative_ppm: int | None
    excluded_uncertain_count: int
    calibration_scope: str
    blockers: tuple[str,...]
    schema_version: str = "bie.audio.calibration-result/1"
    def __post_init__(self):
        if self.schema_version!="bie.audio.calibration-result/1" or self.status not in ("CALIBRATED","NOT_CALIBRATED"): raise AudioError("CALIBRATION_RESULT_VERSION")
        for v in (self.dataset_fingerprint,self.evaluator_profile_fingerprint,self.policy_fingerprint): digest(v)
        for n in ("correct_count","error_count","false_positive_count","false_negative_count","excluded_uncertain_count"): integer(getattr(self,n),n,0,100000)
        if self.threshold_ppm is not None: integer(self.threshold_ppm,"threshold",0,1_000_000)
        for n in ("false_positive_ppm","false_negative_ppm"):
            v=getattr(self,n)
            if v is not None: integer(v,n,0,1_000_000)
        if self.calibration_scope not in _SCOPES: raise AudioError("CALIBRATION_RESULT_SCOPE")
        if type(self.blockers) is not tuple: raise AudioError("CALIBRATION_RESULT_BLOCKERS")
        for b in self.blockers: text(b,"calibration blocker",256)
        if self.status=="CALIBRATED" and (self.threshold_ppm is None or self.blockers): raise AudioError("CALIBRATION_RESULT_CONTRADICTION")
        if self.status=="NOT_CALIBRATED" and not self.blockers: raise AudioError("CALIBRATION_RESULT_NO_REASON")
    def fingerprint(self): return fingerprint(self)


def _ppm(num,den): return (num*1_000_000 + den//2)//den if den else None


def calibrate(dataset:CalibrationDataset, policy:CalibrationPolicy=CalibrationPolicy()):
    if type(dataset) is not CalibrationDataset or type(policy) is not CalibrationPolicy: raise AudioError("CALIBRATION_INPUT")
    usable=[c for c in dataset.cases if c.uncertainty_ppm<=policy.max_case_uncertainty_ppm]
    excluded=len(dataset.cases)-len(usable)
    correct=[c for c in usable if c.label=="CORRECT"]; errors=[c for c in usable if c.label=="PRONUNCIATION_ERROR"]
    blockers=[]
    if len(correct)<policy.min_correct: blockers.append("INSUFFICIENT_CORRECT_CASES")
    if len(errors)<policy.min_error: blockers.append("INSUFFICIENT_ERROR_CASES")
    if policy.require_each_language_both_labels:
        langs={c.language for c in usable}
        for lang in sorted(langs):
            labels={c.label for c in usable if c.language==lang}
            if labels!=_LABELS: blockers.append(f"LANGUAGE_LABEL_COVERAGE:{lang}")
    if blockers:
        return CalibrationResult(dataset.fingerprint(),dataset.evaluator_profile_fingerprint,policy.fingerprint(),"NOT_CALIBRATED",None,
            len(correct),len(errors),0,0,None,None,excluded,dataset.scope,tuple(blockers))
    candidates=sorted({0,1_000_000,*[c.deviation_score_ppm for c in usable]})
    passing=[]
    for threshold in candidates:
        fp=sum(c.deviation_score_ppm>=threshold for c in correct)
        fn=sum(c.deviation_score_ppm<threshold for c in errors)
        fpr=_ppm(fp,len(correct)); fnr=_ppm(fn,len(errors))
        if fpr<=policy.max_false_positive_ppm and fnr<=policy.max_false_negative_ppm:
            passing.append((fpr+fnr,max(fpr,fnr),threshold,fp,fn,fpr,fnr))
    if not passing:
        return CalibrationResult(dataset.fingerprint(),dataset.evaluator_profile_fingerprint,policy.fingerprint(),"NOT_CALIBRATED",None,
            len(correct),len(errors),0,0,None,None,excluded,dataset.scope,("NO_THRESHOLD_MEETS_ERROR_BOUNDS",))
    _,_,threshold,fp,fn,fpr,fnr=min(passing)
    return CalibrationResult(dataset.fingerprint(),dataset.evaluator_profile_fingerprint,policy.fingerprint(),"CALIBRATED",threshold,
        len(correct),len(errors),fp,fn,fpr,fnr,excluded,dataset.scope,())
