"""H9-003: source-target-bound highlight geometry, recomputed for every frame."""
from __future__ import annotations
from .element_compiler_common import require_type,component_name,compile_result,jsx
from .primitive_geometry import *
from .hardening_contracts import literal_js_string


def highlight_geometry(element,scene,target):
    eid,p,acc,src,rsn=require_type(element,'highlight')
    fields(p,{'target_element_ids','mode'},{'color','stroke_width','fill_opacity'})
    ids=sequence(p['target_element_ids'],'highlight targets',maximum=32)
    if any(not isinstance(v,str) or not v for v in ids) or len(set(ids))!=len(ids) or eid in ids:reject('HIGHLIGHT_TARGET_INVALID','unique non-self targets required')
    mode=p['mode']
    if mode not in {'outline','fill','spotlight','underline'}:reject('HIGHLIGHT_MODE_UNSUPPORTED','unknown original highlight mode')
    if scene is None or target is None:reject('HIGHLIGHT_SCENE_CONTEXT_REQUIRED','actual scene geometry and target are required')
    indexed={e['element_id']:e for e in scene['elements']}
    if eid not in indexed or indexed[eid]!=element:reject('HIGHLIGHT_SOURCE_CONTEXT_MISMATCH','exact highlight element must belong to scene')
    for tid in ids:
        if tid not in indexed or indexed[tid]['element_type']=='highlight':reject('HIGHLIGHT_TARGET_MISSING','missing or recursive highlight target')
        for key in ('source_refs','reasoning_refs'):
            if not set(indexed[tid].get(key,[]))<=set(element.get(key,[])):reject('HIGHLIGHT_PROVENANCE_UNBOUND','highlight must carry target '+key)
    from .frame_layout import layer_box,iter_frame_layers,dimensions
    from .frame_runtime_contract import plan_frame_runtime
    from .frame_state_consumer import runtime_at
    from .qa_common import digest
    count=dimensions(scene,target)
    if count*len(ids)>12000:reject('HIGHLIGHT_FRAME_BUDGET','no sampled target following')
    if any(t['element_id']==eid for t in scene.get('tracks',[])):reject('HIGHLIGHT_OWN_TRANSFORM_UNSUPPORTED','highlight follows its targets; separate highlight tracks need an explicit composition rule')
    x,y,w,h=layer_box(element,target);rows=[];plan=plan_frame_runtime(scene,target)
    stroke=num(p.get('stroke_width',2),'highlight stroke',.1,20);shade=color(p.get('color','orange'))
    if shade in {'none','transparent'}:reject('PRIMITIVE_INVISIBLE','highlight color invisible')
    opacity=num(p.get('fill_opacity',.15),'fill opacity',.01,.5)
    if mode in {'outline','underline'} and 'fill_opacity' in p:reject('UNCONSUMED_ELEMENT_PROPERTY','fill_opacity does not apply to outline/underline')
    for f,layers in enumerate(iter_frame_layers(scene,target)):
        state=runtime_at(plan,f) if plan is not None else None;frame=[]
        for tid in ids:
            r=next(row for row in layers if row['element_id']==tid)
            pts=[[a-x,b-y] for a,b in r['polygon']]
            inside(pts,[0,0,w,h],stroke/2)
            binding=state['targets'].get(tid,{}) if state else {}
            visible=r['visible_conservative'] and binding.get('visible',True) and binding.get('opacity',1)>0
            frame.append({'target_id':tid,'points':pts,'visible':visible})
        rows.append(frame)
    return {'mode':mode,'view_box':[0,0,w,h],'frames':rows,'fps':target.fps,'stroke':stroke,'color':shade,'opacity':opacity,'source_scene_sha256':digest(scene)}


def compile_highlight_element(element,*,scene=None,target=None):
    g=highlight_geometry(element,scene,target);eid,p,acc,src,rsn=require_type(element,'highlight')
    alt=text_value(acc.get('alt'),'highlight alt',maximum=4000);name=component_name('Highlight',eid)
    maskid='mask_'+name
    source=f'''import React from "react";
import {{useCurrentFrame,useVideoConfig}} from "remotion";
const geometry = {jsx(g)};
export const evaluateHighlight = (frame:number,fps:number) => {{
 if (!Number.isInteger(frame)||frame<0||frame>=geometry.frames.length||fps!==geometry.fps) throw new Error("HIGHLIGHT_FRAME_TARGET_MISMATCH");
 return geometry.frames[frame];
}};
export const {name}: React.FC = () => {{
 const frame=useCurrentFrame();const {{fps}}=useVideoConfig();const regions=evaluateHighlight(frame,fps).filter(r=>r.visible);
 return <svg data-bie-element-id={{{jsx(eid)}}} data-bie-highlight-mode={{geometry.mode}} role="img" aria-label={{{literal_js_string(alt)}}}
 viewBox={{geometry.view_box.join(" ")}} style={{{{width:"100%",height:"100%",display:"block",pointerEvents:"none"}}}}>
 <title>{{{literal_js_string(alt)}}}</title>
 {{geometry.mode==="spotlight" && regions.length>0 ? <><defs><mask id={{{jsx(maskid)}}} maskUnits="userSpaceOnUse" x={{0}} y={{0}} width={{geometry.view_box[2]}} height={{geometry.view_box[3]}}>
 <rect width={{geometry.view_box[2]}} height={{geometry.view_box[3]}} fill="white"/>
 {{regions.map(r=><polygon key={{r.target_id}} points={{r.points.map(p=>p.join(",")).join(" ")}} fill="black"/>)}}
 </mask></defs><rect width={{geometry.view_box[2]}} height={{geometry.view_box[3]}} fill={{geometry.color}} opacity={{geometry.opacity}} mask={{{jsx('url(#'+maskid+')')}}}/></> : null}}
 {{regions.map(r=> geometry.mode==="underline" ? <line key={{r.target_id}} data-bie-highlight-target={{r.target_id}}
 x1={{r.points[3][0]}} y1={{r.points[3][1]}} x2={{r.points[2][0]}} y2={{r.points[2][1]}} stroke={{geometry.color}} strokeWidth={{geometry.stroke}}/>
 : geometry.mode==="spotlight" ? null : <polygon key={{r.target_id}} data-bie-highlight-target={{r.target_id}} points={{r.points.map(p=>p.join(",")).join(" ")}}
 fill={{geometry.mode==="fill"?geometry.color:"none"}} fillOpacity={{geometry.mode==="fill"?geometry.opacity:1}}
 stroke={{geometry.color}} strokeWidth={{geometry.stroke}} strokeLinejoin="round"/>)}}
 </svg>;
}};
'''
    # Avoid JSX Fragment dependency in explicit diagnostic harnesses.
    source=source.replace('<><defs>','<g><defs>').replace('/></> : null','/></g> : null')
    return compile_result(eid,'highlight',name,source)
