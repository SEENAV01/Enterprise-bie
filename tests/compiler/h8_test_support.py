"""Synthetic H8 fixtures; raster-data fixtures do NOT certify an actual renderer."""
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
from dataclasses import replace
import numpy as np
from PIL import Image
from bie.compiler.qa_common import digest
from bie.compiler.raster_capture import build_raster_targets,frame_file,DIAGNOSTIC_SCOPE
from tests.compiler.h3_test_support import scene, TARGET, track
SMALL=replace(TARGET,width=64,height=48,fps=4)
BROWSER=replace(TARGET,width=640,height=360,fps=4)

def raw_text(text='H8 source-bound text',duration_ms=500):
    p=scene('text',{'text':text,'font_size':24},duration_ms=duration_ms)
    p['scene_id']='h8-synthetic-text';p['elements'][0]['normalized_box']={'x':.1,'y':.1,'width':.8,'height':.7}
    return p

def map_scene(*,overlap=False,tiny_polygon=False):
    coords=[[.3,.4],[.3,.4] if overlap else [.7,.6]]
    layers=[{'kind':'point','points':[p],'label':'P'+str(i),'layer_id':'p'+str(i),'source_ref':'fixture:h3'} for i,p in enumerate(coords)]
    if tiny_polygon:layers.append({'kind':'polygon','layer_id':'small','points':[[.5,.5],[.50001,.5],[.50001,.50001],[.5,.5]],'source_ref':'fixture:h3','label':'Tiny'})
    p=scene('map',{'crs':'normalized','layers':layers,'title':'Technical points','attribution':'Synthetic coordinates'},duration_ms=500)
    p['elements'][0]['normalized_box']={'x':.05,'y':.05,'width':.9,'height':.9}
    return p

def white(w=64,h=48):return np.full((h,w,3),255,np.uint8)
def mask(shape=(24,32),box=(4,4,5,5)):
    a=np.zeros(shape,bool);x,y,w,h=box;a[y:y+h,x:x+w]=True;return a

def feature(tid='a',kind='point',owner='e0',visible=True):
    return {'target_id':tid,'element_id':owner,'layer_id':tid,'kind':kind,'source_ref':'fixture:map','visible':visible}

def save_png(root,name,array):
    p=Path(root)/name;Image.fromarray(array).save(p,format='PNG')
    return {'file':name,'sha256':sha256(p.read_bytes()).hexdigest()}

def capture_fixture(root,raw=None,target=SMALL,*,scope=DIAGNOSTIC_SCOPE,frames_override=None):
    raw=raw or raw_text();targets=build_raster_targets(raw);n=(raw['duration_ms']*target.fps+999)//1000
    frames=[]
    for f in range(n if frames_override is None else frames_override):
        base=white(target.width,target.height);alone=base.copy();alone[12:19,10:30]=0
        r={'frame':f,'full':save_png(root,frame_file(f,'full'),alone),
           'repeat':save_png(root,frame_file(f,'repeat'),alone),
           'inventory':[{'target_id':x['target_id'],'visible':True,'unresolved_effect':False,'box':[4,4,48,30]} for x in targets], 'targets':[]}
        for i,t in enumerate(targets):
            r['targets'].append({'target_id':t['target_id'],**{k:save_png(root,frame_file(f,k,i),a) for k,a in [('baseline',base),('isolated',alone),('muted',base)]}})
        frames.append(r)
    return {'schema_version':'bie.counterfactual-capture.v1','scope':scope,'scene_sha256':digest(raw),
            'manifest_sha256':'a'*64,'width':target.width,'height':target.height,'fps':target.fps,'frame_count':n,'targets':targets,'frames':frames,'browser_errors':[]}
