"""Canonical-state operator service for Section 18 Batch 001."""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import re,uuid
from bie.infrastructure.artifact_store import FileSystemCAS
from bie.infrastructure.persistence import PersistedArtifactRecord,PersistedAttempt,PersistedEvent,PersistenceError,SQLitePersistence
from .control_store import ControlStoreError,OperatorControlStore
from .source_validation import validate_pdf_source

_HEX64=re.compile(r"^[0-9a-f]{64}$");_RUN_ID=re.compile(r"^app-run-[0-9a-f]{16,64}$")
SUPPORTED_PROFILES={"pdf_inspection_v1":{"PDF_INSPECTION":[]}}
class OperatorError(ValueError):pass
def _utcnow():return datetime.now(timezone.utc).isoformat()

class OperatorRunService:
    def __init__(self,data_root:Path,*,id_factory=None,clock=None):
        self.data_root=Path(data_root);self.data_root.mkdir(parents=True,exist_ok=True)
        self.persistence=SQLitePersistence(self.data_root/"runs.sqlite3");self.cas=FileSystemCAS(self.data_root/"cas")
        self.controls=OperatorControlStore(self.data_root/"operator.sqlite3",clock=clock);self.id_factory=id_factory or (lambda:uuid.uuid4().hex)
    def _load(self,run_id):
        if type(run_id) is not str or not _RUN_ID.fullmatch(run_id):raise OperatorError("invalid run id")
        try:return self.persistence.load_run_state(run_id)
        except PersistenceError as exc:
            if str(exc)=="run not found":raise OperatorError("run not found") from exc
            raise
    def create_run(self,config_hash,profile="pdf_inspection_v1"):
        if type(config_hash) is not str or not _HEX64.fullmatch(config_hash):raise OperatorError("invalid config hash")
        if profile not in SUPPORTED_PROFILES:raise OperatorError("unsupported run profile")
        token=str(self.id_factory()).lower()
        if not re.fullmatch(r"[0-9a-f]{16,64}",token):raise OperatorError("invalid run id source")
        run_id="app-run-"+token;self.persistence.create_run(run_id,SUPPORTED_PROFILES[profile]);self.controls.put_run_meta(run_id,profile,config_hash)
        return self.status(run_id)
    def validate_source(self,filename,media_type,payload):return validate_pdf_source(filename,media_type,payload)
    def import_source(self,run_id,filename,media_type,payload):
        run=self._load(run_id);validation=self.validate_source(filename,media_type,payload);self.controls.put_source_validation(run_id,validation)
        if validation["status"]!="VALID":raise OperatorError("source validation failed")
        if run["run_state"]=="EXECUTION_COMPLETE":raise OperatorError("completed run is immutable")
        meta=self.controls.run_meta(run_id);stage_id=next(iter(SUPPORTED_PROFILES[meta["profile"]]))
        current=run["stages"][stage_id]["attempts"][-1]
        if current["state"] not in {"PENDING","READY"}:raise OperatorError("source cannot change after execution starts")
        digest=validation["sha256"];artifact_id=f"source-{run_id.removeprefix('app-run-')[:12]}-{digest[:20]}";blob=self.cas.put_bytes(payload)
        self.persistence.register_artifact(PersistedArtifactRecord(artifact_id,"document.source.pdf",blob.algorithm,blob.digest,blob.size,run_id,stage_id,False,
            {"filename":validation["filename"],"media_type":validation["media_type"],"sha256":digest,"size_bytes":validation["size_bytes"],"validation_schema":validation["schema_version"]},[]))
        self.persistence.save_attempt(run_id,PersistedAttempt(stage_id,current["attempt"],current["state"],[artifact_id],
            list(current["output_artifact_refs"]),list(current["evidence_refs"]),list(current["diagnostics"]),current["remediation_owner"]))
        return {"run_id":run_id,"artifact_id":artifact_id,"validation":validation,"stored":True}
    def source_validation(self,run_id):
        self._load(run_id);v=self.controls.source_validation(run_id)
        return v if v is not None else {"schema_version":"bie.app.source-validation/1","status":"MISSING","errors":["source_not_validated"],"product_accepted":False}
    def status(self,run_id):
        run=self._load(run_id);meta=self.controls.run_meta(run_id);stages=[]
        for sid in sorted(run["stages"]):
            a=run["stages"][sid]["attempts"][-1];stages.append({"stage_id":sid,"state":a["state"],"attempt":a["attempt"],
                "evidence_refs":list(a["evidence_refs"]),"has_diagnostics":bool(a["diagnostics"])})
        return {"schema_version":"bie.app.run-status/1","run_id":run_id,"run_state":run["run_state"],
                "profile":meta["profile"] if meta else None,"config_hash":meta["config_hash"] if meta else None,
                "stages":stages,"control":self.controls.latest(run_id),"progress_percent":None,"product_accepted":False}
    def timeline(self,run_id):
        run=self._load(run_id)
        te=[{"kind":"STAGE_TRANSITION","sequence":r["sequence"],"stage_id":r["stage_id"],"from_state":r["from_state"],"to_state":r["to_state"],
             "attempt":r["attempt"],"timestamp":r["timestamp"],"reason":r["reason"],"evidence_refs":list(r["evidence_refs"])} for r in run["events"]]
        ce=[{"kind":"CONTROL_REQUEST",**r} for r in self.controls.events(run_id)]
        return {"schema_version":"bie.app.stage-timeline/1","run_id":run_id,"transition_events":te,"control_events":ce,"product_accepted":False}
    def failures(self,run_id):
        run=self._load(run_id);rows=[]
        for sid in sorted(run["stages"]):
            a=run["stages"][sid]["attempts"][-1]
            if a["state"] in {"FAILED","BLOCKED"}:rows.append({"stage_id":sid,"state":a["state"],"attempt":a["attempt"],
                "diagnostics":list(a["diagnostics"]),"evidence_refs":list(a["evidence_refs"]),"remediation_owner":a["remediation_owner"]})
        return {"schema_version":"bie.app.failure-view/1","run_id":run_id,"failures":rows,"empty":not rows,"product_accepted":False}
    def retry_stage(self,run_id,stage_id,reason):
        if type(reason) is not str or not reason.strip() or len(reason)>500:raise OperatorError("retry reason required")
        run=self._load(run_id)
        if stage_id not in run["stages"]:raise OperatorError("stage not found")
        cur=run["stages"][stage_id]["attempts"][-1]
        if cur["state"]!="FAILED":raise OperatorError("only failed stage may retry")
        attempt=cur["attempt"]+1;self.persistence.save_attempt(run_id,PersistedAttempt(stage_id,attempt,"READY"))
        self.persistence.append_event(run_id,PersistedEvent(0,stage_id,"FAILED","READY",attempt,_utcnow(),reason.strip(),list(cur["evidence_refs"])))
        self.persistence.set_run_state(run_id,"ACTIVE")
        return {"schema_version":"bie.app.retry/1","run_id":run_id,"stage_id":stage_id,"attempt":attempt,"state":"READY",
                "dispatch_required":True,"product_accepted":False}
    def request_control(self,run_id,action,reason):
        run=self._load(run_id)
        if run["run_state"]=="EXECUTION_COMPLETE":raise OperatorError("completed run cannot be controlled")
        latest=self.controls.latest(run_id)
        if action=="PAUSE" and run["run_state"]!="ACTIVE":raise OperatorError("pause requires active run")
        if action=="RESUME" and (not latest or latest["action"]!="PAUSE" or latest["status"]!="EFFECTIVE"):
            raise OperatorError("resume requires effective pause")
        try:r=self.controls.request(run_id,action,reason)
        except ControlStoreError as exc:raise OperatorError(str(exc)) from exc
        return {"schema_version":"bie.app.run-control/1",**r,"effective":False,"worker_ack_required":True,"product_accepted":False}
    def acknowledge_control(self,request_id,worker_ref):
        try:r=self.controls.acknowledge(request_id,worker_ref)
        except ControlStoreError as exc:raise OperatorError(str(exc)) from exc
        return {"schema_version":"bie.app.run-control/1",**r,"effective":True,"worker_ack_required":False,"product_accepted":False}
