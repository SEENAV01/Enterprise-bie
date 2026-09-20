"""H9 actual emitted registered-action behavior, not metadata-only aliases."""
from .animation_compiler_common import compile_result,component_name,jsx,normalize_track
from .registered_actions import registered_contract,lowered_track,action_progress,fail
from .specialized_camera import progress_source


def registered_progress_source(c):
    guard=f'''if (!Number.isInteger(frame)||frame<0||!Number.isInteger(fps)||fps<1||fps>240) throw new Error("ANIMATION_FRAME_INVALID");
 const first=Math.round({c.start_ms}*fps/1000);const last=Math.round({c.end_ms}*fps/1000)-1;
 if(last<=first) throw new Error("ANIMATION_FRAME_RANGE_COLLAPSES");'''
    if c.action=='static_trace':return guard+'\n const progress: number = Math.min(1,1);'
    if c.action=='progressive_static_trace':return guard+f'''\n const milestones={jsx(c.parameters['milestones'])};
 const progress=[...milestones].reverse().find(m=>frame>=Math.round(m.at_ms*fps/1000))?.progress ?? 0;'''
    return progress_source(c)


def compile_registered_track(track,element,*,typesetter=None):
    c=registered_contract(track);p=c.parameters;f=normalize_track(track)
    if element is None or element.get('element_id')!=c.element_id:fail('REGISTERED_TARGET_REQUIRED','exact source element required')
    from .specialized_motion import _refs
    _refs(f[6],element['source_refs'],'track source_refs');_refs(f[7],element['reasoning_refs'],'track reasoning_refs')
    lower=lowered_track(track)
    if lower:
        from .specialized_dispatch import compile_specialized_track
        from .specialized_motion import specialized_contract
        emitted=compile_specialized_track(lower,element,typesetter=typesetter)
        source=emitted.source_text
        if c.action in {'static_trace','progressive_static_trace'}:
            old=progress_source(specialized_contract(lower))
            if source.count(old)!=1:fail('REGISTERED_LOWERING_DRIFT','known emitter progress contract changed')
            source=source.replace(old,registered_progress_source(c))
        source=source.replace('data-bie-action="'+lower['action']+'"','data-bie-action="'+c.action+'"')
        return compile_result(c.track_id,c.action,emitted.source_path,source)
    name=component_name('Registered',c.track_id)
    if c.action=='static_focus':
        pose=p['pose'];z=pose['zoom'];tx=(p['viewport']['width']/2-pose['focus_x'])*z;ty=(p['viewport']['height']/2-pose['focus_y'])*z
        source=f'''import React from "react";
export const evaluateStaticFocus=()=>({{scale:{z},translate_x:{tx},translate_y:{ty}}});
export const {name}: React.FC<React.PropsWithChildren> = ({{children}}) => <div data-bie-track-id={{{jsx(c.track_id)}}}
 data-bie-element-id={{{jsx(c.element_id)}}} data-bie-action="static_focus" style={{{{width:"100%",height:"100%",transformOrigin:"50% 50%",scale:{z},translate:{jsx(str(tx)+'px '+str(ty)+'px')}}}}}>{{children}}</div>;
'''
    elif c.action in {'simulation_state','state_snapshots'}:
        from .simulation_compiler import compile_simulation_element
        from .simulation_models import simulation_contract
        if element['element_type']!='simulation':fail('SIMULATION_ACTION_TARGET','simulation source required')
        sim=simulation_contract(element['props'])
        if p['model_ref']!=sim.model_ref:fail('SIMULATION_ACTION_MODEL_MISMATCH','wrong source model')
        emitted=compile_simulation_element(element);source=emitted.source_text
        prefix=f'''export const evaluateRegisteredTime=(frame:number,fps:number):number=>{{
 {registered_progress_source(c)}
'''
        if c.action=='simulation_state':prefix+=f" return {p['from_time_s']}+({p['to_time_s']}-{p['from_time_s']})*progress;\n}};\n"
        else:prefix+=f" const snapshots={jsx(p['snapshots'])};\n return [...snapshots].reverse().find(s=>frame>=Math.round(s.at_ms*fps/1000))?.time_s ?? snapshots[0].time_s;\n}};\n"
        old='const time = Math.min(contract.duration_ms/1000, Math.max(0, frame/fps-contract.start_ms/1000));'
        if source.count(old)!=1:fail('REGISTERED_LOWERING_DRIFT','source simulation clock changed')
        source=source.replace(old,'const time = evaluateRegisteredTime(frame,fps);')
        source=source.replace('export const '+emitted.component_name+': React.FC = () =>',prefix+'export const '+name+': React.FC<React.PropsWithChildren> = () =>')
        source=source.replace('<svg viewBox=',f'<svg data-bie-action="{c.action}" data-bie-track-id={{{jsx(c.track_id)}}} viewBox=',1)
    else:
        v=p['viewport'];points=p['points']
        source=f'''import React from "react";
import {{useCurrentFrame,useVideoConfig}} from "remotion";
const points={jsx(points)};
export const evaluateEndpointProgress=(frame:number,fps:number)=>{{ {registered_progress_source(c)} return progress; }};
export const {name}: React.FC<React.PropsWithChildren> = ({{children}}) => {{
 const frame=useCurrentFrame();const {{fps}}=useVideoConfig();const progress=evaluateEndpointProgress(frame,fps);
 return <div data-bie-action="path_endpoints_with_progress_marker" data-bie-track-id={{{jsx(c.track_id)}}}
 style={{{{width:"100%",height:"100%",position:"relative"}}}}>
 {{children}}
 <svg role="img" aria-label="Source path endpoints and stationary progress" viewBox={{{jsx('0 0 '+str(v['width'])+' '+str(v['height']))}}}
 style={{{{position:"absolute",inset:0,width:"100%",height:"100%",display:"block",pointerEvents:"none"}}}}>
 <circle data-bie-path-endpoint="start" cx={{points[0][0]}} cy={{points[0][1]}} r={{4}} fill="currentColor"/>
 <circle data-bie-path-endpoint="end" cx={{points[points.length-1][0]}} cy={{points[points.length-1][1]}} r={{4}} fill="currentColor"/>
 <text x={{points[0][0]}} y={{points[0][1]-10}} textAnchor="middle" fontSize={{14}}>{{{jsx(p['start_label'])}}}</text>
 <text x={{points[points.length-1][0]}} y={{points[points.length-1][1]-10}} textAnchor="middle" fontSize={{14}}>{{{jsx(p['end_label'])}}}</text>
 <text data-bie-progress-marker="stationary" x={{{v['width']/2}}} y={{{v['height']-12}}} textAnchor="middle" fontSize={{16}}>{{"Progress "+Math.round(progress*100)+"%"}}</text>
 </svg></div>;
}};
'''
    return compile_result(c.track_id,c.action,'src/animations/'+name+'.tsx',source)
