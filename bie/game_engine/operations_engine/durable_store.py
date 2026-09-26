from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import json,sqlite3,time
from bie.bie_core.artifact_contracts import ArtifactEnvelope,ProducerIdentity,ProvenanceSource,ProvenanceSummary
from bie.infrastructure.artifact_store import FileSystemCAS,ArtifactCatalog,ArtifactRecord,BlobRef
from bie.infrastructure.idempotency_store import SQLiteIdempotencyStore
from ..canonical import canonical_json
from .errors import GameOperationsError

class DurableGameStore:
    def __init__(self,root:Path):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.cas=FileSystemCAS(self.root/'cas');self.catalog=ArtifactCatalog(self.cas)
        self.db=sqlite3.connect(self.root/'game-operations.sqlite');self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('CREATE TABLE IF NOT EXISTS artifact_records(artifact_id TEXT PRIMARY KEY,record_json TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS jobs(job_key TEXT PRIMARY KEY,fingerprint TEXT NOT NULL,run_id TEXT NOT NULL,session_id TEXT NOT NULL,owner TEXT NOT NULL,state TEXT NOT NULL,checkpoint_json TEXT NOT NULL,result_ref TEXT,attempt INTEGER NOT NULL,updated REAL NOT NULL)')
        self.db.commit();self.idempotency=SQLiteIdempotencyStore(self.root/'idempotency.sqlite');self._restore_records()
    def _restore_records(self):
        pending={}
        for aid,text in self.db.execute('SELECT artifact_id,record_json FROM artifact_records'):
            v=json.loads(text);v['blob']=BlobRef(**v['blob']);pending[aid]=ArtifactRecord(**v)
        while pending:
            ready=[k for k,r in pending.items() if set(r.parent_artifact_ids)<=self.catalog.records.keys()]
            if not ready:raise GameOperationsError('GAME_OPS_ARTIFACT_INDEX_CORRUPT')
            for k in sorted(ready):self.catalog.register(pending.pop(k))
    def _record(self,rec):
        text=canonical_json(asdict(rec)).decode();old=self.db.execute('SELECT record_json FROM artifact_records WHERE artifact_id=?',(rec.artifact_id,)).fetchone()
        if old and old[0]!=text:raise GameOperationsError('GAME_OPS_ARTIFACT_RECORD_CONFLICT')
        if not old:
            with self.db:self.db.execute('INSERT INTO artifact_records VALUES(?,?)',(rec.artifact_id,text))
    def put_envelope(self,envelope:ArtifactEnvelope,stage_id:str,evidence=False):
        envelope.validate();data=canonical_json(asdict(envelope))
        rec=self.catalog.put_artifact(envelope.artifact_id,envelope.artifact_type,data,envelope.run_id,stage_id,[p.artifact_id for p in envelope.parent_refs],evidence,{'content_hash':envelope.content_hash})
        self._record(rec);return envelope.to_ref()
    def source_envelope(self,run_id,document_fingerprint,provenance_refs):
        sources=[ProvenanceSource(r.artifact_id,{'locator':r.locator,'role':r.role},'sha256:'+r.content_sha256) for r in provenance_refs]
        if not sources:raise GameOperationsError('GAME_OPS_PROVENANCE_REQUIRED')
        return ArtifactEnvelope.create('source.asset','1.0.0',run_id,ProducerIdentity('bie.game.operations','1.0.0','deterministic'),[],ProvenanceSummary(sources),{'kind':'game-runtime-input'},{'document_fingerprint':document_fingerprint})
    def derive(self,artifact_type,run_id,parents,payload,stage_id,provenance_sources,metadata=None,evidence=False):
        env=ArtifactEnvelope.create(artifact_type,'1.0.0',run_id,ProducerIdentity('bie.game.operations','1.0.0','deterministic'),list(parents),ProvenanceSummary(list(provenance_sources)),metadata or {},payload)
        return env,self.put_envelope(env,stage_id,evidence)
    def begin_job(self,key,fingerprint_value,run_id,session_id,owner):
        self.idempotency.claim(key,fingerprint_value,owner);row=self.db.execute('SELECT fingerprint,run_id,session_id,owner,state,checkpoint_json,result_ref,attempt FROM jobs WHERE job_key=?',(key,)).fetchone()
        if row:
            fp,rid,sid,prior_owner,state,cp,res,attempt=row
            if (fp,rid,sid)!=(fingerprint_value,run_id,session_id):raise GameOperationsError('GAME_OPS_JOB_CONFLICT')
            if state!='COMPLETED' and prior_owner!=owner:raise GameOperationsError('GAME_OPS_JOB_FOREIGN_OWNER')
            return {'state':state,'checkpoint':json.loads(cp),'result_ref':res,'attempt':attempt,'idempotent':state=='COMPLETED','resumed':state!='COMPLETED'}
        with self.db:self.db.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)',(key,fingerprint_value,run_id,session_id,owner,'RUNNING','{}',None,1,time.time()))
        return {'state':'RUNNING','checkpoint':{},'result_ref':None,'attempt':1,'idempotent':False,'resumed':False}
    def checkpoint(self,key,name,value):
        row=self.db.execute('SELECT checkpoint_json,state FROM jobs WHERE job_key=?',(key,)).fetchone()
        if not row or row[1]=='COMPLETED':raise GameOperationsError('GAME_OPS_JOB_CHECKPOINT_STATE')
        cp=json.loads(row[0]);cp[name]=value
        with self.db:self.db.execute('UPDATE jobs SET checkpoint_json=?,updated=? WHERE job_key=?',(canonical_json(cp).decode(),time.time(),key))
        return cp
    def complete(self,key,owner,result_ref):
        row=self.db.execute('SELECT state,result_ref FROM jobs WHERE job_key=?',(key,)).fetchone()
        if not row:raise GameOperationsError('GAME_OPS_JOB_UNKNOWN')
        if row[0]=='COMPLETED':
            if row[1]!=result_ref:raise GameOperationsError('GAME_OPS_JOB_RESULT_CONFLICT')
            return result_ref
        self.idempotency.complete(key,owner,result_ref)
        with self.db:self.db.execute("UPDATE jobs SET state='COMPLETED',result_ref=?,updated=? WHERE job_key=?",(result_ref,time.time(),key))
        return result_ref
    def close(self):self.idempotency.close();self.db.close()
