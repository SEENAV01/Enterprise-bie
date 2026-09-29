"""Read native COMP RenderReceipt identity without promoting native booleans.

Schema inspected at pinned repository375d99a; no native runtime is vendored or
silently reimplemented. Rebind through ExecutionReceipt and actual decoding before
use. Representative native mappings are tested; current-HEAD adoption is open.
"""
import json,hashlib
from ..release_v2.contracts import ArtifactRef,ContractError,digest

def from_native_render(raw,video,*,run_id,composition_id):
    required={'schema_version','run_id','mode','composition_id','passed','failure_code','errors','output_path','expected_frames','media','input_sha256','recipe_sha256','evidence_directory','execution_kind','process_started','artifact_sha256','artifact_size_bytes','accepted'}
    if type(raw) is not dict or set(raw)!=required or type(video) is not ArtifactRef:raise ContractError('VIDEO_NATIVE_FIELDS')
    if raw['accepted'] is not False or type(raw['passed']) is not bool or type(raw['process_started']) is not bool:raise ContractError('VIDEO_NATIVE_ACCEPTANCE')
    if (raw['run_id'],raw['composition_id'])!=(run_id,composition_id):raise ContractError('VIDEO_NATIVE_RUN')
    if raw['mode'] not in ('full','smoke'):raise ContractError('VIDEO_NATIVE_MODE')
    if type(raw['expected_frames']) is not int or raw['expected_frames']<1 or type(raw['errors']) not in (list,tuple):raise ContractError('VIDEO_NATIVE_SCOPE')
    if raw['passed'] and (not raw['process_started'] or raw['failure_code'] is not None or raw['errors']):raise ContractError('VIDEO_NATIVE_INCONSISTENT_RESULT')
    if (raw['artifact_sha256'],raw['artifact_size_bytes'],raw['output_path'])!=(video.sha256,video.size,video.path):raise ContractError('VIDEO_NATIVE_MEDIA_BINDING')
    try: native_digest=hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    except (ValueError,TypeError) as exc:raise ContractError('VIDEO_NATIVE_JSON') from exc
    return dict(native_receipt_digest=native_digest,reported_passed=raw['passed'],reported_execution_kind=raw['execution_kind'],mode=raw['mode'],requires_full_render=raw['mode']!='full',media_id=video.artifact_id,execution_authenticated=False,actual_media_redecoded=False,product_accepted=False)
