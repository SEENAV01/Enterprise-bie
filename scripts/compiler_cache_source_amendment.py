"""One exact reviewed cache fix; original source ledger and ZIP stay sealed.

Never accept a caller-provided replacement hash. This gate verifies both the
exact original LF Git bytes and the approved producer, not just an old preimage.
"""
from pathlib import Path
import hashlib,json,stat
MANIFEST='post_dir_integration_004.json'
MANIFEST_SHA='33c579d83186d0a11319984e6d047cb41bfea804a6477e5902b77f0432d71c7f'
TARGET='bie/compiler/qa_support/remotion_raster_capture.cjs'
DOCUMENT='docs/section18/compiler-bundle-source-amendment/AMENDMENT.json'
BEFORE='docs/section18/compiler-bundle-source-amendment/remotion_raster_capture.cjs.before'
ORIGINAL='63e0c4c553f973574d2452832b9d29719838340002cf3634885524580f280bff'
REPLACEMENT='444d9c64d76279f8313efaa6449d97a15c19a2906c8f2c4c82d469688a0fc6b3'
EXPECTED=dict(schema='bie.section18.compiler-cache-source-amendment/1',
    original_manifest_git_lf_sha256=MANIFEST_SHA,source_archive='BIE_COMP_HARDENING_H12_INTEGRATED.zip',
    source_archive_sha256='96044db24b5d466dbc5e8c1136865dccece705c4d8ea71ce41b6c4265ce1c0d5',
    original_member='app/bie/compiler/qa_support/remotion_raster_capture.cjs',active_path=TARGET,
    original_sha256=ORIGINAL,original_bytes=4841,preimage_path=BEFORE,replacement_git_lf_sha256=REPLACEMENT,
    scope='APPROVED_ENABLE_CACHING_FALSE_IMMUTABLE_DEPENDENCIES',
    authority='EXPLICIT_USER_KEEP_APPROVED_CACHE_CORRECTION',failed_gate_run=37066598268,
    original_ledgers_and_archives_unchanged=True,security_controls_unchanged=True,
    product_accepted=False,section_implementation_complete=False)

def regular(root,relative,max_bytes):
    p=root/relative
    if not p.resolve().is_relative_to(root.resolve()):raise ValueError('COMP_CACHE_AMENDMENT_PATH')
    for item in (p,*p.parents):
        if item==root:break
        if item.is_symlink():raise ValueError('COMP_CACHE_AMENDMENT_LINK')
    info=p.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_size>max_bytes:
        raise ValueError('COMP_CACHE_AMENDMENT_FILE')
    return p.read_bytes()
def unique(pairs):
    value={}
    for key,item in pairs:
        if key in value:raise ValueError('COMP_CACHE_AMENDMENT_DUPLICATE_KEY')
        value[key]=item
    return value
def resolve(root,manifest_path,manifest):
    if manifest_path.name!=MANIFEST:return manifest,0
    root=Path(root).resolve()
    # The already-canonical sealed ledger is exactly 41,291,704 bytes. This
    # verifier-only bound accommodates that inventory; no worker limit changes.
    manifest_bytes=regular(root,'manifests/'+MANIFEST,42*1024**2).replace(b'\r\n',b'\n')
    if b'\r' in manifest_bytes or hashlib.sha256(manifest_bytes).hexdigest()!=MANIFEST_SHA:
        raise ValueError('COMP_CACHE_AMENDMENT_ORIGINAL_MANIFEST')
    document=json.loads(regular(root,DOCUMENT,16*1024),object_pairs_hook=unique)
    if document!=EXPECTED:raise ValueError('COMP_CACHE_AMENDMENT_DOCUMENT_IDENTITY')
    original=regular(root,BEFORE,64*1024)
    if len(original)!=4841 or hashlib.sha256(original).hexdigest()!=ORIGINAL:
        raise ValueError('COMP_CACHE_AMENDMENT_PREIMAGE')
    active=regular(root,TARGET,64*1024);lf=active.replace(b'\r\n',b'\n')
    # Git checkouts can contain mixed CRLF/LF after an apply_patch edit. Only
    # standard newline conversion is allowed; every normalized byte is pinned.
    if b'\r' in lf or hashlib.sha256(lf).hexdigest()!=REPLACEMENT:
        raise ValueError('COMP_CACHE_AMENDMENT_ACTIVE_BYTES')
    rows=[r for r in manifest['members'] if r['canonical_path']==TARGET]
    expected=dict(archive=EXPECTED['source_archive'],canonical_path=TARGET,canonical_sha256=ORIGINAL,
        member=EXPECTED['original_member'],original_bytes=4841,original_sha256=ORIGINAL,
        state='MIGRATED',transformation='BYTE_IDENTICAL_ADOPTION')
    if rows!=[expected]:raise ValueError('COMP_CACHE_AMENDMENT_ORIGINAL_ROW')
    redirected=dict(expected,canonical_path=BEFORE,state='ARCHIVED_EVIDENCE',
        transformation='Exact reviewed immutable-cache correction; sealed original bytes preserved separately')
    return dict(manifest,members=[redirected if r==expected else r for r in manifest['members']]),1
