"""H10-005: F04 implementation-side evidence gate."""
from __future__ import annotations
from .common import AudioError,fingerprint
from .compiler_handoff import validate_compiler_handoff
from .render_evidence import validate_render_receipt

SCHEMA='bie.audio.f04-gate/1'

def evaluate_f04(*,dir_receipt,compiler_receipt,compiler_files,invalidation_receipt,render_receipt,render_bytes):
    if dir_receipt.get('schema_version')!='bie.audio.dir-audio-handoff/1' or dir_receipt.get('source_text_mutated') is not False:raise AudioError('F04_DIR_HANDOFF')
    validate_compiler_handoff(compiler_receipt,compiler_files);validate_render_receipt(render_receipt,render_bytes)
    if invalidation_receipt.get('schema_version')!='bie.audio.repair-invalidation/1' or invalidation_receipt.get('repository_mutated') is not False:raise AudioError('F04_INVALIDATION')
    if not any(x['task_id']=='RENDER' for x in invalidation_receipt.get('invalidations',[])):raise AudioError('F04_RENDER_INVALIDATION')
    out={'schema_version':SCHEMA,'dir_handoff_fingerprint':dir_receipt['fingerprint'],
         'compiler_handoff_fingerprint':compiler_receipt['fingerprint'],'invalidation_fingerprint':invalidation_receipt['fingerprint'],
         'technical_render_fingerprint':render_receipt['fingerprint'],
         'implementation_side_status':'IMPLEMENTED_FOCUSED_TESTED',
         'canonical_integration_performed':False,'real_ffmpeg_av_render_verified':True,'real_remotion_render_verified':False,
         'live_provider_listening_verified':False,'full_audio_regression_completed':False,'section_exit_permitted':False,'product_accepted':False}
    out['fingerprint']=fingerprint(out);return out

def validate_f04_gate(receipt):
    if receipt.get('schema_version')!=SCHEMA or receipt.get('implementation_side_status')!='IMPLEMENTED_FOCUSED_TESTED':raise AudioError('F04_GATE_RECEIPT')
    if receipt.get('real_remotion_render_verified') is not False or receipt.get('section_exit_permitted') is not False or receipt.get('product_accepted') is not False:raise AudioError('F04_GATE_BOUNDARY')
    core={k:v for k,v in receipt.items() if k!='fingerprint'}
    if receipt.get('fingerprint')!=fingerprint(core):raise AudioError('F04_GATE_FINGERPRINT')
    return receipt
