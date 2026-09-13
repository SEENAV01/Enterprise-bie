from dataclasses import dataclass
@dataclass(frozen=True)
class RepetitionDecision:
    repeat:bool; interval_units:int; mode:str; reason:str
def repetition_policy(mastery,last_success,error_recurrence):
    if not 0<=mastery<=1 or error_recurrence<0: raise ValueError('inputs')
    if not last_success or mastery<.6 or error_recurrence>=2: return RepetitionDecision(True,1,'TARGETED','weak/unstable mastery')
    if mastery<.85: return RepetitionDecision(True,3,'SPACED','developing mastery')
    return RepetitionDecision(True,7,'RETRIEVAL_ONLY','strong mastery; avoid redundant reteaching')
