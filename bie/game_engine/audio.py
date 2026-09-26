from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .ids import require_id, require_unique_ids
from .errors import GameContractError

class AudioCueKind(str,Enum): FEEDBACK='feedback';STATE_CHANGE='state_change';SUCCESS='success';FAILURE='failure';AMBIENT='ambient';NARRATION='narration'
@dataclass(frozen=True)
class AudioCue:
    cue_id:str; kind:AudioCueKind; trigger_event:str; asset_ref:str|None=None; text_ref:str|None=None; duck_narration:bool=False
    def validate(self):
        require_id(self.cue_id,'GAME_AUDIO_CUE_ID');require_id(self.trigger_event,'GAME_AUDIO_TRIGGER')
        if type(self.kind) is not AudioCueKind:raise GameContractError('GAME_AUDIO_KIND')
        if not (self.asset_ref or self.text_ref):raise GameContractError('GAME_AUDIO_SOURCE')
        if self.asset_ref:require_id(self.asset_ref,'GAME_AUDIO_ASSET')
        if self.text_ref:require_id(self.text_ref,'GAME_AUDIO_TEXT')
        return self
@dataclass(frozen=True)
class AudioExperienceContract:
    cues:tuple[AudioCue,...]=()
    def validate(self):
        require_unique_ids([c.cue_id for c in self.cues],'GAME_AUDIO_DUPLICATE')
        for c in self.cues:c.validate()
        return self
