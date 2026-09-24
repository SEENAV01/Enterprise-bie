from __future__ import annotations
import json,tempfile
from functools import lru_cache
from pathlib import Path
from bie.audio.pipeline_contract import prepare_document
from bie.audio.pipeline_bundle import validate_bundle
from tests.audio.pipeline_test_support import actual,context
from bie.audio.dir_audio_handoff import bind_dir_utterances
from bie.audio.compiler_handoff import build_compiler_handoff
from bie.audio.repair_dispatch import invalidation_plan,GRAPH
from bie.audio.render_evidence import render_technical_av
from bie.director.speech_timing import SpeechUtterance
from bie.audio.common import fingerprint

@lru_cache(maxsize=1)
def baseline():
    files,_=actual(); c=context(); bundle=validate_bundle(files,c['request'],c['profile']); plan=bundle['sync'].plan
    utterances=[]
    seen=[]
    for s in plan.segments:
        if s.utterance_id in seen: continue
        seen.append(s.utterance_id); segs=[x for x in plan.segments if x.utterance_id==s.utterance_id]
        refs=[];objs=[]
        for x in segs:
            for sp in x.spans:
                for r in sp.source_refs:
                    if r not in refs:refs.append(r)
            for o in x.objective_ids:
                if o not in objs:objs.append(o)
        utterances.append(SpeechUtterance(s.utterance_id,s.utterance_id,s.scene_id,s.persona_id,
            ''.join(x.display_text for x in segs),s.language,tuple(refs),tuple(objs),s.script_fingerprint,()))
    return files,bundle,plan,tuple(utterances)

def dir_receipt():
    *_,plan,utterances=baseline();return bind_dir_utterances(utterances,plan)

def compiler():
    files,bundle,plan,_=baseline();clock=json.loads(files['MIX_CLOCK.json'])
    return build_compiler_handoff(plan,files['master.wav'],clock,fps=24,caption_target_id='caption:text',
        target_ids_by_scene={'scene:1':('visual:primary',)},rights_ref='rights:synthetic-h5',reasoning_refs=('reasoning:synthetic-h5',))

def repair_intent():
    row={'target_fingerprint':'sha256:'+'5'*64,'owner':'AUDIO/VO','action':'RESYNTHESIZE_UNCHANGED_READING',
         'expected_spoken':'charge','expected_ipa':'tʃɑɹdʒ','source_refs':['source:1'],
         'invalidates':['AUDIO_TTS_CACHE','AUDIO_SYNC','AUDIO_MIX','CAPTIONS','ANIMATION_CLOCKS','AUDIO_QA','RENDER'],
         'decision_fingerprint':'sha256:'+'9'*64,'dispatch_performed':False}
    row['repair_fingerprint']=fingerprint(row);return row

def statuses():return {k:'QA_VERIFIED' for k in GRAPH}

def invalidation():return invalidation_plan(repair_intent(),statuses())

@lru_cache(maxsize=1)
def rendered():
    files,*_=baseline(); td=Path(tempfile.mkdtemp(prefix='bie-h10-render-'))
    receipt,data=render_technical_av(files['master.wav'],files['captions.srt'],td)
    return receipt,data,td
