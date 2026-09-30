"""H3-010: read-only canonical file/contract preflight, never a native run.

Blob IDs were read from the pinned GitHub compiler directory this batch. Section16
remains a separate integration dependency; a version label is not an acceptance.
"""
from pathlib import Path
import ast,hashlib
from ..models import BenchmarkError,digest
from ..av.native import COMMIT
from .custody import open_root,confined_stream

PINS={
 'bie/compiler/render_contracts.py':'060ed3584703ec9d7d24aca57bbba670d94b78d9',
 'bie/compiler/render_runtime.py':'6c83630d54d7c4ecd60476cae80aa3a649431ad6',
 'bie/compiler/artifact_hashing.py':'50303c4228dc0d5388928f0240206000f44f45d8',
 'bie/compiler/full_render.py':'22e158e498e4db3e1d088f132ccec8e85bb572fc'}

def check(checkout,*,expected_commit):
    if expected_commit!=COMMIT:raise BenchmarkError('CANONICAL_COMMIT_REBASE_REQUIRED')
    records=[];reasons=[]
    for name,pin in sorted(PINS.items()):
        try:
            with open_root(checkout) as fd,confined_stream(fd,name) as f:raw=f.read(200001)
            if len(raw)>200000:raise BenchmarkError('CANONICAL_SOURCE_SIZE_LIMIT')
            blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if blob!=pin:raise BenchmarkError('CANONICAL_SOURCE_DRIFT')
            ast.parse(raw.decode('utf-8'))
            records.append({'path':name,'git_blob_sha1':blob,'sha256':hashlib.sha256(raw).hexdigest(),'size_bytes':len(raw),'status':'PIN_MATCH'})
        except (BenchmarkError,SyntaxError,UnicodeError) as exc:
            code=exc.code if isinstance(exc,BenchmarkError) else 'CANONICAL_SOURCE_PARSE_ERROR'
            reasons.append(code);records.append({'path':name,'status':'BLOCKED','reason':code})
    result={'schema_version':'native-adoption-preflight-3','status':'BLOCKED' if reasons else 'PINNED_FILES_MATCH',
       'commit':COMMIT,'files':records,'reasons':sorted(set(reasons)),
       'full_checkout_verified':False,'native_execution_verified':False,'section16_integrated':False,
       'release_authorized':False,'product_accepted':False,
       'remaining':['FULL_CANONICAL_REGRESSION','SECTION16_QA_ADOPTION','PROVISIONED_TRUSTED_NATIVE_RUN','INDEPENDENT_SOURCE_LEARNING_ACCEPTANCE']}
    result['report_sha256']=digest(result);return result
