"""Normalize local compressed audio and mix explicit sample-aligned PCM inputs.

These are actual asset producers feeding H6's existing content-addressed WAV
consumer. They do not generate/recognize speech or infer timing, loudness or rights.
Decoder runs use H7's real no-network Linux worker; never the host unisolated.
"""
from pathlib import Path
from hashlib import sha256
from dataclasses import asdict
from array import array
import io,json,os,sys,tempfile,wave
from .qa_common import CompilerQAError,digest
from .narration_assets import inspect_pcm
from .installed_toolchain import file_hash
from .linux_worker import run_isolated,WorkerPolicy

MAX_BYTES=32*1024**2

def _int(value,low,high,code):
    if type(value)is not int or not low<=value<=high:raise CompilerQAError(code)
    return value

def wav_bytes(pcm,rate,channels):
    out=io.BytesIO()
    with wave.open(out,'wb') as w:w.setnchannels(channels);w.setsampwidth(2);w.setframerate(rate);w.writeframes(pcm)
    return out.getvalue()

def asset_descriptor(data, *, asset_id,rights_ref,source_refs,reasoning_refs):
    from .frame_runtime_contract import ident,text
    ident(asset_id,'asset_id');text(rights_ref,'rights_ref')
    for r in (source_refs,reasoning_refs):
        if not isinstance(r,list) or not r or any(not isinstance(x,str) or not x for x in r) or len(set(r))!=len(r):raise CompilerQAError('AUDIO_PREPARATION_PROVENANCE_REQUIRED')
    meta,_=inspect_pcm(data);h=sha256(data).hexdigest()
    return {'asset_id':asset_id,'public_path':'narration/'+h+'.wav','sha256':h,'byte_length':len(data),**meta,'rights_ref':rights_ref,'source_refs':list(source_refs),'reasoning_refs':list(reasoning_refs)}

def normalize_local_audio(path, *, expected_sha256,sample_rate,channels,ffmpeg='/usr/bin/ffmpeg',ffprobe='/usr/bin/ffprobe'):
    _int(sample_rate,8000,96000,'AUDIO_SAMPLE_RATE');_int(channels,1,2,'AUDIO_CHANNELS')
    path=Path(path).absolute()
    if path.is_symlink() or not path.is_file() or any(p.is_symlink() for p in path.parents):raise CompilerQAError('AUDIO_INPUT_PATH')
    if not isinstance(expected_sha256,str) or len(expected_sha256)!=64:raise CompilerQAError('AUDIO_INPUT_HASH')
    h,n=file_hash(path)
    if h!=expected_sha256 or not 1<=n<=MAX_BYTES:raise CompilerQAError('AUDIO_INPUT_IDENTITY')
    # Copy verified immutable bytes; source mutation between reads is detected.
    data=path.read_bytes()
    if len(data)!=n or sha256(data).hexdigest()!=h:raise CompilerQAError('AUDIO_INPUT_CHANGED')
    executions=[];tools={}
    for label,value in (('ffmpeg',ffmpeg),('ffprobe',ffprobe)):
        p=Path(value)
        if not p.is_absolute() or not p.is_file():raise CompilerQAError('AUDIO_EXPLICIT_TOOL_REQUIRED')
        tools[label]={'sha256':file_hash(p.resolve())[0],'path':str(p)}
    with tempfile.TemporaryDirectory(prefix='bie-audio-prepare-') as td:
        root=Path(td);(root/'input.media').write_bytes(data);(root/'output').mkdir()
        policy=WorkerPolicy(procfs=False,cpu_seconds=60,file_bytes=MAX_BYTES,address_space_bytes=2*1024**3)
        p,k=run_isolated([ffprobe,'-v','error','-show_streams','-show_format','-of','json',str(root/'input.media')],workspace=root,policy=policy,timeout_s=20,max_output_bytes=1024**2)
        executions.append({'operation':'probe','process':asdict(p),'kernel_policy':k})
        if not p.process.passed:raise CompilerQAError('AUDIO_PROBE_BLOCKED:'+p.outcome+':'+p.process.stderr[:500])
        try:j=json.loads(p.process.stdout);streams=j['streams']
        except (ValueError,KeyError):raise CompilerQAError('AUDIO_PROBE_INVALID')
        if len(streams)!=1 or streams[0].get('codec_type')!='audio' or streams[0].get('codec_name') not in {'mp3','flac','vorbis','opus','pcm_s16le'}:raise CompilerQAError('AUDIO_CODEC_PROFILE_UNSUPPORTED')
        codec=streams[0]['codec_name'];source_channels=streams[0].get('channels')
        if source_channels!=channels:raise CompilerQAError('AUDIO_CHANNEL_REMAPPING_NOT_DECLARED')
        command=[ffmpeg,'-nostdin','-v','error','-xerror','-i',str(root/'input.media'),'-map','0:a:0','-vn','-sn','-dn','-map_metadata','-1','-flags:a','+bitexact','-fflags','+bitexact','-c:a','pcm_s16le','-ar',str(sample_rate),'-ac',str(channels),'-threads','1',str(root/'output/normalized.wav')]
        p,k=run_isolated(command,workspace=root,writable=['output'],policy=policy,timeout_s=65,max_output_bytes=1024**2)
        executions.append({'operation':'decode','process':asdict(p),'kernel_policy':k})
        if not p.process.passed:raise CompilerQAError('AUDIO_DECODE_BLOCKED:'+p.outcome+':'+p.process.stderr[:500])
        target=root/'output/normalized.wav';out=target.read_bytes();meta,_=inspect_pcm(out)
        if len(out)>MAX_BYTES or meta['sample_rate']!=sample_rate or meta['channels']!=channels or meta['frame_count']<=0:raise CompilerQAError('AUDIO_NORMALIZED_OUTPUT_INVALID')
    for tool in tools.values():
        if file_hash(Path(tool['path']).resolve())[0]!=tool['sha256']:raise CompilerQAError('AUDIO_TOOL_CHANGED')
    return out,{'schema_version':'bie.audio-normalization.v1','input_sha256':h,'source_codec':codec,'output_sha256':sha256(out).hexdigest(),
                'metadata':meta,'executions':executions,'tools':tools,'decoder_ran':True,'network_isolated':True,
                'speech_alignment':'NOT_VERIFIED','source_semantic_equivalence':'NOT_VERIFIED_CODEC_TRANSFORM_ONLY','accepted':False}

def mix_pcm_segments(assets,segments, *, sample_rate,channels,total_samples):
    _int(sample_rate,8000,96000,'AUDIO_SAMPLE_RATE');_int(channels,1,2,'AUDIO_CHANNELS')
    _int(total_samples,1,(MAX_BYTES-44)//(2*channels),'AUDIO_MIX_BUDGET')
    if not isinstance(assets,dict) or not 1<=len(assets)<=32 or not isinstance(segments,list) or not 1<=len(segments)<=128:raise CompilerQAError('AUDIO_MIX_CONTRACT')
    if any(not isinstance(x,bytes) for x in assets.values()) or sum(len(x) for x in assets.values())>64*1024**2:raise CompilerQAError('AUDIO_MIX_BUDGET')
    values={};hashes={}
    for aid,data in assets.items():
        if not isinstance(aid,str) or not aid or not isinstance(data,bytes) or len(data)>MAX_BYTES:raise CompilerQAError('AUDIO_MIX_ASSET')
        m,pcm=inspect_pcm(data)
        if m['sample_rate']!=sample_rate or m['channels']!=channels:raise CompilerQAError('AUDIO_MIX_CLOCK_MISMATCH')
        v=array('h');v.frombytes(pcm)
        if sys.byteorder!='little':v.byteswap()
        values[aid]=v;hashes[aid]=sha256(data).hexdigest()
    if sum(len(x) for x in assets.values())>64*1024**2:raise CompilerQAError('AUDIO_MIX_BUDGET')
    import math
    ids=set();used=set();prepared=[]
    for s in segments:
        if not isinstance(s,dict) or set(s)!={'segment_id','asset_id','start_sample','trim_sample','sample_count','gain'}:raise CompilerQAError('AUDIO_MIX_SEGMENT_FIELDS')
        if not isinstance(s['segment_id'],str) or not s['segment_id'] or s['segment_id'] in ids or s['asset_id'] not in values:raise CompilerQAError('AUDIO_MIX_SEGMENT_IDENTITY')
        ids.add(s['segment_id']);used.add(s['asset_id']);start=_int(s['start_sample'],0,total_samples-1,'AUDIO_MIX_TIMING');trim=_int(s['trim_sample'],0,len(values[s['asset_id']])//channels-1,'AUDIO_MIX_TRIM');n=_int(s['sample_count'],1,total_samples,'AUDIO_MIX_COUNT')
        if start+n>total_samples or trim+n>len(values[s['asset_id']])//channels:raise CompilerQAError('AUDIO_MIX_RANGE')
        gain=s['gain']
        if type(gain)not in (float,int) or not math.isfinite(gain) or not 0<gain<=1:raise CompilerQAError('AUDIO_MIX_GAIN')
        prepared.append((s['segment_id'],s['asset_id'],start,trim,n,gain))
    if used!=set(assets):raise CompilerQAError('AUDIO_MIX_UNUSED_ASSET')
    if sum(x[4]*channels for x in prepared)>32*1024**2:raise CompilerQAError('AUDIO_MIX_OPERATION_BUDGET')
    # Canonical segment ordering; round only after accumulation, no hidden limiter.
    acc=array('d',[0.])*(total_samples*channels)
    for _,aid,start,trim,n,gain in sorted(prepared):
        src=values[aid]
        for i in range(n*channels):acc[start*channels+i]+=src[trim*channels+i]*gain
    if any(v < -32768 or v > 32767 for v in acc):raise CompilerQAError('AUDIO_MIX_CLIPPING_REJECTED')
    pcm=array('h',(round(v) for v in acc))
    if sys.byteorder!='little':pcm.byteswap()
    data=wav_bytes(pcm.tobytes(),sample_rate,channels)
    return data,{'schema_version':'bie.pcm-sample-mix.v1','input_hashes':hashes,'segments':sorted(segments,key=lambda x:x['segment_id']),
                 'sample_rate':sample_rate,'channels':channels,'total_samples':total_samples,'output_sha256':sha256(data).hexdigest(),
                 'peak_integer_sample':max(abs(round(v)) for v in acc),'timing':'EXPLICIT_SAMPLE_OFFSETS_NO_INFERRED_ALIGNMENT',
                 'clipping':'REJECT_NOT_LIMIT_OR_NORMALIZE','speech_alignment':'NOT_VERIFIED','real_remotion':False,'accepted':False}
