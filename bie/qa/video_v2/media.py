"""Decode actual bounded MP4 bytes at original dimensions; no resampling/seek guesses."""
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib,json
from ..release_v2.contracts import ContractError
from .models import VideoPolicy
from .process import MediaTools,run_bounded

@dataclass(frozen=True,slots=True)
class DecodedVideo:
    width:int
    height:int
    codec:str
    pixel_format:str
    audio_streams:int
    fps:Fraction
    time_base:Fraction
    pts:tuple[int,...]
    durations:tuple[int,...]
    frames:tuple[bytes,...]
    probe_sha256:str
    decode_sha256:str
    tools_digest:str
    @property
    def frames_count(self):return len(self.frames)

def parse_probe(raw,policy):
    if type(policy) is not VideoPolicy:raise ContractError('VIDEO_POLICY_TYPE')
    try:
        streams=raw['streams'];video=[s for s in streams if s['codec_type']=='video'];audio=[s for s in streams if s['codec_type']=='audio']
        if len(video)!=1:raise ContractError('VIDEO_STREAM_COUNT')
        v=video[0];w,h=v['width'],v['height']
        if type(w) is not int or type(h) is not int or (w,h)!=(policy.width,policy.height):raise ContractError('VIDEO_DIMENSIONS')
        if v['codec_name'] not in policy.codecs or v['pix_fmt'] not in policy.pixel_formats:raise ContractError('VIDEO_CODEC_OR_PIXEL_FORMAT')
        if v.get('sample_aspect_ratio','1:1') not in ('1:1','0:1'):raise ContractError('VIDEO_NON_SQUARE_PIXELS')
        if any(s.get('rotation',0)!=0 or s.get('side_data_type')=='Display Matrix' for s in v.get('side_data_list',())):raise ContractError('VIDEO_DISPLAY_TRANSFORM_UNSUPPORTED')
        if v.get('field_order','progressive') not in ('progressive','unknown'):raise ContractError('VIDEO_INTERLACING_UNSUPPORTED')
        frames=[f for f in raw['frames'] if f.get('media_type')=='video']
        if not frames or len(frames)>24000 or len(frames)*w*h*3>policy.max_decoded_bytes:raise ContractError('VIDEO_DECODE_BUDGET')
        # Missing timestamps or durations are not invented from the frame rate.
        pts=[];dur=[]
        for f in frames:
            p=f['best_effort_timestamp'];d=f.get('duration',f.get('pkt_duration'))
            if type(p) is not int or type(d) is not int or d<=0:raise ContractError('VIDEO_FRAME_CLOCK_MISSING')
            if (f.get('width',w),f.get('height',h))!=(w,h):raise ContractError('VIDEO_DYNAMIC_DIMENSIONS')
            pts.append(p);dur.append(d)
        tb=Fraction(v['time_base']);fps=Fraction(v['avg_frame_rate'])
        if not 0<tb<=1 or not 0<fps<=240:raise ContractError('VIDEO_FRAME_CLOCK_INVALID')
        return v,len(audio),tb,fps,tuple(pts),tuple(dur)
    except (KeyError,TypeError,ValueError,ZeroDivisionError) as exc:
        if isinstance(exc,ContractError):raise
        raise ContractError('VIDEO_PROBE_INVALID') from exc

def inspect_bytes(data,policy,tools=None):
    if type(data) is not bytes or not data:raise ContractError('VIDEO_EMPTY_MEDIA')
    if type(policy) is not VideoPolicy:raise ContractError('VIDEO_POLICY_TYPE')
    tools=MediaTools.discover() if tools is None else tools
    if type(tools) is not MediaTools:raise ContractError('VIDEO_TOOLS_TYPE')
    from ..release_v2.contracts import digest
    identities=tools.identity()
    with TemporaryDirectory(prefix='bie-video-') as directory:
        movie=Path(directory)/'input.mp4';movie.write_bytes(data)
        # Force MOV-family demuxing; local embedded data references disabled.
        input_args=['-protocol_whitelist','file','-f','mov','-enable_drefs','0','-use_absolute_path','0']
        entries='stream=index,codec_type,width,height,codec_name,pix_fmt,avg_frame_rate,time_base,sample_aspect_ratio,field_order:stream_side_data:frame=media_type,best_effort_timestamp,duration,pkt_duration,width,height'
        p=run_bounded([tools.ffprobe,'-v','error','-max_alloc','67108864','-threads','1',*input_args,'-show_streams','-show_frames','-show_entries',entries,'-of','json',str(movie)],timeout=policy.max_process_seconds,max_stdout=8388608)
        if p.returncode or p.stderr.strip():raise ContractError('VIDEO_PROBE_FAILED')
        try:raw=json.loads(p.stdout)
        except (ValueError,UnicodeError) as exc:raise ContractError('VIDEO_PROBE_INVALID') from exc
        v,na,tb,fps,pts,dur=parse_probe(raw,policy)
        d=run_bounded([tools.ffmpeg,'-v','error','-nostdin','-xerror','-max_alloc','67108864','-threads','1','-filter_threads','1','-noautorotate','-err_detect','explode',*input_args,'-i',str(movie),'-map','0:v:0','-an','-sn','-dn','-fps_mode','passthrough','-pix_fmt','rgb24','-threads','1','-f','rawvideo','pipe:1'],timeout=policy.max_process_seconds,max_stdout=policy.max_decoded_bytes)
        if d.returncode or d.stderr.strip():raise ContractError('VIDEO_DECODE_FAILED')
        size=policy.width*policy.height*3
        if not d.stdout or len(d.stdout)%size or len(d.stdout)//size!=len(pts):raise ContractError('VIDEO_DECODE_FRAME_COUNT')
        if hashlib.sha256(movie.read_bytes()).digest()!=hashlib.sha256(data).digest():raise ContractError('VIDEO_SNAPSHOT_CHANGED')
        return DecodedVideo(policy.width,policy.height,v['codec_name'],v['pix_fmt'],na,fps,tb,pts,dur,tuple(d.stdout[i:i+size] for i in range(0,len(d.stdout),size)),hashlib.sha256(p.stdout).hexdigest(),hashlib.sha256(d.stdout).hexdigest(),digest(identities))
