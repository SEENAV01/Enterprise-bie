from dataclasses import dataclass
@dataclass(frozen=True)
class TransferQuestion:
    concept_id:str; source_context:str; novel_context:str; prompt:str; evidence_ids:tuple[str,...]
def make_transfer_question(concept_id,source_context,novel_context,prompt,evidence_ids):
    if not all(x.strip() for x in (concept_id,source_context,novel_context,prompt)) or not evidence_ids: raise ValueError('grounding')
    if source_context.strip().lower()==novel_context.strip().lower(): raise ValueError('novel context required')
    return TransferQuestion(concept_id,source_context,novel_context,prompt,tuple(sorted(set(evidence_ids))))
