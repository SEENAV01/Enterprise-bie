from dataclasses import dataclass
@dataclass(frozen=True)
class RetrievalQuestion:
    concept_id:str; prompt:str; answer_key:str; cue_level:str; evidence_ids:tuple[str,...]
def make_retrieval_question(concept_id,prompt,answer_key,evidence_ids,cue_level='NONE'):
    if cue_level not in {'NONE','LOW','MEDIUM','HIGH'}: raise ValueError('cue')
    if not concept_id.strip() or not prompt.strip() or not answer_key.strip() or not evidence_ids: raise ValueError('grounding')
    return RetrievalQuestion(concept_id,prompt,answer_key,cue_level,tuple(sorted(set(evidence_ids))))
