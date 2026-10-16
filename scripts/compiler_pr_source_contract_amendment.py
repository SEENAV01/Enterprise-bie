"""Exact PR preservation compatibility; immutable predecessor bytes, no waiver.

Only the fixed four-path current amendment is admitted. Historical seals and
caller inventories keep their meanings. Legacy active-producer tamper codes
remain stable; document/preimage/unlisted/rollback failures are not remapped.
"""
from hashlib import sha1, sha256
import json
from pathlib import Path

DOCUMENT='docs/productization/task036-pr-source-contract-amendment/AMENDMENT.json'
DOCUMENT_SHA256='5f0e67c886dcd312034d0de2f0ce18943a381a6c20e3effa201e22643a3b3b54'
DIRECTORY='docs/productization/task036-pr-source-contract-amendment/'
PREVIOUS_DOCUMENT='docs/productization/task036-stitch-input-amendment/AMENDMENT.json'
PREVIOUS_SHA256='aa24676ce86cc5e9dc64579139ffd43dac3fddc1ed61fae289d86a26ace7e102'
M1_DOCUMENT='docs/productization/task036-motion-amendment/AMENDMENT.json'
M1_SHA256='b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c'
CACHE='bie/compiler/qa_support/remotion_raster_capture.cjs'
PAINT='bie/compiler/real_paint.py'
TARGETS=frozenset({CACHE,'scripts/compiler_stitch_input_amendment.py',
    'scripts/compiler_media_policy_observation_amendment.py','scripts/compiler_media_source_pin_amendment.py'})

def reader():
    try:
        from compiler_cache_source_amendment import regular, unique, MANIFEST, MANIFEST_SHA
    except ImportError:
        from scripts.compiler_cache_source_amendment import regular, unique, MANIFEST, MANIFEST_SHA
    return regular, unique, MANIFEST, MANIFEST_SHA

def original(root,row,regular):
    raw=regular(root,row['preimage'],64*1024)
    if (len(raw)!=row['original_bytes'] or sha256(raw).hexdigest()!=row['original_sha256'] or
            sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=row['original_git_blob']):
        raise ValueError('PR_SOURCE_CONTRACT_PREIMAGE')
    return raw

def validate(root):
    regular,unique,manifest,manifest_sha=reader();root=Path(root).resolve()
    raw=regular(root,DOCUMENT,16*1024)
    if sha256(raw).hexdigest()!=DOCUMENT_SHA256:raise ValueError('PR_SOURCE_CONTRACT_DOCUMENT')
    doc=json.loads(raw,object_pairs_hook=unique)
    if (set(doc)!={'schema','authority','scope','parent_commit','parent_tree','original_m1_sha256',
            'original_manifest_sha256','previous_amendment_sha256','replacements',
            'rendering_semantics_and_limits_unchanged','product_accepted','independent_review_status','failure_evidence'} or
            doc['schema']!='bie.task036.pr-source-contract-amendment/1' or
            doc['parent_commit']!='2b8b63e328b6dc8a7ffa239f8610d24a39677062' or
            doc['parent_tree']!='af39e0379fdadf0440a216c226295ff3009b40aa' or
            doc['original_m1_sha256']!=M1_SHA256 or doc['original_manifest_sha256']!=manifest_sha or
            doc['previous_amendment_sha256']!=PREVIOUS_SHA256 or
            doc['rendering_semantics_and_limits_unchanged'] is not True or doc['product_accepted'] is not False or
            len(doc['replacements'])!=4 or {r['path'] for r in doc['replacements']}!=TARGETS):
        raise ValueError('PR_SOURCE_CONTRACT_SCOPE')
    for path,expected,budget in ((PREVIOUS_DOCUMENT,PREVIOUS_SHA256,16*1024),
            (M1_DOCUMENT,M1_SHA256,256*1024),('manifests/'+manifest,manifest_sha,42*1024**2)):
        sealed=regular(root,path,budget).replace(b'\r\n',b'\n')
        if b'\r' in sealed or sha256(sealed).hexdigest()!=expected:
            raise ValueError('PR_SOURCE_CONTRACT_PREVIOUS_DOCUMENT')
    prior=json.loads(regular(root,PREVIOUS_DOCUMENT,16*1024),object_pairs_hook=unique)
    for row in doc['replacements']:
        if (set(row)!={'path','preimage','original_bytes','original_sha256','original_git_blob','active_bytes','active_sha256'} or
                row['preimage']!=DIRECTORY+Path(row['path']).name+'.before' or
                type(row['original_bytes']) is not int or not 0<row['original_bytes']<=65536 or
                type(row['active_bytes']) is not int or not 0<row['active_bytes']<=65536):
            raise ValueError('PR_SOURCE_CONTRACT_ROW')
        original(root,row,regular)
        active=regular(root,row['path'],64*1024).replace(b'\r\n',b'\n')
        if b'\r' in active or len(active)!=row['active_bytes'] or sha256(active).hexdigest()!=row['active_sha256']:
            # This is precisely the current legacy cache producer, not a catch
            # or relabel of arbitrary nested document/preimage failures.
            if row['path']==CACHE:raise ValueError('COMP_CACHE_AMENDMENT_ACTIVE_BYTES')
            raise ValueError('PR_SOURCE_CONTRACT_ACTIVE_BYTES')
    # The fixed parent seal authenticates every unrelated active path and its
    # immutable preimage, including the exact unchanged paint producer. This
    # check preserves its legacy code without widening the four-path scope.
    for row in prior['replacements']:
        original(root,row,regular)
        if row['path'] not in TARGETS:
            active=regular(root,row['path'],64*1024).replace(b'\r\n',b'\n')
            if b'\r' in active or len(active)!=row['active_bytes'] or sha256(active).hexdigest()!=row['active_sha256']:
                if row['path']==PAINT:raise ValueError('COMP_PAINT_AMENDMENT_ACTIVE_BYTES')
                raise ValueError('PR_SOURCE_CONTRACT_UNLISTED_ACTIVE_BYTES')
    return doc

def authenticated_previous_bytes(root,path,expected):
    if path not in TARGETS:raise ValueError('PR_SOURCE_CONTRACT_UNLISTED_TARGET')
    doc=validate(root);row,=[r for r in doc['replacements'] if r['path']==path]
    if row['original_sha256']!=expected:raise ValueError('PR_SOURCE_CONTRACT_PARENT_IDENTITY')
    regular,_,_,_=reader()
    return original(Path(root).resolve(),row,regular)
