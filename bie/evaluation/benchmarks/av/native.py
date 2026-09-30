"""H2-009: exact pinned canonical RenderReceipt JSON adapter.

This validates declarations against freshly collected media facts, NOT the
truth of a claimed Remotion execution. H2 never authenticates native execution
from a JSON flag. No repository code is imported or executed by this adapter.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
from ..models import BenchmarkError,digest,digest_string,ident,canonical_json,strict_loads
from .custody import exact_fields,integer,finite,regular_path
from .service import verify_receipt

COMMIT='a68e054025b8fe7756a71e998d9e9103dad8e0f4'
CONTRACT_BLOB='060ed3584703ec9d7d24aca57bbba670d94b78d9'
RUNTIME_BLOB='6c83630d54d7c4ecd60476cae80aa3a649431ad6'
CONTRACT_PATH='bie/compiler/render_contracts.py'
FIELDS={'schema_version','run_id','mode','composition_id','passed','failure_code','errors','output_path',
        'expected_frames','media','input_sha256','recipe_sha256','evidence_directory','execution_kind',
        'process_started','artifact_sha256','artifact_size_bytes','accepted'}
MEDIA_FIELDS={'width','height','fps','decoded_frames','duration_s','codec_name','pixel_format','audio_streams'}

def verify_contract_bytes(contract_path,expected_commit):
    if expected_commit!=COMMIT:raise BenchmarkError('UNSUPPORTED_NATIVE_COMMIT')
    p=regular_path(contract_path)
    with p.open('rb') as f:raw=f.read(100_001)
    if len(raw)>100_000:raise BenchmarkError('NATIVE_CONTRACT_SIZE_LIMIT')
    h=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()
    if h!=CONTRACT_BLOB:raise BenchmarkError('NATIVE_CONTRACT_BLOB_CHANGED')
    return {'commit':COMMIT,'path':CONTRACT_PATH,'git_blob_sha1':h,'sha256':hashlib.sha256(raw).hexdigest()}

def relative(value):
    if type(value) is not str or not value or value.startswith('/') or '\\' in value or ':' in value or any(p in ('','.','..') for p in value.split('/')):
        raise BenchmarkError('NATIVE_PATH_UNSAFE')
    return value

def map_render_receipt(native, collected, *, expected_commit, expected_run_id,expected_input_sha256,
                       expected_recipe_sha256,expected_composition_id,contract_path):
    contract=verify_contract_bytes(contract_path,expected_commit)
    n=strict_loads(canonical_json(native));exact_fields(n,FIELDS)
    r=verify_receipt(collected);observed=r.get('observations')
    if r['status']!='DIAGNOSTIC_PASS' or observed is None:raise BenchmarkError('AV_COLLECTION_NOT_PASSING')
    # Exact schema is confirmed from pinned runtime, not a guessed generic v1.
    if n['schema_version']!='bie.render-receipt.v1':raise BenchmarkError('NATIVE_SCHEMA_UNSUPPORTED')
    for v in (expected_run_id,expected_composition_id,n['run_id'],n['composition_id']):ident(v)
    for v in (expected_input_sha256,expected_recipe_sha256,n['input_sha256'],n['recipe_sha256'],n['artifact_sha256']):digest_string(v)
    if n['run_id']!=expected_run_id or n['composition_id']!=expected_composition_id:raise BenchmarkError('NATIVE_RUN_BINDING_MISMATCH')
    if n['input_sha256']!=expected_input_sha256 or n['recipe_sha256']!=expected_recipe_sha256:raise BenchmarkError('NATIVE_SOURCE_RECIPE_MISMATCH')
    if n['mode']!='full':raise BenchmarkError('NATIVE_PARTIAL_RENDER_REJECTED')
    if n['execution_kind']!='LOCAL_REMOTION_CLI':raise BenchmarkError('NATIVE_FIXTURE_EXECUTION_REJECTED')
    if n['passed'] is not True or n['process_started'] is not True or n['failure_code'] is not None or n['errors']!=[]:
        raise BenchmarkError('NATIVE_RENDER_NOT_SUCCESSFUL')
    if n['accepted'] is not False:raise BenchmarkError('NATIVE_ACCEPTANCE_ESCALATION')
    relative(n['output_path']);relative(n['evidence_directory'])
    if not n['output_path'].endswith('.mp4'):raise BenchmarkError('NATIVE_OUTPUT_PROFILE')
    integer(n['expected_frames'],1,864000);integer(n['artifact_size_bytes'],1,4*1024**3)
    if (n['artifact_sha256'],n['artifact_size_bytes'])!=(observed['artifact']['sha256'],observed['artifact']['bytes']):
        raise BenchmarkError('NATIVE_ARTIFACT_BINDING_MISMATCH')
    m=exact_fields(n['media'],MEDIA_FIELDS);actual=observed['metadata'];v=observed['video']
    if 'mp4' not in actual.get('container_formats',[]):raise BenchmarkError('NATIVE_CONTAINER_PROFILE_MISMATCH')
    for k in ('width','height','decoded_frames','audio_streams'):integer(m[k],0,864000)
    finite(m['fps'],0.001,120);finite(m['duration_s'],0.001,7200)
    if (m['width'],m['height'],m['decoded_frames'],n['expected_frames'])!=(actual['width'],actual['height'],v['decoded_frames'],v['decoded_frames']):
        raise BenchmarkError('NATIVE_DECODED_FACT_MISMATCH')
    from .probe import fraction
    if abs(m['fps']-float(fraction(actual['fps'])))>1e-6 or abs(m['duration_s']-(observed['video_timing']['end_s']-observed['video_timing']['start_s']))>0.01:
        raise BenchmarkError('NATIVE_TIMING_MISMATCH')
    if m['codec_name']!='h264' or actual['codec']!='h264' or m['pixel_format']!='yuv420p' or actual['pixel_format']!='yuv420p':
        raise BenchmarkError('NATIVE_CODEC_PROFILE_MISMATCH')
    if m['audio_streams']!=int(observed['audio'] is not None):raise BenchmarkError('NATIVE_AUDIO_STREAM_MISMATCH')
    return {'schema_version':'native-render-map-2','status':'DECLARATIONS_MATCH_OBSERVED_BYTES',
            'contract':contract,'native_receipt_sha256':digest(n),'av_receipt_sha256':r['receipt_sha256'],
            'native_execution_verified':False,'source_provenance_verified':False,
            'release_authorized':False,'product_accepted':False,
            'remaining':['AUTHENTICATED_NATIVE_WORKER_COLLECTION','SOURCE_MANIFEST_RECIPE_ARTIFACT_CUSTODY',
                         'REAL_BOOK_COMPILE_RENDER_INTEGRATION','INDEPENDENT_QUALITY_ACCEPTANCE']}
