from __future__ import annotations
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
import io,wave,hashlib
from tests.hardening_h2.support import materialized as base_materialized
from bie.game_engine.audio import AudioCue,AudioCueKind,AudioExperienceContract
from bie.game_engine.handoff_engine.materializer import to_compiler_context
from bie.game_engine.compiler_engine.contracts import AssetDescriptor
from bie.game_engine.build_runtime_engine.workspace import build_workspace
from bie.game_engine.runtime_quality_engine.contracts import *

def wav_bytes():
    out=io.BytesIO()
    with wave.open(out,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\x00\x00'*800)
    return out.getvalue()

def profile(asset_ref='audio:narration'):
    cat=LocaleCatalog('ur-IN',{
      'ui.ready':'تیار','ui.audio_play':'بیان چلائیں','ui.attribution':'ماخذ اور حقوق'
    },'rtl')
    rights=RightsRecord(asset_ref,'rights:audio','CC-BY-4.0','Educational narration © source author','source:book')
    return RuntimeExperienceProfile(primary_locale='ur-IN',catalogs=(cat,),rights=(rights,),audio_sync=(AudioSyncRecord('cue:narration:1',0,100,'level_start'),))

def game_with_audio():
    m=base_materialized();doc=m.document;exp=doc.experiences[0];level=exp.levels[0]
    text_ref='text:narration:1';cue=AudioCue('cue:narration:1',AudioCueKind.NARRATION,'level_start','audio:narration',text_ref,False).validate()
    level=replace(level,audio=AudioExperienceContract((cue,)).validate());exp=replace(exp,levels=(level,*exp.levels[1:]));doc=replace(doc,experiences=(exp,)).validate()
    texts=dict(m.text_catalog);texts[text_ref]='یہ سبق حرکت کو سمجھاتا ہے۔'
    return replace(m,document=doc,text_catalog=texts)

@lru_cache(maxsize=1)
def context():
    data=wav_bytes();sha=hashlib.sha256(data).hexdigest();asset=AssetDescriptor('audio:narration','audio/wav',sha,'Narration','rights:audio','CC-BY-4.0','Educational narration © source author','source:book').validate()
    return to_compiler_context(game_with_audio(),assets={'audio:narration':asset},experience_profile=profile())

def build():
    td=TemporaryDirectory(prefix='bie-h4-');ws=build_workspace(context(),{'audio:narration':wav_bytes()},Path(td.name));return td,ws
