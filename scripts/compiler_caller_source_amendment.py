"""Two reviewed caller assertions, never a production/kernel relaxation.

The original adopted ledger/archives remain sealed. Verify original before
images and exact active test bytes before redirecting only these two rows.
"""
from pathlib import Path
import hashlib,json
try:
 from compiler_cache_source_amendment import regular,unique,MANIFEST,MANIFEST_SHA
except ImportError:
 from scripts.compiler_cache_source_amendment import regular,unique,MANIFEST,MANIFEST_SHA
DOCUMENT='docs/section18/compiler-caller-source-amendment/AMENDMENT.json'
ROWS=[
 dict(path='tests/compiler/test_comp_h7_007.py',original_sha256='f4c6da0393840cdc0469dbb8d1817c63dd975846fcffddecdd22c7ad8e01f669',
      original_bytes=5153,active_sha256='18f74637da5e6b3f20d40e020731850911333cc7dd172100712874ec50a8f9a1',active_bytes=5447,
      preimage='docs/section18/compiler-caller-source-amendment/test_comp_h7_007.py.before',methods=12),
 dict(path='tests/compiler/test_comp_h8_005.py',original_sha256='189fd2ceda43553f11651eff700e3113eb08c1adaeb1af690b4db5ac3f5d3227',
      original_bytes=5580,active_sha256='1054b0a2f91aa4604e74a5774ef96a61f097a761887315c5b2eb48e241bb9cdc',active_bytes=5977,
      preimage='docs/section18/compiler-caller-source-amendment/test_comp_h8_005.py.before',methods=15)]
EXPECTED=dict(schema='bie.section18.compiler-caller-maintenance/1',finding='BIE-APP-H1-011',
 original_manifest_git_lf_sha256=MANIFEST_SHA,files=ROWS,failure_run=37153626015,
 failure_type='STATIC_CALLER_NAME_AFTER_APPROVED_KERNEL_WRAPPER',original_method_ids_preserved=27,
 assertion_strengthened='Verify real paint calls scoped wrapper and wrapper driver delegates canonical kernel under8GiB',
 production_bytes_changed=False,kernel_security_unchanged=True,original_ledgers_unchanged=True,
 authority='HUMAN_MINIMAL_EVIDENCE_BACKED_INTEGRATION_REGRESSION_REPAIR',product_accepted=False)
def validate(root):
 root=Path(root).resolve()
 raw=regular(root,'manifests/'+MANIFEST,42*1024**2).replace(b'\r\n',b'\n')
 if b'\r' in raw or hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA:
  raise ValueError('COMP_CALLER_ORIGINAL_MANIFEST')
 original=json.loads(raw,object_pairs_hook=unique)
 document=json.loads(regular(root,DOCUMENT,16*1024),object_pairs_hook=unique)
 if document!=EXPECTED:raise ValueError('COMP_CALLER_DOCUMENT_IDENTITY')
 for row in ROWS:
  before=regular(root,row['preimage'],64*1024)
  if len(before)!=row['original_bytes'] or hashlib.sha256(before).hexdigest()!=row['original_sha256']:
   raise ValueError('COMP_CALLER_PREIMAGE')
  active=regular(root,row['path'],64*1024).replace(b'\r\n',b'\n')
  if b'\r' in active or len(active)!=row['active_bytes'] or hashlib.sha256(active).hexdigest()!=row['active_sha256']:
   raise ValueError('COMP_CALLER_ACTIVE_BYTES')
 return original
def resolve(root,manifest_path,manifest):
 if manifest_path.name!=MANIFEST:return manifest,0
 original=validate(root);members=list(manifest['members'])
 for row in ROWS:
  old=[r for r in original['members'] if r['canonical_path']==row['path']]
  current=[r for r in members if r['canonical_path']==row['path']]
  if len(old)!=1 or current!=old or old[0]['canonical_sha256']!=row['original_sha256']:
   raise ValueError('COMP_CALLER_ORIGINAL_ROW')
  before=dict(old[0],canonical_path=row['preimage'],state='ARCHIVED_EVIDENCE',
   transformation='Reviewed scoped-wrapper caller assertion; original27 method identities preserved')
  members=[before if r==old[0] else r for r in members]
 return dict(manifest,members=members),2
def resolve_source_members(root,manifest_path,manifest,previous_rows):
 if manifest_path.name!=MANIFEST:raise ValueError('COMP_CALLER_SOURCE_MANIFEST')
 original=validate(root)
 if manifest!=original:raise ValueError('COMP_CALLER_SOURCE_INVENTORY')
 result=list(previous_rows)
 for row in ROWS:
  old=[r for r in original['source_members'] if r['canonical_path']==row['path']]
  current=[r for r in result if r['canonical_path']==row['path']]
  if len(old)!=1 or current!=old or old[0]['canonical_sha256']!=row['original_sha256']:
   raise ValueError('COMP_CALLER_SOURCE_ROW')
  result=[dict(r,canonical_path=row['preimage']) if r==old[0] else r for r in result]
 return result
