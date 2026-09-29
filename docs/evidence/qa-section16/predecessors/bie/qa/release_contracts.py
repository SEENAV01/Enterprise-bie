from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone

class ReleaseContractError(ValueError):
    pass

GATE_MODES={"REQUIRED","OPTIONAL","NOT_APPLICABLE"}
EVIDENCE_STATUSES={"PASS","FAIL","ERROR","SKIPPED"}
RELEASE_STATUSES={"BLOCKED","READY_FOR_REVIEW","RELEASE_CANDIDATE","SUCCESS"}

ALWAYS_REQUIRED={"lineage_integrity","source_grounding"}

VIDEO_RUNTIME_REQUIRED={"code_compile","video_render","rendered_frame_inspection"}
GAME_RUNTIME_REQUIRED={"game_build","game_runtime","game_learning_alignment"}

@dataclass(frozen=True)
class GateRequirement:
    gate_id:str
    mode:str
    remediation_layer:str
    description:str=""
    min_evidence_count:int=1

    def validate(self)->None:
        if not self.gate_id: raise ReleaseContractError("gate_id required")
        if self.mode not in GATE_MODES: raise ReleaseContractError("invalid gate mode")
        if not self.remediation_layer: raise ReleaseContractError("remediation_layer required")
        if self.min_evidence_count<0: raise ReleaseContractError("min_evidence_count cannot be negative")
        if self.mode=="REQUIRED" and self.min_evidence_count<1:
            raise ReleaseContractError("required gate needs evidence")

@dataclass(frozen=True)
class ReleasePolicy:
    policy_id:str
    policy_version:str
    enable_video:bool
    enable_game:bool
    gates:List[GateRequirement]
    require_human_review:bool=False

    def validate(self)->None:
        if not self.policy_id or not self.policy_version: raise ReleaseContractError("policy identity required")
        ids=[g.gate_id for g in self.gates]
        if len(ids)!=len(set(ids)): raise ReleaseContractError("duplicate gate_id")
        for g in self.gates:g.validate()
        by={g.gate_id:g for g in self.gates}
        for gate in ALWAYS_REQUIRED:
            if gate not in by or by[gate].mode!="REQUIRED":
                raise ReleaseContractError(f"{gate} must be REQUIRED")
        if self.enable_video:
            for gate in VIDEO_RUNTIME_REQUIRED:
                if gate not in by or by[gate].mode!="REQUIRED":
                    raise ReleaseContractError(f"video policy requires {gate}")
        if self.enable_game:
            for gate in GAME_RUNTIME_REQUIRED:
                if gate not in by or by[gate].mode!="REQUIRED":
                    raise ReleaseContractError(f"game policy requires {gate}")

@dataclass(frozen=True)
class GateEvidence:
    evidence_id:str
    gate_id:str
    status:str
    evaluator:str
    evaluator_version:str
    inspected_artifact_refs:List[str]
    evidence_artifact_refs:List[str]
    measurements:Dict[str,Any]=field(default_factory=dict)
    summary:str=""
    diagnostics:List[str]=field(default_factory=list)
    remediation_layer:Optional[str]=None
    created_at:str=field(default_factory=lambda:datetime.now(timezone.utc).isoformat())

    def validate(self)->None:
        if not self.evidence_id or not self.gate_id: raise ReleaseContractError("evidence identity required")
        if self.status not in EVIDENCE_STATUSES: raise ReleaseContractError("invalid evidence status")
        if not self.evaluator or not self.evaluator_version: raise ReleaseContractError("evaluator identity required")
        if not self.inspected_artifact_refs: raise ReleaseContractError("evidence must identify inspected artifacts")
        if not self.evidence_artifact_refs: raise ReleaseContractError("evidence must reference evidence artifact")
        if self.status in {"FAIL","ERROR"} and not (self.diagnostics or self.summary):
            raise ReleaseContractError("failure evidence requires diagnostics/summary")

@dataclass(frozen=True)
class GateResult:
    gate_id:str
    mode:str
    status:str
    evidence_ids:List[str]
    remediation_layer:str
    diagnostics:List[str]=field(default_factory=list)

@dataclass(frozen=True)
class ReleaseDecision:
    release_status:str
    gate_results:List[GateResult]
    blocking_gates:List[str]
    review_required:bool
    summary:str

class ReleaseEvaluator:
    @staticmethod
    def evaluate(policy:ReleasePolicy, evidence:List[GateEvidence])->ReleaseDecision:
        policy.validate()
        for e in evidence:e.validate()
        by_gate:Dict[str,List[GateEvidence]]={}
        for e in evidence: by_gate.setdefault(e.gate_id,[]).append(e)

        results=[]
        blockers=[]
        for req in policy.gates:
            evs=by_gate.get(req.gate_id,[])
            if req.mode=="NOT_APPLICABLE":
                results.append(GateResult(req.gate_id,req.mode,"SKIPPED",[],req.remediation_layer))
                continue

            if req.mode=="REQUIRED" and len(evs)<req.min_evidence_count:
                blockers.append(req.gate_id)
                results.append(GateResult(req.gate_id,req.mode,"ERROR",[],req.remediation_layer,["missing required evidence"]))
                continue

            if not evs:
                results.append(GateResult(req.gate_id,req.mode,"SKIPPED",[],req.remediation_layer))
                continue

            statuses=[e.status for e in evs]
            diagnostics=[d for e in evs for d in e.diagnostics]

            if "ERROR" in statuses:
                status="ERROR"
            elif "FAIL" in statuses:
                status="FAIL"
            elif req.mode=="REQUIRED" and "SKIPPED" in statuses:
                status="ERROR"
                diagnostics.append("required gate contains SKIPPED evidence")
            elif "PASS" in statuses:
                status="PASS"
            else:
                status="SKIPPED"

            if req.mode=="REQUIRED" and status!="PASS":
                blockers.append(req.gate_id)

            results.append(GateResult(
                req.gate_id,req.mode,status,[e.evidence_id for e in evs],
                req.remediation_layer,diagnostics
            ))

        if blockers:
            release_status="BLOCKED"
        elif policy.require_human_review:
            release_status="READY_FOR_REVIEW"
        else:
            release_status="SUCCESS"

        return ReleaseDecision(
            release_status=release_status,
            gate_results=results,
            blocking_gates=sorted(set(blockers)),
            review_required=policy.require_human_review and not blockers,
            summary=("All required evidence-backed gates passed."
                     if release_status=="SUCCESS"
                     else f"Release blocked/reviewed: {release_status}")
        )

def enterprise_default_policy(enable_video:bool=True, enable_game:bool=True)->ReleasePolicy:
    required={
        "lineage_integrity":"INFRA",
        "source_grounding":"BI/KI/QA",
        "semantic_correctness":"KI/RE/QA",
        "prerequisite_correctness":"PR/RE/PED",
        "pedagogical_correctness":"PED",
        "director_quality":"DIR",
        "visual_quality":"VIS/DSL",
        "animation_quality":"ANI/DSL",
        "timing_audio_sync":"DIR/ANI/COMP",
        "regression":"QA",
        "reproducibility":"INFRA",
        "rights_and_asset_provenance":"INFRA/VIS",
        "security":"INFRA",
    }
    if enable_video:
        required.update({
            "code_compile":"COMP",
            "video_render":"COMP/INFRA",
            "rendered_frame_inspection":"QA/VIS",
        })
    if enable_game:
        required.update({
            "game_build":"GAME/COMP",
            "game_runtime":"GAME/QA",
            "game_learning_alignment":"GAME/PED/QA",
        })

    optional={
        "mathematical_correctness":"RE/QA",
        "accessibility":"QA/VIS/GAME",
        "performance":"INFRA/COMP",
    }

    gates=[GateRequirement(k,"REQUIRED",v) for k,v in sorted(required.items())]
    gates += [GateRequirement(k,"OPTIONAL",v) for k,v in sorted(optional.items())]
    return ReleasePolicy(
        policy_id="bie-enterprise-default",
        policy_version="1.0.0",
        enable_video=enable_video,
        enable_game=enable_game,
        gates=gates,
    )
