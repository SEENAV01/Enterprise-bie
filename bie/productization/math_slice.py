"""Task031 six-stage composition; canonical stores/orchestrator/fencing only."""
from bie.infrastructure.execution_graph import default_enterprise_graph
from bie.infrastructure.orchestrator import StageExecutionResult, StageExecutionFailure
from .durable_slice import KnowledgeProducerService
from .reasoning_slice import ReasoningProducerService
from .contracts import require, ProducerError, digest
from .pr_reasoning import verify_prerequisite
from .math_evidence import (PROFILE, SCHEMA, POLICY, profile_config, binding,
    math_artifact, verify_math, reasoning_artifact, verify_reasoning)

STAGES=("SOURCE","DOCUMENT_INTELLIGENCE","KNOWLEDGE","PREREQUISITE","MATH","REASONING")


class MathProducerService(ReasoningProducerService):
    stages=STAGES
    profile=PROFILE
    capability="producer:"+PROFILE
    graph_for=staticmethod(default_enterprise_graph)
    downstream=tuple(s for s in default_enterprise_graph().stages if s not in STAGES)
    config_for=staticmethod(profile_config)
    blocked_codes=frozenset({"provider_unavailable","math_review_required"})

    def configuration(self,run_id,tenant):
        # Task029/030 continuation records cannot silently adopt the v2 scope.
        require(run_id+"-continuation" not in self.persistence.artifacts_for_run(run_id),
                "producer_profile_scope_mismatch")
        return KnowledgeProducerService.configuration(self,run_id,tenant)

    def continue_completed(self,run_id,tenant):
        raise ProducerError("new_versioned_admission_required")

    def verify_terminal_for_ack(self,run_id,tenant):
        self.status(run_id,tenant)

    def pr_context(self,run_id,config,kid,khash,attempt):
        return binding(run_id,config["source_sha256"],kid,khash,attempt)

    def upstream(self,run_id,config):
        document,knowledge,kid,khash=self.inputs(run_id,config)
        did,dr=self.stage_ref(run_id,"DOCUMENT_INTELLIGENCE")
        pid,pr=self.stage_ref(run_id,"PREREQUISITE")
        require(kid in pr.parent_artifact_ids,"upstream_identity")
        attempt=self.persistence.load_run_state(run_id)["stages"]["PREREQUISITE"]["attempts"][-1]["attempt"]
        prerequisite=verify_prerequisite(self.read(run_id,pid),knowledge,
            self.pr_context(run_id,config,kid,khash,attempt))
        return document,knowledge,prerequisite,did,kid,khash,pid

    def verified_math(self,run_id,config):
        document,k,p,did,kid,khash,pid=self.upstream(run_id,config)
        mid,mr=self.stage_ref(run_id,"MATH")
        require({did,kid,pid}<=set(mr.parent_artifact_ids),"upstream_identity")
        attempt=self.persistence.load_run_state(run_id)["stages"]["MATH"]["attempts"][-1]["attempt"]
        return mid,verify_math(self.read(run_id,mid),document,k,p,
            self.pr_context(run_id,config,kid,khash,attempt),did,pid)

    def executor(self,config,stage,lease):
        if stage not in ("MATH","REASONING"):return super().executor(config,stage,lease)
        def execute(context):
            try:
                run=context.run_id
                document,k,p,did,kid,khash,pid=self.upstream(run,config)
                b=self.pr_context(run,config,kid,khash,context.attempt)
                if stage=="MATH":
                    require(context.input_artifact_refs==[did,kid,pid],"upstream_identity")
                    value=math_artifact(document,k,p,b,did,pid)
                    verify_math(value,document,k,p,b,did,pid)
                    kind="math.evidence"
                else:
                    mid,m=self.verified_math(run,config)
                    require(context.input_artifact_refs==[kid,pid,mid],"upstream_identity")
                    value=reasoning_artifact(k,p,m,b,pid,mid)
                    verify_reasoning(value,k,p,m,b,pid,mid)
                    kind="reasoning.decision_set"
                candidate=self.put(run,stage,kind+".candidates",value,context.input_artifact_refs)
                output=self.put(run,stage,kind,value,context.input_artifact_refs+[candidate])
                receipt=dict(schema="bie.producer.stage-evidence/1",run_id=run,stage=stage,
                    profile=self.profile,attempt=context.attempt,source_sha256=config["source_sha256"],
                    input_artifact_ids=context.input_artifact_refs,
                    input_sha256=[self.record(run,r).blob_digest for r in context.input_artifact_refs],
                    output_artifact_id=output,output_sha256=digest(value),candidate_artifact_id=candidate,
                    policy=POLICY,validation="PASS",grounding="EXACT_SOURCE_BOUND",
                    schema_version=value["schema"],fencing_epoch=lease.epoch,
                    evidence_kind="TECHNICAL_SOURCE_DERIVED",live_provider_executed=False,
                    academic_acceptance=False,product_accepted=False)
                if stage=="MATH":receipt.update(applicability=value["applicability"],engine_identity=value["engine_identity"])
                else:receipt.update(math_artifact_id=mid,math_sha256=digest(m))
                evidence=self.put(run,stage,"producer.evidence",receipt,context.input_artifact_refs+[output],True)
                self.leases.assert_active(lease)
                if stage=="MATH" and value["applicability"]=="REVIEW_REQUIRED":
                    raise StageExecutionFailure(["math_review_required"],[evidence],"PROD031")
                return StageExecutionResult([output],[evidence])
            except StageExecutionFailure:raise
            except Exception as exc:
                code=exc.code if isinstance(exc,ProducerError) else "math_execution_failed"
                ev=self.put(context.run_id,stage,"producer.failure",dict(schema="bie.producer.failure/1",
                    code=code,stage=stage,attempt=context.attempt,source_sha256=config["source_sha256"],product_accepted=False),evidence=True)
                raise StageExecutionFailure([code],[ev],"PROD031") from None
        return execute

    def status(self,run_id,tenant):
        result=KnowledgeProducerService.status(self,run_id,tenant)
        config=self.configuration(run_id,tenant);saved=self.persistence.load_run_state(run_id)
        result.update(prerequisite=None,math=None,reasoning=None,
            safe_diagnostics={s:a["attempts"][-1]["diagnostics"] for s,a in saved["stages"].items() if a["attempts"][-1]["diagnostics"]})
        if result["stages"]["PREREQUISITE"]!="SUCCEEDED":return result
        doc,k,p,did,kid,khash,pid=self.upstream(run_id,config)
        result["prerequisite"]=dict(artifact_id=pid,sha256=digest(p),edge_count=len(p["edges"]),
            node_count=len(p["nodes"]),review_count=len(p["review"]),validation="PASS")
        mid=m=None
        if result["stages"]["MATH"]=="SUCCEEDED":mid,m=self.verified_math(run_id,config)
        elif result["stages"]["MATH"]=="BLOCKED":
            a=saved["stages"]["MATH"]["attempts"][-1]
            for ev in a["evidence_refs"]:
                receipt=self.read(run_id,ev)
                if receipt.get("applicability")=="REVIEW_REQUIRED":
                    mid=receipt["output_artifact_id"]
                    require(self.record(run_id,mid).stage_id=="MATH","foreign_math_artifact")
                    m=verify_math(self.read(run_id,mid),doc,k,p,self.pr_context(run_id,config,kid,khash,a["attempt"]),did,pid)
        if m is not None:
            result["math"]=dict(artifact_id=mid,sha256=digest(m),applicability=m["applicability"],
                equation_count=len(m["equations"]),derivation_step_count=len(m["derivation_steps"]),
                unit_check_count=sum(e["proof"]=="EXACT_EXPLICIT_UNIT_CONVERSION" for e in m["equations"]),
                review_count=len(m["findings"]),schema=SCHEMA,validation="PASS",semantic_acceptance=False)
        if result["stages"]["REASONING"]=="SUCCEEDED":
            require(m is not None,"math_evidence_required")
            rid,rr=self.stage_ref(run_id,"REASONING")
            require({kid,pid,mid}<=set(rr.parent_artifact_ids),"upstream_identity")
            attempt=saved["stages"]["REASONING"]["attempts"][-1]["attempt"]
            r=verify_reasoning(self.read(run_id,rid),k,p,m,
                self.pr_context(run_id,config,kid,khash,attempt),pid,mid)
            result["reasoning"]=dict(artifact_id=rid,sha256=rr.blob_digest,math_artifact_id=mid,
                math_sha256=digest(m),decision_count=len(r["decisions"]),executed_types=r["executed_types"],
                not_executed_types=r["not_executed_types"],requires_review=True,validation="PASS")
        return result
