from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping
import re
from ..errors import GameContractError
from ..ids import require_id, require_text

_RTL_LANGS={'ar','fa','he','ur'}
_LOCALE_RE=re.compile(r'^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$')

@dataclass(frozen=True)
class LocaleCatalog:
    locale:str
    messages:Mapping[str,str]
    direction:str='ltr'
    def validate(self):
        if not isinstance(self.locale,str) or not _LOCALE_RE.fullmatch(self.locale): raise GameContractError('GAME_RUNTIME_LOCALE')
        lang=self.locale.split('-')[0].lower(); expected='rtl' if lang in _RTL_LANGS else 'ltr'
        if self.direction not in {'ltr','rtl'} or self.direction!=expected: raise GameContractError('GAME_RUNTIME_DIRECTION')
        if not self.messages: raise GameContractError('GAME_RUNTIME_MESSAGES_REQUIRED')
        for k,v in self.messages.items(): require_id(k,'GAME_RUNTIME_MESSAGE_ID'); require_text(v,'GAME_RUNTIME_MESSAGE_TEXT')
        return self

@dataclass(frozen=True)
class RightsRecord:
    asset_ref:str; rights_ref:str; license_id:str; attribution:str; source_ref:str
    def validate(self):
        for v,c in ((self.asset_ref,'GAME_RIGHTS_ASSET'),(self.rights_ref,'GAME_RIGHTS_REF'),(self.license_id,'GAME_RIGHTS_LICENSE'),(self.source_ref,'GAME_RIGHTS_SOURCE')): require_id(v,c)
        require_text(self.attribution,'GAME_RIGHTS_ATTRIBUTION'); return self

@dataclass(frozen=True)
class AccessibilityRuntimePolicy:
    keyboard_required:bool=True; focus_visible_required:bool=True; live_region_required:bool=True; reduced_motion_supported:bool=True; min_touch_target_px:int=44
    def validate(self):
        if not all((self.keyboard_required,self.focus_visible_required,self.live_region_required,self.reduced_motion_supported)): raise GameContractError('GAME_RUNTIME_ACCESSIBILITY_WEAKENED')
        if type(self.min_touch_target_px) is not int or self.min_touch_target_px<44: raise GameContractError('GAME_RUNTIME_TOUCH_TARGET')
        return self

@dataclass(frozen=True)
class AudioRuntimePolicy:
    user_activation_required:bool=True; captions_required:bool=True; max_sync_drift_ms:int=120
    def validate(self):
        if not self.user_activation_required or not self.captions_required: raise GameContractError('GAME_AUDIO_RUNTIME_POLICY_WEAKENED')
        if type(self.max_sync_drift_ms) is not int or not 20<=self.max_sync_drift_ms<=250: raise GameContractError('GAME_AUDIO_SYNC_TOLERANCE')
        return self


@dataclass(frozen=True)
class AudioSyncRecord:
    cue_id:str; start_ms:int; end_ms:int; trigger_event:str
    def validate(self):
        require_id(self.cue_id,'GAME_AUDIO_SYNC_CUE');require_id(self.trigger_event,'GAME_AUDIO_SYNC_TRIGGER')
        if type(self.start_ms) is not int or type(self.end_ms) is not int or self.start_ms<0 or self.end_ms<=self.start_ms: raise GameContractError('GAME_AUDIO_SYNC_RANGE')
        return self

@dataclass(frozen=True)
class PerformanceBudget:
    max_initial_js_bytes:int=2_000_000; max_package_bytes:int=25_000_000; max_first_render_ms:int=1500; max_interaction_latency_ms:int=120; max_dom_entities:int=500; mobile_viewport_width:int=360; tablet_viewport_width:int=768
    def validate(self):
        for v in (self.max_initial_js_bytes,self.max_package_bytes,self.max_first_render_ms,self.max_interaction_latency_ms,self.max_dom_entities,self.mobile_viewport_width,self.tablet_viewport_width):
            if type(v) is not int or v<=0: raise GameContractError('GAME_RUNTIME_PERFORMANCE_BUDGET')
        if self.mobile_viewport_width<320 or self.tablet_viewport_width<600: raise GameContractError('GAME_RUNTIME_VIEWPORT_BUDGET')
        return self

@dataclass(frozen=True)
class RuntimeExperienceProfile:
    primary_locale:str
    catalogs:tuple[LocaleCatalog,...]
    rights:tuple[RightsRecord,...]=()
    audio_sync:tuple[AudioSyncRecord,...]=()
    accessibility:AccessibilityRuntimePolicy=AccessibilityRuntimePolicy()
    audio:AudioRuntimePolicy=AudioRuntimePolicy()
    performance:PerformanceBudget=PerformanceBudget()
    product_accepted:bool=False
    def validate(self):
        if self.product_accepted: raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        self.accessibility.validate(); self.audio.validate(); self.performance.validate()
        if not self.catalogs: raise GameContractError('GAME_RUNTIME_CATALOG_REQUIRED')
        by={c.locale:c for c in self.catalogs}
        if len(by)!=len(self.catalogs) or self.primary_locale not in by: raise GameContractError('GAME_RUNTIME_CATALOG_PRIMARY')
        for c in self.catalogs: c.validate()
        rs={r.asset_ref:r for r in self.rights}
        if len(rs)!=len(self.rights): raise GameContractError('GAME_RIGHTS_DUPLICATE')
        for r in self.rights:r.validate()
        ids=[x.cue_id for x in self.audio_sync]
        if len(ids)!=len(set(ids)): raise GameContractError('GAME_AUDIO_SYNC_DUPLICATE')
        for x in self.audio_sync:x.validate()
        return self
    def catalog(self)->LocaleCatalog:
        self.validate(); return {c.locale:c for c in self.catalogs}[self.primary_locale]
    def rights_map(self):
        self.validate(); return {r.asset_ref:r for r in self.rights}
    def audio_sync_map(self):
        self.validate(); return {x.cue_id:x for x in self.audio_sync}
