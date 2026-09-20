"""Synthetic H4 fixtures, not books or accepted lessons."""
from copy import deepcopy
from dataclasses import replace
from tests.compiler.h3_test_support import scene,geo_props,TARGET,ROOT,track,sim_props
from bie.compiler.layout_repair_contracts import default_policy,canonical_scene
from bie.compiler.qa_common import digest
TARGET_BIG=replace(TARGET,width=1280,height=720)

def text_case(text=None,*,expand=True):
    p=scene('text',{'text':text or 'A clear explanation preserves each word and its source. '*8})
    p['scene_id']='h4-text-repair'
    p['elements'][0]['normalized_box']={'x':.05,'y':.05,'width':.18,'height':.06}
    policy=default_policy(p)
    if expand:policy['owners']['e0']['region']={'x':.05,'y':.05,'width':.8,'height':.5}
    policy['reason']='Synthetic visual-owner permission to use this empty region without changing teaching content.'
    return p,policy

def map_case():
    p=scene('map',geo_props());p['scene_id']='h4-map-reflow'
    p['elements'][0]['normalized_box']={'x':.05,'y':.05,'width':.9,'height':.9}
    layers=[]
    for i in range(3):
        layer=deepcopy(p['elements'][0]['props']['layers'][0]);layer['layer_id']='route'+str(i)
        layer['label']='W'*76 if i==2 else 'Technical route '+str(i);layers.append(layer)
    p['elements'][0]['props']['layers']=layers
    return p,default_policy(p)

def equation_case():
    p=scene('equation',{'expression':r'\frac{x^2+1}{\sqrt{y}}','format':'latex'})
    p['scene_id']='h4-equation-resize';p['elements'][0]['normalized_box']={'x':.1,'y':.1,'width':.6,'height':.018}
    policy=default_policy(p);policy['owners']['e0']['region']={'x':.1,'y':.1,'width':.7,'height':.45}
    return p,policy

def observation(compiled,target=TARGET_BIG,*,collide=False):
    from bie.compiler.content_fit_qa import BRIDGE_SCOPE
    from bie.compiler.layout_measurements import required_text
    raw=compiled.effective_document;n=(raw['duration_ms']*target.fps+999)//1000
    rows=[]
    for f in range(n):
        for e in raw['elements']:
            required=required_text(e)
            texts=[{'box':[65,65+24*i,100,20],'font_px':16,'text_id':'t'+str(i),'fragment_id':'t'+str(i)+':0'} for i in range(max(1,len(required)))]
            if collide and len(texts)>1:texts[1]['box']=list(texts[0]['box'])
            rows.append({'element_id':e['element_id'],'frame':f,'visible':True,'layer_box':[60,60,500,600],
                         'ink_boxes':[],'text_boxes':texts,'rendered_text':required,'scroll_overflow':False,'equation_em_px':32 if e['element_type']=='equation' else None})
    return {'scope':BRIDGE_SCOPE,'scene_identity':digest(raw),'manifest_sha256':compiled.codegen.manifest_sha256,
            'width':target.width,'height':target.height,'fps':target.fps,'frame_count':n,'browser_errors':[],
            'fonts_ready':True,'records':rows,'test_double_measurements':True}
