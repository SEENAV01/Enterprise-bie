"""Native FFmpeg INPUT metering. loudnorm output is discarded, never silently adopted."""
from dataclasses import dataclass
from pathlib import Path
import hashlib,json,math,os,shutil,signal,subprocess,tempfile,time
from .common import AudioError,fingerprint
from .mix_contract import MixBuffer,number,dbfs
@dataclass(frozen=True)
class LoudnessMeasurement:
    pcm_fingerprint:str
    integrated_lufs:float|None
    true_peak_dbtp:float|None
    loudness_range_lu:float|None
    threshold_lufs:float|None
    sample_peak_dbfs:float|None
    frames:int
    sample_rate:int
    channels:int
    dual_mono:bool
    runtime_fingerprint:str
    method:str='ffmpeg.loudnorm.input/1'

class FFmpegMeter:
    def __init__(self,executable=None,*,timeout_s=30.0):
        self.timeout_s=number(timeout_s,'deadline',.01,300)
        path=executable or shutil.which('ffmpeg')
        if not path:raise AudioError('MIX_FFMPEG_UNAVAILABLE')
        self.path=Path(path).resolve()
        if not self.path.is_file() or not os.access(self.path,os.X_OK):raise AudioError('MIX_FFMPEG_UNAVAILABLE')
        self.exe_sha256=self._sha()
        try:p=subprocess.run([str(self.path),'-version'],capture_output=True,text=True,env=self._env(),timeout=5)
        except (OSError,subprocess.TimeoutExpired) as e:raise AudioError('MIX_METER_IDENTITY',str(e)[:160])
        if p.returncode or not p.stdout.startswith('ffmpeg version '):raise AudioError('MIX_METER_IDENTITY')
        self.identity={'executable_sha256':self.exe_sha256,'version_output':p.stdout,'meter':'loudnorm-input','threads':1,
                       'scope':'executable hash and reported build/libraries, not full host attestation'}
        self.runtime_fingerprint=fingerprint(self.identity)
    def _sha(self):return hashlib.sha256(self.path.read_bytes()).hexdigest()
    @staticmethod
    def _env():return {'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
    def _run(self,args,root,cancellation):
        if self._sha()!=self.exe_sha256:raise AudioError('MIX_METER_CHANGED')
        if cancellation is not None and cancellation.is_set():raise AudioError('MIX_CANCELLED')
        path=root/'stderr.txt';begin=time.monotonic();process=None
        try:
            with path.open('wb') as log:
                process=subprocess.Popen([str(self.path),*args],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=log,
                                         cwd=root,env=self._env(),start_new_session=True)
                while process.poll() is None:
                    if cancellation is not None and cancellation.is_set():raise AudioError('MIX_CANCELLED')
                    if time.monotonic()-begin>=self.timeout_s:raise AudioError('MIX_METER_TIMEOUT')
                    if path.stat().st_size>1_000_000:raise AudioError('MIX_METER_OUTPUT_LIMIT')
                    time.sleep(min(.01,max(.0001,self.timeout_s-(time.monotonic()-begin))))
                process.wait()
            if time.monotonic()-begin>self.timeout_s:raise AudioError('MIX_METER_TIMEOUT')
            if path.stat().st_size>1_000_000:raise AudioError('MIX_METER_OUTPUT_LIMIT')
            result=path.read_text(errors='replace')
            if process.returncode:raise AudioError('MIX_METER_FAILED',result[-1500:])
            if self._sha()!=self.exe_sha256:raise AudioError('MIX_METER_CHANGED')
            return result
        except OSError as e:raise AudioError('MIX_METER_PROCESS',str(e)[:160])
        finally:
            if process is not None and process.poll() is None:
                os.killpg(process.pid,signal.SIGKILL);process.wait()
    def measure(self,pcm,*,dual_mono=False,cancellation=None):
        if type(pcm)is not MixBuffer or type(dual_mono)is not bool:raise AudioError('MIX_METER_INPUT')
        if dual_mono and pcm.channels!=1:raise AudioError('MIX_DUAL_MONO_REQUIRES_MONO')
        with tempfile.TemporaryDirectory(prefix='bie-meter-') as td:
            root=Path(td);(root/'input.f64').write_bytes(pcm.f64le)
            args=['-nostdin','-hide_banner','-nostats','-threads','1','-filter_threads','1','-f','f64le',
                  '-ar',str(pcm.sample_rate),'-ac',str(pcm.channels),'-i',str(root/'input.f64'),'-af',
                  'loudnorm=I=-23:TP=-1:LRA=50:print_format=json:dual_mono='+str(dual_mono).lower(),'-f','null','-']
            log=self._run(args,root,cancellation)
        a=log.rfind('{');b=log.find('}',a)
        try:raw=json.loads(log[a:b+1])
        except (ValueError,TypeError):raise AudioError('MIX_METER_REPORT')
        def read(k):
            if k not in raw or type(raw[k])is not str:raise AudioError('MIX_METER_REPORT')
            try:v=float(raw[k])
            except ValueError:raise AudioError('MIX_METER_REPORT')
            if v==-math.inf:return None
            if not math.isfinite(v) or not -150<=v<=100:raise AudioError('MIX_METER_NONFINITE')
            return v
        r=LoudnessMeasurement(pcm.fingerprint(),read('input_i'),read('input_tp'),read('input_lra'),read('input_thresh'),
                              dbfs(pcm.sample_peak),pcm.frames,pcm.sample_rate,pcm.channels,dual_mono,self.runtime_fingerprint)
        if pcm.sample_peak>0 and r.true_peak_dbtp is None:raise AudioError('MIX_TRUE_PEAK_UNMEASURED')
        return r
