"""One explicit GAME export amendment; the original lossless ledger stays sealed."""
import hashlib,json

FILE_ID='ce534f7ee4b598b47b52090af6b3bd506f2359c0514fd538f9551979f4c83d1e'
EMPTY='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
LEDGER='f981c9c11834f4136052306613de16bbb241ca4d980b96fec675d3ca767b76d1'
ACTIVE='01217f6b6ac880365e261d336883cd6ac63ba4bdebbb89e6fa70bf8b9b1be160'
BEFORE='docs/evidence/game-section15/predecessors/bie/game_engine/__init__.py'
TARGET='bie/game_engine/__init__.py'
MANIFEST='manifests/game_section15_initializer_amendment.json'

def resolve(root,rows):
    if not (root/MANIFEST).is_file():return rows
    amendment=json.loads((root/MANIFEST).read_text())
    expected={'file_id':FILE_ID,'original_ledger_sha256':LEDGER,'original_sha256':EMPTY,'active_path':TARGET,'active_sha256':ACTIVE,'before_image':BEFORE}
    if any(amendment.get(k)!=v for k,v in expected.items()):raise ValueError('GAME_INITIALIZER_AMENDMENT_IDENTITY')
    if amendment.get('product_accepted') is not False or not amendment.get('reason'):raise ValueError('GAME_INITIALIZER_AMENDMENT_SCOPE')
    for rel,digest in (('manifests/lossless_migration.csv',LEDGER),(BEFORE,EMPTY),(TARGET,ACTIVE)):
        if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=digest:raise ValueError('GAME_INITIALIZER_AMENDMENT_BYTES:'+rel)
    selected=[r for r in rows if r['file_id']==FILE_ID]
    if len(selected)!=1:raise ValueError('GAME_INITIALIZER_ORIGINAL_COVERAGE')
    row=selected[0]
    if (row['canonical_path'],row['canonical_sha256'],row['sha256'],row['bytes'])!=(TARGET,EMPTY,EMPTY,'0'):raise ValueError('GAME_INITIALIZER_ORIGINAL_IDENTITY')
    # One original file retains one effective disposition, at its exact before-image.
    effective={**row,'canonical_path':BEFORE,'disposition':'ARCHIVED_EVIDENCE','reason':amendment['reason'],'transform':'Section 15 explicit initializer export amendment; original bytes preserved'}
    return [effective if r['file_id']==FILE_ID else r for r in rows]
