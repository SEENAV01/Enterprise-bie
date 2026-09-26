from __future__ import annotations
from dataclasses import dataclass
from .ids import require_id, require_unique_ids
from .provenance import ProvenanceBundle
from .errors import GameContractError

@dataclass(frozen=True)
class LearningTarget:
    objective_id:str
    concept_ids:tuple[str,...]
    prerequisite_ids:tuple[str,...]=()
    misconception_ids:tuple[str,...]=()
    mastery_target:float=0.8
    provenance:ProvenanceBundle|None=None
    def validate(self):
        require_id(self.objective_id,'GAME_OBJECTIVE_ID')
        if not self.concept_ids:raise GameContractError('GAME_CONCEPT_REQUIRED')
        for seq,code in ((self.concept_ids,'GAME_CONCEPT_ID'),(self.prerequisite_ids,'GAME_PREREQ_ID'),(self.misconception_ids,'GAME_MISCONCEPTION_ID')):
            require_unique_ids(seq,code+'_DUP');[require_id(x,code) for x in seq]
        if type(self.mastery_target) not in (int,float) or not 0<self.mastery_target<=1:raise GameContractError('GAME_MASTERY_TARGET')
        if self.provenance is None:raise GameContractError('GAME_LEARNING_PROVENANCE')
        self.provenance.validate(('source','reasoning','objective'))
        return self
