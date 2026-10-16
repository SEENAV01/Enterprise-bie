"""Exact failure-only policy observation chain; no arbitrary source exception."""
from hashlib import sha256, sha1
import json
from pathlib import Path

DOCUMENT='docs/productization/task036-media-policy-observation-amendment/AMENDMENT.json'
DOCUMENT_SHA256='ec4108cd8307b6c6511e61cd43e39a78ed5b8e92b6f3611b65ad365f03096fc4'
PREVIOUS_DOCUMENT='docs/productization/task036-media-thread-amendment/AMENDMENT.json'
PREVIOUS_SHA256='6b08edb6b6bbacba67c1c87780809a449a8073dbf882cf5e35a247a81ddc940c'
DIRECTORY='docs/productization/task036-media-policy-observation-amendment/'
TARGETS=frozenset({'bie/compiler/qa_support/remotion_raster_capture.cjs','bie/compiler/qa_support/bounded_media_threads.cjs',
    'bie/compiler/real_paint.py','scripts/compiler_media_thread_amendment.py'})


def validate(root):
    try:
        from compiler_cache_source_amendment import regular, unique, MANIFEST, MANIFEST_SHA
    except ImportError:
        from scripts.compiler_cache_source_amendment import regular, unique, MANIFEST, MANIFEST_SHA
    root=Path(root).resolve()
    raw=regular(root,DOCUMENT,16*1024).replace(b'\r\n',b'\n')
    if b'\r' in raw or sha256(raw).hexdigest()!=DOCUMENT_SHA256:
        raise ValueError('MEDIA_POLICY_OBSERVATION_DOCUMENT')
    doc=json.loads(raw,object_pairs_hook=unique)
    if (set(doc)!={'schema','authority','scope','parent_commit','parent_tree','previous_amendment_sha256',
            'original_m1_sha256','original_manifest_sha256','replacements','native_calls_and_limits_unchanged',
            'diagnostic_schema','product_accepted','independent_review_status'} or
            doc['schema']!='bie.task036.media-policy-observation-source-amendment/1' or
            doc['parent_commit']!='2e08e31b1f16d044af3204d0e12afab5362a9765' or
            doc['parent_tree']!='c1e8262c568a60e4a232c3a5e1b124a101622bff' or
            doc['previous_amendment_sha256']!=PREVIOUS_SHA256 or
            doc['original_m1_sha256']!='b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c' or
            doc['original_manifest_sha256']!=MANIFEST_SHA or doc['native_calls_and_limits_unchanged'] is not True or
            doc['diagnostic_schema']!='bie.capture-controller-failure/2' or doc['product_accepted'] is not False or
            len(doc['replacements'])!=4 or {r['path'] for r in doc['replacements']}!=TARGETS):
        raise ValueError('MEDIA_POLICY_OBSERVATION_SCOPE')
    for path,expected,budget in ((PREVIOUS_DOCUMENT,PREVIOUS_SHA256,16*1024),
        ('docs/productization/task036-motion-amendment/AMENDMENT.json',doc['original_m1_sha256'],256*1024),
        ('docs/productization/task036-capture-observation-amendment/AMENDMENT.json','1526b7588616a16d468e98e8047823a19619fd9bbe555005856f3757b76e1024',16*1024),
        ('docs/productization/task036-media-observation-amendment/AMENDMENT.json','7a624cfa43285762b26cd6987141a574721ccfda140e6cc5585c3cbd6c24b6a7',16*1024),
        ('manifests/'+MANIFEST,MANIFEST_SHA,42*1024**2)):
        if sha256(regular(root,path,budget).replace(b'\r\n',b'\n')).hexdigest()!=expected:
            raise ValueError('MEDIA_POLICY_OBSERVATION_PREVIOUS_DOCUMENT')
    # The prior amendment's exact audit replacements are NOT expanded here.
    prior=json.loads(regular(root,PREVIOUS_DOCUMENT,16*1024),object_pairs_hook=unique)
    for row in prior['replacements']:
        if row['path'] not in TARGETS:
            if sha256(regular(root,row['path'],64*1024).replace(b'\r\n',b'\n')).hexdigest()!=row['active_sha256']:
                raise ValueError('MEDIA_POLICY_OBSERVATION_UNLISTED_AUDIT_CHANGE')
    for row in doc['replacements']:
        if (set(row)!={'path','preimage','original_bytes','original_sha256','original_git_blob','active_bytes','active_sha256'} or
            row['preimage']!=DIRECTORY+Path(row['path']).name+'.before'):
            raise ValueError('MEDIA_POLICY_OBSERVATION_ROW')
        original=regular(root,row['preimage'],64*1024)
        blob=sha1(b'blob '+str(len(original)).encode()+b'\0'+original).hexdigest()
        if len(original)!=row['original_bytes'] or sha256(original).hexdigest()!=row['original_sha256'] or blob!=row['original_git_blob']:
            raise ValueError('MEDIA_POLICY_OBSERVATION_PREIMAGE')
        active=regular(root,row['path'],64*1024).replace(b'\r\n',b'\n')
        if b'\r' in active or len(active)!=row['active_bytes'] or sha256(active).hexdigest()!=row['active_sha256']:
            raise ValueError('MEDIA_POLICY_OBSERVATION_ACTIVE_BYTES')
    return doc


def authenticated_previous_bytes(root,path,expected):
    if path not in TARGETS:raise ValueError('MEDIA_POLICY_OBSERVATION_UNLISTED_TARGET')
    doc=validate(root)
    row,=[r for r in doc['replacements'] if r['path']==path]
    if row['original_sha256']!=expected:raise ValueError('MEDIA_POLICY_OBSERVATION_PARENT_IDENTITY')
    try:
        from compiler_cache_source_amendment import regular
    except ImportError:
        from scripts.compiler_cache_source_amendment import regular
    return regular(Path(root).resolve(),row['preimage'],64*1024)
