from dataclasses import dataclass
@dataclass(frozen=True)
class DiagnosticCheck:
    check_id:str; target_ids:tuple[str,...]; distractor_map:tuple[tuple[str,str],...]; evidence_ids:tuple[str,...]
def make_diagnostic_check(check_id,target_ids,distractor_map,evidence_ids):
    targets=tuple(sorted(set(target_ids))); dm=tuple(sorted(distractor_map.items()))
    if not check_id.strip() or not targets or not dm or not evidence_ids or any(not k.strip() or not v.strip() for k,v in dm): raise ValueError('grounding')
    return DiagnosticCheck(check_id,targets,dm,tuple(sorted(set(evidence_ids))))
