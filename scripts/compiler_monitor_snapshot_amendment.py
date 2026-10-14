"""Exact follow-on monitor preservation, not approval or a native render verdict.

The original ledgers and M1 seal retain their meanings. Expected bytes are fixed
development/review constants, NEVER recomputed from current files at admission.
This new gate authenticates all replacements plus exact historical Git preimages.
"""
from hashlib import sha1,sha256
import json
from pathlib import Path

DOCUMENT='docs/productization/task036-monitor-snapshot-amendment/AMENDMENT.json'
DIRECTORY='docs/productization/task036-monitor-snapshot-amendment/'
DOCUMENT_SHA256='e54734d10ab9d0bcecc396c9b48e39496d3fcf3d72a15c1b06de3fc17769b10d'
M1_DOCUMENT='docs/productization/task036-motion-amendment/AMENDMENT.json'
M1_SHA256='b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c'
INDEX='docs/productization/m1-review/SOURCE_CHAIN_A24EF1CD.json'
INDEX_SHA256='1b60a9dc298e62b2c34a75c0959222abab2738801ba3d6dc2ce2e22e76f658ed'
PARENT='9f6b2560b50375e9426add0071c693faf46734ac'
PARENT_TREE='529355cfc97a894d2162260320c70625b9a2c2b0'
POLICY='owned-leaf-quiescent-proc-observation/1'
TARGETS={
    'bie/compiler/chromium_resource_worker.py': (28552,'aeedfc527fb47df33c448ad2bf1a2553574015e3124a14e35fae1e94f75c2963','a5153925d4a4b940d0778e5018cc332f1ad08bdc',33561,'dea211dec77bbda9470c9f37331d236425c5dbf7dbf73d1769e8ba83e7c6f5eb'),
    'scripts/verify_post_dir.py': (6136,'5ac8affa8795961faf8afeb03a667b3eff10dda81e00984ce2520f9def5bac0f','7e143f40df1405c53ac75b96475e09365807be1d',6360,'9a445227e09fd487139b2dbd7be67d83af4b412b5a5f2c7be5a0f2a0120d15c8'),
    '.gitattributes': (43352,'09543bce9b1b46452ac54bcf201242d094255f89ce98ca3ca5f453ff29e67d9b','03efa1c198a882c85d97749ad0718f1c97978b8e',43758,'19ad19dce97c49b9c4cd90de345dc46afb3e4a408991b6e6945c79ce22eb1823'),
}

def require(value,code):
    if not value:raise ValueError('MONITOR_AMENDMENT_'+code)

def reader():
    try:
        from compiler_cache_source_amendment import regular,unique
    except ImportError:
        from scripts.compiler_cache_source_amendment import regular,unique
    return regular,unique

def validate(root):
    root=Path(root).resolve();regular,unique=reader()
    raw=regular(root,DOCUMENT,16384)
    require(sha256(raw).hexdigest()==DOCUMENT_SHA256,'DOCUMENT')
    document=json.loads(raw,object_pairs_hook=unique)
    require(document['schema']=='bie.task036.monitor-snapshot-source-amendment/1' and
        document['parent_commit']==PARENT and document['parent_tree']==PARENT_TREE and
        document['original_m1_sha256']==M1_SHA256 and
        document['reviewed_source_index_sha256']==INDEX_SHA256 and
        document['monitor_policy']==POLICY and document['accepted'] is False and
        document['product_accepted'] is False and document['permission_errors_preserved'] is True and
        document['terminal_after_error_omission'] is False and
        document['compiler_file_inventory_changed'] is False and
        document['resource_limits_unchanged'] is True and
        document['execution_scheduling_changed'] is True,'SCOPE')
    for path,expected,limit in ((M1_DOCUMENT,M1_SHA256,262144),(INDEX,INDEX_SHA256,131072)):
        require(sha256(regular(root,path,limit)).hexdigest()==expected,'PREVIOUS_AUTHORITY')
    rows=document['replacements']
    require(type(rows) is list and len(rows)==3 and {row['path'] for row in rows}==set(TARGETS),'TARGETS')
    allowed={DOCUMENT}
    for row in rows:
        path=row['path'];before_size,before_sha,blob,active_size,active_sha=TARGETS[path]
        preimage=DIRECTORY+Path(path).name+'.before';allowed.add(preimage)
        require(row==dict(path=path,preimage=preimage,original_bytes=before_size,
            original_sha256=before_sha,original_git_blob=blob,active_bytes=active_size,
            active_sha256=active_sha),'ROW')
        original=regular(root,preimage,65536)
        require(len(original)==before_size and sha256(original).hexdigest()==before_sha and
            sha1(b'blob '+str(len(original)).encode()+b'\0'+original).hexdigest()==blob,'PREIMAGE')
        # Exact follow-on supplies authenticated prior bytes, never a hash waiver.
        # All new replacements are checked before any prior byte is usable.
        try:
            from compiler_monitor_parse_source_amendment import historical_bytes
        except ImportError:
            from scripts.compiler_monitor_parse_source_amendment import historical_bytes
        active=historical_bytes(root,path,read=regular).replace(b'\r\n',b'\n')
        require(b'\r' not in active and len(active)==active_size and
            sha256(active).hexdigest()==active_sha,'ACTIVE_BYTES')
    actual=set()
    for path in (root/DIRECTORY).rglob('*'):
        require(not path.is_symlink(),'UNLISTED_LINK')
        if path.is_file():actual.add(path.relative_to(root).as_posix())
    require(actual==allowed,'UNLISTED_PATH')
    return document

def authenticated_original_worker(root):
    """Only the fixed current worker and its sealed original; never a fallback.

    This verifies bytes, NOT independent review. A consumer must additionally
    authenticate actual current review authority before using this replacement.
    """
    validate(root);regular,_=reader()
    return regular(Path(root).resolve(),DIRECTORY+'chromium_resource_worker.py.before',65536)
