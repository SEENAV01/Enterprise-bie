from dataclasses import asdict,replace
from functools import lru_cache
from pathlib import Path
import json,tempfile,hashlib
from .mix_test_support import real_sync,tone,stem
from .test_audio_batch004_integration import anchored
from bie.audio.mix_pipeline import mix_synchronized,MixedAudio
from bie.audio.mix_meter import FFmpegMeter
from bie.audio.mix_contract import MixBuffer
from bie.audio.tts_contract import AudioFormat
from bie.audio.common import fingerprint

@lru_cache(maxsize=3)
def native(with_stem=False,language='english'):
    sync=real_sync(language);meter=FFmpegMeter();extra=()
    if with_stem:extra=(stem(MixBuffer.from_wav(tone(frames=22050,amp=.02,hz=600).to_wav(),AudioFormat()),asset_id='cue',start_sample=0),)
    result=mix_synchronized(sync,extra,meter=meter,animations=anchored(sync) if language=='english' else None)
    return sync,result,tuple(s.pcm.to_wav() for s in extra)

def intent(result,caption='Brief tone marks the demonstration'):
    return {'schema_version':'bie.audio.caption-intent/1','mix_fingerprint':result.receipt()['fingerprint'],
        'speakers':[], 'sounds':[{'asset_id':'cue','meaningful':True,'caption':caption,'language':'en','source_refs':['synthetic:test']}]}

def reseal(result,c=None,r=None):
    c=result.clock() if c is None else c;r=result.receipt() if r is None else r
    r['clock_fingerprint']=fingerprint(c);r.pop('fingerprint',None);r['fingerprint']=fingerprint(r)
    return replace(result,clock_json=json.dumps(c),receipt_json=json.dumps(r))

def change_pcm(result,transform):
    c=result.clock();r=result.receipt();fmt=AudioFormat(c['sample_rate'],c['channels'])
    pcm=MixBuffer.from_wav(result.wav_bytes,fmt);a=pcm.array().copy();transform(a,c)
    wav=MixBuffer.from_array(a,pcm.sample_rate).to_wav();p=MixBuffer.from_wav(wav,fmt);h=hashlib.sha256(wav).hexdigest()
    c['output_audio_sha256']=h;r['output_audio_sha256']=h;r['delivery_pcm']=p.info();r['peak_control']['output']=p.info()
    r['peak_control']['after']=asdict(FFmpegMeter().measure(p,dual_mono=r['policy']['loudness']['dual_mono']))
    il=r['peak_control']['after']['integrated_lufs'];reached=il is not None and abs(il-r['policy']['loudness']['target_lufs'])<=r['policy']['loudness']['tolerance_lu']
    rev=[]
    if not reached:rev.append('FINAL_LOUDNESS_TARGET_UNMET')
    if r['narration_normalization']['requires_review']:rev.append('NARRATION_LOUDNESS_CONSTRAINED')
    r['final_loudness_target_reached']=bool(reached);r['requires_review']=bool(rev);r['review_reasons']=rev
    return reseal(replace(result,wav_bytes=wav),c,r).validate()
