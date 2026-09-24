"""Exact source-bound mixing input and exclusive artifact publication."""
from dataclasses import fields
from pathlib import Path,PurePosixPath
import hashlib,json,os,shutil,tempfile
from .common import AudioError,exact_fields,fingerprint
from .tts_cache import read_regular,key_lock
from .tts_contract import AudioFormat
from .mix_contract import MixBuffer,hash64,MAX_PCM_BYTES
from .mix_pipeline import MixPolicy,export_mixed_captions,verify_mixed_source
from .loudness_normalization import LoudnessPolicy
from .music_ducking import DuckingPolicy
from .silence_trim import TrimPolicy
from .peak_control import PeakPolicy
from .sfx_mixing import Stem

def read_mix_spec(raw,asset_root,sync):
    exact_fields(raw,('schema_version','plan_fingerprint','timeline_fingerprint','policy','stems'))
    if raw['schema_version']!='bie.audio.mix-spec/1' or raw['plan_fingerprint']!=sync.plan.fingerprint() or raw['timeline_fingerprint']!=sync.timeline.fingerprint():raise AudioError('MIX_SPEC_STALE')
    policies=dict(raw['policy']);exact_fields(policies,tuple(f.name for f in fields(MixPolicy)))
    for name,cls in (('loudness',LoudnessPolicy),('ducking',DuckingPolicy),('trim',TrimPolicy),('peaks',PeakPolicy)):
        exact_fields(policies[name],tuple(f.name for f in fields(cls)));policies[name]=cls(**policies[name])
    policy=MixPolicy(**policies);root=Path(asset_root).resolve()
    if type(raw['stems'])is not list or len(raw['stems'])>128:raise AudioError('MIX_STEMS')
    stems=[];copies={};names=tuple(f.name for f in fields(Stem) if f.name!='pcm')
    for row in raw['stems']:
        exact_fields(row,(*names,'path','sha256','sample_rate','channels'));name=row['path']
        if type(name)is not str or '\\' in name:raise AudioError('MIX_ASSET_PATH')
        p=PurePosixPath(name)
        if p.is_absolute() or any(x in ('','.','..') for x in name.split('/')):raise AudioError('MIX_ASSET_PATH')
        target=root
        for part in p.parts:
            target=target/part
            if target.is_symlink():raise AudioError('MIX_ASSET_SYMLINK')
        if not target.resolve().is_relative_to(root):raise AudioError('MIX_ASSET_PATH')
        data=read_regular(target,MAX_PCM_BYTES+1024);h=hashlib.sha256(data).hexdigest()
        if hash64(row['sha256'])!=h:raise AudioError('MIX_ASSET_HASH')
        if type(row['source_refs'])is not list:raise AudioError('MIX_ASSET_SOURCES')
        kwargs={k:row[k] for k in names};kwargs['source_refs']=tuple(kwargs['source_refs'])
        stems.append(Stem(pcm=MixBuffer.from_wav(data,AudioFormat(row['sample_rate'],row['channels'])),**kwargs));copies[h+'.wav']=data
    return tuple(stems),policy,copies

def publish_mix(result,destination,*,sync=None,inputs=None,allow_review=False):
    result.validate()
    if type(allow_review)is not bool:raise AudioError('MIX_REVIEW_FLAG')
    if result.receipt()['requires_review'] and not allow_review:raise AudioError('MIX_REVIEW_REQUIRED')
    if sync is not None:verify_mixed_source(result,sync)
    destination=Path(destination)
    if destination.exists() or destination.is_symlink():raise AudioError('MIX_OUTPUT_EXISTS')
    destination.parent.mkdir(parents=True,exist_ok=True)
    for parent in (destination.parent,*destination.parent.parents):
        if parent.is_symlink():raise AudioError('MIX_OUTPUT_SYMLINK')
    files={'master.wav':result.wav_bytes,'MIX_CLOCK.json':result.clock_json.encode(),'MIX_RECEIPT.json':result.receipt_json.encode(),
           'captions.vtt':export_mixed_captions(result,'vtt').encode(),'captions.srt':export_mixed_captions(result,'srt').encode()}
    if sync is not None:files.update({'source.wav':sync.wav_bytes,'SOURCE_SYNC.json':json.dumps(sync.receipt(),ensure_ascii=False,sort_keys=True).encode()})
    if inputs:
        for name,data in inputs.items():
            if type(name)is not str or Path(name).name!=name or name in ('','.', '..') or type(data)is not bytes:raise AudioError('MIX_INPUT_COPY')
            files['inputs/'+name]=data
    index={n:{'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)} for n,d in files.items()}
    files['OUTPUT_SHA256.json']=(json.dumps(index,indent=2,sort_keys=True)+'\n').encode()
    tmp=Path(tempfile.mkdtemp(prefix='.bie-mix-',dir=destination.parent))
    try:
        for name,data in files.items():
            p=tmp/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        lock=destination.parent/('.mix-publish-'+hashlib.sha256(str(destination.absolute()).encode()).hexdigest()+'.lock')
        with key_lock(lock,timeout=30):
            if destination.exists() or destination.is_symlink():raise AudioError('MIX_OUTPUT_EXISTS')
            os.rename(tmp,destination)
    finally:
        if tmp.exists():shutil.rmtree(tmp)
    return index
