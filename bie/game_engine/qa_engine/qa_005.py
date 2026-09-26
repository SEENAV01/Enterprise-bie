from __future__ import annotations
from .contracts import *
from .common import *

def evaluate(bundle,plan):
    bundle.validate();refs=provenance_refs(bundle.provenance)
    try:plan.validate()
    except Exception as exc:
        return result('BIE-GAME-QA-005',{'bundle':bundle,'plan':repr(plan)},0,(),(finding('BIE-GAME-QA-005',0,'DIRECTOR_PLAN_INVALID',str(exc),severity=Severity.CRITICAL,refs=refs),),refs)
    required={m for o in bundle.objectives for m in o.misconception_ids};mapped={x.misconception_id for x in plan.misconception_assignments};feedback={m for f in plan.feedback for m,_ in f.misconception_refs};adapt_obj={a.objective_id for a in plan.adaptations if a.action.value in ('remediate','easier_variant')};findings=[]
    missing=sorted(required-mapped);fb=sorted(required-feedback);rem=sorted({x.objective_id for x in plan.misconception_assignments}-adapt_obj)
    if missing:findings.append(finding('BIE-GAME-QA-005',1,'MISCONCEPTION_NOT_MAPPED',','.join(missing),refs=refs))
    if fb:findings.append(finding('BIE-GAME-QA-005',2,'MISCONCEPTION_FEEDBACK_MISSING',','.join(fb),refs=refs))
    if rem:findings.append(finding('BIE-GAME-QA-005',3,'MISCONCEPTION_REMEDIATION_MISSING',','.join(rem),refs=refs))
    nondiagnostic=[x.misconception_id for x in plan.misconception_assignments if not x.diagnostic_required]
    if nondiagnostic:findings.append(finding('BIE-GAME-QA-005',4,'DIAGNOSTIC_NOT_REQUIRED',','.join(nondiagnostic),refs=refs))
    cov=ratio(len(required&mapped&feedback),len(required));metrics=(QualityMetric('misconception_alignment',cov,1,1),QualityMetric('remediation_objectives',float(len(adapt_obj)),1,None,'count'))
    return result('BIE-GAME-QA-005',{'bundle':bundle,'plan':plan.plan_fingerprint},cov,metrics,findings,refs)
