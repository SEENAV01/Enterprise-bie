"""Exact Step4 local Director amendment; integrity is not independent approval.

The original manifest, contributor records and ZIPs stay immutable. Only the
authenticated in-memory audit view redirects seven historical member mappings
and their collision reference to exact Git preimages. No runtime cache or source
allowlist is weakened. Expected identities are fixed authored review inputs.
"""
import hashlib
import json
from pathlib import Path

try:
    from compiler_cache_source_amendment import regular, unique
except ImportError:
    from scripts.compiler_cache_source_amendment import regular, unique

MANIFEST = 'director_integration_003.json'
MANIFEST_SHA = '02733513b9cca98b1255c7e615890ecd7e25726135a0d590a77b40ea5dba0285'
DIRECTORY = 'docs/productization/director-span-step4-amendment/'
DOCUMENT = DIRECTORY + 'AMENDMENT.json'
DOCUMENT_SHA = 'ea220cd84d343887b5b5e77bb69e28136cc2c2aa25df5a6c4a2981a966798377'
PREVIOUS_DOCUMENT = 'docs/productization/director-span-step5-amendment/STEP4_AMENDMENT.json'
PREVIOUS_SHA = '422853c8718e2f996497bae5c2060cb2b409a721ddea5187ed581fcadd1ee6cb'
TARGETS = {'bie/director/qa_contract.py': 1, 'bie/director/narration_annotations.py': 6}


def require(value, code):
    if not value: raise ValueError('DIR_SPAN_AMENDMENT_' + code)


def identity(data):
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                git_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest())


def validate(root):
    root = Path(root).resolve()
    require(hashlib.sha256(regular(root, PREVIOUS_DOCUMENT, 128 * 1024)).hexdigest() == PREVIOUS_SHA,
            'PREVIOUS_DRAFT')
    raw = regular(root, 'manifests/' + MANIFEST, 1024 * 1024)
    require(hashlib.sha256(raw).hexdigest() == MANIFEST_SHA, 'ORIGINAL_MANIFEST')
    original = json.loads(raw, object_pairs_hook=unique)
    data = regular(root, DOCUMENT, 128 * 1024)
    require(hashlib.sha256(data).hexdigest() == DOCUMENT_SHA, 'DOCUMENT_IDENTITY')
    document = json.loads(data, object_pairs_hook=unique)
    require(document['schema'] == 'bie.task036.director-span-source-amendment/1' and
            document['independent_review'] == 'PENDING_NOT_SELF_APPROVED' and
            document['product_accepted'] is False, 'SCOPE')
    require(identity(raw) == {k:document['manifest'][k] for k in ('bytes','sha256','git_blob')}, 'MANIFEST_IDENTITY')
    wiring = document['audit_wiring']
    require(wiring['path'] == 'scripts/verify_ingested_archives.py' and
            wiring['preimage'] == DIRECTORY + 'verify_ingested_archives.py.before', 'WIRING_SCOPE')
    require(identity(regular(root, wiring['preimage'], 65536)) == wiring['before'] and
            identity(regular(root, wiring['path'], 65536)) == wiring['after'], 'AUDIT_WIRING')
    rows = document['files']
    require(len(rows) == 2 and {r['path'] for r in rows} == set(TARGETS), 'TARGETS')
    for row in rows:
        require(row['preimage'] == DIRECTORY + Path(row['path']).name + '.before', 'PREIMAGE_PATH')
        require(identity(regular(root, row['preimage'], 65536)) == row['before'], 'PREIMAGE')
        require(identity(regular(root, row['path'], 65536)) == row['after'], 'ACTIVE_BYTES')
        members = [r for r in original['members'] if r['canonical_path'] == row['path']]
        collisions = [r for r in original['collisions'] if r['canonical_path'] == row['path']]
        require(members == row['member_rows'] and len(members) == TARGETS[row['path']] and
                all(r['canonical_sha256'] == row['before']['sha256'] for r in members), 'MEMBERS')
        require(collisions == row['collision_rows'], 'COLLISIONS')
        contributors = [r for c in collisions for r in c['contributors']]
        expected = [{k:r[k] for k in ('task_id','archive','original_sha256','canonical_sha256','transformation')}
                    for r in members] if len(members) > 1 else []
        require(contributors == expected, 'CONTRIBUTORS')
    inventory = document['original_director_inventory']
    paths = {r['path'] for r in inventory}
    require(len(paths) == len(inventory) == 71 and set(TARGETS) <= paths, 'INVENTORY')
    actual = {p.relative_to(root).as_posix() for p in (root/'bie/director').rglob('*.py')}
    require(actual == paths, 'UNLISTED_SOURCE')
    for row in inventory:
        if row['path'] not in TARGETS:
            require(identity(regular(root, row['path'], 1024 * 1024)) ==
                    {k:row[k] for k in ('bytes','sha256','git_blob')}, 'UNRELATED_SOURCE')
    return original, document


def resolve(root, manifest_path, manifest):
    if manifest_path.name != MANIFEST: return manifest, 0
    original, document = validate(root)
    # Full equality prevents forged/duplicate caller rows from escaping a loop
    # that would otherwise check only the selected paths.
    require(manifest == original, 'CALLER_MANIFEST')
    replacements = {r['path']:r['preimage'] for r in document['files']}
    members = [dict(r, canonical_path=replacements[r['canonical_path']], state='ARCHIVED_EVIDENCE',
                    transformation='Exact Step4 Git preimage; active replacement separately authenticated; independent review pending')
               if r['canonical_path'] in replacements else dict(r) for r in original['members']]
    collisions = [dict(r, canonical_path=replacements[r['canonical_path']],
                       resolution='Historical contributors retained against exact Step4 preimage; active source separately pinned')
                  if r['canonical_path'] in replacements else dict(r) for r in original['collisions']]
    return dict(original, members=members, collisions=collisions), sum(TARGETS.values())
