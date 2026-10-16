"""Exact authorized compiler fixes; original source ledger and ZIP stay sealed.

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
PAINT_TARGET='bie/compiler/real_paint.py'
PAINT_DOCUMENT='docs/section18/compiler-paint-source-amendment/AMENDMENT.json'
PAINT_BEFORE='docs/section18/compiler-paint-source-amendment/real_paint.py.before'
PAINT_ORIGINAL='fc320220631020b0bc246786e659ea105313e11b6a47ef97b99db6ed043e07bf'
PAINT_REPLACEMENT='e2a5765f9c5a67e510dca68c1a70e35a13d9366ff6b9728d9b412776e8d174b9'
PAINT_EXPECTED=dict(schema='bie.section18.compiler-paint-source-amendment/1',
    original_manifest_git_lf_sha256=MANIFEST_SHA,source_archive=EXPECTED['source_archive'],
    source_archive_sha256=EXPECTED['source_archive_sha256'],original_member='app/bie/compiler/real_paint.py',
    archive_original_sha256='53d36304609c6150ab29d42992d8391046e20bde632acb76cbed70cb8f534afd',
    archive_original_bytes=13450,active_path=PAINT_TARGET,canonical_original_sha256=PAINT_ORIGINAL,
    canonical_original_bytes=13446,preimage_path=PAINT_BEFORE,replacement_git_lf_sha256=PAINT_REPLACEMENT,
    scope='APPROVED_STRICT_TYPESCRIPT_HELPER_COVERAGE_AND_NARROW_WASM_INVOCATION',
    authority='EXPLICIT_HUMAN_APPROVAL_MINIMAL_COVERAGE_FIX_AND_BOUNDED_WASM_OPTION',failed_gate_run=37083405153,
    original_ledgers_and_archives_unchanged=True,address_space_bytes=8589934592,
    security_controls_unchanged=True,product_accepted=False,section_implementation_complete=False)
NATIVE_DOCUMENT='docs/section18/compiler-native-source-amendment/AMENDMENT.json'
NATIVE_DIRECTORY='docs/section18/compiler-native-source-amendment'
RENDER_TARGET='bie/compiler/render_runtime.py'
RENDER_BEFORE=NATIVE_DIRECTORY+'/render_runtime.py.before'
RENDER_ORIGINAL='5d7027a508ba284924f83f4495486a27343c5975f74e5f5644efff462f2be7a1'
NATIVE_PINS={
    TARGET:'c5e7f4a322c592dd87dfcb557924e4210ab94aed5a9bea94e9c851739dd50503',
    PAINT_TARGET:'9ddc3d9d9898e089f83be97971eb12e7b92957f9454f6e30bae00beadb69284c',
    RENDER_TARGET:'d014b020bf54f5c3c13a1831ff3b5345c94903d915e230030f1b771175598e26',
}
NATIVE_EXPECTED=dict(schema='bie.section18.compiler-native-source-amendment/1',
    original_manifest_git_lf_sha256=MANIFEST_SHA,
    previous_documents=[DOCUMENT,PAINT_DOCUMENT],previous_documents_unchanged=True,
    previous_active_sources=[
        dict(path=NATIVE_DIRECTORY+'/previous-remotion_raster_capture.cjs.before',sha256=REPLACEMENT,bytes=4946),
        dict(path=NATIVE_DIRECTORY+'/previous-real_paint.py.before',sha256=PAINT_REPLACEMENT,bytes=13862)],
    active_git_lf_sha256=NATIVE_PINS,
    render_original=dict(path=RENDER_BEFORE,sha256=RENDER_ORIGINAL,bytes=22149),
    evidence=dict(run=37146010192,artifact_id=11282286127,
        candidate='da1fd40b47bbe87c6788564ec1e6f077e284f1a9',
        tree='2167e95f2be5933c01cd499255411dc19379c571',bytes=2357364,
        sha256='2ae0d4626406826a05d92f37af353254fb8c14fa822d30d00d79f4cead007646',
        resource_methods=58,wasm_methods=5,bundle_methods=2,render_methods=4,
        failures=0,errors=0,skips=0),
    scope=['APPROVED_SCOPED_CHROMIUM_BOUNDARY','ORIGINAL_LAYOUT_WAIT_BEFORE_RASTER_INVENTORY',
           'EXPLICIT_BT709_LIMITED_RANGE_CONVERSION'],
    authority='EXPLICIT_HUMAN_BOUNDED_CHROMIUM_CORRECTION_AND_GENUINE_FAILURE_REPAIR',
    node_address_space_bytes=8589934592,chromium_address_space_bytes=2199023255552,
    physical_memory_bytes=2147483648,swap_max=0,
    original_ledgers_and_archives_unchanged=True,pinned_toolchain_unchanged=True,
    inherited_security_controls_preserved=True,product_accepted=False)

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
def validate_native_revision(root):
    document=json.loads(regular(root,NATIVE_DOCUMENT,16*1024),object_pairs_hook=unique)
    if document!=NATIVE_EXPECTED:raise ValueError('COMP_NATIVE_AMENDMENT_DOCUMENT_IDENTITY')
    for row in NATIVE_EXPECTED['previous_active_sources']:
        raw=regular(root,row['path'],64*1024)
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise ValueError('COMP_NATIVE_AMENDMENT_PREVIOUS_SOURCE')
def resolve(root,manifest_path,manifest):
    if manifest_path.name!=MANIFEST:return manifest,0
    root=Path(root).resolve()
    # The already-canonical sealed ledger is exactly 41,291,704 bytes. This
    # verifier-only bound accommodates that inventory; no worker limit changes.
    manifest_bytes=regular(root,'manifests/'+MANIFEST,42*1024**2).replace(b'\r\n',b'\n')
    if b'\r' in manifest_bytes or hashlib.sha256(manifest_bytes).hexdigest()!=MANIFEST_SHA:
        raise ValueError('COMP_CACHE_AMENDMENT_ORIGINAL_MANIFEST')
    validate_native_revision(root)
    document=json.loads(regular(root,DOCUMENT,16*1024),object_pairs_hook=unique)
    if document!=EXPECTED:raise ValueError('COMP_CACHE_AMENDMENT_DOCUMENT_IDENTITY')
    original=regular(root,BEFORE,64*1024)
    if len(original)!=4841 or hashlib.sha256(original).hexdigest()!=ORIGINAL:
        raise ValueError('COMP_CACHE_AMENDMENT_PREIMAGE')
    active=regular(root,TARGET,64*1024);lf=active.replace(b'\r\n',b'\n')
    # Git checkouts can contain mixed CRLF/LF after an apply_patch edit. Only
    # standard newline conversion is allowed; every normalized byte is pinned.
    if b'\r' in lf or hashlib.sha256(lf).hexdigest()!=NATIVE_PINS[TARGET]:
        raise ValueError('COMP_CACHE_AMENDMENT_ACTIVE_BYTES')
    rows=[r for r in manifest['members'] if r['canonical_path']==TARGET]
    expected=dict(archive=EXPECTED['source_archive'],canonical_path=TARGET,canonical_sha256=ORIGINAL,
        member=EXPECTED['original_member'],original_bytes=4841,original_sha256=ORIGINAL,
        state='MIGRATED',transformation='BYTE_IDENTICAL_ADOPTION')
    if rows!=[expected]:raise ValueError('COMP_CACHE_AMENDMENT_ORIGINAL_ROW')
    redirected=dict(expected,canonical_path=BEFORE,state='ARCHIVED_EVIDENCE',
        transformation='Exact reviewed immutable-cache correction; sealed original bytes preserved separately')
    manifest=dict(manifest,members=[redirected if r==expected else r for r in manifest['members']])
    document=json.loads(regular(root,PAINT_DOCUMENT,16*1024),object_pairs_hook=unique)
    if document!=PAINT_EXPECTED:raise ValueError('COMP_PAINT_AMENDMENT_DOCUMENT_IDENTITY')
    original=regular(root,PAINT_BEFORE,64*1024)
    if len(original)!=13446 or hashlib.sha256(original).hexdigest()!=PAINT_ORIGINAL:
        raise ValueError('COMP_PAINT_AMENDMENT_PREIMAGE')
    active=regular(root,PAINT_TARGET,64*1024);lf=active.replace(b'\r\n',b'\n')
    if b'\r' in lf or hashlib.sha256(lf).hexdigest()!=NATIVE_PINS[PAINT_TARGET]:
        raise ValueError('COMP_PAINT_AMENDMENT_ACTIVE_BYTES')
    rows=[r for r in manifest['members'] if r['canonical_path']==PAINT_TARGET]
    expected=dict(archive=PAINT_EXPECTED['source_archive'],canonical_path=PAINT_TARGET,
        canonical_sha256=PAINT_ORIGINAL,member=PAINT_EXPECTED['original_member'],
        original_bytes=PAINT_EXPECTED['archive_original_bytes'],original_sha256=PAINT_EXPECTED['archive_original_sha256'],
        state='MIGRATED',transformation='CANONICAL_PATH_ADAPTATION_OR_DOCUMENTED_AMENDMENT')
    if rows!=[expected]:raise ValueError('COMP_PAINT_AMENDMENT_ORIGINAL_ROW')
    redirected=dict(expected,canonical_path=PAINT_BEFORE,state='ARCHIVED_EVIDENCE',
        transformation='Exact reviewed TypeScript coverage and bounded Wasm invocation; original canonical bytes retained')
    manifest=dict(manifest,members=[redirected if r==expected else r for r in manifest['members']])
    original=regular(root,RENDER_BEFORE,64*1024)
    if len(original)!=22149 or hashlib.sha256(original).hexdigest()!=RENDER_ORIGINAL:
        raise ValueError('COMP_RENDER_AMENDMENT_PREIMAGE')
    active=regular(root,RENDER_TARGET,64*1024);lf=active.replace(b'\r\n',b'\n')
    if b'\r' in lf or hashlib.sha256(lf).hexdigest()!=NATIVE_PINS[RENDER_TARGET]:
        raise ValueError('COMP_RENDER_AMENDMENT_ACTIVE_BYTES')
    rows=[r for r in manifest['members'] if r['canonical_path']==RENDER_TARGET]
    expected=dict(archive=EXPECTED['source_archive'],canonical_path=RENDER_TARGET,
        canonical_sha256=RENDER_ORIGINAL,member='app/'+RENDER_TARGET,
        original_bytes=22149,original_sha256=RENDER_ORIGINAL,
        state='MIGRATED',transformation='BYTE_IDENTICAL_ADOPTION')
    if rows!=[expected]:raise ValueError('COMP_RENDER_AMENDMENT_ORIGINAL_ROW')
    redirected=dict(expected,canonical_path=RENDER_BEFORE,state='ARCHIVED_EVIDENCE',
        transformation='Exact reviewed Chromium invocation and governed BT709 conversion; original bytes retained')
    return dict(manifest,members=[redirected if r==expected else r for r in manifest['members']]),3

def resolve_source_members(root,manifest_path,manifest):
    """Reconcile the legacy exact-source caller, never skip an active source.

    Original source_members stay sealed. Resolve validates both active producer
    replacements and preimages first; every unrelated source is unchanged.
    No caller-mutated inventory or arbitrary replacement is accepted.
    """
    if manifest_path.name!=MANIFEST:raise ValueError('COMP_SOURCE_MEMBER_MANIFEST')
    root=Path(root).resolve()
    sealed_bytes=regular(root,'manifests/'+MANIFEST,42*1024**2).replace(b'\r\n',b'\n')
    if b'\r' in sealed_bytes or hashlib.sha256(sealed_bytes).hexdigest()!=MANIFEST_SHA:
        raise ValueError('COMP_CACHE_AMENDMENT_ORIGINAL_MANIFEST')
    sealed=json.loads(sealed_bytes,object_pairs_hook=unique)
    if manifest!=sealed:raise ValueError('COMP_SOURCE_MEMBER_INVENTORY')
    _,count=resolve(root,manifest_path,manifest)
    if count!=3:raise ValueError('COMP_SOURCE_MEMBER_AMENDMENT_COUNT')
    remap={TARGET:(ORIGINAL,BEFORE),PAINT_TARGET:(PAINT_ORIGINAL,PAINT_BEFORE),
        RENDER_TARGET:(RENDER_ORIGINAL,RENDER_BEFORE)}
    selected=[r for r in manifest['source_members'] if r['canonical_path'] in remap]
    if len(selected)!=3 or {r['canonical_path'] for r in selected}!=set(remap):
        raise ValueError('COMP_SOURCE_MEMBER_ORIGINAL_ROWS')
    result=[]
    for row in manifest['source_members']:
        selected=remap.get(row['canonical_path'])
        if selected is not None:
            original,before=selected
            if row['canonical_sha256']!=original:raise ValueError('COMP_SOURCE_MEMBER_ORIGINAL_HASH')
            row=dict(row,canonical_path=before)
        result.append(row)
    return result
