"""Exact pinned-helper integration repair; immutable preimages, no hash waiver."""
from hashlib import sha256, sha1
import json
from pathlib import Path

DOCUMENT='docs/productization/task036-media-source-pin-amendment/AMENDMENT.json'
DOCUMENT_SHA256='101ba72e26da7f25ff4807111548987e1414f7c3d4a05d99b3338939f69e53b8'
PREVIOUS_DOCUMENT='docs/productization/task036-media-policy-observation-amendment/AMENDMENT.json'
PREVIOUS_SHA256='ec4108cd8307b6c6511e61cd43e39a78ed5b8e92b6f3611b65ad365f03096fc4'
DIRECTORY='docs/productization/task036-media-source-pin-amendment/'
TARGETS=frozenset({'bie/compiler/real_paint.py','scripts/compiler_media_policy_observation_amendment.py'})
HELPER='bie/compiler/qa_support/bounded_media_threads.cjs'
HELPER_SHA256='af0eae48357c10fbdfbda113b945c9f443684dac593b56d2049f57502f5b6ad5'


def stitch_input_preimage(root,path,expected):
    try:
        from compiler_stitch_input_amendment import authenticated_previous_bytes
    except ImportError:
        from scripts.compiler_stitch_input_amendment import authenticated_previous_bytes
    return authenticated_previous_bytes(root,path,expected)


def validate(root):
    try:
        from compiler_cache_source_amendment import regular, unique
    except ImportError:
        from scripts.compiler_cache_source_amendment import regular, unique
    root=Path(root).resolve()
    # Authenticate the latest chain even if every active file was rolled back
    # together to this historical amendment's bytes. The latest resolver does
    # not call older validators, so this cannot recurse through the chain.
    try:
        from compiler_stitch_input_amendment import validate as latest
    except ImportError:
        from scripts.compiler_stitch_input_amendment import validate as latest
    latest(root)
    try:
        from compiler_pr_source_contract_amendment import authenticated_previous_bytes as current_preimage
    except ImportError:
        from scripts.compiler_pr_source_contract_amendment import authenticated_previous_bytes as current_preimage
    raw=regular(root,DOCUMENT,16*1024).replace(b'\r\n',b'\n')
    if b'\r' in raw or sha256(raw).hexdigest()!=DOCUMENT_SHA256:
        raise ValueError('MEDIA_SOURCE_PIN_DOCUMENT')
    doc=json.loads(raw,object_pairs_hook=unique)
    if (set(doc)!={'schema','authority','scope','parent_commit','parent_tree','previous_amendment_sha256',
            'original_m1_sha256','helper_path','helper_bytes','helper_sha256','replacements',
            'rendering_and_resource_limits_unchanged','product_accepted','independent_review_status'} or
        doc['schema']!='bie.task036.media-source-pin-amendment/1' or
        doc['parent_commit']!='f55f6915647816edc14cdb5ad043dedd2cdb39b2' or
        doc['parent_tree']!='2d71be0c97dee32f0614ef1356393340a18aeaae' or
        doc['previous_amendment_sha256']!=PREVIOUS_SHA256 or
        doc['original_m1_sha256']!='b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c' or
        doc['helper_path']!=HELPER or type(doc['helper_bytes']) is not int or doc['helper_bytes']!=3632 or
        doc['helper_sha256']!=HELPER_SHA256 or doc['rendering_and_resource_limits_unchanged'] is not True or
        doc['product_accepted'] is not False or len(doc['replacements'])!=2 or
        {row['path'] for row in doc['replacements']}!=TARGETS):
        raise ValueError('MEDIA_SOURCE_PIN_SCOPE')
    prior_raw=regular(root,PREVIOUS_DOCUMENT,16*1024).replace(b'\r\n',b'\n')
    if sha256(prior_raw).hexdigest()!=PREVIOUS_SHA256:raise ValueError('MEDIA_SOURCE_PIN_PREVIOUS_DOCUMENT')
    prior=json.loads(prior_raw,object_pairs_hook=unique)
    for row in prior['replacements']:
        if row['path'] not in TARGETS:
            active=regular(root,row['path'],64*1024).replace(b'\r\n',b'\n')
            if row['path']=='bie/compiler/qa_support/remotion_raster_capture.cjs':
                active=current_preimage(root,row['path'],row['active_sha256'])
            if row['path']==HELPER and sha256(active).hexdigest()!=row['active_sha256']:
                active=stitch_input_preimage(root,row['path'],row['active_sha256'])
            if len(active)!=row['active_bytes'] or sha256(active).hexdigest()!=row['active_sha256']:
                raise ValueError('MEDIA_SOURCE_PIN_UNLISTED_CHANGE')
    helper=regular(root,HELPER,64*1024).replace(b'\r\n',b'\n')
    if sha256(helper).hexdigest()!=HELPER_SHA256:
        helper=stitch_input_preimage(root,HELPER,HELPER_SHA256)
    if len(helper)!=3632 or sha256(helper).hexdigest()!=HELPER_SHA256:raise ValueError('MEDIA_SOURCE_PIN_HELPER')
    for row in doc['replacements']:
        if (set(row)!={'path','preimage','original_bytes','original_sha256','original_git_blob','active_bytes','active_sha256'} or
            row['preimage']!=DIRECTORY+Path(row['path']).name+'.before'):
            raise ValueError('MEDIA_SOURCE_PIN_ROW')
        old=regular(root,row['preimage'],64*1024)
        blob=sha1(b'blob '+str(len(old)).encode()+b'\0'+old).hexdigest()
        if (len(old)!=row['original_bytes'] or sha256(old).hexdigest()!=row['original_sha256'] or
            blob!=row['original_git_blob']):raise ValueError('MEDIA_SOURCE_PIN_PREIMAGE')
        current=regular(root,row['path'],64*1024).replace(b'\r\n',b'\n')
        if sha256(current).hexdigest()!=row['active_sha256']:
            current=stitch_input_preimage(root,row['path'],row['active_sha256'])
        if b'\r' in current or len(current)!=row['active_bytes'] or sha256(current).hexdigest()!=row['active_sha256']:
            raise ValueError('MEDIA_SOURCE_PIN_ACTIVE')
    return doc


def authenticated_previous_bytes(root,path,expected):
    if path not in TARGETS:raise ValueError('MEDIA_SOURCE_PIN_UNLISTED_TARGET')
    doc=validate(root)
    row,=[r for r in doc['replacements'] if r['path']==path]
    if row['original_sha256']!=expected:raise ValueError('MEDIA_SOURCE_PIN_PARENT')
    try:
        from compiler_cache_source_amendment import regular
    except ImportError:
        from scripts.compiler_cache_source_amendment import regular
    return regular(Path(root).resolve(),row['preimage'],64*1024)
