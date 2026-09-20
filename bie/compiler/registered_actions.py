"""H9-004 bounded consumers for the seven existing registered action names.

Source actions are retained. A lowering is explicit and used by both emission and
frame checks; it is not a PASS label for a similarly-named metadata variant.
"""
from __future__ import annotations
from copy import deepcopy
from collections.abc import Mapping
import math
from dataclasses import replace
from .animation_compiler_common import normalize_track,AnimationCompilerError
from .specialized_motion import _fields,_number,_text,_refs,fail,SCHEMA as SPECIAL_SCHEMA

SCHEMA='bie.comp-registered-action.v1'
ACTIONS=frozenset({'simulation_state','static_focus','static_trace','crossfade_states','state_snapshots','progressive_static_trace','path_endpoints_with_progress_marker'})
CONTENT_ACTIONS=ACTIONS-{'static_focus'}


def is_registered(track):
    action=track.get('action') if isinstance(track,Mapping) else getattr(track,'action',None)
    return isinstance(action,str) and action in ACTIONS


def _rows(rows,start,end,source,reason,*,key):
    if not isinstance(rows,(list,tuple)) or not 2<=len(rows)<=32:fail('REGISTERED_MILESTONES_INVALID','2..32 explicit observations required')
    checked=[]
    for row in rows:
        _fields(row,{'at_ms',key,'observation_ref'})
        if type(row['at_ms'])is not int or not start<=row['at_ms']<end:fail('REGISTERED_MILESTONE_TIME','observation time outside track')
        _text(row['observation_ref'],'observation_ref',512)
        if row['observation_ref'] not in reason:fail('REGISTERED_OBSERVATION_UNBOUND','observation_ref must be in track reasoning_refs')
        checked.append({'at_ms':row['at_ms'],key:_number(row[key],key,0,3600 if key=='time_s' else 1),'observation_ref':row['observation_ref']})
    if checked[0]['at_ms']!=start or any(b['at_ms']<=a['at_ms'] or b[key]<=a[key] for a,b in zip(checked,checked[1:])):fail('REGISTERED_MILESTONE_ORDER','strict chronological and increasing progression required, starting at track start')
    if key=='progress' and (checked[0][key]!=0 or checked[-1][key]!=1):fail('REGISTERED_ENDPOINTS_REQUIRED','progress must retain both endpoints')
    return checked


def registered_contract(track):
    from .animation_behavior import MotionContract
    tid,eid,action,start,end,p,src,rsn=normalize_track(track)
    if action not in ACTIONS or p.get('schema_version')!=SCHEMA:fail('ANIMATION_ACTION_UNSUPPORTED','registered action requires explicit '+SCHEMA+' parameters')
    if end>3600000:fail('ANIMATION_TIME_BOUNDS','one-hour track budget')
    if len(src)!=len(set(src)) or len(rsn)!=len(set(rsn)):fail('REGISTERED_PROVENANCE_INVALID','duplicate references')
    q={'schema_version':SCHEMA};owned=('content',)
    if action=='static_focus':
        _fields(p,{'schema_version','projection','coordinate_space','viewport','pose'})
        if p['projection']!='orthographic-2d' or p['coordinate_space']!='element-pixels':fail('CAMERA_SPACE_UNSUPPORTED','explicit element-pixel orthographic view required')
        _fields(p['viewport'],{'width','height'});_fields(p['pose'],{'focus_x','focus_y','zoom'})
        v={k:_number(p['viewport'][k],k,1,8192) for k in ('width','height')}
        pose={'focus_x':_number(p['pose']['focus_x'],'focus_x',0,v['width']),'focus_y':_number(p['pose']['focus_y'],'focus_y',0,v['height']),'zoom':_number(p['pose']['zoom'],'zoom',.1,10)}
        q.update(projection=p['projection'],coordinate_space=p['coordinate_space'],viewport=v,pose=pose);owned=('scale','translate')
    elif action in {'static_trace','progressive_static_trace'}:
        required={'schema_version','series_id','progress_model','head_marker'}|({'milestones'} if action=='progressive_static_trace' else set())
        _fields(p,required)
        if p['progress_model']!='screen-arc-length' or type(p['head_marker'])is not bool:fail('TRACE_PROGRESS_MODEL_UNSUPPORTED','screen-arc-length and boolean marker required')
        q.update(series_id=_text(p['series_id'],'series_id',128),progress_model=p['progress_model'],head_marker=p['head_marker'])
        if action=='progressive_static_trace':q['milestones']=_rows(p['milestones'],start,end,src,rsn,key='progress')
    elif action=='crossfade_states':
        _fields(p,{'schema_version','states','transition_fraction'},{'easing'})
        from .specialized_motion import specialized_contract
        base={**p,'schema_version':SPECIAL_SCHEMA,'mode':'typeset-state-crossfade'}
        c=specialized_contract({'track_id':tid,'element_id':eid,'action':'morph','start_ms':start,'end_ms':end,'parameters':base,'source_refs':src,'reasoning_refs':rsn})
        q.update(states=c.parameters['states'],transition_fraction=c.parameters['transition_fraction'],easing=c.easing)
    elif action=='simulation_state':
        _fields(p,{'schema_version','model_ref','from_time_s','to_time_s'},{'easing'})
        q.update(model_ref=_text(p['model_ref'],'model_ref',128),from_time_s=_number(p['from_time_s'],'from_time_s',0,3600),to_time_s=_number(p['to_time_s'],'to_time_s',0,3600),easing=p.get('easing','linear'))
        if q['to_time_s']<=q['from_time_s'] or q['easing'] not in {'linear','smoothstep'}:fail('SIMULATION_ACTION_TIME_INVALID','increasing explicit model times and supported easing required')
    elif action=='state_snapshots':
        _fields(p,{'schema_version','model_ref','snapshots'})
        q.update(model_ref=_text(p['model_ref'],'model_ref',128),snapshots=_rows(p['snapshots'],start,end,src,rsn,key='time_s'))
    else:
        _fields(p,{'schema_version','coordinate_space','viewport','points','start_label','end_label','marker_mode'})
        if p['coordinate_space']!='element-pixels' or p['marker_mode']!='stationary-numeric':fail('PATH_ENDPOINT_MODE_UNSUPPORTED','explicit stationary numeric progress marker required')
        _fields(p['viewport'],{'width','height'});v={k:_number(p['viewport'][k],k,64,8192) for k in ('width','height')}
        points=p['points']
        if not isinstance(points,(list,tuple)) or not 2<=len(points)<=256:fail('ANIMATION_PATH_INVALID','2..256 source points required')
        checked=[]
        for point in points:
            if not isinstance(point,(list,tuple)) or len(point)!=2:fail('ANIMATION_PATH_INVALID','2D point required')
            qpt=[_number(point[0],'x',10,v['width']-10),_number(point[1],'y',30,v['height']-40)]
            if checked and math.dist(checked[-1],qpt)<1e-8:fail('ANIMATION_PATH_INVALID','nonzero segments required')
            checked.append(qpt)
        q.update(coordinate_space=p['coordinate_space'],viewport=v,points=checked,start_label=_text(p['start_label'],'start_label',300),end_label=_text(p['end_label'],'end_label',300),marker_mode=p['marker_mode'])
    return MotionContract(tid,eid,action,start,end,q.get('easing','linear'),q,owned)


def _track(c,action,parameters):
    # References are supplied by the original caller at compilation/binding.
    return {'track_id':c.track_id,'element_id':c.element_id,'action':action,'start_ms':c.start_ms,'end_ms':c.end_ms,'parameters':parameters}


def lowered_track(track):
    c=registered_contract(track);tid,eid,action,start,end,p,src,rsn=normalize_track(track)
    if action=='crossfade_states':
        params={k:v for k,v in c.parameters.items() if k!='schema_version'};params.update(schema_version=SPECIAL_SCHEMA,mode='typeset-state-crossfade');name='morph'
    elif action in {'static_trace','progressive_static_trace'}:
        params={k:v for k,v in c.parameters.items() if k not in {'schema_version','milestones'}};params['schema_version']=SPECIAL_SCHEMA;name='trace'
    else:return None
    return {**_track(c,name,params),'source_refs':list(src),'reasoning_refs':list(rsn)}


def action_progress(c,frame,fps):
    from .animation_behavior import frame_window
    if type(frame)is not int or frame<0:fail('ANIMATION_FRAME_INVALID','nonnegative frame required')
    a,b=frame_window(c,fps)
    if c.action=='static_trace':return 1.
    if c.action=='progressive_static_trace':
        return next((row['progress'] for row in reversed(c.parameters['milestones']) if frame>=int(math.floor(row['at_ms']*fps/1000+.5))),0.)
    u=max(0.,min(1.,(frame-a)/(b-a)))
    return u*u*(3-2*u) if c.easing=='smoothstep' else u


def action_model_time(c,frame,fps):
    action_progress(c,frame,fps)
    if c.action=='simulation_state':return c.parameters['from_time_s']+(c.parameters['to_time_s']-c.parameters['from_time_s'])*action_progress(c,frame,fps)
    if c.action=='state_snapshots':return next((r['time_s'] for r in reversed(c.parameters['snapshots']) if frame>=int(math.floor(r['at_ms']*fps/1000+.5))),c.parameters['snapshots'][0]['time_s'])
    fail('REGISTERED_ACTION_TYPE','not a model-state action')


def registered_motion_state(c,frame,fps):
    action_progress(c,frame,fps)
    if c.action=='static_focus':
        p=c.parameters;pose=p['pose'];z=pose['zoom']
        return {'scale':z,'translate_x':(p['viewport']['width']/2-pose['focus_x'])*z,'translate_y':(p['viewport']['height']/2-pose['focus_y'])*z}
    return {}


def validate_registered_binding(track,element,target,duration_ms):
    from .animation_behavior import frame_window
    c=registered_contract(track);f=normalize_track(track)
    if element['element_id']!=c.element_id:fail('REGISTERED_TARGET_MISMATCH','source target differs')
    _refs(f[6],element['source_refs'],'track source_refs');_refs(f[7],element['reasoning_refs'],'track reasoning_refs')
    a,b=frame_window(c,target.fps)
    if b>=(duration_ms*target.fps+999)//1000:fail('ANIMATION_EXCEEDS_SCENE','final sample outside scene')
    p=c.parameters
    if c.action in {'static_focus','path_endpoints_with_progress_marker'}:
        box=element.get('normalized_box')
        if not isinstance(box,Mapping) or any(not math.isclose(p['viewport'][axis],box[axis]*getattr(target,axis),abs_tol=1e-6,rel_tol=0) for axis in ('width','height')):fail('CAMERA_VIEWPORT_MISMATCH','actual source box differs from action viewport')
    if c.action in {'static_trace','progressive_static_trace','crossfade_states'}:
        from .specialized_motion import specialized_contract,validate_binding,graph_contract
        base=lowered_track(track);bc=specialized_contract(base)
        validate_binding(bc,element,target,duration_ms,f[6],f[7])
        if c.action=='progressive_static_trace':
            g=graph_contract(element);s=next(s for s in g['series'] if s['series_id']==p['series_id'])
            accum=0.;required=[0.]
            for l in s['lengths']:accum+=l;required.append(accum/s['total_length'])
            values=[r['progress'] for r in p['milestones']]
            if any(not any(abs(x-y)<1e-9 for y in values) for x in required):fail('TRACE_VERTEX_MILESTONE_MISSING','every source polyline vertex must be observed')
    if c.action in {'simulation_state','state_snapshots'}:
        from .simulation_models import simulation_contract
        if element['element_type']!='simulation':fail('SIMULATION_ACTION_TARGET','analytic simulation required')
        sim=simulation_contract(element['props'])
        if sim.model_ref!=p['model_ref']:fail('SIMULATION_ACTION_MODEL_MISMATCH','different source model')
        values=[p['from_time_s'],p['to_time_s']] if c.action=='simulation_state' else [r['time_s'] for r in p['snapshots']]
        if values[0]!=0 or values[-1]!=sim.duration_ms/1000:fail('SIMULATION_ACTION_ENDPOINTS','source model initial/final states must be retained')
        if c.action=='simulation_state':
            effective_rate=(values[-1]-values[0])/((b-a)/target.fps)
            omega=dict(sim.parameters).get('omega',0)
            if omega/(2*math.pi)*effective_rate*8>target.fps:fail('SIMULATION_FRAME_ALIASING','time-remapping undersamples oscillator')
    for key in ('milestones','snapshots'):
        if key not in p:continue
        sample=[int(math.floor(row['at_ms']*target.fps/1000+.5)) for row in p[key]]
        if sample[0]!=a or sample[-1]>b or len(set(sample))!=len(sample):fail('REGISTERED_STATES_UNSAMPLED','observations collapse or fall outside rendered frame window')
    if c.action=='path_endpoints_with_progress_marker':
        from .shape_compiler import shape_geometry
        if element['element_type']!='shape' or element['props'].get('shape_kind') not in {'line','polyline'}:fail('PATH_SOURCE_TARGET','line/polyline shape required')
        g=shape_geometry(element['props']);source=element['props']['geometry']
        points=source.get('points',[[source.get('x1'),source.get('y1')],[source.get('x2'),source.get('y2')]])
        if [list(x) for x in points]!=p['points'] or g['view_box']!=[0,0,p['viewport']['width'],p['viewport']['height']]:fail('PATH_SOURCE_GEOMETRY_MISMATCH','endpoint display must retain exact source path')
    return {'track_id':c.track_id,'element_id':c.element_id,'action':c.action,'schema_version':SCHEMA,'source_refs':list(f[6]),'reasoning_refs':list(f[7]),'lowered_action':(lowered_track(track) or {}).get('action'),'sample_start_frame':a,'sample_end_frame':b,'learning_equivalence_verified':False,'accepted':False}


def registered_actions_for_kind(kind):
    """Name-level capability declarations; parameter/combination gates still apply."""
    result=set() if kind=='highlight' else {'static_focus'}
    result |= {'equation':{'crossfade_states'},'graph':{'static_trace','progressive_static_trace'},
               'simulation':{'simulation_state','state_snapshots'},'shape':{'path_endpoints_with_progress_marker'}}.get(kind,set())
    return result
