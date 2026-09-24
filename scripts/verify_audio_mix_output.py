#!/usr/bin/env python3
"""Independent native inspection and numerical replay of a published MIX output.

Does not call MIX gain/duck/sum/trim/peak functions. Receipts are not signatures;
this checks source/media consistency and selected DSP arithmetic, not listening QA.
"""
from pathlib import Path, PurePosixPath
import argparse,hashlib,json,os,re,subprocess,sys,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'dependency_snapshot'))
from bie.audio.mix_pipeline import MixedAudio


def pcm(path):
    with wave.open(str(path),'rb') as w:
        if w.getsampwidth()!=2:raise ValueError('PCM16_REQUIRED')
        data=w.readframes(w.getnframes());return np.frombuffer(data,dtype='<i2').reshape(-1,w.getnchannels()).astype(np.float64)/32768,w.getframerate()

def check(folder):
    folder=Path(folder);index=json.loads((folder/'OUTPUT_SHA256.json').read_text())
    if set(index)!={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}-{'OUTPUT_SHA256.json'}:raise ValueError('FILE_SET_MISMATCH')
    for name,row in index.items():
        rel=PurePosixPath(name)
        if rel.is_absolute() or '..'in rel.parts:raise ValueError('OUTPUT_PATH')
        path=folder/rel
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):raise ValueError('OUTPUT_SYMLINK')
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=row['sha256'] or len(data)!=row['bytes']:raise ValueError('OUTPUT_HASH')
    result=MixedAudio((folder/'master.wav').read_bytes(),(folder/'MIX_CLOCK.json').read_text(),(folder/'MIX_RECEIPT.json').read_text()).validate()
    c,r=result.clock(),result.receipt();source,rate=pcm(folder/'source.wav');actual,_=pcm(folder/'master.wav')
    start,end=c['source_start_sample'],c['source_end_sample'];voice=source[start:end]*10**(r['narration_normalization']['applied_gain_db']/20)
    buses=[]
    for role in ('music','sfx'):
        bus=np.zeros_like(source)
        for st in sorted(r[role]['stems'],key=lambda x:x['asset_id']):
            # Every copied input is named by its WAV hash. Match its decoded PCM identity.
            matches=[]
            for p in (folder/'inputs').glob('*.wav'):
                x,sr=pcm(p)
                if sr==rate and hashlib.sha256(x.astype('<f8').tobytes()).hexdigest()==st['pcm']['f64le_sha256']:matches.append(x)
            if not matches:raise ValueError('SOURCE_ASSET_UNAVAILABLE')
            x=matches[0][st['trim_start']:st['trim_end']]
            if st['channel_map']=='mono_dual':x=np.repeat(x,2,axis=1)
            elif st['channel_map']=='mono_equal_power':
                theta=(st['pan']+1)*np.pi/4;x=x*np.array([[np.cos(theta),np.sin(theta)]])
            x=np.tile(x,(st['repeat'],1))*10**(st['gain_db']/20)
            fi,fo=st['fade_in_samples'],st['fade_out_samples']
            if fi:x[:fi]*=(np.arange(fi)/fi)[:,None]
            if fo:x[-fo:]*=(np.arange(fo-1,-1,-1)/fo)[:,None]
            bus[st['start_sample']:st['start_sample']+len(x)]+=x
        buses.append(bus[start:end])
    music,sfx=buses;env=np.ones(len(voice));depth=10**(r['policy']['ducking']['reduction_db']/20)
    for w in r['ducking']['windows']:
        a,s,e,b=w['attack_start'],w['active_start'],w['active_end'],w['release_end']
        if a<s:env[a:s]=np.linspace(1,depth,s-a,endpoint=False)
        env[s:e]=depth
        if e<b:env[e:b]=np.linspace(depth,1,b-e,endpoint=False)
    # Rounding paths can differ by a few float ULPs; compare delivered PCM samples.
    music*=env[:,None];pause_env=np.ones(len(music));fade=r['pause_music_automation']['pause_fade_samples']
    for p in r['pause_music_automation']['windows']:
        a,b=p['start'],p['end'];lo=max(0,a-fade);hi=min(len(music),b+fade)
        if lo<a:pause_env[lo:a]=np.minimum(pause_env[lo:a],np.linspace(1,1/(a-lo),a-lo))
        pause_env[a:b]=0
        if b<hi:pause_env[b:hi]=np.minimum(pause_env[b:hi],np.arange(hi-b)/(hi-b))
    mixed=(voice+music*pause_env[:,None]+sfx)*10**(r['programme_normalization']['applied_gain_db']/20)*10**(r['peak_control']['applied_gain_db']/20)
    q=np.rint(mixed*32768)
    if np.max(q)>32767 or np.min(q)<-32768:raise ValueError('REFERENCE_WOULD_CLIP')
    max_error=float(np.max(np.abs(q-actual*32768)))
    if max_error>1:raise ValueError('SAMPLE_REFERENCE_MISMATCH:'+str(max_error))
    probe=subprocess.run(['ffprobe','-v','error','-select_streams','a:0','-show_entries','stream=codec_name,sample_rate,channels,duration_ts,time_base','-of','json',str(folder/'master.wav')],capture_output=True,text=True,timeout=30,check=True)
    info=json.loads(probe.stdout)['streams'][0]
    if int(info['sample_rate'])!=rate or int(info['channels'])!=actual.shape[1] or int(info['duration_ts'])!=len(actual):raise ValueError('FFPROBE_CLOCK_MISMATCH')
    # Different FFmpeg filter pathway from production loudnorm metering.
    dual=':dualmono=true' if r['policy']['loudness']['dual_mono'] else ''
    native=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-nostats','-i',str(folder/'master.wav'),'-af','ebur128=peak=true'+dual,'-f','null','-'],capture_output=True,text=True,timeout=30,check=True)
    summary=native.stderr.rsplit('Summary:',1)[-1]
    il=float(re.search(r'\bI:\s*([\-\d.]+)\s*LUFS',summary).group(1));tp=float(re.search(r'\bPeak:\s*([\-\d.]+)\s*dBFS',summary).group(1))
    measured=r['peak_control']['after']
    if abs(il-measured['integrated_lufs'])>.25 or abs(tp-measured['true_peak_dbtp'])>.25:raise ValueError('NATIVE_METER_DISAGREEMENT')
    if tp>r['policy']['peaks']['ceiling_dbtp']+.1:raise ValueError('NATIVE_PEAK_CEILING')
    silent=[]
    for p in c['pauses']:
        zero=not np.any(actual[p['start_sample']:p['end_sample']]);silent.append(zero)
    if r['policy']['pause_mode']=='all_stems_silent' and not all(silent):raise ValueError('PAUSE_NOT_SILENT')
    return {'passed':True,'published_files_verified':len(index),'audio_sha256':r['output_audio_sha256'],
        'sample_reference_max_error_pcm16':max_error,'samples_compared_per_channel':len(actual),'channels':actual.shape[1],
        'ffprobe':info,'ebur128_integrated_lufs':il,'ebur128_true_peak_dbtp':tp,'independent_filter_tolerance':.25,
        'protected_pause_zero_checks':silent,'removed_leading_samples':start,'removed_trailing_samples':len(source)-end,
        'input_output_sample_rate_same':True,'source_sync_rewritten':False,'native_stderr_summary':summary,
        'scope':'independent numerical replay and separate FFmpeg filter; shared libav native libraries, not independent acoustic laboratory',
        'human_listening_verified':False,'real_book_accepted':False,'product_accepted':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    report=check(a.folder);text=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if a.output:a.output.write_text(text)
    print(text)
