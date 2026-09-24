"""Independent sample equation replay. Does not call production gain/duck/mix/trim.

Same NumPy arithmetic and PCM conventions, not an independently certified DSP.
The receipt is untrusted and must already have passed source/clock validation.
"""
import numpy as np
from dataclasses import fields
from .sfx_mixing import Stem
from .common import integer
from .mix_contract import number
from .common import AudioError
from .mix_contract import MixBuffer
from .tts_contract import AudioFormat

def replay_mix(mixed,sync,asset_wavs=()):
    c=mixed.clock();r=mixed.receipt();rate=c['sample_rate'];fmt=AudioFormat(rate,c['channels'])
    source=MixBuffer.from_wav(sync.wav_bytes,fmt).array();actual=MixBuffer.from_wav(mixed.wav_bytes,fmt).array()
    if type(asset_wavs)is not tuple or len(asset_wavs)>128 or any(type(d)is not bytes for d in asset_wavs):raise AudioError('QA_STEM_BYTES')
    available={}
    # WAV headers determine the explicit mono/stereo input shape.
    import io,wave
    for data in asset_wavs:
        with wave.open(io.BytesIO(data),'rb') as w:af=AudioFormat(w.getframerate(),w.getnchannels())
        p=MixBuffer.from_wav(data,af);available[p.sha256]=p
    buses=[]
    for role in ('music','sfx'):
        bus=np.zeros_like(source)
        rows=r[role]['stems']
        if type(rows)is not list or len(rows)>128 or len({x['asset_id'] for x in rows})!=len(rows):raise AudioError('QA_STEM_COUNT')
        for st in sorted(rows,key=lambda x:x['asset_id']):
            p=available.get(st['pcm']['f64le_sha256'])
            if p is None:raise AudioError('QA_STEM_BYTES_MISSING',st['asset_id'])
            if p.info()!=st['pcm'] or p.sample_rate!=rate:raise AudioError('QA_STEM_METADATA')
            args={f.name:st[f.name] for f in fields(Stem) if f.name!='pcm'}
            args['source_refs']=tuple(args['source_refs']);typed=Stem(pcm=p,**args)
            if typed.role!=role or typed.start_sample+typed.length>len(source) or st['output_start']!=typed.start_sample or st['output_end']!=typed.start_sample+typed.length:raise AudioError('QA_STEM_CLOCK')
            if (typed.channel_map=='identity' and p.channels!=fmt.channels) or (typed.channel_map!='identity' and (p.channels!=1 or fmt.channels!=2)):raise AudioError('QA_STEM_CHANNEL_MAP')
            x=p.array()[st['trim_start']:st['trim_end']].copy()
            if st['channel_map']=='mono_dual':x=np.repeat(x,2,axis=1)
            elif st['channel_map']=='mono_equal_power':
                theta=(st['pan']+1)*np.pi/4;x=x*np.array([[np.cos(theta),np.sin(theta)]])
            elif st['channel_map']!='identity':raise AudioError('QA_STEM_CHANNEL_MAP')
            x=np.tile(x,(st['repeat'],1))*10**(st['gain_db']/20)
            fi,fo=st['fade_in_samples'],st['fade_out_samples']
            if fi:x[:fi]*=(np.arange(fi)/fi)[:,None]
            if fo:x[-fo:]*=(np.arange(fo-1,-1,-1)/fo)[:,None]
            bus[st['start_sample']:st['start_sample']+len(x)]+=x
        buses.append(bus)
    for k in ('narration_normalization','programme_normalization','peak_control'):
        number(r[k]['applied_gain_db'],'applied gain',-120,36)
    start,end=c['source_start_sample'],c['source_end_sample'];voice=source[start:end]*10**(r['narration_normalization']['applied_gain_db']/20)
    music,sfx=(b[start:end] for b in buses);env=np.ones(len(voice));depth=10**(r['policy']['ducking']['reduction_db']/20)
    if type(r['ducking']['windows'])is not list or len(r['ducking']['windows'])>20000:raise AudioError('QA_DUCK_WINDOWS')
    previous=0
    for w in r['ducking']['windows']:
        a,s,e,b=(w[k] for k in ('attack_start','active_start','active_end','release_end'))
        for value in (a,s,e,b):integer(value,'duck boundary',0,len(voice))
        if not previous<=a<=s<e<=b:raise AudioError('QA_DUCK_WINDOW_ORDER')
        previous=b
        if a<s:env[a:s]=np.linspace(1,depth,s-a,endpoint=False)
        env[s:e]=depth
        if e<b:env[e:b]=np.linspace(depth,1,b-e,endpoint=False)
    music*=env[:,None];pause_env=np.ones(len(music));fade=r['pause_music_automation']['pause_fade_samples']
    integer(fade,'pause fade',0,rate*2)
    if type(r['pause_music_automation']['windows'])is not list or len(r['pause_music_automation']['windows'])>20000:raise AudioError('QA_PAUSE_WINDOW_BUDGET')
    previous=0
    for p in r['pause_music_automation']['windows']:
        a,b=p['start'],p['end'];integer(a,'pause start',previous,len(music));integer(b,'pause end',a+1,len(music));previous=b
        lo=max(0,a-fade);hi=min(len(music),b+fade)
        if lo<a:pause_env[lo:a]=np.minimum(pause_env[lo:a],np.linspace(1,1/(a-lo),a-lo))
        pause_env[a:b]=0
        if b<hi:pause_env[b:hi]=np.minimum(pause_env[b:hi],np.arange(hi-b)/(hi-b))
    expected=(voice+music*pause_env[:,None]+sfx)*10**(r['programme_normalization']['applied_gain_db']/20)*10**(r['peak_control']['applied_gain_db']/20)
    q=np.rint(expected*32768)
    if not np.isfinite(q).all() or q.min()<-32768 or q.max()>32767:raise AudioError('QA_REPLAY_WOULD_CLIP')
    error=float(np.max(np.abs(q-np.rint(actual*32768))))
    return {'compared_samples':int(q.size),'maximum_pcm16_sample_difference':error,
            'tolerance_pcm16_units':1,'matched':bool(error<=1),'independent_library_implementation':False}
