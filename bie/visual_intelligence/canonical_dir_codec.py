from __future__ import annotations
from dataclasses import dataclass,is_dataclass,asdict
from hashlib import sha256
from typing import Any,Mapping
import json
CANONICAL_DIR_COMMIT='73840d86a78e5f31438e2a1bad34f3b2a8433eb9'; CANONICAL_DIR_TREE='adf64727adaf2ec9dd92c8f1ea03e2df2b8d738c'; CANONICAL_DIR_MODULE_COUNT=71; CANONICAL_DIR_TASK_COUNT=59; CANONICAL_DIR_TEST_COUNT=683
class CanonicalDirCodecError(ValueError):pass
class ExactDirSourceUnavailableError(CanonicalDirCodecError):pass
class StaleCanonicalDirArtifactError(CanonicalDirCodecError):pass
@dataclass(frozen=True)
class CanonicalDirSourceReceipt:
 commit_sha:str;tree_sha:str;module_count:int;task_count:int;test_count:int;runtime_source_verified:bool=False
 def validate(self):
  if self.commit_sha!=CANONICAL_DIR_COMMIT or self.tree_sha!=CANONICAL_DIR_TREE:raise CanonicalDirCodecError('canonical DIR commit/tree mismatch')
  if self.module_count!=71 or self.task_count!=59 or self.test_count<683:raise CanonicalDirCodecError('canonical DIR counts mismatch')
@dataclass(frozen=True)
class DirPacket:
 handoff_id:str;revision:int;source_id:str;source_revision:int;narration_revision:int;visual_intents:tuple;timing_cues:tuple;evidence_refs:tuple[str,...];reasoning_refs:tuple[str,...];fingerprint:str;current:bool=True;review_required:bool=True;accepted:bool=False
def mp(x):
 if isinstance(x,Mapping):return dict(x)
 if is_dataclass(x):return asdict(x)
 if hasattr(x,'to_dict'):return dict(x.to_dict())
 if hasattr(x,'__dict__'):return dict(x.__dict__)
 raise CanonicalDirCodecError('artifact is not decodable')
def tok(v,n):
 if not isinstance(v,str) or not v.strip():raise CanonicalDirCodecError(n+' blank')
 return v.strip()
def rev(v,n):
 if isinstance(v,bool) or not isinstance(v,int) or v<1:raise CanonicalDirCodecError(n+' invalid')
 return v
def decode_canonical_dir_packet(raw,receipt,require_exact_runtime_source=True):
 receipt.validate()
 if require_exact_runtime_source and not receipt.runtime_source_verified:raise ExactDirSourceUnavailableError('canonical DIR source is not mounted/verified')
 d=mp(raw);required=('handoff_id','revision','source_id','source_revision','narration_revision','visual_intents','timing_cues')
 miss=[k for k in required if k not in d]
 if miss:raise CanonicalDirCodecError('missing fields:'+str(miss))
 if not d.get('current',True) or d.get('invalidated_by'):raise StaleCanonicalDirArtifactError('stale DIR handoff')
 ids=set();ev=set();rr=set();ins=[]
 for rawi in d['visual_intents']:
  i=mp(rawi);iid=tok(i.get('intent_id'),'intent_id')
  if iid in ids:raise CanonicalDirCodecError('duplicate intent')
  ids.add(iid);e=tuple(i.get('evidence_refs',()));r=tuple(i.get('reasoning_refs',()))
  if not e or not r:raise CanonicalDirCodecError('intent lineage missing')
  ev.update(e);rr.update(r);ins.append(i)
 nr=rev(d['narration_revision'],'narration_revision');cues=[]
 for rawc in d['timing_cues']:
  c=mp(rawc)
  if c.get('intent_id') not in ids:raise CanonicalDirCodecError('cue unknown intent')
  if c.get('narration_revision')!=nr:raise StaleCanonicalDirArtifactError('cue narration revision mismatch')
  if not isinstance(c.get('start_ms'),int) or not isinstance(c.get('end_ms'),int) or c['start_ms']<0 or c['end_ms']<=c['start_ms']:raise CanonicalDirCodecError('bad cue interval')
  cues.append(c)
 payload={'handoff_id':d['handoff_id'],'revision':d['revision'],'source_id':d['source_id'],'source_revision':d['source_revision'],'narration_revision':nr,'intents':ins,'cues':cues,'commit':receipt.commit_sha,'tree':receipt.tree_sha}
 f=sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
 return DirPacket(tok(d['handoff_id'],'handoff_id'),rev(d['revision'],'revision'),tok(d['source_id'],'source_id'),rev(d['source_revision'],'source_revision'),nr,tuple(ins),tuple(cues),tuple(sorted(ev)),tuple(sorted(rr)),f)
