from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .errors import GameContractError

class ExperienceMode(str,Enum): MANIPULATION='manipulation';SIMULATION='simulation';PREDICTION='prediction';DIAGNOSIS='diagnosis';CONSTRUCTION='construction';TIMELINE='timeline';MAP='map';EQUATION='equation';CAUSAL_SYSTEM='causal_system';RETRIEVAL='retrieval';REFERENCE='reference'

@dataclass(frozen=True)
class ExperienceQualityIntent:
    studio_grade_target:bool=True
    anti_slide_default:bool=True
    mcq_only_core_experience_forbidden:bool=True
    semantic_visuals_required:bool=True
    stateful_interaction_required:bool=True
    pedagogical_motion_required_when_dynamic:bool=True
    purposeful_camera_only:bool=True
    accessibility_required:bool=True
    provenance_required:bool=True
    deterministic_replay_required:bool=True
    def validate(self):
        required=(self.studio_grade_target,self.anti_slide_default,self.mcq_only_core_experience_forbidden,self.semantic_visuals_required,self.stateful_interaction_required,self.accessibility_required,self.provenance_required,self.deterministic_replay_required)
        if not all(x is True for x in required):raise GameContractError('GAME_QUALITY_INTENT_WEAKENED')
        return self
