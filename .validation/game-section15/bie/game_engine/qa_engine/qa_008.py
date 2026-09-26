from __future__ import annotations
from .contracts import *
from .common import *
from .policy import GameQAPolicy

def evaluate(runtime_result,policy=GameQAPolicy()):
    policy.validate();findings=[];refs=tuple(r.receipt_id for r in runtime_result.receipts)
    checks=[]
    try:runtime_result.manifest.validate();checks.append(('manifest',True))
    except Exception as e:checks.append(('manifest',False));findings.append(finding('BIE-GAME-QA-008',1,'RUNTIME_MANIFEST_INVALID',str(e),refs=refs))
    for name,obj,idx in (('browser',runtime_result.browser,2),('interaction',runtime_result.interaction,3),('replay',runtime_result.replay,4),('deployment',runtime_result.deployment,8)):
        try:
            if obj is None: raise ValueError('required runtime evidence missing')
            obj.validate();checks.append((name,True))
        except Exception as e:checks.append((name,False));findings.append(finding('BIE-GAME-QA-008',idx,'RUNTIME_'+name.upper()+'_INVALID',str(e),refs=refs))
    exc_ok=True
    for e in runtime_result.exceptions:
        try:e.validate()
        except Exception as err:exc_ok=False;findings.append(finding('BIE-GAME-QA-008',5,'RUNTIME_EXCEPTION_EVIDENCE_INVALID',str(err),refs=refs))
    checks.append(('exceptions',exc_ok))
    if runtime_result.browser.external_requests or runtime_result.browser.console_errors or runtime_result.browser.page_errors:findings.append(finding('BIE-GAME-QA-008',6,'RUNTIME_BROWSER_ERRORS','browser emitted network/console/page errors',refs=refs))
    if not runtime_result.replay.identical_second_run:findings.append(finding('BIE-GAME-QA-008',7,'RUNTIME_REPLAY_NONDETERMINISTIC','second replay differs',refs=refs))
    passed=sum(v for _,v in checks);score=passed/len(checks);metrics=(QualityMetric('runtime_evidence_components',float(passed),float(len(checks)),float(len(checks)),'count'),QualityMetric('external_requests',float(len(runtime_result.browser.external_requests)),0,0,'count'),QualityMetric('runtime_errors',float(len(runtime_result.browser.console_errors)+len(runtime_result.browser.page_errors)),0,0,'count'))
    return result('BIE-GAME-QA-008',runtime_result,score,metrics,findings,refs)
