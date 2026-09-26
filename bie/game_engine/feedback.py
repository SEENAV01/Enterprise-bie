from __future__ import annotations
from dataclasses import dataclass
from .ids import require_id
from .errors import GameContractError

@dataclass(frozen=True)
class FeedbackContract:
    success_message_ref:str; failure_message_ref:str; misconception_feedback:tuple[tuple[str,str],...]=(); explanation_ref:str|None=None; reveal_answer_on_failure:bool=False
    def validate(self):
        require_id(self.success_message_ref,'GAME_FEEDBACK_SUCCESS');require_id(self.failure_message_ref,'GAME_FEEDBACK_FAILURE')
        if self.reveal_answer_on_failure:raise GameContractError('GAME_FEEDBACK_PREMATURE_ANSWER_REVEAL')
        seen=set()
        for m,r in self.misconception_feedback:
            require_id(m,'GAME_FEEDBACK_MISCONCEPTION');require_id(r,'GAME_FEEDBACK_REF')
            if m in seen:raise GameContractError('GAME_FEEDBACK_DUP_MISCONCEPTION')
            seen.add(m)
        if self.explanation_ref:require_id(self.explanation_ref,'GAME_FEEDBACK_EXPLANATION')
        return self
