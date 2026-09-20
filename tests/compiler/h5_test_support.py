"""Synthetic H5 technical inputs; API doubles are always labelled as such."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import json,subprocess,tempfile
from tests.compiler.h3_test_support import scene as parent_scene, TARGET, track, ROOT
from tests.compiler.h2_test_support import runtime
from bie.compiler.specialized_motion import SCHEMA
BIG = replace(TARGET,width=1280,height=720)


def scene(kind='text',props=None, duration_ms=2000):
    raw=parent_scene(kind,props if props is not None else {'text':'A source-bound camera focuses on this explanation.'},duration_ms)
    raw['scene_id']='h5-'+kind;raw['source_refs']=['fixture:h5'];raw['reasoning_refs']=['reasoning:h5']
    raw['elements'][0].update(source_refs=raw['source_refs'][:],reasoning_refs=raw['reasoning_refs'][:])
    raw['elements'][0]['normalized_box']={'x':.15,'y':.2,'width':.5,'height':.5}
    return raw


def attach(p,action,params,tid='h5track',**kw):
    e=p['elements'][0]
    p['tracks'].append(track(action,{'schema_version':SCHEMA,**params},track_id=tid,element_id=e['element_id'],end_ms=p['duration_ms'],source_refs=e['source_refs'][:],reasoning_refs=e['reasoning_refs'][:],**kw))
    return p


def camera_scene(target=BIG):
    p=scene();b=p['elements'][0]['normalized_box'];w=b['width']*target.width;h=b['height']*target.height
    return attach(p,'camera',{'projection':'orthographic-2d','coordinate_space':'element-pixels','viewport':{'width':w,'height':h},
        'from':{'focus_x':w/2,'focus_y':h/2,'zoom':.55},'to':{'focus_x':w/2,'focus_y':h/2,'zoom':1.}},tid='camera')


def equation_scene():
    expressions=[r'2(x+1)=6',r'x+1=3',r'x=2']
    p=scene('equation',{'expression':expressions[0],'format':'latex','font_size':32,'side_conditions':['x is real']})
    e=p['elements'][0]
    states=[{'expression':x,'alt':'Equation step '+str(i+1)+': '+x,'source_refs':e['source_refs'][:],'reasoning_refs':e['reasoning_refs'][:]} for i,x in enumerate(expressions)]
    return attach(p,'morph',{'mode':'typeset-state-crossfade','transition_fraction':.4,'states':states},tid='steps')


def trace_scene():
    props={'series':[{'series_id':'signal','label':'Displacement','points':[[-2,-1],[-1,2],[1,-2],[2,1]]},
                     {'series_id':'reference','label':'Zero reference','points':[[-2,0],[2,0]]}],
           'x_domain':[-2,2],'y_domain':[-3,3],'x_label':'Time','y_label':'Position','x_unit':'s','y_unit':'m'}
    p=scene('graph',props);p['elements'][0]['normalized_box']={'x':.1,'y':.1,'width':.65,'height':.7}
    return attach(p,'trace',{'series_id':'signal','progress_model':'screen-arc-length','head_marker':True},tid='trace')


def full_tree(compiled,frames=(0,23,47),target=BIG):
    req={'files':{f.path:f.content for f in compiled.codegen.files},'frames':list(frames),'width':target.width,'height':target.height,'fps':target.fps}
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'req.json';p.write_text(json.dumps(req))
        r=subprocess.run(['node',str(ROOT/'bie/compiler/qa_support/layout_bridge.cjs'),str(p)],capture_output=True,text=True,timeout=40)
        if r.returncode:raise AssertionError(r.stderr)
        return json.loads(r.stdout)


def nodes(tree):
    if isinstance(tree, dict):
        yield tree
        for child in tree.get('children', []):yield from nodes(child)
    elif isinstance(tree,list):
        for child in tree:yield from nodes(child)
