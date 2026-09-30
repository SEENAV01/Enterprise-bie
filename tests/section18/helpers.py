from pathlib import Path
import json
from bie.product_app.operator_service import OperatorRunService
from bie.infrastructure.persistence import PersistedArtifactRecord,PersistedAttempt,PersistedEvent
PDF=b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n"
CONFIG="a"*64
def service(tmp):return OperatorRunService(Path(tmp),id_factory=lambda:"0123456789abcdef")
def fail_stage(s,run_id,stage_id="PDF_INSPECTION"):
    run=s.persistence.load_run_state(run_id);cur=run["stages"][stage_id]["attempts"][-1]
    s.persistence.save_attempt(run_id,PersistedAttempt(stage_id,cur["attempt"],"FAILED",list(cur["input_artifact_refs"]),[],["evidence:test"],["synthetic failure"],"QA"))
    s.persistence.append_event(run_id,PersistedEvent(0,stage_id,cur["state"],"FAILED",cur["attempt"],"2026-09-30T00:00:00+00:00","fixture failure",["evidence:test"]))
    s.persistence.set_run_state(run_id,"BLOCKED")
def graph_artifact(s,run_id,kind,artifact_id="graph-1"):
    body={"schema_version":"bie.graph.v1","nodes":[{"id":"a","label":"A","source_refs":["src:1"]},{"id":"b","label":"B","source_refs":["src:2"]}],
          "edges":[{"source":"a","target":"b","relation":"depends_on","evidence_refs":["ev:1"]}]}
    raw=json.dumps(body,separators=(",",":")).encode();blob=s.cas.put_bytes(raw);atype="knowledge.concept_graph" if kind=="concept" else "knowledge.prerequisite_graph"
    s.persistence.register_artifact(PersistedArtifactRecord(artifact_id,atype,blob.algorithm,blob.digest,blob.size,run_id,"PDF_INSPECTION",False,{},[]));return artifact_id
