"""Exact pinned final-stitch input reconciliation; no current-byte self-blessing."""
from hashlib import sha256, sha1
import json
from pathlib import Path

DOCUMENT='docs/productization/task036-stitch-input-amendment/AMENDMENT.json'
DOCUMENT_SHA256='aa24676ce86cc5e9dc64579139ffd43dac3fddc1ed61fae289d86a26ace7e102'
PREVIOUS_DOCUMENT='docs/productization/task036-media-source-pin-amendment/AMENDMENT.json'
PREVIOUS_SHA256='101ba72e26da7f25ff4807111548987e1414f7c3d4a05d99b3338939f69e53b8'
DIRECTORY='docs/productization/task036-stitch-input-amendment/'
TARGETS=frozenset({'bie/compiler/qa_support/bounded_media_threads.cjs','bie/compiler/real_paint.py',
    'scripts/compiler_media_source_pin_amendment.py','scripts/compiler_media_policy_observation_amendment.py'})
HELPER='bie/compiler/qa_support/bounded_media_threads.cjs'
HELPER_SHA256='2f2788895f598cea5c37449f1b54761c420a9c03e0d4e56cf4bd8fdd84fd0bb9'
M1_DOCUMENT='docs/productization/task036-motion-amendment/AMENDMENT.json'
M1_SHA256='b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c'


def validate(root):
    try:
        from compiler_cache_source_amendment import regular, unique
    except ImportError:
        from scripts.compiler_cache_source_amendment import regular, unique
    root=Path(root).resolve()
    raw=regular(root,DOCUMENT,16*1024).replace(b'\r\n',b'\n')
    if b'\r' in raw or sha256(raw).hexdigest()!=DOCUMENT_SHA256:raise ValueError('STITCH_INPUT_DOCUMENT')
    doc=json.loads(raw,object_pairs_hook=unique)
    if (set(doc)!={'schema','authority','scope','parent_commit','parent_tree','previous_amendment_sha256',
            'original_m1_sha256','helper_path','helper_bytes','helper_sha256','replacements',
            'runtime_policy','source_evidence','original_arguments_conserved','limits_unchanged',
            'product_accepted','independent_review_status'} or
        doc['schema']!='bie.task036.stitch-input-amendment/1' or
        doc['parent_commit']!='17da2a5a24d8dec3065bc8a292fb848e423a9bb5' or
        doc['parent_tree']!='6006d4c45dcdad92fe108dad4db4b300354cfc06' or
        doc['previous_amendment_sha256']!=PREVIOUS_SHA256 or doc['original_m1_sha256']!=M1_SHA256 or
        doc['helper_path']!=HELPER or type(doc['helper_bytes']) is not int or doc['helper_bytes']!=4440 or
        doc['helper_sha256']!=HELPER_SHA256 or doc['product_accepted'] is not False or
        doc['original_arguments_conserved'] is not True or doc['limits_unchanged'] is not True or
        len(doc['replacements'])!=4 or {r['path'] for r in doc['replacements']}!=TARGETS or
        doc['runtime_policy']!={'schema':'bie.comp-m1.media-threads/1','profile':'producer-motion-v1',
            'remotion_version':'4.0.506','decoder_threads':1,'encoder_threads':1,'filter_threads':1}):
        raise ValueError('STITCH_INPUT_SCOPE')
    for path,expected in ((PREVIOUS_DOCUMENT,PREVIOUS_SHA256),(M1_DOCUMENT,M1_SHA256),
        ('docs/productization/task036-media-policy-observation-amendment/AMENDMENT.json',
            'ec4108cd8307b6c6511e61cd43e39a78ed5b8e92b6f3611b65ad365f03096fc4')):
        if sha256(regular(root,path,256*1024).replace(b'\r\n',b'\n')).hexdigest()!=expected:
            raise ValueError('STITCH_INPUT_PREVIOUS_DOCUMENT')
    # Authenticate all sealed direct-parent preimages and every unlisted active
    # path of both adjacent amendments. Do not recursively call older resolvers.
    for name in (PREVIOUS_DOCUMENT,'docs/productization/task036-media-policy-observation-amendment/AMENDMENT.json'):
        prior=json.loads(regular(root,name,16*1024),object_pairs_hook=unique)
        for row in prior['replacements']:
            old=regular(root,row['preimage'],64*1024)
            if (len(old)!=row['original_bytes'] or sha256(old).hexdigest()!=row['original_sha256'] or
                sha1(b'blob '+str(len(old)).encode()+b'\0'+old).hexdigest()!=row['original_git_blob']):
                raise ValueError('STITCH_INPUT_PRIOR_PREIMAGE')
            if row['path'] not in TARGETS:
                active=regular(root,row['path'],64*1024).replace(b'\r\n',b'\n')
                if len(active)!=row['active_bytes'] or sha256(active).hexdigest()!=row['active_sha256']:
                    raise ValueError('STITCH_INPUT_UNLISTED_CHANGE')
    for row in doc['replacements']:
        if (set(row)!={'path','preimage','original_bytes','original_sha256','original_git_blob','active_bytes','active_sha256'} or
            row['preimage']!=DIRECTORY+Path(row['path']).name+'.before' or
            type(row['original_bytes']) is not int or type(row['active_bytes']) is not int):
            raise ValueError('STITCH_INPUT_ROW')
        old=regular(root,row['preimage'],64*1024)
        if (len(old)!=row['original_bytes'] or sha256(old).hexdigest()!=row['original_sha256'] or
            sha1(b'blob '+str(len(old)).encode()+b'\0'+old).hexdigest()!=row['original_git_blob']):
            raise ValueError('STITCH_INPUT_PREIMAGE')
        active=regular(root,row['path'],64*1024).replace(b'\r\n',b'\n')
        if b'\r' in active or len(active)!=row['active_bytes'] or sha256(active).hexdigest()!=row['active_sha256']:
            raise ValueError('STITCH_INPUT_ACTIVE')
    return doc


def authenticated_previous_bytes(root,path,expected):
    if path not in TARGETS:raise ValueError('STITCH_INPUT_UNLISTED_TARGET')
    doc=validate(root)
    row,=[r for r in doc['replacements'] if r['path']==path]
    if row['original_sha256']!=expected:raise ValueError('STITCH_INPUT_PARENT')
    try:
        from compiler_cache_source_amendment import regular
    except ImportError:
        from scripts.compiler_cache_source_amendment import regular
    return regular(Path(root).resolve(),row['preimage'],64*1024)
