"""H9-002: explicit node layout and directed/undirected edges, no invented facts."""
from .element_compiler_common import require_type,component_name,compile_result,jsx
from .primitive_geometry import *
from .hardening_contracts import literal_js_string


def diagram_geometry(props,source_refs,reasoning_refs):
    fields(props,{'diagram_kind','nodes','edges','view_box'})
    kind=text_value(props['diagram_kind'],'diagram_kind',maximum=128);box=viewbox(props['view_box'])
    result=[];indexed={}
    def refs(row):
        for name,allowed in [('source_refs',source_refs),('reasoning_refs',reasoning_refs)]:
            vals=row.get(name,list(allowed))
            if not isinstance(vals,(list,tuple)) or not vals or any(not isinstance(v,str) for v in vals) or not set(vals)<=set(allowed) or len(set(vals))!=len(vals):reject('DIAGRAM_PROVENANCE_UNBOUND',name)
    for n in sequence(props['nodes'],'nodes',maximum=128):
        fields(n,{'node_id','label','x','y','width','height'},{'fill','stroke','font_size','source_refs','reasoning_refs'})
        nid=text_value(n['node_id'],'node_id',maximum=128)
        if nid in indexed:reject('DIAGRAM_DUPLICATE_NODE',nid)
        refs(n);q={'node_id':nid,'label':text_value(n['label'],'label',maximum=4000)}
        q.update({k:num(n[k],k,.01 if k in {'width','height'} else -1e6) for k in ('x','y','width','height')})
        inside([[q['x'],q['y']],[q['x']+q['width'],q['y']+q['height']]],box,1)
        q.update(fill=color(n.get('fill','white')),stroke=color(n.get('stroke','currentColor')),font_size=num(n.get('font_size',16),'font_size',8,200))
        if q['fill'] in {'transparent','none'}:reject('DIAGRAM_NODE_FILL_REQUIRED','readable bounded node backing required')
        q['source_refs']=list(n.get('source_refs',source_refs));q['reasoning_refs']=list(n.get('reasoning_refs',reasoning_refs))
        for old in result:
            if min(q['x']+q['width'],old['x']+old['width'])>max(q['x'],old['x']) and min(q['y']+q['height'],old['y']+old['height'])>max(q['y'],old['y']):reject('DIAGRAM_NODE_OVERLAP','explicit layout overlaps nodes')
        indexed[nid]=q;result.append(q)
    edges=[];seen=set()
    for i,e in enumerate(sequence(props['edges'],'edges',minimum=0,maximum=256)):
        fields(e,{'from','to','directed'},{'edge_id','label','label_position','source_refs','reasoning_refs'})
        if e['from'] not in indexed or e['to'] not in indexed:reject('DIAGRAM_EDGE_TARGET_MISSING','edge endpoint missing')
        if e['from']==e['to']:reject('DIAGRAM_SELF_LOOP_UNSUPPORTED','explicit loop routing is not supported')
        if type(e['directed'])is not bool:reject('DIAGRAM_EDGE_DIRECTION_REQUIRED','boolean directed required')
        key=(e['from'],e['to']) if e['directed'] else tuple(sorted([e['from'],e['to']]))
        key=(e['directed'],*key)
        if key in seen:reject('DIAGRAM_DUPLICATE_EDGE','duplicate visual relation')
        seen.add(key);refs(e)
        a,b=indexed[e['from']],indexed[e['to']]
        start=rect_boundary(a,[b['x']+b['width']/2,b['y']+b['height']/2]);end=rect_boundary(b,[a['x']+a['width']/2,a['y']+a['height']/2])
        length=math.dist(start,end)
        if length<8:reject('DIAGRAM_EDGE_TOO_SHORT','insufficient room for directed edge')
        # An unrelated node may not hide a declared relation.
        for n in result:
            if n['node_id'] in {e['from'],e['to']}:continue
            lo,hi=0.,1.;dx,dy=end[0]-start[0],end[1]-start[1]
            for p,q in [(-dx,start[0]-n['x']),(dx,n['x']+n['width']-start[0]),(-dy,start[1]-n['y']),(dy,n['y']+n['height']-start[1])]:
                if p==0:
                    if q<0:lo,hi=1.,0.;break
                elif p<0:lo=max(lo,q/p)
                else:hi=min(hi,q/p)
            if lo<hi and hi>0 and lo<1:reject('DIAGRAM_EDGE_OCCLUDED','edge intersects an unrelated node')
        label=text_value(e.get('label',''),'edge label',maximum=2000,nonempty=False)
        if bool(label)!=('label_position' in e):reject('DIAGRAM_LABEL_POSITION_REQUIRED','nonempty edge label needs explicit position')
        lp=point(e['label_position']) if label else [0,0]
        if label:inside([lp],box)
        dx,dy=(end[0]-start[0])/length,(end[1]-start[1])/length;head=min(8.,length/3)
        arrow=[[end[0]-head*dx+head*.45*dy,end[1]-head*dy-head*.45*dx],end,[end[0]-head*dx-head*.45*dy,end[1]-head*dy+head*.45*dx]] if e['directed'] else []
        edges.append({'edge_id':text_value(e.get('edge_id','edge:'+str(i)),'edge_id',maximum=128),'from':e['from'],'to':e['to'],'start':start,'end':end,'arrow':arrow,'directed':e['directed'],'label':label,'label_position':lp,'source_refs':list(e.get('source_refs',source_refs)),'reasoning_refs':list(e.get('reasoning_refs',reasoning_refs))})
    if len({e['edge_id'] for e in edges})!=len(edges):reject('DIAGRAM_DUPLICATE_EDGE_ID','edge_id repeated')
    return {'kind':kind,'view_box':box,'nodes':result,'edges':edges}


def compile_diagram_element(element):
    eid,p,acc,src,rsn=require_type(element,'diagram');g=diagram_geometry(p,src,rsn)
    alt=text_value(acc.get('alt'),'diagram alt',maximum=4000);name=component_name('Diagram',eid)
    source=f'''import React from "react";
type DiagramNode = {{node_id:string;label:string;x:number;y:number;width:number;height:number;font_size:number;fill:string;stroke:string;source_refs:string[];reasoning_refs:string[]}};
type DiagramEdge = {{edge_id:string;from:string;to:string;directed:boolean;start:number[];end:number[];arrow:number[][];label:string;label_position:number[];source_refs:string[];reasoning_refs:string[]}};
const geometry: {{kind:string;view_box:number[];nodes:DiagramNode[];edges:DiagramEdge[]}} = {jsx(g)};
export const {name}: React.FC = () => <svg data-bie-element-id={{{jsx(eid)}}} data-bie-diagram-kind={{{jsx(g['kind'])}}}
 role="img" aria-label={{{literal_js_string(alt)}}} viewBox={{geometry.view_box.join(" ")}} style={{{{width:"100%",height:"100%",display:"block"}}}}>
 <title>{{{literal_js_string(alt)}}}</title>
 {{geometry.edges.map(e=><g key={{e.edge_id}} data-bie-edge-id={{e.edge_id}} data-bie-from={{e.from}} data-bie-to={{e.to}}>
  <line x1={{e.start[0]}} y1={{e.start[1]}} x2={{e.end[0]}} y2={{e.end[1]}} stroke="currentColor" strokeWidth={{2}} />
  {{e.directed?<polyline points={{e.arrow.map(p=>p.join(",")).join(" ")}} fill="none" stroke="currentColor" strokeWidth={{2}}/>:null}}
  {{e.label?<text x={{e.label_position[0]}} y={{e.label_position[1]}} textAnchor="middle" fontSize={{14}}>{{e.label}}</text>:null}}
 </g>)}}
 {{geometry.nodes.map(n=><g key={{n.node_id}} data-bie-node-id={{n.node_id}}>
  <rect x={{n.x}} y={{n.y}} width={{n.width}} height={{n.height}} fill={{n.fill}} stroke={{n.stroke}} strokeWidth={{2}}/>
  <text x={{n.x+n.width/2}} y={{n.y+n.height/2}} textAnchor="middle" dominantBaseline="central" fontSize={{n.font_size}} fill="currentColor">{{n.label}}</text>
 </g>)}}
</svg>;
'''
    return compile_result(eid,'diagram',name,source)
