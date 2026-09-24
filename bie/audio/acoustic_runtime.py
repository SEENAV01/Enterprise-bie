"""H2-002: explicit pinned native deployment and bounded local measurement worker.

The legacy C ABI is intentional and version-labelled; no latest-version claim,
no cloud fallback, and no production-kernel/isolation claim is made here.
"""
from __future__ import annotations
from pathlib import Path
from threading import Event
import hashlib, json, os, platform, signal, stat, subprocess, sys, tempfile, time
from .common import AudioError, fingerprint, integer, strict_json
from .acoustic_contract import (AcousticPolicy, ENGINE, SCOPE, BOUNDARIES,
    canonical, fields, sha, validate_job)

MODEL_NAMES=('mdef','means','variances','transition_matrices','sendump','feat.params','noisedict')
ROOT=Path(__file__).resolve().parents[2]


def implementation_identity():
    paths=sorted(Path(__file__).parent.glob('acoustic_*.py'))
    launcher=ROOT/'scripts/audio_acoustic_worker.py'
    if launcher.is_symlink() or not launcher.is_file():
        raise AudioError('ACOUSTIC_WORKER_LAUNCHER_INVALID')
    paths.append(launcher)
    return fingerprint({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


def file_record(path):
    p=Path(path)
    if not p.is_absolute() or p.is_symlink() or not p.is_file():
        raise AudioError('ACOUSTIC_RUNTIME_FILE')
    if any(parent.is_symlink() for parent in p.parents):
        raise AudioError('ACOUSTIC_RUNTIME_SYMLINK')
    if not 0 < p.stat().st_size <= 150_000_000:
        raise AudioError('ACOUSTIC_RUNTIME_FILE_BUDGET')
    return {'path':str(p), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes':p.stat().st_size}


def probe_local_runtime():
    """Identify the explicit installed legacy adapter. Probe is NOT approval."""
    if sys.platform != 'linux':raise AudioError('ACOUSTIC_NATIVE_PLATFORM_UNSUPPORTED')
    roots=(Path('/usr/lib/x86_64-linux-gnu'),Path('/usr/lib/aarch64-linux-gnu'))
    native={}
    for role,name in [('pocketsphinx','libpocketsphinx.so.3'),('sphinxbase','libsphinxbase.so.3')]:
        p=next((d/name for d in roots if (d/name).is_file()),None)
        if p is None:raise AudioError('ACOUSTIC_NATIVE_UNAVAILABLE',role)
        native[role]=file_record(p.resolve())
    model=Path('/usr/share/pocketsphinx/model/en-us').resolve()
    for name in MODEL_NAMES:native['hmm/'+name]=file_record(model/'en-us'/name)
    for role,name in [('dictionary','cmudict-en-us.dict'),('phone_lm','en-us-phone.lm.bin'),('word_lm','en-us.lm.bin')]:
        native[role]=file_record(model/name)
    native['ffmpeg']=file_record(Path('/usr/bin/ffmpeg').resolve())
    out={'schema_version':'bie.audio.acoustic-runtime/1','engine':ENGINE,
         'language':'en-US','scope':SCOPE,'abi':'legacy-libpocketsphinx.so.3-cmd_ln_parse_r',
         'decoder_frame_rate':100, 'analysis_sample_rate':16000,
         'resampling':'ffmpeg-swr-mono-s16le-16000-no-dither',
         'platform':platform.platform(),'python':platform.python_version(),
         'implementation_fingerprint':implementation_identity(), 'files':native,
         'model_rights':'Installed OS package only; not bundled or independently rights-audited',
         **BOUNDARIES}
    out['fingerprint']=fingerprint(out)
    return out


def verify_runtime(snapshot):
    keys=('schema_version','engine','language','scope','abi','decoder_frame_rate',
        'analysis_sample_rate','resampling','platform','python','implementation_fingerprint',
        'files','model_rights',*BOUNDARIES,'fingerprint')
    fields(snapshot,keys,'ACOUSTIC_RUNTIME_FIELDS')
    if (snapshot['schema_version']!='bie.audio.acoustic-runtime/1' or snapshot['engine']!=ENGINE
        or snapshot['language']!='en-US' or snapshot['scope']!=SCOPE
        or snapshot['abi']!='legacy-libpocketsphinx.so.3-cmd_ln_parse_r'
        or type(snapshot['decoder_frame_rate']) is not int or snapshot['decoder_frame_rate']!=100
        or type(snapshot['analysis_sample_rate']) is not int or snapshot['analysis_sample_rate']!=16000
        or snapshot['resampling']!='ffmpeg-swr-mono-s16le-16000-no-dither'
        or any(snapshot[k]!=v or type(snapshot[k]) is not type(v) for k,v in BOUNDARIES.items())):
        raise AudioError('ACOUSTIC_RUNTIME_CAPABILITY')
    required={'pocketsphinx','sphinxbase','dictionary','phone_lm','word_lm','ffmpeg',*('hmm/'+n for n in MODEL_NAMES)}
    if type(snapshot['files']) is not dict or set(snapshot['files'])!=required:
        raise AudioError('ACOUSTIC_RUNTIME_FILE_SET')
    if fingerprint({k:v for k,v in snapshot.items() if k!='fingerprint'})!=snapshot['fingerprint']:
        raise AudioError('ACOUSTIC_RUNTIME_TAMPER')
    if snapshot['implementation_fingerprint']!=implementation_identity() or snapshot['python']!=platform.python_version() or snapshot['platform']!=platform.platform():
        raise AudioError('ACOUSTIC_RUNTIME_IMPLEMENTATION_DRIFT')
    for role,row in snapshot['files'].items():
        fields(row,('path','sha256','bytes'));sha(row['sha256'])
        if file_record(row['path']) != row:raise AudioError('ACOUSTIC_RUNTIME_FILE_DRIFT',role)
    parents={str(Path(snapshot['files']['hmm/'+n]['path']).parent) for n in MODEL_NAMES}
    if len(parents)!=1:raise AudioError('ACOUSTIC_MODEL_DIRECTORY')
    return snapshot


def run_native(job,wav,snapshot,*,cancellation=None):
    policy=validate_job(job,wav);verify_runtime(snapshot)
    cancel=cancellation if cancellation is not None else Event()
    if cancel.is_set():raise AudioError('ACOUSTIC_CANCELLED')
    worker=ROOT/'scripts/audio_acoustic_worker.py'
    began=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='bie-acoustic-') as td:
        root=Path(td);os.chmod(root,0o700)
        (root/'request.json').write_bytes(canonical({'job':job,'runtime':snapshot}))
        (root/'source.wav').write_bytes(wav)
        env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8',
             'HOME':td,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
             'PYTHONDONTWRITEBYTECODE':'1'}
        with (root/'worker.log').open('w+b') as log:
            p=subprocess.Popen([sys.executable,'-I','-B',str(worker),td],cwd=td,
                               env=env,stdout=log,stderr=log,start_new_session=True)
            try:
                while True:
                    if cancel.is_set():raise AudioError('ACOUSTIC_CANCELLED')
                    if time.monotonic()-began>policy.deadline_seconds:
                        raise AudioError('ACOUSTIC_WORKER_TIMEOUT')
                    for child in root.iterdir():
                        limit=policy.max_source_bytes if child.name=='source.wav' else 8_000_000
                        if child.is_symlink() or (child.is_file() and child.stat().st_size>limit):
                            raise AudioError('ACOUSTIC_WORKER_OUTPUT_LIMIT')
                    if p.poll() is not None:break
                    time.sleep(.02)
                if cancel.is_set():raise AudioError('ACOUSTIC_CANCELLED')
                if time.monotonic()-began>policy.deadline_seconds:raise AudioError('ACOUSTIC_WORKER_TIMEOUT')
                output=root/'result.json'
                if p.returncode!=0 or not output.is_file() or output.is_symlink():
                    # Never reflect arbitrary native logs/source text to the public error.
                    raise AudioError('ACOUSTIC_WORKER_FAILED',str(p.returncode))
                if output.stat().st_size>4_000_000:raise AudioError('ACOUSTIC_WORKER_OUTPUT_LIMIT')
                result=strict_json(output.read_text())
            finally:
                if p.poll() is None:
                    os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5)
    verify_runtime(snapshot)
    from .acoustic_evidence import validate_measurement
    validate_measurement(result,job,snapshot['fingerprint'])
    return result
