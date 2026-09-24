"""BIE-AUDIO-VO-010: identity-keyed, atomic local cache with every-read validation.

Linux advisory key locks prevent duplicate synthesis across cooperating processes.
The directory must be controlled by the service account; this is not a hostile
shared-filesystem sandbox, distributed cache or publisher-signature authority.
"""
from contextlib import contextmanager
from dataclasses import asdict,dataclass
from pathlib import Path
from threading import Event
import fcntl,hashlib,json,os,re,shutil,stat,tempfile,time
from .common import AudioError,fingerprint,strict_json,text
from .pcm_audio import validate_wav
from .tts_generation import SpeechAsset,generate_speech
from .tts_contract import ProviderFailure


def safe_directory(path):
    path=Path(path).absolute()
    if any(p.is_symlink() for p in (path,*path.parents)):raise AudioError('CACHE_SYMLINK')
    path.mkdir(parents=True,exist_ok=True,mode=0o700)
    if not path.is_dir():raise AudioError('CACHE_DIRECTORY')
    return path


def read_regular(path,limit):
    try:fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    except OSError as exc:raise AudioError('CACHE_FILE_INVALID',path.name) from exc
    with os.fdopen(fd,'rb') as f:
        info=os.fstat(f.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size>limit:raise AudioError('CACHE_FILE_INVALID',path.name)
        data=f.read(limit+1)
        if len(data)>limit:raise AudioError('CACHE_FILE_TOO_LARGE')
        return data


@contextmanager
def key_lock(path,*,timeout,cancellation=None):
    fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise AudioError('CACHE_LOCK_INVALID')
        deadline=time.monotonic()+timeout
        while True:
            if cancellation is not None and cancellation.is_set():raise ProviderFailure('CANCELLED')
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);break
            except BlockingIOError:
                if time.monotonic()>=deadline:raise AudioError('CACHE_LOCK_TIMEOUT')
                time.sleep(.025)
        yield
    finally:
        fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)


@dataclass(frozen=True)
class CacheOutcome:
    asset: SpeechAsset
    cache_hit: bool
    key: str


class TTSCache:
    def __init__(self,root,*,namespace,lock_timeout=60):
        text(namespace,'cache namespace',256)
        if type(lock_timeout)not in (int,float) or not 0<lock_timeout<=300:raise AudioError('CACHE_LOCK_POLICY')
        self.namespace=namespace;self.root=safe_directory(Path(root)/hashlib.sha256(namespace.encode()).hexdigest())
        self.locks=safe_directory(self.root/'locks');self.entries=safe_directory(self.root/'entries');self.lock_timeout=lock_timeout
    def key(self,request):return fingerprint(('bie.tts-cache/1',self.namespace,request.fingerprint()))[7:]
    def _load(self,folder,request):
        if folder.is_symlink() or not folder.is_dir():raise AudioError('CACHE_ENTRY_INVALID')
        if {p.name for p in folder.iterdir()}!={'speech.wav','receipt.json'}:raise AudioError('CACHE_ENTRY_INCOMPLETE')
        wav=read_regular(folder/'speech.wav',32000000);receipt=read_regular(folder/'receipt.json',2000000)
        r=strict_json(receipt.decode('utf-8'));info,raw=validate_wav(wav,request.settings.format)
        expected_keys={'schema_version','request_fingerprint','request','media','provider_audio_sha256','provider_pcm_sha256','requested_pause_samples','invocation_id','attempts','diagnostics','audio_generated','word_timestamps_verified','pronunciation_verified','cinematic_quality_verified','product_accepted'}
        if type(r)is not dict or set(r)!=expected_keys or r['request_fingerprint']!=request.fingerprint() or fingerprint(r['request'])!=fingerprint(request) or r['media']!=asdict(info):raise AudioError('CACHE_IDENTITY_MISMATCH')
        if r['schema_version']!='bie.audio.speech-asset/1' or r['audio_generated']is not True or any(r[k]is not False for k in ('word_timestamps_verified','pronunciation_verified','cinematic_quality_verified','product_accepted')):raise AudioError('CACHE_ACCEPTANCE_TAMPER')
        if type(r['attempts'])is not int or not 1<=r['attempts']<=4 or type(r['diagnostics'])is not list or any(type(d)is not str for d in r['diagnostics']):raise AudioError('CACHE_RECEIPT_FIELDS')
        if type(r['provider_audio_sha256'])is not str or not re.fullmatch('[0-9a-f]{64}',r['provider_audio_sha256']):raise AudioError('CACHE_PROVIDER_HASH')
        if type(r['requested_pause_samples'])is not int or r['requested_pause_samples']!=(request.segment.pause_after_ms*request.settings.format.sample_rate+500)//1000:raise AudioError('CACHE_PAUSE_MISMATCH')
        tail=r['requested_pause_samples']*request.settings.format.channels*2
        if tail>len(raw) or (tail and any(raw[-tail:])) or hashlib.sha256(raw[:-tail] if tail else raw).hexdigest()!=r['provider_pcm_sha256']:raise AudioError('CACHE_PCM_TIMING_MISMATCH')
        text(r['invocation_id'],'cached invocation',1024)
        return SpeechAsset(request,wav,info,r['provider_audio_sha256'],r['provider_pcm_sha256'],r['requested_pause_samples'],r['invocation_id'],r['attempts'],tuple(r['diagnostics']))
    def get_or_generate(self,request,provider,*,cancellation=None):
        if cancellation is not None and cancellation.is_set():raise ProviderFailure('CANCELLED')
        # Do not return an old voice/model result when deployment identity has changed.
        if provider.catalog().fingerprint()!=request.catalog_fingerprint:raise ProviderFailure('PROVIDER_CATALOG_CHANGED')
        key=self.key(request);folder=self.entries/key
        with key_lock(self.locks/(key+'.lock'),timeout=self.lock_timeout,cancellation=cancellation):
            if folder.exists() or folder.is_symlink():return CacheOutcome(self._load(folder,request),True,key)
            asset=generate_speech(request,provider,cancellation=cancellation)
            temporary=Path(tempfile.mkdtemp(prefix='.pending-',dir=self.entries))
            try:
                for name,content in [('speech.wav',asset.wav_bytes),('receipt.json',(json.dumps(asset.receipt(),ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())]:
                    with (temporary/name).open('xb') as f:f.write(content);f.flush();os.fsync(f.fileno())
                # Both files are visible together only after validation and atomic rename.
                self._load(temporary,request)
                if folder.exists() or folder.is_symlink():raise AudioError('CACHE_CONCURRENT_CONFLICT')
                os.rename(temporary,folder)
                fd=os.open(self.entries,os.O_RDONLY|os.O_DIRECTORY)
                try:os.fsync(fd)
                finally:os.close(fd)
            finally:
                if temporary.exists():shutil.rmtree(temporary)
            return CacheOutcome(asset,False,key)
