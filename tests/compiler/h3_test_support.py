"""Synthetic H3 test scenes; never textbook or accepted pedagogical content."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tests.compiler.h2_test_support import scene as parent_scene,sim_props,geo_props,track,runtime,nodes
from bie.compiler.qa_scene_compile import CompilerQATarget
from bie.compiler.qa_common import digest
ROOT=Path(__file__).resolve().parents[2]
TARGET=replace(CompilerQATarget(),compiler_version='1.3.0-comp-h3')

def scene(kind='text',props=None,duration_ms=1000):
    p=parent_scene(kind,props if props is not None else {'text':'Bounded H3 technical text'})
    p['scene_id']='h3-technical-scene';p['duration_ms']=duration_ms
    p['source_refs']=['fixture:h3'];p['reasoning_refs']=['reasoning:h3']
    p['metadata']={'fixture':'synthetic-not-real-book'}
    e=p['elements'][0];e['element_id']='e0';e['source_refs']=['fixture:h3'];e['reasoning_refs']=['reasoning:h3']
    e['normalized_box']={'x':.15,'y':.2,'width':.35,'height':.3}
    return p

def move(p=None,params=None):
    p=deepcopy(p or scene());p['tracks']=[track('transform',params or {'from':{'translate_x':0},'to':{'translate_x':80}},track_id='h3move',element_id='e0',source_refs=['fixture:h3'],reasoning_refs=['reasoning:h3'])]
    return p

def variant(p):
    p=deepcopy(p);registry={}
    for e in p['elements']:
        ts=[t for t in p.get('tracks',[]) if t['element_id']==e['element_id']]
        if not ts and e['element_type'] not in {'simulation','particle_system','video'}:continue
        ref='variant:'+e['element_id'];e['accessibility']['reduced_motion_variant']=ref
        v={'element_id':e['element_id'],'track_replacements':{t['track_id']:{'action':'enter','parameters':{}} for t in ts},
           'reason':'Explicit static/fade alternative for this synthetic fixture; not learning acceptance.',
           'source_refs':list(e['source_refs']),'reasoning_refs':list(e['reasoning_refs'])}
        if e['element_type']=='simulation':v['freeze_frame']=48
        registry[ref]=v
    p['metadata']['compiler_h3']={'reduced_motion_variants':registry}
    return p

def measurement(raw,target=TARGET,manifest='a'*64):
    count=(raw['duration_ms']*target.fps+999)//1000
    return {'scope':'REAL_CHROMIUM_WHOLE_SCENE_WITH_EXPLICIT_REACT_REMOTION_TEST_DOUBLES',
            'scene_identity':digest(raw),'manifest_sha256':manifest,'width':target.width,'height':target.height,
            'fps':target.fps,'frame_count':count,'browser_errors':[],'fonts_ready':True,
            'records':[{'element_id':e['element_id'],'frame':f,'visible':True,'layer_box':[50,50,200,100],
                       'ink_boxes':[[60,60,100,20]],'text_boxes':[{'box':[60,60,100,20],'font_px':16}],
                       'scroll_overflow':False,'equation_em_px':None} for f in range(count) for e in raw['elements']]}
