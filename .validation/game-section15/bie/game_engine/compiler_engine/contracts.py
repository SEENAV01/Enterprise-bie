from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping
from ..canonical import fingerprint
from ..document import GameDocument
from ..mechanics_engine.semantic_events import SemanticInteractionEvent
from ..ids import require_id,require_text
from .errors import GameCompilerError

class ArtifactKind(str,Enum):
    GAME_IR='game_ir';REACT_RUNTIME='react_runtime';HTML_RUNTIME='html_runtime';STATE_MACHINE='state_machine';RULE_PROGRAM='rule_program';INTERACTION_PROGRAM='interaction_program';SCORING_PROGRAM='scoring_program';FEEDBACK_PROGRAM='feedback_program';ADAPTATION_PROGRAM='adaptation_program';TELEMETRY_PROGRAM='telemetry_program';RUNTIME_MANIFEST='runtime_manifest';SOURCE_MAP='source_map';BOOTSTRAP='bootstrap';ASSET_MANIFEST='asset_manifest';RUNTIME_CONTROLLER='runtime_controller'

@dataclass(frozen=True)
class ScoringPolicy:
    policy_id:str;correct_points:float;incorrect_points:float=0.0;hint_cost:float=0.0;floor:float=0.0;mastery_weighted:bool=True;speed_pressure:bool=False
    def validate(self):
        require_id(self.policy_id,'GAME_COMP_SCORING_ID')
        for x in (self.correct_points,self.incorrect_points,self.hint_cost,self.floor):
            if type(x) not in (int,float):raise GameCompilerError('GAME_COMP_SCORING_NUMBER')
        if self.correct_points<=0 or self.hint_cost<0 or self.floor<0:raise GameCompilerError('GAME_COMP_SCORING_RANGE')
        if self.speed_pressure:raise GameCompilerError('GAME_COMP_SPEED_PRESSURE_FORBIDDEN')
        if self.mastery_weighted is not True:raise GameCompilerError('GAME_COMP_MASTERY_WEIGHTING_REQUIRED')
        return self

@dataclass(frozen=True)
class MasteryPolicy:
    policy_id:str;threshold:float;minimum_attempts:int=1
    def validate(self):
        require_id(self.policy_id,'GAME_COMP_MASTERY_ID')
        if type(self.threshold) not in (int,float) or not 0<self.threshold<=1:raise GameCompilerError('GAME_COMP_MASTERY_THRESHOLD')
        if type(self.minimum_attempts) is not int or self.minimum_attempts<1:raise GameCompilerError('GAME_COMP_MASTERY_ATTEMPTS')
        return self

@dataclass(frozen=True)
class AssetDescriptor:
    asset_ref:str;media_type:str;content_sha256:str;alt_text:str|None=None;rights_ref:str|None=None;license_id:str|None=None;attribution:str|None=None;source_ref:str|None=None
    def validate(self):
        require_id(self.asset_ref,'GAME_COMP_ASSET_REF');require_text(self.media_type,'GAME_COMP_ASSET_MEDIA')
        if len(self.content_sha256)!=64 or any(c not in '0123456789abcdef' for c in self.content_sha256):raise GameCompilerError('GAME_COMP_ASSET_HASH')
        rights=(self.rights_ref,self.license_id,self.attribution,self.source_ref)
        if any(x is not None for x in rights):
            if not all(x is not None for x in rights):raise GameCompilerError('GAME_COMP_ASSET_RIGHTS_PARTIAL')
            require_id(self.rights_ref,'GAME_COMP_ASSET_RIGHTS');require_id(self.license_id,'GAME_COMP_ASSET_LICENSE');require_text(self.attribution,'GAME_COMP_ASSET_ATTRIBUTION');require_id(self.source_ref,'GAME_COMP_ASSET_SOURCE')
        return self

@dataclass(frozen=True)
class CompilerSecurityPolicy:
    allow_remote_network:bool=False;allow_inline_script:bool=False;allow_eval:bool=False;allow_dynamic_import:bool=False;telemetry_raw_text:bool=False;product_accepted:bool=False
    def validate(self):
        if any((self.allow_remote_network,self.allow_inline_script,self.allow_eval,self.allow_dynamic_import,self.telemetry_raw_text,self.product_accepted)):raise GameCompilerError('GAME_COMP_SECURITY_WEAKENED')
        return self

@dataclass(frozen=True)
class CompilerContext:
    document:GameDocument;text_catalog:Mapping[str,str];scoring_policies:Mapping[str,ScoringPolicy];mastery_policies:Mapping[str,MasteryPolicy];assets:Mapping[str,AssetDescriptor];mechanic_events:tuple[SemanticInteractionEvent,...];runtime_capabilities:tuple[str,...];telemetry_allowlist:tuple[str,...];security:CompilerSecurityPolicy=CompilerSecurityPolicy();compile_profile:str='studio-enterprise-v1';product_accepted:bool=False;experience_profile:object|None=None
    def validate(self):
        self.document.validate();self.security.validate();require_id(self.compile_profile,'GAME_COMP_PROFILE')
        if not self.text_catalog:raise GameCompilerError('GAME_COMP_TEXT_CATALOG_REQUIRED')
        for k,v in self.text_catalog.items():require_id(k,'GAME_COMP_TEXT_REF');require_text(v,'GAME_COMP_TEXT_VALUE')
        if not self.scoring_policies or not self.mastery_policies:raise GameCompilerError('GAME_COMP_POLICY_REQUIRED')
        for p in self.scoring_policies.values():p.validate()
        for p in self.mastery_policies.values():p.validate()
        for a in self.assets.values():a.validate()
        if self.experience_profile is not None:
            self.experience_profile.validate()
            rights=self.experience_profile.rights_map()
            missing=[ref for ref in self.assets if ref not in rights]
            if missing:raise GameCompilerError('GAME_COMP_ASSET_RIGHTS_MISSING',','.join(sorted(missing)))
            for ref,a in self.assets.items():
                r=rights[ref]
                if (a.rights_ref,a.license_id,a.attribution,a.source_ref)!=(r.rights_ref,r.license_id,r.attribution,r.source_ref):raise GameCompilerError('GAME_COMP_ASSET_RIGHTS_MISMATCH',ref)
        for e in self.mechanic_events:e.validate()
        if len(set(self.telemetry_allowlist))!=len(self.telemetry_allowlist):raise GameCompilerError('GAME_COMP_TELEMETRY_ALLOWLIST_DUPLICATE')
        if self.product_accepted:raise GameCompilerError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self

@dataclass(frozen=True)
class CompiledArtifact:
    kind:ArtifactKind;path:str;media_type:str;content:str;sha256:str;source_refs:tuple[str,...];product_accepted:bool=False
    def validate(self):
        if type(self.kind) is not ArtifactKind:raise GameCompilerError('GAME_COMP_ARTIFACT_KIND')
        if not self.path or self.path.startswith('/') or '..' in self.path.split('/'):raise GameCompilerError('GAME_COMP_ARTIFACT_PATH')
        require_text(self.media_type,'GAME_COMP_ARTIFACT_MEDIA')
        actual=hashlib_sha(self.content)
        if actual!=self.sha256:raise GameCompilerError('GAME_COMP_ARTIFACT_HASH')
        if not self.source_refs:raise GameCompilerError('GAME_COMP_ARTIFACT_PROVENANCE')
        if self.product_accepted:raise GameCompilerError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self

def hashlib_sha(content:str)->str:
    import hashlib
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def artifact(kind:ArtifactKind,path:str,media_type:str,content:str,source_refs:tuple[str,...])->CompiledArtifact:
    return CompiledArtifact(kind,path,media_type,content,hashlib_sha(content),tuple(sorted(set(source_refs))),False).validate()

@dataclass(frozen=True)
class CompileReceipt:
    receipt_id:str;input_fingerprint:str;bundle_fingerprint:str;artifact_hashes:tuple[tuple[str,str],...];compiler_profile:str;deterministic:bool=True;security_verified:bool=True;product_accepted:bool=False
    def validate(self):
        require_id(self.receipt_id,'GAME_COMP_RECEIPT_ID')
        if not self.input_fingerprint.startswith('sha256:') or not self.bundle_fingerprint.startswith('sha256:'):raise GameCompilerError('GAME_COMP_RECEIPT_HASH')
        if not self.artifact_hashes or not self.deterministic or not self.security_verified or self.product_accepted:raise GameCompilerError('GAME_COMP_RECEIPT_SCOPE')
        return self

@dataclass(frozen=True)
class CompiledBundle:
    artifacts:tuple[CompiledArtifact,...];receipt:CompileReceipt;product_accepted:bool=False
    def validate(self):
        if not self.artifacts:raise GameCompilerError('GAME_COMP_BUNDLE_EMPTY')
        paths=[a.path for a in self.artifacts]
        if len(paths)!=len(set(paths)):raise GameCompilerError('GAME_COMP_ARTIFACT_DUPLICATE_PATH')
        [a.validate() for a in self.artifacts];self.receipt.validate()
        if self.product_accepted:raise GameCompilerError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self
