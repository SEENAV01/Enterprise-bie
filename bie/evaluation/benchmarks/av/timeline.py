"""H2-006: complete decoded frame/sample timestamp coverage, no packet shortcuts."""
from __future__ import annotations
import hashlib
from fractions import Fraction
from ..models import BenchmarkError
from .process import Lines, stream, executable
from .probe import input_args, fraction

class Timeline:
    def __init__(self,kind,metadata,limits):
        if kind not in ('video','audio'):raise BenchmarkError('UNSUPPORTED_TIMELINE_KIND')
        self.kind=kind;self.meta=metadata;self.limits=limits;self.count=0;self.samples=0
        self.first=None;self.last=None;self.end=None;self.last_duration=None;self.max_gap=Fraction(0)
        self.max_overlap=Fraction(0);self.max_step_error=Fraction(0);self.hash=hashlib.sha256()
    def line(self,line):
        pairs=[x.split('=',1) for x in line.split('|') if '=' in x]
        row=dict(pairs)
        if 'media_type' not in row:return # optional empty side-data-only line
        if row['media_type']!=self.kind:raise BenchmarkError('TIMING_WRONG_STREAM')
        self.count+=1
        max_count=self.limits.max_frames if self.kind=='video' else self.limits.max_duration_s*1000
        if self.count>max_count:raise BenchmarkError('TIMING_FRAME_LIMIT')
        pts=fraction(row.get('best_effort_timestamp_time'))
        if pts<0 or pts>self.limits.max_duration_s:raise BenchmarkError('TIMESTAMP_OUT_OF_RANGE')
        if self.kind=='video':
            if str(self.meta['width'])!=row.get('width') or str(self.meta['height'])!=row.get('height'):
                raise BenchmarkError('VARIABLE_FRAME_DIMENSIONS')
            duration=fraction(row.get('duration_time','0'))
            if duration<=0:duration=1/fraction(self.meta['fps'])
        else:
            try:n=int(row['nb_samples'])
            except (KeyError,ValueError) as e:raise BenchmarkError('INVALID_FRAME_SAMPLES') from e
            if not 0<n<=self.meta['audio']['rate']*10:raise BenchmarkError('INVALID_FRAME_SAMPLES')
            self.samples+=n;duration=Fraction(n,self.meta['audio']['rate'])
        if self.last is not None:
            if pts<=self.last:raise BenchmarkError('NONMONOTONIC_DECODED_PTS')
            gap=pts-self.end;self.max_gap=max(self.max_gap,gap);self.max_overlap=max(self.max_overlap,-gap)
            if self.kind=='video':self.max_step_error=max(self.max_step_error,abs((pts-self.last)-1/fraction(self.meta['fps'])))
        if self.first is None:self.first=pts
        self.last=pts;self.last_duration=duration;self.end=pts+duration
        self.hash.update(f'{pts}:{duration}\n'.encode())
    def finish(self):
        if not self.count:raise BenchmarkError('NO_DECODED_TIMESTAMPS')
        return {'frames':self.count,'samples':self.samples,'start_s':float(self.first),'end_s':float(self.end),
                'max_gap_s':float(self.max_gap),'max_overlap_s':float(self.max_overlap),
                'max_step_error_s':float(self.max_step_error),'pts_sha256':self.hash.hexdigest()}

def decode_timeline(path,kind,metadata,limits,deadline):
    acc=Timeline(kind,metadata,limits);lines=Lines(acc.line)
    spec='v:0' if kind=='video' else 'a:0'
    argv=[executable('ffprobe'),'-v','error','-threads','1',*input_args(path),'-select_streams',spec,
          '-show_frames','-show_entries','frame=media_type,best_effort_timestamp_time,duration_time,width,height,nb_samples',
          '-of','compact=p=0']
    cmd=stream(argv,path.parent,deadline,lines.feed,max_stdout=limits.max_timing_bytes,max_stderr=limits.max_stderr_bytes)
    lines.finish();return acc.finish(),cmd

def consistency(meta,video,vt,audio,at,*,tolerance_s=0.01):
    """Reject incomplete evidence; return measured synchronization violations."""
    if video['decoded_frames']!=vt['frames']:raise BenchmarkError('VIDEO_TIMING_COUNT_MISMATCH')
    if (audio is None)!=(at is None):raise BenchmarkError('AUDIO_TIMING_MISSING')
    reasons=[]
    if abs(vt['start_s'])>tolerance_s:reasons.append('VIDEO_START_OFFSET')
    if vt['max_gap_s']>tolerance_s or vt['max_overlap_s']>tolerance_s:reasons.append('VIDEO_TIMELINE_GAP_OR_OVERLAP')
    if vt['max_step_error_s']>tolerance_s:reasons.append('NONCONSTANT_FRAME_RATE')
    if abs(vt['end_s']-float(fraction(meta['duration_s'])))>max(tolerance_s,1/float(fraction(meta['fps']))):
        reasons.append('CONTAINER_VIDEO_DURATION_MISMATCH')
    if audio is not None:
        if audio['samples_per_channel']!=at['samples']:raise BenchmarkError('AUDIO_TIMING_SAMPLE_MISMATCH')
        if at['max_gap_s']>tolerance_s or at['max_overlap_s']>tolerance_s:reasons.append('AUDIO_TIMELINE_GAP_OR_OVERLAP')
        if abs(at['start_s']-vt['start_s'])>tolerance_s:reasons.append('AUDIO_VIDEO_START_OFFSET')
        if abs(at['end_s']-vt['end_s'])>max(tolerance_s,0.05):reasons.append('AUDIO_VIDEO_END_OFFSET')
    return reasons
