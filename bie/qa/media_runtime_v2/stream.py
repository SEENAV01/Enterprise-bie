"""HARD019 streaming full-frame inspection; HARD018 pixel motion/flash signals.

Every decoded presentation frame is inspected, not resized or frame-skipped.
Chunk boundaries preserve the previous frame. Frame clocks come from ffprobe
against the same private byte snapshot. Flash metrics are conservative screening
signals, not accessibility/medical certification. RGB is an explicit SDR profile.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import deque
from fractions import Fraction
from pathlib import Path
import hashlib,json
import numpy as np
from .common import *
from .storage import StreamArtifact,snapshot,verify_chunk_manifest
from .process import pipe,capture

@dataclass(frozen=True)
class StreamPolicy:
    width: int
    height: int
    fps: str
    frames: int
    require_audio: bool=False
    max_input_bytes: int=2*1024**3
    max_working_pixel_bytes: int=128*1024**2
    max_frames: int=216000
    chunk_frames: int=120
    timeout_s: int=180
    black_max: int=3
    uniform_range: int=1
    jump_mean_milli: int=80000
    flash_delta_milli: int=100000
    max_flash_pairs_second: int=3
    max_freeze_frames: int=24
    blank_windows: tuple=()
    motion_windows: tuple=()
    allowed_cut_frames: tuple=()
    sample_frames: tuple=(0,)
    def __post_init__(self):
        integer(self.width,'width',2,4096);integer(self.height,'height',2,2160)
        require(1<=q(self.fps)<=240,'H5_FPS')
        integer(self.max_frames,'frame_limit',1,864000);integer(self.frames,'frames',1,self.max_frames)
        integer(self.max_input_bytes,'input',1,16*1024**3)
        integer(self.max_working_pixel_bytes,'pixel_budget',1024,512*1024**2)
        require(self.width*self.height*3*8<=self.max_working_pixel_bytes,'H5_FRAME_MEMORY_BUDGET')
        integer(self.chunk_frames,'chunk_frames',1,4096);integer(self.timeout_s,'timeout',1,3600)
        integer(self.black_max,'black',0,254);integer(self.uniform_range,'uniform',0,254)
        integer(self.jump_mean_milli,'jump',1,255000);integer(self.flash_delta_milli,'flash',1,255000)
        integer(self.max_flash_pairs_second,'flash_pairs',0,60);integer(self.max_freeze_frames,'freeze',1,10000)
        require(type(self.require_audio)is bool,'H5_AUDIO_FLAG')
        for intervals in (self.blank_windows,self.motion_windows):
            require(type(intervals)is tuple and len(intervals)<=256,'H5_INTERVALS')
            last=-1
            for row in intervals:
                require(type(row)is tuple and len(row)==2,'H5_INTERVAL')
                a,b=row;integer(a,'first',0,self.frames-1);integer(b,'last',1,self.frames)
                require(a<b and a>=last,'H5_INTERVAL_ORDER');last=b
        for values,limit in ((self.allowed_cut_frames,4096),(self.sample_frames,64)):
            require(type(values)is tuple and len(values)<=limit and tuple(sorted(set(values)))==values,'H5_FRAME_SET')
            for i in values:integer(i,'frame',0,self.frames-1)
    @property
    def content_digest(self): return digest(asdict(self))


def inside(i,windows):return any(a<=i<b for a,b in windows)

def spatial_range(pixels):
    # Equivalent full-channel extrema, avoiding the slow Nx3 axis-0 reduction.
    # Every pixel still participates. No scaling, sampling or weaker threshold.
    require(pixels.ndim==1 and len(pixels)%3==0 and len(pixels)>0,'H5_RGB_VECTOR')
    return max(int(pixels[k::3].max())-int(pixels[k::3].min()) for k in range(3))


def lines(handle):
    pending=b''
    while b:=handle['read'](8192):
        pending+=b
        require(len(pending)<=131072,'H5_PROBE_LINE_BUDGET')
        rows=pending.split(b'\n');pending=rows.pop()
        for row in rows:
            if row:yield row.decode('ascii',errors='strict')
    if pending:yield pending.decode('ascii',errors='strict')


def _timestamps(handle):
    for line in lines(handle):
        pairs=dict(p.split('=',1) for p in line.split('|') if '=' in p)
        if 'best_effort_timestamp' in pairs:
            raw=pairs['best_effort_timestamp']
            require(raw not in ('N/A','') and raw.lstrip('-').isdigit(),'H5_PTS_UNAVAILABLE')
            yield int(raw)


def _chunk(first,last,count,hasher,first_pts,last_pts):
    return dict(first_frame=first,last_frame=last,frame_count=count,frame_digest=hasher.hexdigest(),first_pts=qt(first_pts),last_pts=qt(last_pts))


def inspect(root,ref:StreamArtifact,binding:Binding,policy:StreamPolicy,*,ffmpeg:Tool,ffprobe:Tool,samples_dir=None):
    policy_binding(binding,policy);fm=ffmpeg.verify();fp=ffprobe.verify()
    sample_root=Path(samples_dir) if samples_dir is not None else None
    if sample_root is not None:sample_root.mkdir(parents=True,exist_ok=False)
    findings=[];counts={};first_failures={};chunks=[];samples=[]
    def defect(code,frame):
        counts[code]=counts.get(code,0)+1;first_failures.setdefault(code,frame)
    with snapshot(root,ref,maximum=policy.max_input_bytes) as (src,byte_manifest):
        raw=capture([fp,'-v','error','-protocol_whitelist','file,pipe','-show_streams','-of','json',str(src)],timeout=policy.timeout_s)
        meta=json.loads(raw);streams=meta.get('streams',[])
        videos=[s for s in streams if s.get('codec_type')=='video'];audios=[s for s in streams if s.get('codec_type')=='audio']
        require(len(videos)==1,'H5_ONE_VIDEO_STREAM')
        v=videos[0]
        require((v.get('width'),v.get('height'))==(policy.width,policy.height),'H5_VIDEO_DIMENSIONS')
        require(q(v['avg_frame_rate'])==q(policy.fps),'H5_VIDEO_FRAME_RATE')
        require(v.get('pix_fmt') in ('yuv420p','yuv422p','yuv444p','rgb24','bgr0','gbrp'),'H5_VIDEO_PIXEL_PROFILE')
        require(v.get('color_transfer') not in ('smpte2084','arib-std-b67'),'H5_HDR_UNSUPPORTED')
        require(not any('rotation' in x or 'displaymatrix' in x for x in v.get('side_data_list',[])),'H5_ROTATED_VIDEO_UNSUPPORTED')
        if policy.require_audio and not audios:defect('H5_REQUIRED_AUDIO_MISSING',0)
        timebase=q(v['time_base']);expected_duration=Fraction(policy.frames,1)/q(policy.fps)
        # Presentation duration is checked from integer ticks, not rounded format duration.
        if 'duration_ts' in v and abs(int(v['duration_ts'])*timebase-expected_duration)>timebase:
            defect('H5_VIDEO_DURATION',0)
        for a in audios:
            if policy.require_audio and 'duration_ts' in a and 'time_base' in a:
                d=int(a['duration_ts'])*q(a['time_base'])
                if abs(d-expected_duration)>Fraction(1,1)/q(policy.fps):defect('H5_AUDIO_DURATION',0)
        framebytes=policy.width*policy.height*3
        previous=None;last_mean=None;flash_edges=deque();freeze=0;pts0=None;last_pts=None;count=0
        chunk_hash=hashlib.sha256();all_hash=hashlib.sha256();first=0;chunk_count=0;chunk_first_pts=None
        cmd=[fm,'-v','error','-xerror','-nostdin','-threads','1','-protocol_whitelist','file,pipe','-i',str(src),'-map','0:v:0','-an','-sn','-dn','-vsync','0','-pix_fmt','rgb24','-f','rawvideo','pipe:1']
        pcmd=[fp,'-v','error','-protocol_whitelist','file,pipe','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp','-of','compact=p=0:nk=0',str(src)]
        with pipe(cmd,timeout=policy.timeout_s) as rgb, pipe(pcmd,timeout=policy.timeout_s) as clocks:
            ts=iter(_timestamps(clocks))
            while True:
                b=rgb['read'](framebytes)
                if not b:break
                require(len(b)==framebytes,'H5_TRUNCATED_RGB_FRAME')
                require(count<policy.frames and count<policy.max_frames,'H5_EXCESS_FRAMES')
                try: pts=next(ts)*timebase
                except StopIteration as exc:raise ContractError('H5_MISSING_FRAME_TIMESTAMP') from exc
                if pts0 is None:pts0=pts
                if abs(pts-Fraction(count,1)/q(policy.fps))>timebase:defect('H5_FRAME_CADENCE',count)
                if last_pts is not None and pts<=last_pts:defect('H5_NONMONOTONIC_PTS',count)
                pixels=np.frombuffer(b,dtype=np.uint8);mn=int(pixels.min());mx=int(pixels.max())
                mean_milli=int(int(pixels.sum(dtype=np.uint64))*1000//len(pixels))
                if not inside(count,policy.blank_windows) and (mx<=policy.black_max or spatial_range(pixels)<=policy.uniform_range):defect('H5_BLANK_FRAME',count)
                if previous is not None:
                    delta=np.abs(pixels.astype(np.int16)-previous).sum(dtype=np.int64)
                    delta_milli=int(int(delta)*1000//len(pixels))
                    if count not in policy.allowed_cut_frames and delta_milli>policy.jump_mean_milli:defect('H5_UNEXPECTED_FRAME_JUMP',count)
                    if inside(count,policy.motion_windows) and delta==0:freeze+=1
                    else:freeze=0
                    if freeze>=policy.max_freeze_frames:defect('H5_FROZEN_REQUIRED_MOTION',count)
                    if abs(mean_milli-last_mean)>=policy.flash_delta_milli:
                        sign=1 if mean_milli>last_mean else -1
                        flash_edges.append((pts,sign))
                    while flash_edges and pts-flash_edges[0][0]>=1:flash_edges.popleft()
                    alternating=sum(a[1]!=b[1] for a,b in zip(flash_edges,list(flash_edges)[1:]))
                    if (alternating+1)//2>policy.max_flash_pairs_second:defect('H5_FLASH_SCREENING_LIMIT',count)
                previous=pixels.copy();last_mean=mean_milli;last_pts=pts
                row={'frame':count,'pts':qt(pts),'rgb_sha256':hashlib.sha256(b).hexdigest()}
                encoded=canonical_bytes(row)+b'\n';chunk_hash.update(encoded);all_hash.update(encoded)
                if count in policy.sample_frames:
                    sample=dict(row)
                    if sample_root is not None:
                        from PIL import Image
                        dest=sample_root/f'frame-{count:08d}.png'
                        Image.frombytes('RGB',(policy.width,policy.height),b).save(dest)
                        sample.update(png_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),path=dest.name)
                    samples.append(sample)
                if chunk_count==0:chunk_first_pts=pts
                chunk_count+=1;count+=1
                if chunk_count==policy.chunk_frames:
                    chunks.append(_chunk(first,count-1,chunk_count,chunk_hash,chunk_first_pts,pts))
                    first=count;chunk_count=0;chunk_hash=hashlib.sha256()
            require(count==policy.frames,'H5_MISSING_FRAMES')
            require(next(ts,None) is None,'H5_EXTRA_FRAME_TIMESTAMPS')
        require(not rgb['stderr'] and not clocks['stderr'],'H5_DECODER_REPORTED_ERROR')
        if chunk_count:chunks.append(_chunk(first,count-1,chunk_count,chunk_hash,chunk_first_pts,last_pts))
        require(len(samples)==len(policy.sample_frames),'H5_SAMPLE_COVERAGE')
    for code,i in sorted(first_failures.items()):fail(findings,code,str(i))
    details={'artifact':asdict(ref),'binding':asdict(binding),'policy_digest':policy.content_digest,'byte_manifest':byte_manifest,
             'frames':count,'width':policy.width,'height':policy.height,'fps':policy.fps,'decoded_bytes':count*framebytes,
             'logical_pixel_working_budget_bytes':policy.max_working_pixel_bytes,'frame_chain_sha256':all_hash.hexdigest(),
             'chunks':chunks,'samples':samples,'defect_counts':counts,'first_defect_frames':first_failures,
             'audio_stream_count':len(audios),'probe_sha256':hashlib.sha256(raw).hexdigest(),
             'ffmpeg':asdict(ffmpeg),'ffprobe':asdict(ffprobe),'full_frame_coverage':True,
             'native_compiler_executed':False,'playback_or_acoustic_sync_proven':False}
    return findings_report('BIE-QA-HARD-019',binding,findings,details)


def validate_coverage(details,policy):
    """Consistency only; authenticity still requires byte-bound execution authority."""
    require(details['policy_digest']==policy.content_digest,'H5_COVERAGE_POLICY')
    verify_chunk_manifest(details['byte_manifest']);require(details['artifact']==details['byte_manifest']['artifact'],'H5_COVERAGE_ARTIFACT')
    require(details['frames']==policy.frames and details['full_frame_coverage'] is True,'H5_COVERAGE_COUNT')
    require(details['decoded_bytes']==policy.frames*policy.width*policy.height*3,'H5_DECODED_BYTE_COUNT')
    cursor=0
    for c in details['chunks']:
        require(c['first_frame']==cursor and c['last_frame']==cursor+c['frame_count']-1,'H5_FRAME_CHUNK_GAP')
        integer(c['frame_count'],'count',1,policy.chunk_frames)
        if c['last_frame']<policy.frames-1:require(c['frame_count']==policy.chunk_frames,'H5_SHORT_FRAME_CHUNK')
        require(q(c['first_pts'])<=q(c['last_pts']),'H5_CHUNK_TIME_ORDER');sha256(c['frame_digest'],'frame_chunk')
        cursor+=c['frame_count']
    require(cursor==policy.frames,'H5_FRAME_CHUNK_GAP')
    require([s['frame'] for s in details['samples']]==list(policy.sample_frames),'H5_SAMPLE_COVERAGE')
    return True
