from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import sqlite3, json, threading, time

class PersistenceError(ValueError): pass

SCHEMA_VERSION = 1
VALID_STAGE_STATES={"PENDING","READY","RUNNING","SUCCEEDED","FAILED","BLOCKED","INVALIDATED"}
VALID_RUN_STATES={"CREATED","ACTIVE","BLOCKED","EXECUTION_COMPLETE"}

@dataclass(frozen=True)
class PersistedAttempt:
    stage_id:str
    attempt:int
    state:str
    input_artifact_refs:List[str]=field(default_factory=list)
    output_artifact_refs:List[str]=field(default_factory=list)
    evidence_refs:List[str]=field(default_factory=list)
    diagnostics:List[str]=field(default_factory=list)
    remediation_owner:Optional[str]=None

@dataclass(frozen=True)
class PersistedEvent:
    sequence:int
    stage_id:str
    from_state:str
    to_state:str
    attempt:int
    timestamp:str
    reason:str
    evidence_refs:List[str]

@dataclass(frozen=True)
class PersistedArtifactRecord:
    artifact_id:str
    artifact_type:str
    blob_algorithm:str
    blob_digest:str
    blob_size:int
    run_id:str
    stage_id:str
    evidence:bool
    metadata:Dict[str,object]
    parent_artifact_ids:List[str]

class SQLitePersistence:
    def __init__(self,path:Path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self._lock=threading.RLock()
        self._init_db()

    def _conn(self):
        c=sqlite3.connect(str(self.path),timeout=30,isolation_level=None)
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA journal_mode=WAL")
        return c

    def _init_db(self):
        with self._lock, self._conn() as c:
            c.executescript("""
            BEGIN IMMEDIATE;
            CREATE TABLE IF NOT EXISTS schema_meta(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runs(
                run_id TEXT PRIMARY KEY,
                run_state TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS stages(
                run_id TEXT NOT NULL,
                stage_id TEXT NOT NULL,
                required_predecessors_json TEXT NOT NULL,
                PRIMARY KEY(run_id,stage_id),
                FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS attempts(
                run_id TEXT NOT NULL,
                stage_id TEXT NOT NULL,
                attempt INTEGER NOT NULL,
                state TEXT NOT NULL,
                input_refs_json TEXT NOT NULL,
                output_refs_json TEXT NOT NULL,
                evidence_refs_json TEXT NOT NULL,
                diagnostics_json TEXT NOT NULL,
                remediation_owner TEXT,
                PRIMARY KEY(run_id,stage_id,attempt),
                FOREIGN KEY(run_id,stage_id) REFERENCES stages(run_id,stage_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS transition_events(
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                stage_id TEXT NOT NULL,
                from_state TEXT NOT NULL,
                to_state TEXT NOT NULL,
                attempt INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                reason TEXT NOT NULL,
                evidence_refs_json TEXT NOT NULL,
                FOREIGN KEY(run_id,stage_id) REFERENCES stages(run_id,stage_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS artifact_records(
                artifact_id TEXT PRIMARY KEY,
                artifact_type TEXT NOT NULL,
                blob_algorithm TEXT NOT NULL,
                blob_digest TEXT NOT NULL,
                blob_size INTEGER NOT NULL,
                run_id TEXT NOT NULL,
                stage_id TEXT NOT NULL,
                evidence INTEGER NOT NULL,
                metadata_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS artifact_parents(
                artifact_id TEXT NOT NULL,
                parent_artifact_id TEXT NOT NULL,
                PRIMARY KEY(artifact_id,parent_artifact_id),
                FOREIGN KEY(artifact_id) REFERENCES artifact_records(artifact_id) ON DELETE CASCADE
            );
            COMMIT;
            """)
            row=c.execute("SELECT value FROM schema_meta WHERE key='schema_version'").fetchone()
            if row is None:
                c.execute("INSERT INTO schema_meta(key,value) VALUES('schema_version',?)",(str(SCHEMA_VERSION),))
            elif int(row[0])!=SCHEMA_VERSION:
                raise PersistenceError(f"unsupported schema version {row[0]}")

    def create_run(self,run_id:str,predecessor_map:Dict[str,List[str]],run_state:str="CREATED")->None:
        if not run_id or run_state not in VALID_RUN_STATES: raise PersistenceError("invalid run")
        now=time.time()
        with self._lock, self._conn() as c:
            try:
                c.execute("BEGIN IMMEDIATE")
                c.execute("INSERT INTO runs(run_id,run_state,created_at,updated_at) VALUES(?,?,?,?)",
                          (run_id,run_state,now,now))
                for sid,preds in predecessor_map.items():
                    c.execute("INSERT INTO stages(run_id,stage_id,required_predecessors_json) VALUES(?,?,?)",
                              (run_id,sid,json.dumps(preds,sort_keys=True)))
                    c.execute("""INSERT INTO attempts(run_id,stage_id,attempt,state,input_refs_json,output_refs_json,
                              evidence_refs_json,diagnostics_json,remediation_owner)
                              VALUES(?,?,?,?,?,?,?,?,?)""",
                              (run_id,sid,1,"PENDING","[]","[]","[]","[]",None))
                c.execute("COMMIT")
            except Exception:
                c.execute("ROLLBACK"); raise

    def save_attempt(self,run_id:str,a:PersistedAttempt)->None:
        if a.state not in VALID_STAGE_STATES or a.attempt<1: raise PersistenceError("invalid attempt")
        with self._lock, self._conn() as c:
            try:
                c.execute("BEGIN IMMEDIATE")
                row=c.execute("SELECT state,input_refs_json,output_refs_json,evidence_refs_json,diagnostics_json,remediation_owner "
                              "FROM attempts WHERE run_id=? AND stage_id=? AND attempt=?",
                              (run_id,a.stage_id,a.attempt)).fetchone()
                values=(a.state,json.dumps(a.input_artifact_refs),json.dumps(a.output_artifact_refs),
                        json.dumps(a.evidence_refs),json.dumps(a.diagnostics),a.remediation_owner)
                if row is None:
                    c.execute("""INSERT INTO attempts(run_id,stage_id,attempt,state,input_refs_json,output_refs_json,
                               evidence_refs_json,diagnostics_json,remediation_owner) VALUES(?,?,?,?,?,?,?,?,?)""",
                              (run_id,a.stage_id,a.attempt,*values))
                else:
                    c.execute("""UPDATE attempts SET state=?,input_refs_json=?,output_refs_json=?,evidence_refs_json=?,
                               diagnostics_json=?,remediation_owner=? WHERE run_id=? AND stage_id=? AND attempt=?""",
                              (*values,run_id,a.stage_id,a.attempt))
                c.execute("UPDATE runs SET updated_at=? WHERE run_id=?",(time.time(),run_id))
                c.execute("COMMIT")
            except Exception:
                c.execute("ROLLBACK"); raise

    def append_event(self,run_id:str,event:PersistedEvent)->int:
        with self._lock, self._conn() as c:
            try:
                c.execute("BEGIN IMMEDIATE")
                cur=c.execute("""INSERT INTO transition_events(run_id,stage_id,from_state,to_state,attempt,timestamp,reason,evidence_refs_json)
                                 VALUES(?,?,?,?,?,?,?,?)""",
                              (run_id,event.stage_id,event.from_state,event.to_state,event.attempt,event.timestamp,
                               event.reason,json.dumps(event.evidence_refs)))
                seq=cur.lastrowid
                c.execute("COMMIT")
                return int(seq)
            except Exception:
                c.execute("ROLLBACK"); raise

    def set_run_state(self,run_id:str,state:str)->None:
        if state not in VALID_RUN_STATES: raise PersistenceError("invalid run state")
        with self._lock, self._conn() as c:
            c.execute("UPDATE runs SET run_state=?,updated_at=? WHERE run_id=?",(state,time.time(),run_id))
            if c.total_changes==0: raise PersistenceError("run not found")

    def load_run_state(self,run_id:str)->Dict[str,object]:
        with self._conn() as c:
            rr=c.execute("SELECT run_state FROM runs WHERE run_id=?",(run_id,)).fetchone()
            if rr is None: raise PersistenceError("run not found")
            stages={}
            rows=c.execute("SELECT stage_id,required_predecessors_json FROM stages WHERE run_id=?",(run_id,)).fetchall()
            for sid,preds_json in rows:
                at=c.execute("""SELECT attempt,state,input_refs_json,output_refs_json,evidence_refs_json,diagnostics_json,remediation_owner
                                FROM attempts WHERE run_id=? AND stage_id=? ORDER BY attempt""",(run_id,sid)).fetchall()
                stages[sid]={
                    "required_predecessors":json.loads(preds_json),
                    "attempts":[{
                        "attempt":r[0],"state":r[1],"input_artifact_refs":json.loads(r[2]),
                        "output_artifact_refs":json.loads(r[3]),"evidence_refs":json.loads(r[4]),
                        "diagnostics":json.loads(r[5]),"remediation_owner":r[6]
                    } for r in at]
                }
            events=[{
                "sequence":r[0],"stage_id":r[1],"from_state":r[2],"to_state":r[3],"attempt":r[4],
                "timestamp":r[5],"reason":r[6],"evidence_refs":json.loads(r[7])
            } for r in c.execute("""SELECT sequence,stage_id,from_state,to_state,attempt,timestamp,reason,evidence_refs_json
                                    FROM transition_events WHERE run_id=? ORDER BY sequence""",(run_id,)).fetchall()]
            return {"run_id":run_id,"run_state":rr[0],"stages":stages,"events":events}

    def register_artifact(self,r:PersistedArtifactRecord)->None:
        if not r.artifact_id or not r.blob_digest: raise PersistenceError("invalid artifact")
        with self._lock, self._conn() as c:
            try:
                c.execute("BEGIN IMMEDIATE")
                existing=c.execute("""SELECT artifact_type,blob_algorithm,blob_digest,blob_size,run_id,stage_id,evidence,metadata_json
                                      FROM artifact_records WHERE artifact_id=?""",(r.artifact_id,)).fetchone()
                canonical=(r.artifact_type,r.blob_algorithm,r.blob_digest,r.blob_size,r.run_id,r.stage_id,
                           int(r.evidence),json.dumps(r.metadata,sort_keys=True,separators=(",",":")))
                if existing is not None:
                    existing_canonical=(*existing[:7],json.dumps(json.loads(existing[7]),sort_keys=True,separators=(",",":")))
                    if existing_canonical!=canonical:
                        raise PersistenceError("artifact immutable conflict")
                    c.execute("COMMIT"); return
                for p in r.parent_artifact_ids:
                    if c.execute("SELECT 1 FROM artifact_records WHERE artifact_id=?",(p,)).fetchone() is None:
                        raise PersistenceError(f"missing parent {p}")
                c.execute("""INSERT INTO artifact_records(artifact_id,artifact_type,blob_algorithm,blob_digest,blob_size,run_id,stage_id,evidence,metadata_json)
                             VALUES(?,?,?,?,?,?,?,?,?)""",
                          (r.artifact_id,*canonical))
                for p in r.parent_artifact_ids:
                    c.execute("INSERT INTO artifact_parents(artifact_id,parent_artifact_id) VALUES(?,?)",(r.artifact_id,p))
                c.execute("COMMIT")
            except Exception:
                c.execute("ROLLBACK"); raise

    def load_artifact(self,artifact_id:str)->PersistedArtifactRecord:
        with self._conn() as c:
            r=c.execute("""SELECT artifact_id,artifact_type,blob_algorithm,blob_digest,blob_size,run_id,stage_id,evidence,metadata_json
                           FROM artifact_records WHERE artifact_id=?""",(artifact_id,)).fetchone()
            if r is None: raise PersistenceError("artifact not found")
            parents=[x[0] for x in c.execute("SELECT parent_artifact_id FROM artifact_parents WHERE artifact_id=? ORDER BY parent_artifact_id",
                                             (artifact_id,)).fetchall()]
            return PersistedArtifactRecord(r[0],r[1],r[2],r[3],r[4],r[5],r[6],bool(r[7]),json.loads(r[8]),parents)

    def artifacts_for_run(self,run_id:str)->List[str]:
        with self._conn() as c:
            return [r[0] for r in c.execute("SELECT artifact_id FROM artifact_records WHERE run_id=? ORDER BY artifact_id",(run_id,)).fetchall()]

    def evidence_for_run(self,run_id:str)->List[str]:
        with self._conn() as c:
            return [r[0] for r in c.execute("SELECT artifact_id FROM artifact_records WHERE run_id=? AND evidence=1 ORDER BY artifact_id",(run_id,)).fetchall()]
