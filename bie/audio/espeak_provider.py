"""VO-009 real offline eSpeak adapter, not a neural/cinematic voice claim.

Deployment must install eSpeak itself. We do not ship its binary/data. No shell,
network endpoint, credential or arbitrary SSML is accepted from a narration file.
A bounded subprocess is NOT a full hostile-code OS sandbox.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from threading import Event
import hashlib,json,os,re,shutil,signal,subprocess,tempfile,time,uuid
import xml.etree.ElementTree as ET
from .common import AudioError,fingerprint
from .tts_contract import AudioFormat,LocaleBinding,Voice,VoiceCatalog,ProviderAudio,ProviderFailure,SynthesisRequest
from .pcm_audio import validate_wav


class EspeakProvider:
    provider_id='espeak-local'
    def __init__(self, executable=None, *, timeout_seconds=30, max_output_bytes=32000000):
        found=executable or shutil.which('espeak')
        if not found:raise ProviderFailure('PROVIDER_UNAVAILABLE','eSpeak is not installed')
        self.executable=Path(found).resolve(strict=True)
        if not self.executable.is_file():raise ProviderFailure('PROVIDER_EXECUTABLE')
        if type(timeout_seconds)not in (int,float) or not 0<timeout_seconds<=300:raise AudioError('PROVIDER_TIMEOUT_POLICY')
        if type(max_output_bytes)is not int or not 1000<=max_output_bytes<=100000000:raise AudioError('PROVIDER_OUTPUT_POLICY')
        self.timeout_seconds=timeout_seconds;self.max_output_bytes=max_output_bytes;self.invocations=0
        self.snapshot=self._snapshot()
        self.runtime=fingerprint(self.snapshot)
        raw=self._command(['--voices'])
        self.installed={line.split()[1] for line in raw.splitlines()[1:] if len(line.split())>=4}
        self._catalog=self._make_catalog()
    def _command(self,args):
        p=subprocess.run([str(self.executable),*args],capture_output=True,text=True,timeout=10,check=False,
            env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'})
        if p.returncode or len(p.stdout)>500000:raise ProviderFailure('PROVIDER_DISCOVERY_FAILED',p.stderr[:200])
        return p.stdout
    def _snapshot(self):
        version=self._command(['--version']).strip()
        m=re.search(r'Data at:\s*(.+)',version)
        if not m:raise ProviderFailure('PROVIDER_DATA_LOCATION')
        data=Path(m.group(1)).resolve(strict=True)
        files=sorted(p for p in data.rglob('*') if p.is_file())
        if not files or len(files)>10000:raise ProviderFailure('PROVIDER_DATA_BUDGET')
        total=0;identities=[]
        for p in files:
            if p.is_symlink() or not p.resolve().is_relative_to(data):raise ProviderFailure('PROVIDER_DATA_SYMLINK')
            size=p.stat().st_size;total+=size
            if total>64000000:raise ProviderFailure('PROVIDER_DATA_BUDGET')
            identities.append((p.relative_to(data).as_posix(),size,hashlib.sha256(p.read_bytes()).hexdigest()))
        # Dynamic library identities matter to output; resolve installed trusted executable dependencies.
        ldd=subprocess.run(['/usr/bin/ldd',str(self.executable)],capture_output=True,text=True,timeout=10,check=False)
        if ldd.returncode:raise ProviderFailure('PROVIDER_LIBRARY_DISCOVERY')
        libraries=[]
        for path in sorted(set(re.findall(r'(/[^\s()]+)',ldd.stdout))):
            p=Path(path).resolve(strict=True)
            if p.is_file():libraries.append((str(p),hashlib.sha256(p.read_bytes()).hexdigest()))
        return {'adapter':'bie.espeak-local/1','version':version,'executable_sha256':hashlib.sha256(self.executable.read_bytes()).hexdigest(),
            'data_files':identities,'libraries':libraries,'adapter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    def _make_catalog(self):
        bindings=[]
        for tag,engine in (('en','en'),('en-US','en-us'),('en-GB','en-gb'),('hi','hi')):
            if engine in self.installed:bindings.append(LocaleBinding(tag,engine))
        if not bindings:raise ProviderFailure('NO_DEPLOYED_VOICES')
        voices=tuple(Voice('espeak:'+b.language,self.provider_id,self.snapshot['version'],self.runtime,b.language,tuple(bindings),
            (AudioFormat(),),('language-switch','rate-wpm','pitch','amplitude','ssml-safe-subset'),'technical_formant',
            ('installed:eSpeak/'+self.runtime[7:],),20000,80000,False) for b in bindings)
        return VoiceCatalog('installed:'+self.runtime,tuple(sorted(voices,key=lambda v:(v.provider_id,v.voice_id))))
    def catalog(self):
        if fingerprint(self._snapshot())!=self.runtime:raise ProviderFailure('PROVIDER_RUNTIME_CHANGED')
        return self._catalog
    def serialize(self, request:SynthesisRequest):
        if request.voice not in self._catalog.voices:raise ProviderFailure('PROVIDER_VOICE_NOT_DEPLOYED')
        if request.settings.style!='neutral':raise ProviderFailure('PROVIDER_STYLE_UNSUPPORTED')
        if any(p.phonemes is not None for p in request.segment.spans):raise ProviderFailure('PROVIDER_PHONEMES_UNSUPPORTED')
        if '[[' in request.segment.spoken_text or ']]' in request.segment.spoken_text:raise ProviderFailure('RESERVED_PHONEME_MARKUP')
        aliases={b.language:b.engine_voice for b in request.voice.locales}
        root=ET.Element('speak',{'version':'1.0','xml:lang':request.segment.language})
        # Language switches remain explicit. Every source-derived string is XML-escaped.
        for span in request.segment.spans:
            child=ET.SubElement(root,'voice',{'name':aliases[span.language]});child.text=span.spoken
        encoded=ET.tostring(root,encoding='utf-8')
        if len(encoded)>160000:raise ProviderFailure('SSML_REQUEST_BUDGET')
        return encoded
    def synthesize(self, request:SynthesisRequest, *, cancellation:Event | None=None):
        if type(request)is not SynthesisRequest:raise AudioError('TTS_REQUEST_REQUIRED')
        if cancellation is not None and cancellation.is_set():raise ProviderFailure('CANCELLED')
        if fingerprint(self._snapshot())!=self.runtime:raise ProviderFailure('PROVIDER_RUNTIME_CHANGED')
        markup=self.serialize(request);self.invocations+=1
        with tempfile.TemporaryDirectory(prefix='bie-espeak-') as td:
            root=Path(td);inp=root/'speech.ssml';out=root/'speech.wav';inp.write_bytes(markup)
            argv=[str(self.executable),'-b','1','-m','-v',dict((x.language,x.engine_voice) for x in request.voice.locales)[request.segment.language],
                '-s',str(request.settings.rate_wpm),'-p',str(request.settings.pitch),'-a',str(request.settings.amplitude),'-f',str(inp),'-w',str(out)]
            stdout_file=(root/'stdout.log').open('w+b');stderr_file=(root/'stderr.log').open('w+b')
            start=time.monotonic()
            proc=subprocess.Popen(argv,stdout=stdout_file,stderr=stderr_file,start_new_session=True,
                env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','HOME':td},cwd=td)
            try:
                while True:
                    if cancellation is not None and cancellation.is_set():raise ProviderFailure('CANCELLED')
                    if time.monotonic()-start>self.timeout_seconds:raise ProviderFailure('PROVIDER_TIMEOUT')
                    if out.exists() and out.stat().st_size>self.max_output_bytes:raise ProviderFailure('PROVIDER_OUTPUT_LIMIT')
                    if sum((root/n).stat().st_size for n in ('stdout.log','stderr.log'))>32000:raise ProviderFailure('PROVIDER_LOG_LIMIT')
                    remaining=self.timeout_seconds-(time.monotonic()-start)
                    if remaining<=0:raise ProviderFailure('PROVIDER_TIMEOUT')
                    try:
                        proc.wait(timeout=min(.05,remaining))
                        if time.monotonic()-start>self.timeout_seconds:raise ProviderFailure('PROVIDER_TIMEOUT')
                        break
                    except subprocess.TimeoutExpired:continue
                stdout_file.seek(0);stderr_file.seek(0);stdout=stdout_file.read(32001);stderr=stderr_file.read(32001)
                if proc.returncode:raise ProviderFailure('PROVIDER_PROCESS_FAILED',stderr.decode('utf-8','replace')[:300])
                if len(stdout)+len(stderr)>32000:raise ProviderFailure('PROVIDER_LOG_LIMIT')
                if out.is_symlink() or not out.is_file() or out.stat().st_size>self.max_output_bytes:raise ProviderFailure('PROVIDER_OUTPUT_MISSING_OR_LARGE')
                wav=out.read_bytes();validate_wav(wav,request.settings.format,max_bytes=self.max_output_bytes)
            finally:
                if proc.poll()is None:
                    os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=5)
                stdout_file.close();stderr_file.close()
        if fingerprint(self._snapshot())!=self.runtime:raise ProviderFailure('PROVIDER_RUNTIME_CHANGED')
        return ProviderAudio(request.fingerprint(),self.provider_id,request.voice.fingerprint(),self.runtime,wav,'espeak:'+uuid.uuid4().hex,
            ('LOCAL_FORMANT_SPEECH_NOT_CINEMATIC_ACCEPTANCE','NO_WORD_ALIGNMENT','CODE_SWITCH_MAY_CHANGE_TIMBRE'))
