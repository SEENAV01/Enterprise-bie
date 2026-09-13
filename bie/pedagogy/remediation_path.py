from dataclasses import dataclass
@dataclass(frozen=True)
class RemediationPath:
    concept_id:str; actions:tuple[str,...]; severity:str
def choose_remediation_path(concept_id,mastery,prerequisite_mastery,misconception_detected):
    if not concept_id.strip() or not 0<=mastery<=1 or any(not 0<=v<=1 for v in prerequisite_mastery.values()): raise ValueError('inputs')
    weak=sorted(k for k,v in prerequisite_mastery.items() if v<.6); actions=[]
    if weak: actions.append('bridge prerequisites: '+', '.join(weak))
    if misconception_detected: actions.append('misconception remediation')
    actions+=['guided worked example','targeted retrieval','transfer re-check']
    sev='HIGH' if mastery<.4 or len(weak)>1 else 'MEDIUM' if mastery<.7 else 'LOW'
    return RemediationPath(concept_id,tuple(actions),sev)
