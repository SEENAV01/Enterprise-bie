"""H9 synthetic source contracts and explicit diagnostic runtime helpers."""
from copy import deepcopy
from dataclasses import replace
from tests.compiler.h3_test_support import scene,track,TARGET
from tests.compiler.h2_test_support import runtime,sim_props
from tests.compiler.h5_test_support import full_tree,nodes,trace_scene as old_trace,equation_scene as old_equation
from bie.compiler.registered_actions import SCHEMA
T=replace(TARGET,width=800,height=450,fps=12)


def shape_scene(kind='rectangle'):
    geos={'rectangle':{'x':20,'y':20,'width':60,'height':50},'circle':{'cx':50,'cy':50,'r':30},'ellipse':{'cx':50,'cy':50,'rx':30,'ry':20},'line':{'x1':20,'y1':20,'x2':80,'y2':70},'arrow':{'x1':20,'y1':20,'x2':80,'y2':70,'head_length':10},'polygon':{'points':[[20,20],[80,20],[60,75],[25,60]]},'polyline':{'points':[[20,20],[50,60],[80,30]]}}
    p=scene('shape',{'shape_kind':kind,'geometry':{'view_box':[0,0,100,100],**geos[kind]},'style':{'stroke':'blue','stroke_width':2,'fill':'none'}},1000)
    p['scene_id']='h9-shape-'+kind;p['elements'][0]['accessibility']['alt']='Source '+kind
    p['elements'][0]['normalized_box']={'x':.15,'y':.1,'width':.7,'height':.8}
    return p


def diagram_scene():
    p=scene('diagram',{'diagram_kind':'causal','view_box':[0,0,600,280],
        'nodes':[{'node_id':'a','label':'Input {x}','x':20,'y':70,'width':150,'height':90,'font_size':20},
                 {'node_id':'b','label':'Output','x':400,'y':70,'width':170,'height':90,'font_size':20},
                 {'node_id':'isolated','label':'Context','x':220,'y':200,'width':160,'height':50,'font_size':20}],
        'edges':[{'from':'a','to':'b','directed':True,'label':'causes','label_position':[290,95]}]},1000)
    p['scene_id']='h9-diagram';p['elements'][0]['accessibility']['alt']='Explicit technical causal diagram; Context is an isolated node'
    p['elements'][0]['normalized_box']={'x':.05,'y':.1,'width':.9,'height':.8};return p


def highlight_scene(mode='outline',moving=False):
    p=scene('text',{'text':'Source-bound highlight','font_size':24},1000)
    p['scene_id']='h9-highlight-'+mode;p['elements'][0]['normalized_box']={'x':.22,'y':.3,'width':.5,'height':.2}
    h=deepcopy(p['elements'][0]);h.update(element_id='h',element_type='highlight',props={'target_element_ids':['e0'],'mode':mode},accessibility={'alt':'Emphasize the supplied text'},normalized_box={'x':.05,'y':.05,'width':.9,'height':.9})
    p['elements'].append(h);p['metadata']['compiler_h3']={'layout':{'allow_overlap':[{'elements':['e0','h'],'reason':'Source-requested noninteractive highlight overlay','source_refs':p['source_refs'],'reasoning_refs':p['reasoning_refs']}]}}
    if moving:p['tracks']=[track('transform',{'from':{'translate_x':0},'to':{'translate_x':50}},element_id='e0',source_refs=p['source_refs'],reasoning_refs=p['reasoning_refs'])]
    return p


def attach(p,action,params):
    e=p['elements'][0];p['tracks']=[track(action,{'schema_version':SCHEMA,**params},track_id='h9-action',element_id=e['element_id'],end_ms=p['duration_ms'],source_refs=e['source_refs'][:],reasoning_refs=e['reasoning_refs'][:])];return p


def action_scene(action):
    if action=='static_focus':
        p=scene('text',{'text':'Static focus on source text','font_size':26},1000);p['elements'][0]['normalized_box']={'x':.1,'y':.1,'width':.8,'height':.7}
        return attach(p,action,{'projection':'orthographic-2d','coordinate_space':'element-pixels','viewport':{'width':640,'height':315},'pose':{'focus_x':320,'focus_y':157.5,'zoom':1.}})
    if action=='crossfade_states':
        p=old_equation();params=deepcopy(p['tracks'][0]['parameters']);params.pop('schema_version');params.pop('mode');return attach(p,action,params)
    if action in {'static_trace','progressive_static_trace'}:
        from bie.compiler.specialized_motion import graph_contract
        p=old_trace();params=deepcopy(p['tracks'][0]['parameters']);params.pop('schema_version')
        if action=='progressive_static_trace':
            s=graph_contract(p['elements'][0])['series'][0];total=0.;values=[0.]
            for length in s['lengths']:total+=length;values.append(total/s['total_length'])
            values[-1]=1.;params['milestones']=[{'at_ms':i*500,'progress':v,'observation_ref':p['reasoning_refs'][0]} for i,v in enumerate(values)]
        return attach(p,action,params)
    if action in {'simulation_state','state_snapshots'}:
        p=scene('simulation',sim_props('acceleration'),2000);p['elements'][0]['normalized_box']={'x':.05,'y':.05,'width':.9,'height':.9}
        params={'model_ref':p['elements'][0]['props']['model_ref']}
        if action=='simulation_state':params.update(from_time_s=0,to_time_s=2)
        else:params['snapshots']=[{'at_ms':0,'time_s':0,'observation_ref':p['reasoning_refs'][0]},{'at_ms':750,'time_s':1,'observation_ref':p['reasoning_refs'][0]},{'at_ms':1500,'time_s':2,'observation_ref':p['reasoning_refs'][0]}]
        return attach(p,action,params)
    p=shape_scene('polyline');p['elements'][0]['normalized_box']={'x':.1,'y':.1,'width':.75,'height':.8};v={'width':600,'height':360};points=[[80,110],[300,230],[490,80]]
    p['elements'][0]['props']['geometry']={'view_box':[0,0,600,360],'points':deepcopy(points)}
    return attach(p,action,{'coordinate_space':'element-pixels','viewport':v,'points':points,'start_label':'Start','end_label':'End','marker_mode':'stationary-numeric'})
