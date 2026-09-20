"""Synthetic H6 inputs and PCM test signals; not speech or a real lesson."""
from copy import deepcopy
from pathlib import Path
from dataclasses import replace
from hashlib import sha256
import io, math, struct, wave
from tests.compiler.h3_test_support import scene as parent_scene, TARGET, ROOT
from bie.compiler.frame_runtime_contract import SCHEMA
BIG=replace(TARGET,width=1280,height=720)
REFS={'source_refs':['fixture:h6'],'reasoning_refs':['reasoning:h6']}


def state_scene():
    p=parent_scene(duration_ms=2000)
    p.update(scene_id='h6-state', **deepcopy(REFS))
    p['elements'][0].update(**deepcopy(REFS))
    p['elements'][0]['props']={'text':'Before: x = 1 {literal}'}
    p['elements'][0]['normalized_box']={'x':.1,'y':.1,'width':.8,'height':.4}
    p['metadata']={'fixture':'synthetic-not-book','state_paths':['lesson.phase'],
        'compiler_h6':{'schema_version':SCHEMA,'initial_state':{'lesson.phase':p['elements'][0]['props']['text']},
                       'state_lineage':{'lesson.phase':deepcopy(REFS)}}}
    p['state_bindings']=[{'binding_id':'phase','state_path':'lesson.phase','target_id':'e0','property_name':'text','read_only':True}]
    p['events']=[{'event_id':'step1','at_ms':500,'event_type':'state.set','target_ids':['e0'],
                 'payload':{'state_path':'lesson.phase','value':'After: x = 2 <not markup>',**deepcopy(REFS)}},
                {'event_id':'step2','at_ms':1250,'event_type':'state.set','target_ids':['e0'],
                 'payload':{'state_path':'lesson.phase','value':'समझें — اردو — INITIAL {2+2}',**deepcopy(REFS)}}]
    return p


def wav_signal(seconds=2,rate=48000,channels=1,frequency=440):
    b=io.BytesIO()
    with wave.open(b,'wb') as w:
        w.setnchannels(channels);w.setsampwidth(2);w.setframerate(rate)
        values=[round(6000*math.sin(2*math.pi*frequency*i/rate)) for i in range(int(seconds*rate))]
        w.writeframes(b''.join(struct.pack('<h',v)*channels for v in values))
    return b.getvalue()


def narration_scene():
    p=state_scene();e=deepcopy(p['elements'][0]);e.update(element_id='captions')
    e['props']={'text':'A first caption: x = 1.'};e['normalized_box']={'x':.1,'y':.65,'width':.8,'height':.25}
    p['elements'].append(e);p['narration_cues']=[
      {'cue_id':'cue1','start_ms':250,'end_ms':1000,'text_ref':'text:c1','narration_revision':1,'target_ids':['e0']},
      {'cue_id':'cue2','start_ms':1250,'end_ms':2000,'text_ref':'text:c2','narration_revision':1,'target_ids':['e0']}]
    data=wav_signal();h=sha256(data).hexdigest();path='narration/'+h+'.wav'
    texts={'text:c1':{'text':e['props']['text'],**deepcopy(REFS)},'text:c2':{'text':'दूसरा चरण — x = 2 {safe}.',**deepcopy(REFS)}}
    cfg=p['metadata']['compiler_h6'];cfg.update(narration_revision=1,caption_target_id='captions',narration_texts=texts,
      audio_assets=[{'asset_id':'signal','public_path':path,'sha256':h,'byte_length':len(data),'sample_rate':48000,
                     'channels':1,'sample_width':2,'frame_count':96000,'rights_ref':'generated-test-tone',**deepcopy(REFS)}],
      audio_segments=[{'cue_id':c['cue_id'],'asset_id':'signal','trim_before_frames':0,'volume':.5,
                       'transcript_sha256':sha256(texts[c['text_ref']]['text'].encode()).hexdigest()} for c in p['narration_cues']])
    return p,{path:data}


def write_assets(root,assets):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    for rel,b in assets.items():
        f=root/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
    return root


def execute(compiled, frames=None, target=BIG):
    import json, subprocess, tempfile
    if frames is None:frames=list(range((compiled.effective_document['duration_ms']*target.fps+999)//1000))
    req={'files':{f.path:f.content for f in compiled.codegen.files},'frames':list(frames),'fps':target.fps,'width':target.width,'height':target.height}
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'request.json';p.write_text(json.dumps(req))
        r=subprocess.run(['node',str(ROOT/'app/bie/compiler/qa_support/frame_runtime_bridge.cjs'),str(p)],capture_output=True,text=True,timeout=40)
        if r.returncode:raise AssertionError(r.stderr)
        return json.loads(r.stdout)


def nodes(tree):
    if isinstance(tree,dict):
        yield tree
        for child in tree.get('children',[]):yield from nodes(child)
    elif isinstance(tree,list):
        for child in tree:yield from nodes(child)
