"""H10-004: actual bounded FFmpeg technical AV+caption render evidence.

This is real process/media evidence but explicitly not a Remotion render, human
listening evaluation, cinematic-quality certificate, or product acceptance.
"""
from __future__ import annotations
import hashlib,json,shutil,tempfile,io,wave,re
from pathlib import Path
from .common import AudioError,fingerprint

SCHEMA='bie.audio.technical-av-render/1'

def _run(cmd,cwd,timeout=30):
    try:
        from bie.compiler.render_process import run_bounded_process
    except Exception as exc:raise AudioError('RENDER_PROCESS_DEPENDENCY_MISSING') from exc
    out=run_bounded_process(cmd,cwd=cwd,timeout_s=timeout,max_output_bytes=512*1024)
    if out.outcome!='SUCCEEDED' or not out.process.passed:raise AudioError('TECHNICAL_RENDER_PROCESS_FAILED',out.outcome)
    return out

def render_technical_av(master_wav:bytes,captions_srt:bytes,output_dir,*,fps=24,width=640,height=360):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):raise AudioError('FFMPEG_TOOLCHAIN_UNAVAILABLE')
    root=Path(output_dir);root.mkdir(parents=True,exist_ok=True)
    wav=root/'master.wav';srt=root/'captions.srt';mp4=root/'technical_av.mp4';wav.write_bytes(master_wav);srt.write_bytes(captions_srt)
    try:
        with wave.open(io.BytesIO(master_wav),'rb') as w: duration=w.getnframes()/w.getframerate()
    except Exception as exc: raise AudioError('TECHNICAL_RENDER_WAV_INVALID') from exc
    # Use a finite video source and explicit duration. This avoids -shortest dropping a
    # subtitle packet whose cue ends near the audio boundary.
    d=f'{duration:.6f}'
    cmd=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','lavfi','-i',f'testsrc2=size={width}x{height}:rate={fps}:duration={d}',
         '-i',str(wav.name),'-i',str(srt.name),'-map','0:v:0','-map','1:a:0','-map','2:s:0','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p',
         '-c:a','aac','-c:s','mov_text','-t',d,str(mp4.name)]
    run=_run(cmd,root,45)
    probe=_run(['ffprobe','-v','error','-show_entries','stream=index,codec_type,codec_name,duration:format=duration','-of','json',str(mp4.name)],root,15)
    try:p=json.loads(probe.process.stdout)
    except Exception as exc:raise AudioError('FFPROBE_JSON_INVALID') from exc
    types=[x.get('codec_type') for x in p.get('streams',[])]
    if not {'video','audio','subtitle'}<=set(types):raise AudioError('TECHNICAL_RENDER_STREAM_MISSING')
    extracted=root/'captions.roundtrip.srt'
    _run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-i',str(mp4.name),'-map','0:s:0','-c:s','srt',str(extracted.name)],root,15)
    roundtrip=extracted.read_bytes()
    def caption_text(data):
        lines=[]
        for line in data.decode('utf-8',errors='strict').replace('\r','').split('\n'):
            v=line.strip()
            if not v or v.isdigit() or '-->' in v: continue
            lines.append(v)
        return ' '.join(lines)
    if not roundtrip or caption_text(roundtrip)!=caption_text(captions_srt):raise AudioError('TECHNICAL_RENDER_CAPTION_ROUNDTRIP')
    data=mp4.read_bytes()
    if len(data)<1000:raise AudioError('TECHNICAL_RENDER_TOO_SMALL')
    receipt={'schema_version':SCHEMA,'ffmpeg_executable':shutil.which('ffmpeg'),'ffprobe_executable':shutil.which('ffprobe'),
      'output_sha256':hashlib.sha256(data).hexdigest(),'output_bytes':len(data),'stream_types':types,
      'streams':p['streams'],'format_duration':p.get('format',{}).get('duration'),
      'caption_roundtrip_text_sha256':hashlib.sha256(caption_text(roundtrip).encode()).hexdigest(),
      'ffmpeg_exit_code':run.process.exit_code,'ffprobe_exit_code':probe.process.exit_code,
      'real_ffmpeg_av_render_verified':True,'audio_stream_verified':True,'caption_stream_verified':True,
      'real_remotion_render_verified':False,'human_listening_verified':False,'cinematic_quality_verified':False,'product_accepted':False}
    # Paths are excluded from fingerprint/evidence identity to keep receipts relocatable.
    safe={k:v for k,v in receipt.items() if k not in ('ffmpeg_executable','ffprobe_executable')}
    receipt['fingerprint']=fingerprint(safe)
    return receipt,data

def validate_render_receipt(receipt,mp4_bytes):
    if receipt.get('schema_version')!=SCHEMA or receipt.get('real_ffmpeg_av_render_verified') is not True:raise AudioError('TECHNICAL_RENDER_RECEIPT')
    if receipt.get('real_remotion_render_verified') is not False or receipt.get('product_accepted') is not False:raise AudioError('TECHNICAL_RENDER_BOUNDARY')
    if hashlib.sha256(mp4_bytes).hexdigest()!=receipt.get('output_sha256') or len(mp4_bytes)!=receipt.get('output_bytes'):raise AudioError('TECHNICAL_RENDER_BYTES')
    if not {'video','audio','subtitle'}<=set(receipt.get('stream_types',[])):raise AudioError('TECHNICAL_RENDER_STREAMS')
    safe={k:v for k,v in receipt.items() if k not in ('ffmpeg_executable','ffprobe_executable','fingerprint')}
    if receipt.get('fingerprint')!=fingerprint(safe):raise AudioError('TECHNICAL_RENDER_FINGERPRINT')
    return receipt
