"""H5-002 fixed local speech operation, invoked only inside the canonical worker.

No key, credential, durable database or host source tree is mounted here.
"""
from __future__ import annotations
from pathlib import Path
import sys
import tempfile
from .common import AudioError, fingerprint, strict_json
from .acoustic_contract import canonical, fields, sha
from .pipeline_contract import OPERATION, SCOPE, BOUNDARIES, PipelineLimits, validate_request
from .pipeline_bundle import index_files
from .pipeline_stems import decode_stems


def main():
    from .tts_cache import read_regular,TTSCache
    from .timed_espeak_provider import TimedEspeakProvider
    from .voice_selection import SelectionPolicy
    from .caption_alignment import CaptionPolicy
    from .sync_pipeline import prepare_sync
    from .mix_meter import FFmpegMeter
    from .mix_pipeline import mix_synchronized,export_mixed_captions,verify_mixed_source
    wrapper=strict_json(read_regular(Path('/work/request.json'),4_000_000).decode())
    fields(wrapper,('operation','nonce','request','selected_runtime'))
    if wrapper['operation']!=OPERATION:raise AudioError('PIPELINE_CHILD_OPERATION')
    sha(wrapper['nonce']);request=wrapper['request'];limits=PipelineLimits(**request['limits'])
    plan=validate_request(request);selected=wrapper['selected_runtime']
    fields(selected,('provider_runtime_fingerprint','catalog_fingerprint','meter_runtime_fingerprint','numpy_version'))
    provider=TimedEspeakProvider('/usr/bin/espeak');meter=FFmpegMeter('/usr/bin/ffmpeg')
    import numpy as np
    actual={'provider_runtime_fingerprint':provider.runtime,'catalog_fingerprint':provider.catalog().fingerprint(),
        'meter_runtime_fingerprint':meter.runtime_fingerprint,'numpy_version':np.__version__}
    if selected!=actual:raise AudioError('PIPELINE_CHILD_RUNTIME_DRIFT_'+','.join(k for k in actual if actual[k]!=selected[k]))
    with tempfile.TemporaryDirectory(prefix='bie-local-pipeline-cache-') as td:
        cache=TTSCache(td,namespace='audio-local-pipeline-v1')
        selection=SelectionPolicy(('espeak-timed-local',),('technical_formant',),require_same_voice_code_switching=False)
        sync=prepare_sync(plan,provider,cache,selection,caption_policy=CaptionPolicy(channel='display'))
        if sync.timeline.total_samples>limits.max_audio_seconds*sync.timeline.sample_rate:
            raise AudioError('PIPELINE_AUDIO_BUDGET')
        stems=decode_stems(request['mix_stems'],sync.assets[0].request.settings.format) if request['mix_stems'] else ()
        mixed=mix_synchronized(sync,stems,meter=meter)
        verify_mixed_source(mixed,sync)
    files={'master.wav':mixed.wav_bytes,'source.wav':sync.wav_bytes,
        'SOURCE_SYNC.json':canonical(sync.receipt()),'MIX_CLOCK.json':mixed.clock_json.encode(),
        'MIX_RECEIPT.json':mixed.receipt_json.encode(),
        'captions.vtt':export_mixed_captions(mixed,'vtt').encode(),
        'captions.srt':export_mixed_captions(mixed,'srt').encode(),
        'ENGINE_EVIDENCE.json':canonical(list(sync.engine_evidence))}
    summary={'schema_version':'bie.audio.local-pipeline-summary/1','operation':OPERATION,'scope':SCOPE,
        'request_fingerprint':request['fingerprint'],'plan_fingerprint':plan.fingerprint(),
        'segments':len(sync.assets),'provider_calls':provider.invocations,'mix_stems':len(stems),'mix_stems_fingerprint':request['mix_stems_fingerprint'],
        'timing_replay_calls':len(sync.assets),'internal_cache_hits':list(sync.cache_hits),
        'source_sync_fingerprint':fingerprint(sync.receipt()),'mix_fingerprint':mixed.receipt()['fingerprint'],
        'technical_review_required':True,**BOUNDARIES}
    files['PIPELINE_SUMMARY.json']=canonical(summary)
    index=index_files(files,limits)
    out=Path('/work/output')
    for name,data in sorted(files.items()):
        with (out/name).open('xb') as f:f.write(data)
    answer={'operation':OPERATION,'nonce':wrapper['nonce'],'request_fingerprint':request['fingerprint'],
        'files':index}
    with (out/'result.json').open('xb') as f:f.write(canonical(answer))
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,RuntimeError,KeyError,TypeError) as exc:
        print(getattr(exc,'code','PIPELINE_CHILD_FAILED'),file=sys.stderr)
        raise SystemExit(2)
