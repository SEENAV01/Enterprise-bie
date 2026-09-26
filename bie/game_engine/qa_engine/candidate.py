from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from ..ids import require_id,require_text
from ..canonical import fingerprint
from ..errors import GameContractError
from ..strategy_engine.contracts import StrategySignalBundle
from ..director_engine.contracts import DirectorPlan
from ..document import GameDocument
from ..compiler_engine.contracts import CompiledBundle,CompilerContext
from ..build_runtime_engine.pipeline import RuntimeBuildResult
from ..state_engine.reachability import TransitionSystem

@dataclass(frozen=True)
class CandidateBenchmarkRecord:
    domain:str;strategy:str;mechanics:tuple[str,...];expected_mechanic:str;plan_fingerprint:str;document_fingerprint:str;evidence_refs:tuple[str,...]
    def validate(self):
        require_id(self.domain,'GAME_QA_BENCHMARK_DOMAIN');require_id(self.strategy,'GAME_QA_BENCHMARK_STRATEGY');require_id(self.expected_mechanic,'GAME_QA_BENCHMARK_EXPECTED');
        if not self.mechanics or self.expected_mechanic not in self.mechanics or not self.plan_fingerprint.startswith('sha256:') or not self.document_fingerprint.startswith('sha256:') or not self.evidence_refs:raise GameContractError('GAME_QA_BENCHMARK_RECORD')
        return self

@dataclass(frozen=True)
class CandidateGameEvidence:
    candidate_id:str;signals:StrategySignalBundle;plans:tuple[DirectorPlan,...];document:GameDocument;compiler_context:CompilerContext;compiled_bundle:CompiledBundle;runtime_result:RuntimeBuildResult;transition_system:TransitionSystem;start_state_id:str;challenge_targets:tuple[tuple[str,str],...];goal_state_ids:tuple[str,...];benchmark_records:tuple[CandidateBenchmarkRecord,...];source_root:Path;evidence_refs:tuple[str,...];product_accepted:bool=False
    def validate(self):
        require_id(self.candidate_id,'GAME_QA_CANDIDATE_ID');self.signals.validate();self.document.validate();self.compiler_context.validate();self.compiled_bundle.validate()
        if not self.plans:raise GameContractError('GAME_QA_CANDIDATE_PLANS_REQUIRED')
        for p in self.plans:p.validate()
        self.transition_system.validate();require_id(self.start_state_id,'GAME_QA_START_STATE')
        if not self.challenge_targets or not self.goal_state_ids:raise GameContractError('GAME_QA_STATE_TARGETS_REQUIRED')
        if not self.benchmark_records:raise GameContractError('GAME_QA_BENCHMARK_RECORDS_REQUIRED')
        for b in self.benchmark_records:b.validate()
        if not isinstance(self.source_root,Path) or not self.source_root.exists() or not self.evidence_refs or self.product_accepted:raise GameContractError('GAME_QA_CANDIDATE_SCOPE')
        # Cross-bind supplied artifacts so QA cannot mix evidence from different games.
        if self.compiler_context.document.fingerprint()!=self.document.fingerprint() or self.compiled_bundle.receipt.input_fingerprint!=fingerprint(self.compiler_context):raise GameContractError('GAME_QA_CANDIDATE_COMPILE_BINDING')
        if self.runtime_result.manifest.compiler_bundle_fingerprint!=self.compiled_bundle.receipt.bundle_fingerprint:raise GameContractError('GAME_QA_CANDIDATE_RUNTIME_BINDING')
        plan_objs={o.objective_id for p in self.plans for o in p.objective_assignments};signal_objs={o.objective_id for o in self.signals.objectives}
        if plan_objs!=signal_objs:raise GameContractError('GAME_QA_CANDIDATE_OBJECTIVE_BINDING')
        return self
    def fingerprint(self):self.validate();return fingerprint({'candidate_id':self.candidate_id,'signals':self.signals,'plans':tuple(p.plan_fingerprint for p in self.plans),'document':self.document.fingerprint(),'compiler_input':fingerprint(self.compiler_context),'compiled':self.compiled_bundle.receipt.bundle_fingerprint,'runtime':self.runtime_result.manifest.package_fingerprint,'start':self.start_state_id,'targets':self.challenge_targets,'goals':self.goal_state_ids,'benchmarks':self.benchmark_records,'evidence':self.evidence_refs})
