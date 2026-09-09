from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
import hashlib, json, os, tempfile

class ArtifactStoreError(ValueError): pass

def sha256_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

@dataclass(frozen=True)
class BlobRef:
    algorithm:str
    digest:str
    size:int
    def validate(self):
        if self.algorithm!="sha256": raise ArtifactStoreError("unsupported digest algorithm")
        if len(self.digest)!=64 or any(c not in "0123456789abcdef" for c in self.digest):
            raise ArtifactStoreError("invalid sha256 digest")
        if self.size<0: raise ArtifactStoreError("invalid blob size")

@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id:str
    artifact_type:str
    blob:BlobRef
    run_id:str
    stage_id:str
    parent_artifact_ids:List[str]=field(default_factory=list)
    evidence:bool=False
    metadata:Dict[str,object]=field(default_factory=dict)

    def validate(self):
        if not self.artifact_id or not self.artifact_type or not self.run_id or not self.stage_id:
            raise ArtifactStoreError("artifact record identity fields required")
        self.blob.validate()
        if self.artifact_id in self.parent_artifact_ids:
            raise ArtifactStoreError("artifact cannot parent itself")

class FileSystemCAS:
    def __init__(self,root:Path):
        self.root=Path(root)
        (self.root/"blobs"/"sha256").mkdir(parents=True,exist_ok=True)

    def _path(self,digest:str)->Path:
        return self.root/"blobs"/"sha256"/digest[:2]/digest

    def put_bytes(self,data:bytes)->BlobRef:
        digest=sha256_bytes(data); ref=BlobRef("sha256",digest,len(data)); path=self._path(digest)
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            existing=path.read_bytes()
            if sha256_bytes(existing)!=digest:
                raise ArtifactStoreError("existing CAS blob corrupted")
            return ref
        fd,tmp=tempfile.mkstemp(prefix=".cas-",dir=str(path.parent))
        try:
            with os.fdopen(fd,"wb") as f:
                f.write(data); f.flush(); os.fsync(f.fileno())
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
        return ref

    def get_bytes(self,ref:BlobRef)->bytes:
        ref.validate(); path=self._path(ref.digest)
        if not path.exists(): raise ArtifactStoreError("blob missing")
        data=path.read_bytes()
        if len(data)!=ref.size or sha256_bytes(data)!=ref.digest:
            raise ArtifactStoreError("blob integrity verification failed")
        return data

    def exists(self,ref:BlobRef)->bool:
        try:self.get_bytes(ref);return True
        except ArtifactStoreError:return False

class ArtifactCatalog:
    def __init__(self,cas:FileSystemCAS):
        self.cas=cas
        self.records:Dict[str,ArtifactRecord]={}
        self.by_run:Dict[str,Set[str]]={}
        self.by_stage:Dict[tuple,Set[str]]={}
        self.children:Dict[str,Set[str]]={}

    def register(self,record:ArtifactRecord)->None:
        record.validate()
        if not self.cas.exists(record.blob):
            raise ArtifactStoreError("artifact references missing/corrupt blob")
        existing=self.records.get(record.artifact_id)
        if existing is not None:
            if existing!=record:
                raise ArtifactStoreError("artifact id already registered with different immutable record")
            return
        for parent in record.parent_artifact_ids:
            if parent not in self.records:
                raise ArtifactStoreError(f"missing parent artifact {parent}")
        self.records[record.artifact_id]=record
        self.by_run.setdefault(record.run_id,set()).add(record.artifact_id)
        self.by_stage.setdefault((record.run_id,record.stage_id),set()).add(record.artifact_id)
        for p in record.parent_artifact_ids:self.children.setdefault(p,set()).add(record.artifact_id)

    def put_artifact(self,artifact_id:str,artifact_type:str,data:bytes,run_id:str,stage_id:str,
                     parent_artifact_ids:Optional[List[str]]=None,evidence:bool=False,
                     metadata:Optional[Dict[str,object]]=None)->ArtifactRecord:
        blob=self.cas.put_bytes(data)
        rec=ArtifactRecord(artifact_id,artifact_type,blob,run_id,stage_id,
                           list(parent_artifact_ids or []),evidence,dict(metadata or {}))
        self.register(rec);return rec

    def get_record(self,artifact_id:str)->ArtifactRecord:
        if artifact_id not in self.records: raise ArtifactStoreError("artifact not found")
        return self.records[artifact_id]

    def read_artifact(self,artifact_id:str)->bytes:
        return self.cas.get_bytes(self.get_record(artifact_id).blob)

    def artifacts_for_run(self,run_id:str)->List[ArtifactRecord]:
        return [self.records[x] for x in sorted(self.by_run.get(run_id,set()))]

    def artifacts_for_stage(self,run_id:str,stage_id:str)->List[ArtifactRecord]:
        return [self.records[x] for x in sorted(self.by_stage.get((run_id,stage_id),set()))]

    def evidence_for_run(self,run_id:str)->List[ArtifactRecord]:
        return [r for r in self.artifacts_for_run(run_id) if r.evidence]

    def parents_of(self,artifact_id:str)->List[ArtifactRecord]:
        r=self.get_record(artifact_id)
        return [self.records[x] for x in r.parent_artifact_ids]

    def children_of(self,artifact_id:str)->List[ArtifactRecord]:
        self.get_record(artifact_id)
        return [self.records[x] for x in sorted(self.children.get(artifact_id,set()))]

    def trace_to_roots(self,artifact_id:str)->Set[str]:
        roots=set(); visiting=set()
        def walk(aid):
            if aid in visiting: raise ArtifactStoreError("lineage cycle detected")
            visiting.add(aid); r=self.get_record(aid)
            if not r.parent_artifact_ids: roots.add(aid)
            else:
                for p in r.parent_artifact_ids:walk(p)
            visiting.remove(aid)
        walk(artifact_id);return roots

    def verify_all(self)->List[str]:
        bad=[]
        for aid,r in self.records.items():
            if not self.cas.exists(r.blob):bad.append(aid)
        return sorted(bad)
