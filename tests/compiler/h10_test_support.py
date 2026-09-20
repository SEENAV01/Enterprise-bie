"""Finite H10 technical combination cases; no real-book or pedagogical claim."""
from copy import deepcopy
from dataclasses import replace
from tests.compiler.h9_test_support import T as T9,action_scene,shape_scene,highlight_scene
from tests.compiler.h5_test_support import trace_scene,equation_scene,camera_scene
from tests.compiler.h3_test_support import scene,track
from bie.compiler.state_motion_composition import SCHEMA,POLICY

T=replace(T9,width=1280,height=720)

def bind(raw, properties=('visible',), *, consent=True):
    p=deepcopy(raw);e=p['elements'][0];eid=e['element_id'];duration=p['duration_ms']
    cfg={'schema_version':'bie.comp-frame-runtime.v1','initial_state':{},'state_lineage':{}}
    p['metadata']['compiler_h6']=cfg;p['metadata']['state_paths']=[];p['state_bindings']=[];p['events']=[]
    for prop in properties:
        path='lesson.'+prop;p['metadata']['state_paths'].append(path)
        values={'visible':[True,False,True],'opacity':[.6,0.,.8],'text':[e['props'].get('text',''),'{changed} <literal>', 'Final — समझें']}[prop]
        cfg['initial_state'][path]=values[0]
        refs={k:deepcopy(p[k]) for k in ('source_refs','reasoning_refs')}
        cfg['state_lineage'][path]=refs
        p['state_bindings'].append({'binding_id':'bound-'+prop,'state_path':path,'target_id':eid,'property_name':prop,'read_only':True})
        for i,ms in enumerate([duration//3,2*duration//3],start=1):
            p['events'].append({'event_id':prop+'-'+str(i),'at_ms':ms,'event_type':'state.set','target_ids':[eid],
                'payload':{'state_path':path,'value':values[i],**deepcopy(refs)}})
    if consent:
        p['metadata']['compiler_h10']={'schema_version':SCHEMA,'compositions':[{
            'target_id':eid,'track_ids':[t['track_id'] for t in p['tracks'] if t['element_id']==eid],
            'state_properties':sorted(set(properties)&{'visible','opacity'}),'policy':POLICY,
            'source_refs':deepcopy(p['source_refs']),'reasoning_refs':deepcopy(p['reasoning_refs'])}]}
    return p


def composed_scene(action='trace',properties=('visible',),*,target=T):
    if action=='trace':p=trace_scene()
    elif action=='morph':p=equation_scene()
    elif action=='camera':
        p=camera_scene(target);p['tracks'][0]['parameters']['from']['zoom']=1.
        p['tracks'][0]['parameters']['to']['zoom']=1.05
    elif action in {'enter','exit','reveal','emphasize','transform','path_follow'}:
        p=scene(duration_ms=1500);p['elements'][0]['normalized_box']={'x':.2,'y':.2,'width':.5,'height':.5}
        params={'enter':{},'exit':{},'reveal':{'direction':'left'},'emphasize':{'peak_scale':1.05},
                'transform':{'from':{'translate_x':0},'to':{'translate_x':40}},
                'path_follow':{'coordinate_space':'pixels','points':[[0,0],[30,20]]}}[action]
        p['tracks']=[track(action,params,track_id='motion',element_id='e0',end_ms=p['duration_ms'],
                           source_refs=p['source_refs'],reasoning_refs=p['reasoning_refs'])]
    else:
        p=action_scene(action)
        if action=='static_focus':
            b=p['elements'][0]['normalized_box'];v={'width':b['width']*target.width,'height':b['height']*target.height}
            q=p['tracks'][0]['parameters'];q['viewport']=v;q['pose']={'focus_x':v['width']/2,'focus_y':v['height']/2,'zoom':1.}
        if action=='path_endpoints_with_progress_marker':
            q=p['tracks'][0]['parameters'];v={'width':.75*target.width,'height':.8*target.height};q['viewport']=v
            q['points']=[[.15*v['width'],.3*v['height']],[.5*v['width'],.5*v['height']],[.8*v['width'],.3*v['height']]]
            p['elements'][0]['props']['geometry']={'view_box':[0,0,v['width'],v['height']],'points':deepcopy(q['points'])}
    return bind(p,properties)


def native_request(p, action=None,required=True):
    p=deepcopy(p);e=p['elements'][0]
    p['capability_requests']=[{'capability_id':'comp:'+e['element_type'],'element_id':e['element_id'],
       'element_type':e['element_type'],'requested_action':action or p['tracks'][0]['action'],'required':required}]
    return p
