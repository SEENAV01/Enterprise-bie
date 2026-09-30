"""H2-004: every full-resolution RGB8 frame, constant frame-memory inspection.

No frame sampling, resizing, seeking, FPS conversion or maximum-frame truncation.
Dark component/freeze statistics are diagnostics, not semantic or aesthetic QA.
"""
from __future__ import annotations
import hashlib
from ..models import BenchmarkError
from .process import stream, executable
from .probe import input_args

DARK_TABLE=bytes(1 if i<=16 else 0 for i in range(256))

class VideoAccumulator:
    def __init__(self,width,height,max_frames):
        from .custody import integer
        integer(width,1,7680);integer(height,1,4320);integer(max_frames,1,864000)
        self.stride=width*height*3;self.maximum=max_frames;self.pending=bytearray()
        self.count=0;self.dark_frames=0;self.same_transitions=0
        self.max_dark_run=0;self.max_same_run=0;self._dark=0;self._same=0;self._previous=None
        self.all_hash=hashlib.sha256();self.frame_chain=hashlib.sha256();self.first=None;self.last=None
    def feed(self,b):
        self.all_hash.update(b);self.pending.extend(b)
        while len(self.pending)>=self.stride:
            frame=bytes(self.pending[:self.stride]);del self.pending[:self.stride]
            h=hashlib.sha256(frame).hexdigest();self.frame_chain.update(bytes.fromhex(h));self.count+=1
            if self.count>self.maximum: raise BenchmarkError('AV_FRAME_LIMIT')
            if self.first is None:self.first=h
            self.last=h
            dark=frame.translate(DARK_TABLE).count(1)/self.stride>=0.995
            self.dark_frames+=int(dark);self._dark=self._dark+1 if dark else 0
            self.max_dark_run=max(self.max_dark_run,self._dark)
            same=h==self._previous
            self.same_transitions+=int(same);self._same=self._same+1 if same else 0
            self.max_same_run=max(self.max_same_run,self._same);self._previous=h
    def finish(self):
        if self.pending: raise BenchmarkError('PARTIAL_DECODED_FRAME')
        if not self.count:raise BenchmarkError('NO_DECODED_FRAMES')
        return {'decoded_frames':self.count,'dark_frames':self.dark_frames,'same_transitions':self.same_transitions,
                'max_dark_run_frames':self.max_dark_run,'max_same_run_transitions':self.max_same_run,
                'decoded_sha256':self.all_hash.hexdigest(),'frame_chain_sha256':self.frame_chain.hexdigest(),
                'first_frame_sha256':self.first,'last_frame_sha256':self.last,
                'frame_bytes':self.stride,'inspection':'ALL_PIXELS_RGB8_ALL_FRAMES'}

def decode_video(path,metadata,limits,deadline):
    acc=VideoAccumulator(metadata['width'],metadata['height'],limits.max_frames)
    argv=[executable('ffmpeg'),'-nostdin','-v','error','-xerror','-threads','1','-noautorotate',
          *input_args(path),'-map',f"0:{metadata['video_index']}",'-an','-sn','-dn',
          '-fps_mode','passthrough','-threads','1','-pix_fmt','rgb24','-f','rawvideo','pipe:1']
    cmd=stream(argv,path.parent,deadline,acc.feed,max_stdout=limits.max_decoded_bytes,max_stderr=limits.max_stderr_bytes)
    result=acc.finish()
    if cmd['stdout_bytes']!=result['decoded_frames']*acc.stride: raise BenchmarkError('VIDEO_BYTE_COUNT_MISMATCH')
    return result,cmd
