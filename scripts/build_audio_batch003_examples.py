#!/usr/bin/env python3
"""Source-pinned synthetic SYNC specifications; not a real-book fixture."""
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'dependency_snapshot'))
from audio_synthesize import prepare_input
from bie.audio.multilingual_terms import apply_languages
from audio_synthesize import read_language_terms

def main():
    out=ROOT/'examples/audio_batch003';out.mkdir(exist_ok=True)
    base=json.loads((ROOT/'examples/audio_batch002/english.json').read_text())
    raw=deepcopy(base);raw['segments']=[];raw['drafts']=[];raw['segment_order']=[];raw['pauses']=[]
    rows=[('First observe the graph.','scene:1',450),('Now trace the change.','scene:1',300),('The next scene preserves the narration order.','scene:2',0)]
    for i,(value,scene,pause) in enumerate(rows,1):
        sid='narration:'+str(i);s=deepcopy(base['segments'][0]);s.update(segment_id=sid,scene_id=scene)
        d=deepcopy(base['drafts'][0]);d.update(segment_id=sid,text=value)
        raw['segments'].append(s);raw['drafts'].append(d);raw['segment_order'].append(sid)
        if pause:raw['pauses'].append({'utterance_id':sid,'offset':len(value),'milliseconds':pause,'source_refs':['synthetic:requested-pause']})
    (out/'scene_animation_pause.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
    p=prepare_input(raw,'batch001-144')
    spec={'schema_version':'bie.audio.word-anchor-input/1','plan_fingerprint':p.fingerprint(),'bindings':[{
        'binding_id':'trace:1','target_id':'technical:graph','action':'graph_trace',
        'start_segment_id':p.segments[0].segment_id,'first_word':0,
        'end_segment_id':p.segments[1].segment_id,'last_word':3,
        'source_refs':['synthetic:audio-fixture:1'],'reasoning_refs':['synthetic:trace-after-observe'],
        'start_offset_ms':0,'end_offset_ms':0,'minimum_frames':12,'pause_mode':'hold','after':[],
        'expected_first_word':'First','expected_last_word':'change'}]}
    (out/'scene_animation_pause.spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
