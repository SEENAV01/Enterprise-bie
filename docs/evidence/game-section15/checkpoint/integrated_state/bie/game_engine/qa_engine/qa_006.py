from __future__ import annotations
import json,re
from .contracts import *
from .common import *

def _compiled(bundle):
    art=next((a for a in bundle.artifacts if a.path=='runtime/feedback.ts'),None)
    if art is None:return None,None
    m=re.search(r'export const feedbackProgram = (\{.*\}) as const;',art.content);return art,(json.loads(m.group(1)) if m else None)
def evaluate(document,bundle):
    document.validate();art,data=_compiled(bundle);findings=[];refs=tuple(art.source_refs) if art else ('feedback-program',);source=[]
    for exp in document.experiences:
      for level in exp.levels:
       for ch in level.challenges:source.append(ch)
    if not art or not data:findings.append(finding('BIE-GAME-QA-006',1,'FEEDBACK_ARTIFACT_MISSING','compiled feedback program missing',refs=refs));return result('BIE-GAME-QA-006',document,0,(),findings,refs)
    rows={x['challenge_id']:x for x in data['feedback']}
    for ch in source:
        row=rows.get(ch.challenge_id)
        if not row:findings.append(finding('BIE-GAME-QA-006',2,'CHALLENGE_FEEDBACK_MISSING',ch.challenge_id,refs=refs));continue
        if row.get('reveal_answer_on_failure') is not False:findings.append(finding('BIE-GAME-QA-006',3,'PREMATURE_ANSWER_REVEAL',ch.challenge_id,refs=refs))
        if not row.get('success') or not row.get('failure') or row['success'].strip()==row['failure'].strip():findings.append(finding('BIE-GAME-QA-006',4,'FEEDBACK_NOT_DISTINCT',ch.challenge_id,refs=refs))
        need={m for m,_ in ch.feedback.misconception_feedback};have={x['misconception_id'] for x in row.get('misconceptions',[])}
        if need-have:findings.append(finding('BIE-GAME-QA-006',5,'MISCONCEPTION_FEEDBACK_COMPILE_GAP',','.join(sorted(need-have)),refs=refs))
        if ch.feedback.explanation_ref and not row.get('explanation'):findings.append(finding('BIE-GAME-QA-006',6,'EXPLANATION_MISSING',ch.challenge_id,refs=refs))
    cov=ratio(len(source)-sum(1 for ch in source if ch.challenge_id not in rows),len(source));score=1 if not findings else max(0,cov-.15*len(findings));metrics=(QualityMetric('feedback_compile_coverage',cov,1,1),QualityMetric('blocking_feedback_findings',float(sum(f.blocking for f in findings)),0,0,'count'))
    return result('BIE-GAME-QA-006',{'doc':document.fingerprint(),'bundle':bundle.receipt.bundle_fingerprint},score,metrics,findings,refs)
