from __future__ import annotations
import json,re
from .contracts import *
from .common import *

def _metadata(content):
    m=re.search(r'export const ruleMetadata = (\{.*\}) as const;',content)
    if not m:raise ValueError('rule metadata missing')
    return json.loads(m.group(1))
def evaluate(document,bundle):
    document.validate();rules=[];state_ids=set();refs=[]
    for exp in document.experiences:
      for level in exp.levels:
        state_ids.update(level.state.type_map());rules.extend(level.interaction.rules)
    art=next((a for a in bundle.artifacts if a.path=='runtime/rules.ts'),None);findings=[]
    if art is None:return result('BIE-GAME-QA-002',document,0,(),(finding('BIE-GAME-QA-002',1,'COMPILED_RULE_ARTIFACT_MISSING','runtime/rules.ts missing'),),('rule-program',))
    data=_metadata(art.content);compiled={x['rule_id']:x for x in data['rules']};source={r.rule_id:r for r in rules}
    missing=sorted(set(source)-set(compiled));extra=sorted(set(compiled)-set(source));unsafe=('eval(' in art.content or 'new Function' in art.content or data.get('uses_eval') is not False)
    if missing:findings.append(finding('BIE-GAME-QA-002',1,'RULES_MISSING',','.join(missing),refs=art.source_refs))
    if extra:findings.append(finding('BIE-GAME-QA-002',2,'RULES_EXTRA',','.join(extra),refs=art.source_refs))
    if unsafe:findings.append(finding('BIE-GAME-QA-002',3,'UNSAFE_RULE_EXECUTION','dynamic expression execution detected',severity=Severity.CRITICAL,refs=art.source_refs))
    ungrounded=[r.rule_id for r in rules if not r.grounding_refs]
    if ungrounded:findings.append(finding('BIE-GAME-QA-002',4,'UNGROUNDED_RULES',','.join(ungrounded),refs=art.source_refs))
    target_bad=[]
    for r in rules:
      for e in r.effects:
        if e.target_variable_id not in state_ids:target_bad.append(r.rule_id+':'+e.target_variable_id)
    if target_bad:findings.append(finding('BIE-GAME-QA-002',5,'RULE_TARGET_MISSING',','.join(target_bad),refs=art.source_refs))
    coverage=ratio(len(set(source)&set(compiled)),len(source));score=1.0 if not findings else max(0,coverage-.25*len(findings))
    metrics=(QualityMetric('rule_compile_coverage',coverage,1,1),QualityMetric('unsafe_dynamic_execution',float(unsafe),0,0),QualityMetric('ungrounded_rules',float(len(ungrounded)),0,0,'count'))
    return result('BIE-GAME-QA-002',{'doc':document.fingerprint(),'bundle':bundle.receipt.bundle_fingerprint},score,metrics,findings,art.source_refs)
