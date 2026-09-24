"""H9-005: governed pronunciation decisions and repair intents.

PASS is possible only with a current bound report, held-out independent calibration,
and production release authority. This module does not dispatch repairs or invalidate
canonical DIR/ANI/COMP artifacts; F04 owns that integration.
"""
from __future__ import annotations
from dataclasses import dataclass
from .common import AudioError, digest, fingerprint, refs, text
from .evaluator_capability import EvaluatorProfile
from .evaluator_contract import EvaluationReport, EvaluationRequest, validate_report
from .acoustic_calibration import CalibrationResult
from .evaluator_authority import SignedAuthority, AuthorityTrust, verify_authority


@dataclass(frozen=True)
class PronunciationFinding:
    target_fingerprint: str
    verdict: str
    code: str
    owner: str
    evidence_refs: tuple[str,...]
    def __post_init__(self):
        digest(self.target_fingerprint)
        if self.verdict not in ("PASS","FAIL","REVIEW","BLOCKED"): raise AudioError("PRONUNCIATION_VERDICT")
        text(self.code,"finding code",128); text(self.owner,"finding owner",128); refs(self.evidence_refs,"finding evidence")


@dataclass(frozen=True)
class PronunciationDecision:
    request_fingerprint: str
    report_fingerprint: str
    calibration_fingerprint: str
    authority_fingerprint: str
    overall: str
    findings: tuple[PronunciationFinding,...]
    pronunciation_verified: bool
    product_accepted: bool = False
    schema_version: str = "bie.audio.pronunciation-decision/1"
    def __post_init__(self):
        if self.schema_version!="bie.audio.pronunciation-decision/1" or self.overall not in ("PASS","FAIL","REVIEW","BLOCKED"): raise AudioError("PRONUNCIATION_DECISION_VERSION")
        for v in (self.request_fingerprint,self.report_fingerprint,self.calibration_fingerprint,self.authority_fingerprint): digest(v)
        if type(self.findings) is not tuple or not self.findings or any(type(x) is not PronunciationFinding for x in self.findings): raise AudioError("PRONUNCIATION_FINDINGS")
        if type(self.pronunciation_verified) is not bool or type(self.product_accepted) is not bool or self.product_accepted: raise AudioError("PRONUNCIATION_PRODUCT_BOUNDARY")
        if self.pronunciation_verified != (self.overall=="PASS"): raise AudioError("PRONUNCIATION_VERIFIED_CONTRADICTION")
    def fingerprint(self): return fingerprint(self)


def decide(request:EvaluationRequest, report:EvaluationReport, profile:EvaluatorProfile, calibration:CalibrationResult,
           signed_authority:SignedAuthority, trust:AuthorityTrust, *, now:int|None=None, max_uncertainty_ppm:int=250_000):
    validate_report(report,request,profile)
    if type(calibration) is not CalibrationResult: raise AudioError("PRONUNCIATION_CALIBRATION_REQUIRED")
    auth=verify_authority(signed_authority,trust,profile,calibration,now=now)
    if calibration.evaluator_profile_fingerprint!=profile.fingerprint(): raise AudioError("PRONUNCIATION_CALIBRATION_BINDING")
    rows={x.target_fingerprint:x for x in report.targets}; findings=[]
    if not auth["production_authorized"] or calibration.status!="CALIBRATED" or calibration.threshold_ppm is None:
        for t in request.targets:
            findings.append(PronunciationFinding(t.target_fingerprint,"BLOCKED","PRODUCTION_CALIBRATION_OR_AUTHORITY_MISSING","AUDIO/QA",(f"report:{report.fingerprint()}",)))
        overall="BLOCKED"
    else:
        for t in request.targets:
            r=rows[t.target_fingerprint]
            evidence=(f"report:{report.fingerprint()}",f"calibration:{calibration.fingerprint()}",f"authority:{auth['authority_fingerprint']}")
            if r.status!="MEASURED": findings.append(PronunciationFinding(t.target_fingerprint,"BLOCKED","EVALUATOR_TARGET_NOT_MEASURED","AUDIO/QA",evidence)); continue
            if r.uncertainty_ppm is None or r.uncertainty_ppm>max_uncertainty_ppm:
                findings.append(PronunciationFinding(t.target_fingerprint,"REVIEW","EVALUATOR_UNCERTAINTY_HIGH","AUDIO/QA",evidence)); continue
            if r.deviation_score_ppm>=calibration.threshold_ppm:
                findings.append(PronunciationFinding(t.target_fingerprint,"FAIL","CALIBRATED_PRONUNCIATION_MISMATCH","AUDIO/VO",evidence))
            else:
                findings.append(PronunciationFinding(t.target_fingerprint,"PASS","CALIBRATED_PRONUNCIATION_MATCH","AUDIO/QA",evidence))
        verdicts={x.verdict for x in findings}
        overall="FAIL" if "FAIL" in verdicts else "BLOCKED" if "BLOCKED" in verdicts else "REVIEW" if "REVIEW" in verdicts else "PASS"
    return PronunciationDecision(request.fingerprint(),report.fingerprint(),calibration.fingerprint(),auth["authority_fingerprint"],overall,tuple(findings),overall=="PASS")


def repair_intents(decision:PronunciationDecision, request:EvaluationRequest):
    if type(decision) is not PronunciationDecision or type(request) is not EvaluationRequest or decision.request_fingerprint!=request.fingerprint(): raise AudioError("PRONUNCIATION_REPAIR_INPUT")
    targets={x.target_fingerprint:x for x in request.targets}; out=[]
    for finding in decision.findings:
        if finding.verdict!="FAIL": continue
        t=targets[finding.target_fingerprint]
        row={"target_fingerprint":t.target_fingerprint,"owner":"AUDIO/VO","action":"RESYNTHESIZE_UNCHANGED_READING",
             "expected_spoken":t.expected_spoken,"expected_ipa":t.expected_ipa,"source_refs":list(t.source_refs),
             "invalidates":["AUDIO_TTS_CACHE","AUDIO_SYNC","AUDIO_MIX","CAPTIONS","ANIMATION_CLOCKS","AUDIO_QA","RENDER"],
             "decision_fingerprint":decision.fingerprint(),"dispatch_performed":False}
        row["repair_fingerprint"]=fingerprint(row); out.append(row)
    return tuple(out)
