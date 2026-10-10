"""Exact governed-M1 thread-policy amendment, never runtime self-blessing.

Historical documents and preimages remain sealed. This follows both observation
amendments and admits one exact new helper, not a generic compiler exception.
"""
from hashlib import sha256, sha1
import json
from pathlib import Path

DOCUMENT = 'docs/productization/task036-media-thread-amendment/AMENDMENT.json'
DOCUMENT_SHA256 = '6b08edb6b6bbacba67c1c87780809a449a8073dbf882cf5e35a247a81ddc940c'
PREVIOUS_DOCUMENT = 'docs/productization/task036-media-observation-amendment/AMENDMENT.json'
PREVIOUS_SHA256 = '7a624cfa43285762b26cd6987141a574721ccfda140e6cc5585c3cbd6c24b6a7'
CAPTURE_DOCUMENT = 'docs/productization/task036-capture-observation-amendment/AMENDMENT.json'
CAPTURE_SHA256 = '1526b7588616a16d468e98e8047823a19619fd9bbe555005856f3757b76e1024'
M1_DOCUMENT = 'docs/productization/task036-motion-amendment/AMENDMENT.json'
M1_SHA256 = 'b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c'
TARGETS = frozenset({'bie/compiler/qa_support/remotion_raster_capture.cjs', 'bie/compiler/real_paint.py',
    'scripts/compiler_media_observation_amendment.py', 'scripts/compiler_motion_source_amendment.py'})
NATIVE_TARGETS = frozenset({'bie/compiler/qa_support/remotion_raster_capture.cjs', 'bie/compiler/real_paint.py'})
ADDITIONS = frozenset({'bie/compiler/qa_support/bounded_media_threads.cjs'})
DIRECTORY = 'docs/productization/task036-media-thread-amendment/'


def validate(root):
    try:
        from compiler_cache_source_amendment import regular, unique, MANIFEST, MANIFEST_SHA
    except ImportError:
        from scripts.compiler_cache_source_amendment import regular, unique, MANIFEST, MANIFEST_SHA
    root = Path(root).resolve()
    raw = regular(root, DOCUMENT, 16 * 1024).replace(b'\r\n', b'\n')
    if b'\r' in raw or sha256(raw).hexdigest() != DOCUMENT_SHA256:
        raise ValueError('MEDIA_THREAD_AMENDMENT_DOCUMENT_IDENTITY')
    doc = json.loads(raw, object_pairs_hook=unique)
    if (set(doc) != {'schema','authority','scope','parent_commit','parent_tree','original_m1_sha256',
        'previous_amendment_sha256','capture_amendment_sha256','original_manifest_sha256',
        'replacements','additions','legacy_default_unchanged','resource_limits_unchanged',
        'motion_semantics_unchanged','runtime_policy','product_accepted','independent_review_status'} or
        doc['schema'] != 'bie.task036.media-thread-source-amendment/1' or
        doc['parent_commit'] != '7c9bafce7cc025f7e134ec6fb46a66197686ec5e' or
        doc['parent_tree'] != '01eb1a9e52a41f1fd1488e06f056a0aab437d396' or
        doc['original_m1_sha256'] != M1_SHA256 or doc['previous_amendment_sha256'] != PREVIOUS_SHA256 or
        doc['capture_amendment_sha256'] != CAPTURE_SHA256 or doc['original_manifest_sha256'] != MANIFEST_SHA or
        doc['product_accepted'] is not False or doc['legacy_default_unchanged'] is not True or
        doc['resource_limits_unchanged'] is not True or doc['motion_semantics_unchanged'] is not True or
        len(doc['replacements']) != 4 or {r['path'] for r in doc['replacements']} != TARGETS or
        len(doc['additions']) != 1 or {r['path'] for r in doc['additions']} != ADDITIONS or
        doc['runtime_policy'] != {'schema':'bie.comp-m1.media-threads/1','profile':'producer-motion-v1',
            'remotion_version':'4.0.506','decoder_threads':1,'encoder_threads':1,'filter_threads':1}):
        raise ValueError('MEDIA_THREAD_AMENDMENT_SCOPE')
    for path, expected, budget in ((M1_DOCUMENT,M1_SHA256,256*1024),
        (PREVIOUS_DOCUMENT,PREVIOUS_SHA256,16*1024),(CAPTURE_DOCUMENT,CAPTURE_SHA256,16*1024),
        ('manifests/'+MANIFEST,MANIFEST_SHA,42*1024**2)):
        prior = regular(root,path,budget).replace(b'\r\n',b'\n')
        if b'\r' in prior or sha256(prior).hexdigest()!=expected:
            raise ValueError('MEDIA_THREAD_AMENDMENT_PREVIOUS_IDENTITY')
    for path, expected in (
        ('scripts/compiler_cache_source_amendment.py','9c040865300c73ac0322f70e6eb017e0dbd591798fe3175a9d73acd9ac3a84ba'),
        ('scripts/compiler_capture_observation_amendment.py','6681cdcb6c8965316b786032cd771531402d2028f701a02d9ed8a21c9ce057b4')):
        if sha256(regular(root,path,64*1024).replace(b'\r\n',b'\n')).hexdigest()!=expected:
            raise ValueError('MEDIA_THREAD_AMENDMENT_UNLISTED_AUDIT_CHANGE')
    for row in doc['replacements']:
        if (set(row)!={'path','preimage','original_bytes','original_sha256','original_git_blob','active_bytes','active_sha256'} or
            row['preimage']!=DIRECTORY+Path(row['path']).name+'.before'):
            raise ValueError('MEDIA_THREAD_AMENDMENT_ROW')
        original = regular(root,row['preimage'],64*1024)
        blob = sha1(b'blob '+str(len(original)).encode()+b'\0'+original).hexdigest()
        if (len(original)!=row['original_bytes'] or sha256(original).hexdigest()!=row['original_sha256'] or
            blob!=row['original_git_blob']):raise ValueError('MEDIA_THREAD_AMENDMENT_PREIMAGE')
        active = regular(root,row['path'],64*1024).replace(b'\r\n',b'\n')
        if b'\r' in active or len(active)!=row['active_bytes'] or sha256(active).hexdigest()!=row['active_sha256']:
            raise ValueError('MEDIA_THREAD_AMENDMENT_ACTIVE_BYTES')
    for row in doc['additions']:
        if set(row)!={'path','active_bytes','active_sha256'}:raise ValueError('MEDIA_THREAD_AMENDMENT_ADDITION')
        active = regular(root,row['path'],64*1024).replace(b'\r\n',b'\n')
        if b'\r' in active or len(active)!=row['active_bytes'] or sha256(active).hexdigest()!=row['active_sha256']:
            raise ValueError('MEDIA_THREAD_AMENDMENT_ADDED_BYTES')
    return doc


def authenticated_previous_bytes(root,path,previous_sha256):
    if path not in NATIVE_TARGETS:raise ValueError('MEDIA_THREAD_AMENDMENT_UNLISTED_TARGET')
    doc = validate(root)
    row, = [r for r in doc['replacements'] if r['path']==path]
    if row['original_sha256']!=previous_sha256:raise ValueError('MEDIA_THREAD_AMENDMENT_PARENT_IDENTITY')
    try:
        from compiler_cache_source_amendment import regular
    except ImportError:
        from scripts.compiler_cache_source_amendment import regular
    original = regular(Path(root).resolve(),row['preimage'],64*1024)
    blob = sha1(b'blob '+str(len(original)).encode()+b'\0'+original).hexdigest()
    if (len(original)!=row['original_bytes'] or sha256(original).hexdigest()!=previous_sha256 or
        blob!=row['original_git_blob']):raise ValueError('MEDIA_THREAD_AMENDMENT_PREIMAGE')
    return original


def authenticated_added_paths(root):
    validate(root)
    return ADDITIONS
