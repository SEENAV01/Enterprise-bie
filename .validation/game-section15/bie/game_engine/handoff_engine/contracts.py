from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from ..ids import require_id,require_text,require_sha256
from ..errors import GameContractError
from ..provenance import ProvenanceBundle
from ..visual import VisualKind
from ..director_engine.contracts import DirectorPlan,DirectorContext
from ..strategy_engine.contracts import StrategySignalBundle
from ..compiler_engine.contracts import ScoringPolicy,MasteryPolicy
from ..document import GameDocument
from ..canonical import fingerprint

@dataclass(frozen=True)
class ObjectiveTextMaterial:
    objective_id:str; level_title:str; level_purpose:str; challenge_title:str; mission_prompt:str; success_message:str; failure_message:str; explanation:str; accessible_description:str
    def validate(self):
        require_id(self.objective_id,'GAME_MAT_OBJECTIVE_ID')
        for v,c in ((self.level_title,'GAME_MAT_LEVEL_TITLE'),(self.level_purpose,'GAME_MAT_LEVEL_PURPOSE'),(self.challenge_title,'GAME_MAT_CHALLENGE_TITLE'),(self.mission_prompt,'GAME_MAT_MISSION'),(self.success_message,'GAME_MAT_SUCCESS'),(self.failure_message,'GAME_MAT_FAILURE'),(self.explanation,'GAME_MAT_EXPLANATION'),(self.accessible_description,'GAME_MAT_ACCESSIBLE_DESCRIPTION')):require_text(v,c)
        if self.success_message.strip()==self.failure_message.strip():raise GameContractError('GAME_MAT_FEEDBACK_NOT_DISTINCT')
        return self

@dataclass(frozen=True)
class ObjectiveVisualMaterial:
    objective_id:str; kind:VisualKind; semantic_role:str; source_ref:str; accessible_description:str
    def validate(self):
        require_id(self.objective_id,'GAME_MAT_VISUAL_OBJECTIVE');require_id(self.semantic_role,'GAME_MAT_VISUAL_ROLE');require_id(self.source_ref,'GAME_MAT_VISUAL_SOURCE');require_text(self.accessible_description,'GAME_MAT_VISUAL_DESCRIPTION')
        if type(self.kind) is not VisualKind:raise GameContractError('GAME_MAT_VISUAL_KIND')
        return self

@dataclass(frozen=True)
class MaterializationPolicy:
    game_ir_version:str='2.0.0'; scoring_policy_id:str='policy:game:score'; mastery_policy_id:str='policy:game:mastery'; telemetry_allowlist:tuple[str,...]=('game_started','challenge_completed','mechanic_completed'); compile_profile:str='studio-enterprise-v1'; product_accepted:bool=False
    def validate(self):
        require_id(self.scoring_policy_id,'GAME_MAT_SCORING_ID');require_id(self.mastery_policy_id,'GAME_MAT_MASTERY_ID');require_id(self.compile_profile,'GAME_MAT_COMPILE_PROFILE')
        if not self.telemetry_allowlist or len(self.telemetry_allowlist)!=len(set(self.telemetry_allowlist)):raise GameContractError('GAME_MAT_TELEMETRY_ALLOWLIST')
        if self.product_accepted:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self

@dataclass(frozen=True)
class MaterializationInputs:
    plan:DirectorPlan; signals:StrategySignalBundle; texts:Mapping[str,ObjectiveTextMaterial]; visuals:Mapping[str,ObjectiveVisualMaterial]; provenance:ProvenanceBundle; policy:MaterializationPolicy=MaterializationPolicy()
    def validate(self):
        self.plan.validate();self.signals.validate();self.provenance.validate(('source','reasoning'));self.policy.validate()
        expected={x.objective_id for x in self.plan.objective_assignments}
        if set(self.texts)!=expected:raise GameContractError('GAME_MAT_TEXT_COVERAGE')
        if set(self.visuals)!=expected:raise GameContractError('GAME_MAT_VISUAL_COVERAGE')
        for oid,v in self.texts.items():v.validate();
        for oid,v in self.visuals.items():v.validate()
        if {x.objective_id for x in self.signals.objectives}!=expected:raise GameContractError('GAME_MAT_SIGNAL_PLAN_COVERAGE')
        return self

@dataclass(frozen=True)
class MaterializationReceipt:
    receipt_id:str; plan_fingerprint:str; document_fingerprint:str; input_fingerprint:str; output_fingerprint:str; evidence_refs:tuple[str,...]; deterministic:bool=True; unresolved_fields:tuple[str,...]=(); product_accepted:bool=False
    def validate(self):
        require_id(self.receipt_id,'GAME_MAT_RECEIPT_ID')
        for h in (self.plan_fingerprint,self.document_fingerprint,self.input_fingerprint,self.output_fingerprint):
            if not isinstance(h,str) or not h.startswith('sha256:'):raise GameContractError('GAME_MAT_RECEIPT_HASH')
        if not self.evidence_refs or not self.deterministic or self.unresolved_fields or self.product_accepted:raise GameContractError('GAME_MAT_RECEIPT_SCOPE')
        return self

@dataclass(frozen=True)
class MaterializedGame:
    document:GameDocument; text_catalog:Mapping[str,str]; scoring_policies:Mapping[str,ScoringPolicy]; mastery_policies:Mapping[str,MasteryPolicy]; runtime_capabilities:tuple[str,...]; telemetry_allowlist:tuple[str,...]; receipt:MaterializationReceipt; product_accepted:bool=False
    def validate(self):
        self.document.validate();self.receipt.validate()
        if not self.text_catalog or not self.scoring_policies or not self.mastery_policies or not self.runtime_capabilities or not self.telemetry_allowlist:raise GameContractError('GAME_MAT_OUTPUT_INCOMPLETE')
        for p in self.scoring_policies.values():p.validate()
        for p in self.mastery_policies.values():p.validate()
        if self.product_accepted:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self

@dataclass(frozen=True)
class EvidenceDigest:
    evidence_id:str; locator:str; sha256:str; role:str
    def validate(self):require_id(self.evidence_id,'GAME_UPSTREAM_EVIDENCE_ID');require_id(self.locator,'GAME_UPSTREAM_EVIDENCE_LOCATOR');require_sha256(self.sha256,'GAME_UPSTREAM_EVIDENCE_HASH');return self

@dataclass(frozen=True)
class CanonicalAdapterResult:
    signals:StrategySignalBundle; director_context:DirectorContext; upstream_fingerprint:str; canonical_blob_ids:tuple[tuple[str,str],...]; evidence_ids:tuple[str,...]; product_accepted:bool=False
    def validate(self):
        self.signals.validate();self.director_context.validate()
        if not self.upstream_fingerprint.startswith('sha256:') or not self.canonical_blob_ids or not self.evidence_ids or self.product_accepted:raise GameContractError('GAME_UPSTREAM_ADAPTER_SCOPE')
        return self
