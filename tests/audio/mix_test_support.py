from pathlib import Path
from dataclasses import asdict
from functools import lru_cache
import json,sys,tempfile,importlib,ast
import numpy as np
from bie.audio.mix_contract import MixBuffer
from bie.audio.sfx_mixing import Stem
ROOT=Path(__file__).resolve().parents[2]
def tone(frames=44100,rate=22050,amp=.1,hz=440,channels=1):
 x=amp*np.sin(2*np.pi*hz*np.arange(frames)/rate)
 return MixBuffer.from_array(np.repeat(x[:,None],channels,axis=1),rate)
def constant(frames=1000,value=.1,rate=22050,channels=1):return MixBuffer.from_array(np.full((frames,channels),value),rate)
def stem(pcm,**kw):
 defaults=dict(asset_id='test',role='sfx',pcm=pcm,start_sample=0,trim_start=0,trim_end=pcm.frames,source_refs=('synthetic:test',),rights_ref='synthetic:own-generated')
 defaults.update(kw);return Stem(**defaults)
def locate(name):
 for p in (ROOT/'bie/audio').glob('*.py'):
  if any(isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name for n in ast.parse(p.read_text()).body):
   return getattr(importlib.import_module('bie.audio.'+p.stem),name)
 raise ImportError(name)
@lru_cache(maxsize=2)
def real_sync(example='english'):
 sys.path.insert(0,str(ROOT/'scripts'))
 from audio_synthesize import prepare_input
 path=ROOT/('examples/audio_batch003/scene_animation_pause.json' if example=='english' else 'examples/audio_batch002/hindi.json')
 plan=prepare_input(json.loads(path.read_text()),'batch001-144')
 policy=locate('SelectionPolicy')(('espeak-timed-local',),('technical_formant',),require_same_voice_code_switching=False)
 cache=locate('TTSCache')(Path(tempfile.mkdtemp(prefix='bie-mix-tests-')),namespace='batch004-tests')
 return locate('prepare_sync')(plan,locate('TimedEspeakProvider')(),cache,policy,caption_policy=locate('CaptionPolicy')(channel='display'))
def spec(sync,stems=()):
 from bie.audio.mix_pipeline import MixPolicy
 return {'schema_version':'bie.audio.mix-spec/1','plan_fingerprint':sync.plan.fingerprint(),'timeline_fingerprint':sync.timeline.fingerprint(),'policy':asdict(MixPolicy()),'stems':list(stems)}
