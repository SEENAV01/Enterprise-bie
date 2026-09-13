from dataclasses import dataclass
@dataclass(frozen=True)
class FormativeCheck:
    check_id:str; objective_id:str; prompt:str; success_criterion:str; evidence_ids:tuple[str,...]
def make_formative_check(check_id,objective_id,prompt,success_criterion,evidence_ids):
    if not all(str(x).strip() for x in (check_id,objective_id,prompt,success_criterion)) or not evidence_ids: raise ValueError('grounding')
    return FormativeCheck(check_id,objective_id,prompt,success_criterion,tuple(sorted(set(evidence_ids))))
