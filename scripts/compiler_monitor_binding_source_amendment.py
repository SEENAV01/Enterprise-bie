"""Exact raw-record EOL follow-on; authentication is not independent approval."""
from pathlib import Path
from hashlib import sha1,sha256
import json
D='docs/productization/task036-monitor-binding-amendment/'
DOCUMENT=D+'AMENDMENT.json'
DOCUMENT_SHA='4058b2a59b7e8fa68465389d2c8273c753729594dec2e55957c3cb3cf5af6dfa'
PREVIOUS='docs/productization/task036-monitor-parse-amendment/AMENDMENT.json'
PREVIOUS_SHA='a60c6bd3c343fcca66b44260040849c93e248fc8dd62a08ee6dbbb5640395df9'
TARGETS={
    '.gitattributes':(44112,'368b9b6744f1a6b7fa8a85b2e7e50b20da8b983e48358bb69239ecabeedfe654','04a28643550748fd0c9a59306027b5ab7b0bee99',44516,'6b5ffd6788ff349e53c7a32748c81e1c05160ccc6ad5ad271a1b1956c58ea4d9'),
    'scripts/compiler_monitor_parse_source_amendment.py':(4900,'b641f3a1665100a2d8ad2b64b25866292c8aa5b1562a39c9bb72f5208b9c7975','0bb20a86848149df31f0b93ca9182b2e6b70fe11',5246,'972ea3e88d489c12ea5896a635fe75a9f1d1c29e0d06eee4f49da77c06a80455')}

def require(value,code):
    if not value:raise ValueError('MONITOR_BINDING_AMENDMENT_'+code)

def validate(root,*,read=None):
    try:from compiler_cache_source_amendment import regular,unique
    except ImportError:from scripts.compiler_cache_source_amendment import regular,unique
    if read is not None:regular=read
    root=Path(root).resolve();raw=regular(root,DOCUMENT,16384)
    require(sha256(raw).hexdigest()==DOCUMENT_SHA,'DOCUMENT')
    doc=json.loads(raw,object_pairs_hook=unique)
    require(doc['schema']=='bie.task036.monitor-binding-source-amendment/1' and
        doc['scope']=='EXACT_NEW_REVIEW_SEAL_EOL_AND_CHAINED_ATTRIBUTE_ADMISSION_ONLY' and
        doc['parent_commit']=='ef6d83cccb938755890aebad9852a1fc6e246407' and
        doc['parent_tree']=='03bb5d9c501bd39c5bfd40e0239495be50e39ed8' and
        doc['previous_amendment_sha256']==PREVIOUS_SHA and
        doc['native_compiler_sources_changed'] is False and doc['resource_limits_changed'] is False and
        doc['security_policy_weakened'] is False and doc['product_accepted'] is False and
        doc['independent_review_status']=='EXACT_SOURCE_ADMISSION_REASSESSMENT_REQUIRED','SCOPE')
    require(sha256(regular(root,PREVIOUS,16384)).hexdigest()==PREVIOUS_SHA,'PREVIOUS_SEAL')
    rows=doc['replacements']
    require(type(rows) is list and len(rows)==2 and {r['path'] for r in rows}==set(TARGETS),'TARGETS')
    allowed={DOCUMENT}
    for row in rows:
        path=row['path'];size,digest,blob,new_size,new_digest=TARGETS[path]
        before=D+Path(path).name+'.before';allowed.add(before)
        require(row==dict(path=path,preimage=before,original_bytes=size,original_sha256=digest,
            original_git_blob=blob,active_bytes=new_size,active_sha256=new_digest),'ROW')
        raw=regular(root,before,65536)
        require(len(raw)==size and sha256(raw).hexdigest()==digest and
            sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==blob,'PREIMAGE')
        active=regular(root,path,65536).replace(b'\r\n',b'\n')
        require(b'\r' not in active and len(active)==new_size and sha256(active).hexdigest()==new_digest,'ACTIVE')
    actual=set()
    for path in (root/D).rglob('*'):
        require(not path.is_symlink(),'UNLISTED_LINK')
        if path.is_file():actual.add(path.relative_to(root).as_posix())
    require(actual==allowed,'UNLISTED_PATH')
    return doc

def historical_attribute_bytes(root,*,read=None):
    validate(root,read=read)
    try:from compiler_cache_source_amendment import regular
    except ImportError:from scripts.compiler_cache_source_amendment import regular
    if read is not None:regular=read
    raw=regular(Path(root).resolve(),D+'.gitattributes.before',65536)
    size,digest,blob,_,_=TARGETS['.gitattributes']
    require(len(raw)==size and sha256(raw).hexdigest()==digest and
        sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==blob,'PREIMAGE')
    return raw
