from __future__ import annotations
from dataclasses import dataclass
from .ids import require_id, require_text, require_semver, require_unique_ids
from .learning import LearningTarget
from .state import StateModel
from .interaction import InteractionContract
from .visual import VisualExperienceContract
from .audio import AudioExperienceContract
from .feedback import FeedbackContract
from .adaptation import AdaptationContract
from .quality_intent import ExperienceMode, ExperienceQualityIntent
from .provenance import ProvenanceBundle
from .expressions import Expr, validate_expr
from .errors import GameContractError
from .canonical import fingerprint

_NONTRIVIAL={ExperienceMode.MANIPULATION,ExperienceMode.SIMULATION,ExperienceMode.PREDICTION,ExperienceMode.DIAGNOSIS,ExperienceMode.CONSTRUCTION,ExperienceMode.TIMELINE,ExperienceMode.MAP,ExperienceMode.EQUATION,ExperienceMode.CAUSAL_SYSTEM}

@dataclass(frozen=True)
class ChallengeContract:
    challenge_id:str; title:str; mission_prompt_ref:str; mode:ExperienceMode; learning:LearningTarget; success_condition:Expr; failure_conditions:tuple[Expr,...]; feedback:FeedbackContract; difficulty:float; mastery_weight:float
    def validate(self,state:StateModel):
        require_id(self.challenge_id,'GAME_CHALLENGE_ID');require_text(self.title,'GAME_CHALLENGE_TITLE');require_id(self.mission_prompt_ref,'GAME_CHALLENGE_PROMPT_REF')
        if type(self.mode) is not ExperienceMode:raise GameContractError('GAME_EXPERIENCE_MODE')
        self.learning.validate();validate_expr(self.success_condition,state.type_map())
        if not self.failure_conditions:raise GameContractError('GAME_FAILURE_CONDITION_REQUIRED')
        for e in self.failure_conditions:validate_expr(e,state.type_map())
        self.feedback.validate()
        if type(self.difficulty) not in (int,float) or not 0<=self.difficulty<=1:raise GameContractError('GAME_DIFFICULTY')
        if type(self.mastery_weight) not in (int,float) or not 0<self.mastery_weight<=1:raise GameContractError('GAME_MASTERY_WEIGHT')
        return self

@dataclass(frozen=True)
class GameLevelContract:
    level_id:str; title:str; purpose:str; state:StateModel; interaction:InteractionContract; visual:VisualExperienceContract; audio:AudioExperienceContract; adaptation:AdaptationContract; challenges:tuple[ChallengeContract,...]
    def validate(self):
        require_id(self.level_id,'GAME_LEVEL_ID');require_text(self.title,'GAME_LEVEL_TITLE');require_text(self.purpose,'GAME_LEVEL_PURPOSE')
        self.state.validate();self.interaction.validate(self.state);self.visual.validate();self.audio.validate();self.adaptation.validate(self.state)
        if not self.challenges:raise GameContractError('GAME_CHALLENGE_REQUIRED')
        require_unique_ids([c.challenge_id for c in self.challenges],'GAME_CHALLENGE_DUPLICATE')
        for c in self.challenges:c.validate(self.state)
        # Core experience must include at least one non-trivial experiential mode.
        if not any(c.mode in _NONTRIVIAL for c in self.challenges):raise GameContractError('GAME_SLIDE_OR_QUIZ_ONLY_EXPERIENCE_FORBIDDEN')
        # Dynamic/non-reference gameplay requires semantic motion for at least one state-bound visual.
        if any(c.mode in {ExperienceMode.MANIPULATION,ExperienceMode.SIMULATION,ExperienceMode.PREDICTION,ExperienceMode.CAUSAL_SYSTEM} for c in self.challenges) and not self.visual.motion:
            raise GameContractError('GAME_DYNAMIC_EXPERIENCE_REQUIRES_MOTION')
        return self

@dataclass(frozen=True)
class GameExperienceContract:
    game_id:str; title:str; levels:tuple[GameLevelContract,...]; scoring_policy_ref:str; mastery_policy_ref:str; quality_intent:ExperienceQualityIntent=ExperienceQualityIntent()
    def validate(self):
        require_id(self.game_id,'GAME_ID');require_text(self.title,'GAME_TITLE');require_id(self.scoring_policy_ref,'GAME_SCORING_POLICY_REF');require_id(self.mastery_policy_ref,'GAME_MASTERY_POLICY_REF')
        if not self.levels:raise GameContractError('GAME_LEVEL_REQUIRED')
        require_unique_ids([l.level_id for l in self.levels],'GAME_LEVEL_DUPLICATE')
        self.quality_intent.validate();[l.validate() for l in self.levels]
        return self

@dataclass(frozen=True)
class GameDocument:
    game_ir_version:str; document_id:str; experiences:tuple[GameExperienceContract,...]; provenance:ProvenanceBundle; product_accepted:bool=False
    def validate(self):
        require_semver(self.game_ir_version,'GAME_IR_VERSION');require_id(self.document_id,'GAME_DOCUMENT_ID')
        if not self.experiences:raise GameContractError('GAME_EXPERIENCE_REQUIRED')
        require_unique_ids([e.game_id for e in self.experiences],'GAME_EXPERIENCE_DUPLICATE')
        self.provenance.validate(('source','reasoning'));[e.validate() for e in self.experiences]
        if self.product_accepted is not False:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self
    def fingerprint(self):self.validate();return fingerprint(self)
