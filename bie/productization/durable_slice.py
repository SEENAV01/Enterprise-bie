"""Three-stage durable composition around unchanged canonical stores/engines.

No cross-store atomicity claim. Explicit fenced recovery repairs interruptions;
it never substitutes an in-memory run or automatically redrives failed work.
"""
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from importlib.metadata import version
import time
import uuid

from bie.infrastructure.artifact_store import BlobRef
from bie.infrastructure.persistence import (SQLitePersistence, PersistedAttempt,
    PersistedEvent, PersistedArtifactRecord, PersistenceError)
from bie.infrastructure.idempotency_store import SQLiteIdempotencyStore, IdempotencyError
from bie.infrastructure.durable_task_queue import SQLiteDurableTaskQueue, DurableTaskMessage
from bie.infrastructure.run_state import build_run_state, StageAttempt
from bie.infrastructure.orchestrator import (EnterpriseOrchestrator, StageDefinition,
    StageExecutionResult, StageExecutionFailure)
from bie.infrastructure.execution_graph import legacy_enterprise_graph_v1
from bie.director.director_durable_recovery import DirectorLeaseStore
from bie.document_intelligence.real_pdf_text_runtime import inspect_real_pdf_text
from .contracts import (PROFILE, ProducerError, require, canonical, strict_json,
    digest, sha, identifier, profile_config, structured_document, validate_document, KNOWLEDGE_SCHEMA)
from .candidates import produce

STAGES = ("SOURCE", "DOCUMENT_INTELLIGENCE", "KNOWLEDGE")
CAPABILITY = "producer:" + PROFILE
DOWNSTREAM = tuple(s for s in legacy_enterprise_graph_v1().stages if s not in STAGES)


def run_identity(tenant, key):
    identifier(tenant); identifier(key)
    return "prod-" + digest(dict(tenant=tenant, key=key, profile=PROFILE))


class ClosedPersistence(SQLitePersistence):
    """Connection ownership only; same canonical schema/transactions/methods."""
    @contextmanager
    def _conn(self):
        connection = super()._conn()
        try:
            with connection:
                yield connection
        finally:
            connection.close()


class DurableArtifactResolver:
    def __init__(self, service, run_id):
        self.service, self.run_id = service, run_id

    def outputs_for_stage(self, run_id, stage):
        require(run_id == self.run_id, "foreign_run")
        current = self.service.persistence.load_run_state(run_id)["stages"][stage]["attempts"][-1]
        return [r.artifact_id for r in (self.service.record(run_id, ref)
                for ref in current["output_artifact_refs"])]

    def register_stage_outputs(self, run_id, stage, refs):
        require(run_id == self.run_id and refs, "foreign_run")
        expected = self.service.graph_for().stages[stage].emits
        for ref in refs:
            record = self.service.record(run_id, ref)
            require(record.stage_id == stage and record.artifact_type == expected,
                    "output_contract_mismatch")


class PersistedRunAdapter:
    """Hydrate canonical RunStateMachine; persist each canonical transition."""
    def __init__(self, service, run_id):
        self.service, self.run_id = service, run_id
        saved = service.persistence.load_run_state(run_id)
        graph = service.graph_for()
        require(set(saved["stages"]) == set(service.stages) and all(
            saved["stages"][s]["required_predecessors"] == graph.stages[s].required_predecessors
            for s in service.stages), "producer_profile_scope_mismatch")
        self.state = build_run_state(run_id, {s:list(saved["stages"][s]["required_predecessors"])
                                            for s in service.stages})
        self.state.run_state = saved["run_state"]
        for stage in service.stages:
            self.state.stages[stage].attempts = [StageAttempt(**{
                k:v for k,v in a.items() if k != "stage_id"})
                for a in saved["stages"][stage]["attempts"]]
        self.state.validate()
        original = self.state._transition
        def transition(runtime, to_state, reason="", evidence_refs=None):
            original(runtime, to_state, reason, evidence_refs)
            self.save(runtime)
        self.state._transition = transition

    def save(self, runtime):
        self.service.write_guard()
        a = runtime.current
        self.service.persistence.save_attempt(self.run_id, PersistedAttempt(runtime.stage_id,
            a.attempt, a.state, a.input_artifact_refs, a.output_artifact_refs,
            a.evidence_refs, a.diagnostics, a.remediation_owner))
        if runtime.events:
            event = runtime.events[-1]
            self.service.persistence.append_event(self.run_id, PersistedEvent(0, **asdict(event)))

    def finish(self):
        self.service.write_guard()
        self.state._refresh_run_state()
        self.service.persistence.set_run_state(self.run_id, self.state.run_state)


class KnowledgeProducerService:
    """Native trusted composition. Authorization belongs to its Section18 port.

    Uses a governed per-run namespace and the already admitted budgeted CAS.
    It does not construct a second CAS or alter PdfInspectionJobService.
    """
    # Versioned composition hooks; the Task029 defaults/intent remain unchanged.
    stages = STAGES
    profile = PROFILE
    capability = CAPABILITY
    downstream = DOWNSTREAM
    completion_stage = "KNOWLEDGE"
    config_for = staticmethod(profile_config)
    identity_for = staticmethod(run_identity)
    blocked_codes = frozenset({"provider_unavailable"})
    graph_for = staticmethod(legacy_enterprise_graph_v1)

    def __init__(self, root, cas, *, registry=None, fault=None, authorize=None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.cas, self.registry = cas, registry
        self.persistence = ClosedPersistence(self.root / "runs.sqlite3")
        self.queue = SQLiteDurableTaskQueue(self.root / "queue.sqlite3")
        self.idempotency = SQLiteIdempotencyStore(str(self.root / "idempotency.sqlite3"))
        # Existing generic fenced DIR lease primitive; no DIR execution occurs.
        self.leases = DirectorLeaseStore(self.root / "idempotency.sqlite3")
        self.owner = "producer-" + uuid.uuid4().hex
        self.fault = fault or (lambda _: None)
        self.authorize = authorize or (lambda: None)
        self.active_lease = None

    def write_guard(self):
        self.authorize()
        if self.active_lease is not None:
            self.leases.assert_active(self.active_lease)

    def close(self):
        self.idempotency.close(); self.leases.close()

    def verify_terminal_for_ack(self, run_id, tenant):
        """Profile-specific semantic revalidation hook; legacy ACK policy unchanged."""
        return None

    def record(self, run_id, artifact_id):
        record = self.persistence.load_artifact(identifier(artifact_id))
        require(record.run_id == run_id, "foreign_artifact")
        if artifact_id.startswith("artifact-"):
            require(artifact_id == "artifact-" + digest(dict(run=run_id,stage=record.stage_id,
                kind=record.artifact_type,sha=record.blob_digest,suffix="")),"artifact_identity_mismatch")
        self.cas.get_bytes(BlobRef(record.blob_algorithm, record.blob_digest, record.blob_size))
        return record

    def read(self, run_id, artifact_id):
        record = self.record(run_id, artifact_id)
        return strict_json(self.cas.get_bytes(BlobRef(record.blob_algorithm,
                                                    record.blob_digest, record.blob_size)))

    def put(self, run_id, stage, kind, value, parents=(), evidence=False, suffix=""):
        self.write_guard()
        parents = list(dict.fromkeys(parents))
        raw = canonical(value)
        require(len(raw) <= 4*1024*1024, "artifact_budget")
        blob = self.cas.put_bytes(raw)
        self.fault("after_" + stage + "_" + kind + "_cas")
        self.fault("after_" + stage + "_cas")
        artifact_id = "artifact-" + digest(dict(run=run_id, stage=stage,
            kind=kind, sha=blob.digest, suffix=suffix))
        for parent in parents:
            self.record(run_id, parent)
        self.write_guard()
        self.persistence.register_artifact(PersistedArtifactRecord(artifact_id,kind,
            blob.algorithm,blob.digest,blob.size,run_id,stage,evidence,
            {"privacy":"SAFE_EVIDENCE" if evidence else "PRIVATE", "profile":self.profile},list(parents)))
        self.record(run_id, artifact_id)
        return artifact_id

    def configuration(self, run_id, tenant):
        identifier(run_id); identifier(tenant)
        require(run_id.startswith("prod-"), "foreign_run")
        config = self.read(run_id, run_id + "-config")
        require(config["tenant"] == tenant and config["config"] ==
                self.config_for(config["config"]["provider"],config["config"]["model"]), "foreign_run")
        require(config["run_id"] == run_id and self.root.name == run_id, "foreign_run")
        require(set(self.persistence.load_run_state(run_id)["stages"])==set(self.stages),
                "producer_profile_scope_mismatch")
        require(config["fingerprint"] == digest({k:v for k,v in config.items()
                if k not in ("run_id","fingerprint")}), "intent_tampered")
        require(config["privacy"] == "PRIVATE_LOCAL_CAS" and config["rights"] == "LOCAL_PROCESSING_ONLY",
                "source_rights")
        return config

    def admit(self, source, tenant, key, config=None):
        """source is obtained from the authoritative control-plane source index."""
        self.write_guard()
        identifier(tenant); identifier(key)
        config = self.config_for() if config is None else config
        require(config == self.config_for(config.get("provider"),config.get("model")), "profile_config")
        require(source["tenant"] == tenant and source["media_type"] == "application/pdf"
                and source["privacy"] == "PRIVATE_LOCAL_CAS"
                and source["rights"] == "LOCAL_PROCESSING_ONLY", "foreign_source")
        source_ref = BlobRef("sha256",source["sha256"],source["size_bytes"])
        require(0 < source_ref.size <= 25*1024*1024, "source_budget")
        # Never trust the caller hash: read the authoritative CAS and verify it.
        self.cas.get_bytes(source_ref)
        intent = dict(tenant=tenant, source=source["source_id"], source_sha256=source_ref.digest,
                      source_bytes=source_ref.size, config=config,
                      privacy=source["privacy"], rights=source["rights"])
        fingerprint = digest(intent)
        run_id = self.identity_for(tenant,key)
        require(self.root.name == run_id, "namespace_mismatch")
        claim = self.idempotency.claim("producer:"+tenant+":"+key, fingerprint, "admission")
        if claim.state == "COMPLETED":
            require(claim.result_ref == run_id, "intent_conflict")
            self.configuration(run_id,tenant)
            return run_id
        graph = self.graph_for()
        self.write_guard()
        try:
            self.persistence.create_run(run_id, {s:list(graph.stages[s].required_predecessors) for s in self.stages})
        except Exception:
            # Only a verified already-created exact run is a valid admission replay.
            saved = self.persistence.load_run_state(run_id)
            require(set(saved["stages"]) == set(self.stages), "admission_inconsistent")
        cfg = dict(intent, run_id=run_id, fingerprint=fingerprint)
        self.write_guard()
        blob = self.cas.put_bytes(canonical(cfg))
        self.write_guard()
        self.persistence.register_artifact(PersistedArtifactRecord(run_id+"-config","producer.config",
            "sha256",blob.digest,blob.size,run_id,"SOURCE",False,{"privacy":"PRIVATE"},[]))
        self.persistence.register_artifact(PersistedArtifactRecord(run_id+"-source","source.document",
            "sha256",source_ref.digest,source_ref.size,run_id,"SOURCE",False,
            {"privacy":"PRIVATE","admitted_source_id":source["source_id"],"tenant":tenant},[]))
        self.fault("after_source_admission")
        self.write_guard()
        self.idempotency.complete("producer:"+tenant+":"+key,"admission",run_id)
        self.schedule(run_id)
        return run_id

    def task_id(self, run_id, stage, attempt):
        return "work-" + digest(dict(run=run_id,stage=stage,attempt=attempt))

    def schedule(self, run_id):
        adapter = PersistedRunAdapter(self,run_id)
        for stage in self.stages:
            runtime = adapter.state.stages[stage]
            if runtime.current.state in ("PENDING","READY") and adapter.state.predecessors_succeeded(stage):
                if runtime.current.state == "PENDING": adapter.state.mark_ready(stage)
                refs = [run_id+"-source"] if stage == "SOURCE" else [ref
                    for predecessor in self.graph_for().stages[stage].required_predecessors
                    for ref in DurableArtifactResolver(self,run_id).outputs_for_stage(run_id,predecessor)]
                self.write_guard()
                self.queue.enqueue(DurableTaskMessage(self.task_id(run_id,stage,runtime.current.attempt),
                    run_id,stage,runtime.current.attempt,digest(refs),[self.capability],refs,max_deliveries=1))
                adapter.finish()
                return

    def executor(self, config, stage, lease):
        def execute(context):
            try:
                run_id = context.run_id
                parents = [run_id+"-source"] if stage == "SOURCE" else context.input_artifact_refs
                if stage == "SOURCE":
                    self.record(run_id,run_id+"-source")
                    output = run_id+"-source"
                    receipt = dict(source_sha256=config["source_sha256"], source_id=config["source"],
                                   source_bytes=config["source_bytes"], source_verified=True)
                elif stage == "DOCUMENT_INTELLIGENCE":
                    source = self.record(run_id,parents[0])
                    require(source.blob_digest == config["source_sha256"], "source_hash_mismatch")
                    raw = self.cas.get_bytes(BlobRef("sha256",source.blob_digest,source.blob_size))
                    inspection = inspect_real_pdf_text(raw)
                    from bie.document_intelligence import real_pdf_text_runtime
                    identity = sha(Path(real_pdf_text_runtime.__file__).read_bytes())
                    document = structured_document(inspection,parents[0],identity)
                    output = self.put(run_id,stage,"document.structured",document,parents)
                    receipt = dict(source_sha256=inspection.source_hash,document_sha256=digest(document),
                        runtime_sha256=identity,document_schema=document["schema"],
                        reading_order_policy=document["reading_order_policy"],
                        packages={name:version(name) for name in ("pypdf","pdfplumber")},
                        page_count=inspection.page_count,blocks=len(document["blocks"]))
                else:
                    document = validate_document(self.read(run_id,parents[0]))
                    require(document["source_sha256"] == config["source_sha256"], "source_hash_mismatch")
                    candidates, graph, receipt = produce(document,config["config"],self.registry)
                    candidate_id = self.put(run_id,stage,"knowledge.candidates",candidates,parents)
                    output = self.put(run_id,stage,"knowledge.graph",graph,parents+[candidate_id])
                    receipt = dict(receipt,candidate_artifact_id=candidate_id)
                self.leases.assert_active(lease)
                self.authorize()
                receipt = dict(receipt,schema="bie.producer.stage-evidence/1",run_id=run_id,stage=stage,
                    attempt=context.attempt,profile=self.profile,input_artifact_ids=parents,output_artifact_id=output,
                    output_sha256=self.record(run_id,output).blob_digest,fencing_epoch=lease.epoch,
                    evidence_kind="TECHNICAL_SOURCE_DERIVED",academic_acceptance=False,product_accepted=False)
                evidence = self.put(run_id,stage,"producer.evidence",receipt,parents+[output],True)
                self.leases.assert_active(lease)
                return StageExecutionResult([output],[evidence])
            except Exception as exc:
                code = exc.code if isinstance(exc,ProducerError) else "producer_execution_failed"
                evidence = self.put(context.run_id,stage,"producer.failure",dict(
                    schema="bie.producer.failure/1",code=code,stage=stage,attempt=context.attempt,
                    source_sha256=config["source_sha256"],product_accepted=False),evidence=True)
                raise StageExecutionFailure([code],[evidence],"PROD029") from None
        return execute

    def work_once(self, run_id, tenant):
        self.authorize()
        config = self.configuration(run_id,tenant)
        self.schedule(run_id)
        delivery = self.queue.poll(self.owner,visibility_timeout=120,capability_tags=[self.capability])
        if delivery is None: return self.status(run_id,tenant)
        task = delivery.task
        require(task.run_id == run_id and task.stage_id in self.stages and task.required_capability_tags == [self.capability],
                "foreign_task")
        lease = self.leases.acquire(task.task_id,config["fingerprint"],self.owner,ttl_seconds=120)
        self.active_lease = lease
        with self.leases.db:
            self.leases.db.execute("BEGIN IMMEDIATE")
            self.leases.assert_active(lease)
            self.authorize()
            adapter = PersistedRunAdapter(self,run_id)
            require(adapter.state.stages[task.stage_id].current.attempt == task.attempt, "stale_worker")
            graph = self.graph_for()
            definitions = {s:StageDefinition(s,list(graph.stages[s].required_predecessors),
                graph.stages[s].consumes,graph.stages[s].emits,"PROD029") for s in self.stages}
            orchestrator = EnterpriseOrchestrator(adapter.state,definitions,
                {task.stage_id:self.executor(config,task.stage_id,lease)},
                DurableArtifactResolver(self,run_id),config["config"])
            try:
                orchestrator.execute_stage(task.stage_id)
            except StageExecutionFailure:
                runtime = adapter.state.stages[task.stage_id]
                if len(runtime.current.diagnostics)==1 and runtime.current.diagnostics[0] in self.blocked_codes:
                    code=runtime.current.diagnostics[0]
                    # Preserve Task029's historical provider-unavailable event text.
                    adapter.state._transition(runtime,"BLOCKED","provider unavailable" if code=="provider_unavailable" else code,runtime.current.evidence_refs)
            self.leases.assert_active(lease)
            adapter.finish()
            self.fault("after_"+task.stage_id+"_terminal")
            succeeded = adapter.state.stages[task.stage_id].current.state == "SUCCEEDED"
            if succeeded:
                for ref in adapter.state.stages[task.stage_id].current.evidence_refs: self.record(run_id,ref)
                self.verify_terminal_for_ack(run_id, tenant)
                self.write_guard()
                self.queue.ack(task.task_id,self.owner)
            else:
                self.write_guard()
                self.queue.dead_letter(task.task_id,"producer_stage_failed")
        self.leases.complete(lease,task.task_id)
        self.active_lease = None
        self.fault("before_next_admission")
        if succeeded: self.schedule(run_id)
        return self.status(run_id,tenant)

    def recover(self, run_id, tenant):
        """Explicit authorized recovery; active leases may never be overridden."""
        config = self.configuration(run_id,tenant)
        adapter = PersistedRunAdapter(self,run_id)
        for stage in self.stages:
            runtime = adapter.state.stages[stage]; attempt=runtime.current
            task_id=self.task_id(run_id,stage,attempt.attempt)
            try: delivery=self.queue.get(task_id)
            except Exception: continue
            if attempt.state == "RUNNING" or delivery.state == "DELIVERED":
                lease=self.leases.acquire(task_id,config["fingerprint"],self.owner,ttl_seconds=120)
                self.active_lease=lease
                require(lease.owner == self.owner and lease.state == "ACTIVE", "recovery_inconsistent")
                with self.leases.db:
                    self.leases.db.execute("BEGIN IMMEDIATE"); self.leases.assert_active(lease)
                    if attempt.state == "SUCCEEDED":
                        for ref in attempt.output_artifact_refs+attempt.evidence_refs: self.record(run_id,ref)
                        self.verify_terminal_for_ack(run_id, tenant)
                        self.write_guard()
                        self.queue.ack(task_id,delivery.consumer_id)
                    else:
                        evidence=self.put(run_id,stage,"producer.recovery",dict(
                            code="interrupted_attempt",attempt=attempt.attempt,epoch=lease.epoch),evidence=True)
                        adapter.state.recover_interrupted(stage,evidence)
                        self.queue.dead_letter(task_id,"interrupted_attempt")
                        adapter.state.retry(stage); adapter.save(runtime)
                    adapter.finish()
                self.leases.complete(lease,task_id)
                self.active_lease=None
        self.schedule(run_id)
        return self.status(run_id,tenant)

    def status(self, run_id, tenant):
        config=self.configuration(run_id,tenant)
        saved=self.persistence.load_run_state(run_id)
        states={s:saved["stages"][s]["attempts"][-1]["state"] for s in self.stages}
        graph_summary=None
        for stage in self.stages:
            attempt=saved["stages"][stage]["attempts"][-1]
            if attempt["state"] == "SUCCEEDED":
                for ref in attempt["output_artifact_refs"]+attempt["evidence_refs"]:self.record(run_id,ref)
        if states["KNOWLEDGE"] == "SUCCEEDED":
            ref=saved["stages"]["KNOWLEDGE"]["attempts"][-1]["output_artifact_refs"][0]
            graph=self.read(run_id,ref)
            require(graph["schema"] == KNOWLEDGE_SCHEMA and graph["source_sha256"] == config["source_sha256"],
                    "knowledge_source_mismatch")
            document_ref=saved["stages"]["DOCUMENT_INTELLIGENCE"]["attempts"][-1]["output_artifact_refs"][0]
            document=validate_document(self.read(run_id,document_ref))
            graph_summary=dict(artifact_id=ref,sha256=digest(graph),concept_count=len(graph["nodes"]),
                claim_count=len(graph["claims"]),relation_count=len(graph["edges"]),
                anchor_count=len({a for c in graph["claims"] for a in c["anchor_ids"]}),
                concept_ids=sorted(graph["nodes"]),source_pages=sorted({b["physical_page"] for b in document["blocks"]}),
                validation="PASS",grounding="VERBATIM_SOURCE_BOUND",evidence_kind=graph["evidence_kind"])
        return dict(run_id=run_id,profile=self.profile,source_sha256=config["source_sha256"],stages=states,
            downstream={s:"NOT_RUN" for s in self.downstream},knowledge=graph_summary,
            slice_complete=states[self.completion_stage]=="SUCCEEDED",product_accepted=False,
            academic_acceptance=False,live_provider_executed=False)
