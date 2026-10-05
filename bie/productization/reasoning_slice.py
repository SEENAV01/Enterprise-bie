"""Versioned Task030 extension of Task029; same stores, resolver and worker fencing."""
import json
from bie.infrastructure.orchestrator import StageExecutionResult, StageExecutionFailure
from bie.infrastructure.persistence import PersistedArtifactRecord
from bie.infrastructure.execution_graph import default_enterprise_graph
from .durable_slice import KnowledgeProducerService, PersistedRunAdapter, run_identity, STAGES as ORIGINAL_STAGES
from .contracts import ProducerError, require, digest, canonical, identifier, profile_config as old_config
from .pr_reasoning import (PROFILE, PR_SCHEMA, RE_SCHEMA, POLICY, profile_config, verify_knowledge,
    binding, prerequisite_artifact, verify_prerequisite, reasoning_artifact, verify_reasoning, gateway_candidate)

STAGES=ORIGINAL_STAGES+("PREREQUISITE","REASONING")


class ReasoningProducerService(KnowledgeProducerService):
    stages=STAGES
    profile=PROFILE
    capability="producer:"+PROFILE
    downstream=tuple(s for s in default_enterprise_graph().stages if s not in STAGES)
    completion_stage="REASONING"
    config_for=staticmethod(profile_config)
    # Preserve the existing admitted Task029 tenant/key run identity.
    identity_for=staticmethod(run_identity)
    blocked_codes=frozenset({"provider_unavailable","math_evidence_required"})

    def __init__(self,*args,continuation_registry=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.continuation_registry=continuation_registry

    def configuration(self,run_id,tenant):
        identifier(run_id);identifier(tenant)
        if run_id+"-continuation" not in self.persistence.artifacts_for_run(run_id):
            return super().configuration(run_id,tenant)
        extension=self.read(run_id,run_id+"-continuation")
        require(set(extension)=={"tenant","source","source_sha256","source_bytes","privacy","rights",
            "config","run_id","fingerprint","legacy_config_sha256","knowledge_artifact_id","knowledge_sha256"},
            "continuation_contract")
        require(extension["tenant"]==tenant and extension["run_id"]==run_id and self.root.name==run_id,
            "foreign_run")
        require(extension["config"]==profile_config(extension["config"]["provider"],extension["config"]["model"]),
            "profile_config")
        require(extension["fingerprint"]==digest({k:v for k,v in extension.items() if k not in ("run_id","fingerprint")}),
            "intent_tampered")
        claim=self.idempotency.get("continuation:"+run_id)
        require(claim and claim.fingerprint==extension["fingerprint"] and claim.state=="COMPLETED"
            and claim.result_ref==run_id,"recovery_inconsistent")
        require(digest(self.read(run_id,run_id+"-config"))==extension["legacy_config_sha256"],"legacy_intent_tampered")
        require(self.record(run_id,extension["knowledge_artifact_id"]).blob_digest==extension["knowledge_sha256"],
            "knowledge_identity")
        require(set(self.persistence.load_run_state(run_id)["stages"])==set(STAGES),"admission_inconsistent")
        return extension

    def continue_completed(self,run_id,tenant):
        """Explicit versioned promotion, never silently broaden the old profile.

        Adds two canonical stage/attempt rows transactionally in the same run DB.
        The old config/attempt/artifact records are immutable and retained. An old
        profile reader rejects this explicit scope change instead of misreporting
        the newly executed stages as NOT_RUN. Repeat this admission after interruption.
        """
        self.write_guard()
        legacy=self.read(run_id,run_id+"-config")
        require(legacy["tenant"]==tenant and legacy["run_id"]==run_id and self.root.name==run_id,"foreign_run")
        require(legacy["config"]==old_config(legacy["config"]["provider"],legacy["config"]["model"]),"legacy_profile_required")
        require(legacy["fingerprint"]==digest({k:v for k,v in legacy.items() if k not in ("run_id","fingerprint")}),"intent_tampered")
        saved=self.persistence.load_run_state(run_id)
        require(set(saved["stages"]) in (set(ORIGINAL_STAGES),set(STAGES)),"admission_inconsistent")
        for stage in ORIGINAL_STAGES:
            a=saved["stages"][stage]["attempts"][-1]
            require(a["state"]=="SUCCEEDED","knowledge_not_succeeded")
            require(self.queue.get(self.task_id(run_id,stage,a["attempt"])).state=="ACKED","predecessor_not_acked")
            for ref in a["output_artifact_refs"]+a["evidence_refs"]:self.record(run_id,ref)
        document,knowledge,kid,khash=self.inputs(run_id,legacy)
        intent={k:v for k,v in legacy.items() if k not in ("run_id","fingerprint","config")}
        intent.update(config=profile_config(legacy["config"]["provider"],legacy["config"]["model"]),
            legacy_config_sha256=digest(legacy),knowledge_artifact_id=kid,knowledge_sha256=khash)
        fingerprint=digest(intent)
        claim=self.idempotency.claim("continuation:"+run_id,fingerprint,"continuation")
        if claim.state=="COMPLETED":
            require(claim.result_ref==run_id,"intent_conflict")
            self.configuration(run_id,tenant);self.schedule(run_id);return run_id
        cfg=dict(intent,run_id=run_id,fingerprint=fingerprint)
        self.put_continuation(run_id,cfg,kid)
        self.fault("after_continuation_publication")
        graph=default_enterprise_graph()
        self.write_guard()
        with self.persistence._lock,self.persistence._conn() as db:
            db.execute("BEGIN IMMEDIATE")
            for stage in STAGES[len(ORIGINAL_STAGES):]:
                preds=json.dumps(graph.stages[stage].required_predecessors,sort_keys=True)
                current=db.execute("SELECT required_predecessors_json FROM stages WHERE run_id=? AND stage_id=?",(run_id,stage)).fetchone()
                require(current is None or current[0]==preds,"stage_contract_conflict")
                if current is None:
                    db.execute("INSERT INTO stages VALUES(?,?,?)",(run_id,stage,preds))
                    db.execute("INSERT INTO attempts VALUES(?,?,1,'PENDING','[]','[]','[]','[]',NULL)",(run_id,stage))
            db.commit()
        self.fault("after_continuation_stage_admission")
        self.idempotency.complete("continuation:"+run_id,"continuation",run_id)
        self.schedule(run_id)
        return run_id

    def put_continuation(self,run_id,value,kid):
        blob=self.cas.put_bytes(canonical(value));self.write_guard()
        self.persistence.register_artifact(PersistedArtifactRecord(run_id+"-continuation","producer.continuation",
            blob.algorithm,blob.digest,blob.size,run_id,"KNOWLEDGE",False,
            {"privacy":"PRIVATE","profile":PROFILE},[run_id+"-config",kid]))

    def stage_ref(self,run_id,stage):
        saved=self.persistence.load_run_state(run_id)["stages"][stage]["attempts"][-1]
        require(saved["state"]=="SUCCEEDED" and len(saved["output_artifact_refs"])==1,"predecessor_not_succeeded")
        ref=saved["output_artifact_refs"][0];record=self.record(run_id,ref)
        require(record.stage_id==stage and record.artifact_type==default_enterprise_graph().stages[stage].emits,
            "upstream_contract")
        return ref,record

    def inputs(self,run_id,config):
        did,dr=self.stage_ref(run_id,"DOCUMENT_INTELLIGENCE")
        kid,kr=self.stage_ref(run_id,"KNOWLEDGE")
        document=self.read(run_id,did);knowledge=self.read(run_id,kid)
        require(document["source_artifact_id"]==run_id+"-source" and document["source_sha256"]==config["source_sha256"]
            and did in kr.parent_artifact_ids,"upstream_identity")
        verify_knowledge(knowledge,document)
        return document,knowledge,kid,kr.blob_digest

    def pr_context(self,run_id,config,kid,khash,attempt):
        return binding(run_id,config["source_sha256"],kid,khash,attempt)

    def executor(self,config,stage,lease):
        if stage in ORIGINAL_STAGES:return super().executor(config,stage,lease)
        def execute(context):
            try:
                document,knowledge,kid,khash=self.inputs(context.run_id,config)
                b=self.pr_context(context.run_id,config,kid,khash,context.attempt)
                if stage=="PREREQUISITE":
                    require(context.input_artifact_refs==[kid],"upstream_identity")
                    value,receipt=gateway_candidate(stage,knowledge,document,config["config"],registry=self.continuation_registry)
                    output_value=dict(b,schema=PR_SCHEMA,nodes=sorted(knowledge["nodes"]),**value)
                    verify_prerequisite(output_value,knowledge,b)
                    kind="prerequisite.graph"
                else:
                    pid,pr=self.stage_ref(context.run_id,"PREREQUISITE")
                    require(context.input_artifact_refs==[kid,pid] and kid in pr.parent_artifact_ids,"upstream_identity")
                    ps=self.persistence.load_run_state(context.run_id)["stages"]["PREREQUISITE"]["attempts"][-1]
                    prerequisite=verify_prerequisite(self.read(context.run_id,pid),knowledge,
                        self.pr_context(context.run_id,config,kid,khash,ps["attempt"]))
                    value,receipt=gateway_candidate(stage,knowledge,document,config["config"],prerequisite=prerequisite,
                        prerequisite_id=pid,registry=self.continuation_registry)
                    output_value=dict(b,schema=RE_SCHEMA,prerequisite_artifact_id=pid,
                        prerequisite_sha256=pr.blob_digest,**value)
                    verify_reasoning(output_value,knowledge,prerequisite,b,pid,document)
                    kind="reasoning.decision_set"
                candidate=self.put(context.run_id,stage,kind+".candidates",value,context.input_artifact_refs)
                output=self.put(context.run_id,stage,kind,output_value,context.input_artifact_refs+[candidate])
                receipt.update(schema="bie.producer.stage-evidence/1",run_id=context.run_id,stage=stage,
                    attempt=context.attempt,profile=PROFILE,source_sha256=config["source_sha256"],
                    input_artifact_ids=context.input_artifact_refs,input_sha256=[self.record(context.run_id,r).blob_digest for r in context.input_artifact_refs],
                    output_artifact_id=output,output_sha256=digest(output_value),candidate_artifact_id=candidate,
                    schema_version=PR_SCHEMA if stage=="PREREQUISITE" else RE_SCHEMA,
                    fencing_epoch=lease.epoch,evidence_kind="TECHNICAL_SOURCE_DERIVED",product_accepted=False)
                evidence=self.put(context.run_id,stage,"producer.evidence",receipt,context.input_artifact_refs+[output],True)
                self.leases.assert_active(lease)
                return StageExecutionResult([output],[evidence])
            except Exception as exc:
                code=exc.code if isinstance(exc,ProducerError) else "producer_execution_failed"
                ev=self.put(context.run_id,stage,"producer.failure",dict(schema="bie.producer.failure/1",
                    code=code,stage=stage,attempt=context.attempt,source_sha256=config["source_sha256"],product_accepted=False),evidence=True)
                raise StageExecutionFailure([code],[ev],"PROD030") from None
        return execute

    def status(self,run_id,tenant):
        result=super().status(run_id,tenant);config=self.configuration(run_id,tenant)
        saved=self.persistence.load_run_state(run_id)
        result.update(prerequisite=None,reasoning=None,safe_diagnostics={s:a["attempts"][-1]["diagnostics"] for s,a in saved["stages"].items() if a["attempts"][-1]["diagnostics"]})
        if result["stages"]["KNOWLEDGE"]!="SUCCEEDED":return result
        document,knowledge,kid,khash=self.inputs(run_id,config)
        if result["stages"]["PREREQUISITE"]=="SUCCEEDED":
            pid,pr=self.stage_ref(run_id,"PREREQUISITE");attempt=saved["stages"]["PREREQUISITE"]["attempts"][-1]["attempt"]
            p=verify_prerequisite(self.read(run_id,pid),knowledge,self.pr_context(run_id,config,kid,khash,attempt))
            result["prerequisite"]=dict(artifact_id=pid,sha256=pr.blob_digest,edge_count=len(p["edges"]),node_count=len(p["nodes"]),
                teaching_order_status="TECHNICAL_TOPOLOGICAL_ORDER",review_count=len(p["review"]),validation="PASS")
        if result["stages"]["REASONING"]=="SUCCEEDED":
            rid,rr=self.stage_ref(run_id,"REASONING");attempt=saved["stages"]["REASONING"]["attempts"][-1]["attempt"]
            r=verify_reasoning(self.read(run_id,rid),knowledge,p,self.pr_context(run_id,config,kid,khash,attempt),pid,document)
            result["reasoning"]=dict(artifact_id=rid,sha256=rr.blob_digest,decision_count=len(r["decisions"]),
                executed_types=r["executed_types"],not_executed_types=r["not_executed_types"],requires_review=True,validation="PASS")
        return result
