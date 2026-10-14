"""Exact chained capture/parse amendment; byte authentication is not approval."""
from pathlib import Path
from hashlib import sha1,sha256
import json
D='docs/productization/task036-monitor-parse-amendment/'
DOCUMENT=D+'AMENDMENT.json'
DOCUMENT_SHA='a60c6bd3c343fcca66b44260040849c93e248fc8dd62a08ee6dbbb5640395df9'
PREVIOUS='docs/productization/task036-monitor-snapshot-amendment/AMENDMENT.json'
PREVIOUS_SHA='e54734d10ab9d0bcecc396c9b48e39496d3fcf3d72a15c1b06de3fc17769b10d'
M1='docs/productization/task036-motion-amendment/AMENDMENT.json'
M1_SHA='b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c'
TARGETS={
    'bie/compiler/chromium_resource_worker.py':(33561,'dea211dec77bbda9470c9f37331d236425c5dbf7dbf73d1769e8ba83e7c6f5eb','0b81e73273859de8a6dbd98e55a28f151e958c23',35814,'be4ac9863c6b5153568dec53d052e3d95973b4562e04d1efa2a0d8d5180e0aea'),
    'scripts/compiler_monitor_snapshot_amendment.py':(4898,'c21b98b6614c4bed85d0a101b410bd08322a04a6416e47cc543783515cd1b03a','b7ee86cb6b6d04e2b0171fb02b284cec38f8a2a5',5284,'227cfada9176f1c8f742cb05afaa909e70135ddf9cac251a795f393ad1f2ec6d'),
    '.gitattributes':(43758,'19ad19dce97c49b9c4cd90de345dc46afb3e4a408991b6e6945c79ce22eb1823','801341c120f949ea6a54753820e15dd2bc47d9b4',44112,'368b9b6744f1a6b7fa8a85b2e7e50b20da8b983e48358bb69239ecabeedfe654'),
}

def require(value,code):
    if not value:raise ValueError('MONITOR_PARSE_AMENDMENT_'+code)

def reader():
    try:from compiler_cache_source_amendment import regular,unique
    except ImportError:from scripts.compiler_cache_source_amendment import regular,unique
    return regular,unique

def validate(root,*,read=None):
    root=Path(root).resolve();regular,unique=reader()
    if read is not None:regular=read
    raw=regular(root,DOCUMENT,16384)
    require(sha256(raw).hexdigest()==DOCUMENT_SHA,'DOCUMENT')
    doc=json.loads(raw,object_pairs_hook=unique)
    require(doc['schema']=='bie.task036.monitor-parse-source-amendment/1' and
        doc['parent_commit']=='e8b07e9426c4d7d701b3b452e5be2c159cfbdc90' and
        doc['parent_tree']=='87094caefec2c20edef6fdead06274609004cb80' and
        doc['previous_monitor_sha256']==PREVIOUS_SHA and doc['original_m1_sha256']==M1_SHA and
        doc['policy']=='coherent-owned-capture-pure-parse-after-thaw/1' and
        doc['resource_limits_changed'] is False and doc['security_policy_weakened'] is False and
        doc['permission_errors_preserved'] is True and doc['terminal_after_error_omission'] is False and
        doc['pending_capture_generations']==1 and doc['pending_capture_max_bytes']==128*2*1024**2 and
        doc['partial_membership_sampling'] is False and doc['compiler_file_inventory_changed'] is False and
        doc['ordinary_task036_requires_current_review'] is True and
        doc['independent_review_status']=='REASSESSMENT_AND_ACTUAL_LINUX_RENDER_REQUIRED' and
        doc['accepted'] is False and doc['product_accepted'] is False,'SCOPE')
    for path,expected in ((PREVIOUS,PREVIOUS_SHA),(M1,M1_SHA)):
        require(sha256(regular(root,path,262144)).hexdigest()==expected,'HISTORICAL_SEAL')
    rows=doc['replacements']
    require(type(rows) is list and len(rows)==3 and
        {row['path'] for row in rows}==set(TARGETS),'TARGETS')
    allowed={DOCUMENT}
    for row in rows:
        path=row['path'];size,digest,blob,new_size,new_digest=TARGETS[path]
        before=D+Path(path).name+'.before';allowed.add(before)
        require(row==dict(path=path,preimage=before,original_bytes=size,original_sha256=digest,
            original_git_blob=blob,active_bytes=new_size,active_sha256=new_digest),'ROW')
        raw=regular(root,before,65536)
        require(len(raw)==size and sha256(raw).hexdigest()==digest and
            sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==blob,'PREIMAGE')
        if path=='.gitattributes':
            try:from compiler_monitor_binding_source_amendment import historical_attribute_bytes
            except ImportError:from scripts.compiler_monitor_binding_source_amendment import historical_attribute_bytes
            current=historical_attribute_bytes(root,read=regular).replace(b'\r\n',b'\n')
        else:current=regular(root,path,65536).replace(b'\r\n',b'\n')
        require(b'\r' not in current and len(current)==new_size and sha256(current).hexdigest()==new_digest,'ACTIVE')
    actual=set()
    for path in (root/D).rglob('*'):
        require(not path.is_symlink(),'UNLISTED_LINK')
        if path.is_file():actual.add(path.relative_to(root).as_posix())
    require(actual==allowed,'UNLISTED_PATH')
    return doc

def historical_bytes(root,path,*,read=None):
    """Fixed original-gate substitution AFTER full current authentication, no fallback."""
    doc=validate(root,read=read);regular,_=reader()
    if read is not None:regular=read
    require(path in TARGETS or path=='scripts/verify_post_dir.py','PATH')
    if path=='scripts/verify_post_dir.py':return regular(Path(root).resolve(),path,65536)
    size,digest,blob,_,_=TARGETS[path]
    raw=regular(Path(root).resolve(),D+Path(path).name+'.before',65536)
    require(len(raw)==size and sha256(raw).hexdigest()==digest and
        sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==blob,'PREIMAGE')
    return raw
