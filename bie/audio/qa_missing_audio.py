"""QA-003: exact expected segment coverage and narration-present mix replay."""
from .qa_contract import Finding,check,TASKS
from .mix_pipeline import verify_mixed_source
from .mix_contract import MixBuffer
from .tts_contract import AudioFormat
from .qa_signal_replay import replay_mix
import numpy as np

def missing_audio_qa(mixed,sync,asset_wavs=()):
    verify_mixed_source(mixed,sync);c=mixed.clock();pcm=MixBuffer.from_wav(mixed.wav_bytes,AudioFormat(c['sample_rate'],c['channels']));fs=[];rows=[]
    for p in c['segments']:
        part=pcm.array()[p['start_sample']:p['provider_end_sample']];nonzero=int(np.count_nonzero(part))
        rows.append({'segment_id':p['segment_id'],'nonzero_delivered_samples':nonzero})
        if not nonzero:fs.append(Finding('SEGMENT_SILENT','FAIL','AUDIO/VO-MIX',p['segment_id'],'Expected speech segment has no nonzero delivered PCM.'))
    replay=replay_mix(mixed,sync,asset_wavs)
    if not replay['matched']:fs.append(Finding('MIX_REPLAY_MISMATCH','FAIL','AUDIO/MIX','master.wav','Delivered PCM does not match source narration plus declared stems/gains. Background energy cannot substitute missing narration.'))
    return check(TASKS[2],'Source-bound segment/asset coverage and sample-level mix replay',fs,
        {'segments':rows,'replay':replay,'source_segment_count':len(sync.plan.segments),'semantic_transcript_verified':False})
