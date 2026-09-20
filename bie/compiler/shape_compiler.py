"""H9-001: the seven existing Shape DSL kinds become safe, bounded SVG."""
from .element_compiler_common import require_type,component_name,compile_result,jsx
from .primitive_geometry import *
from .hardening_contracts import literal_js_string

KINDS=frozenset({'rectangle','circle','ellipse','line','polygon','polyline','arrow'})

def shape_geometry(props):
    fields(props,{'shape_kind','geometry'},{'style'})
    kind=props['shape_kind']
    if not isinstance(kind,str) or kind not in KINDS:reject('SHAPE_KIND_UNSUPPORTED','unknown original shape kind')
    g=props['geometry'];s=style(props.get('style',{}))
    keys={'rectangle':{'x','y','width','height'},'circle':{'cx','cy','r'},'ellipse':{'cx','cy','rx','ry'},
          'line':{'x1','y1','x2','y2'},'arrow':{'x1','y1','x2','y2','head_length'},'polygon':{'points'},'polyline':{'points'}}[kind]
    fields(g,keys|{'view_box'})
    box=viewbox(g['view_box']);attrs={};extra=[]
    if kind in {'polygon','polyline'}:
        pts=[point(p) for p in sequence(g['points'],'points',minimum=3 if kind=='polygon' else 2,maximum=256)]
        if kind=='polygon' and pts[0]==pts[-1]:pts=pts[:-1]
        if len(pts)<(3 if kind=='polygon' else 2) or any(math.dist(a,b)<1e-8 for a,b in zip(pts,pts[1:])):reject('PRIMITIVE_DEGENERATE','distinct consecutive vertices required')
        if kind=='polygon':simple_polygon(pts)
        attrs={'points':' '.join(','.join(map(str,p)) for p in pts)};bounds=pts;tag=kind
    elif kind=='rectangle':
        attrs={k:num(g[k],k,.001 if k in {'width','height'} else -1e6) for k in keys}
        bounds=[[attrs['x'],attrs['y']],[attrs['x']+attrs['width'],attrs['y']+attrs['height']]];tag='rect'
    elif kind in {'circle','ellipse'}:
        attrs={k:num(g[k],k,.001 if k in {'r','rx','ry'} else -1e6) for k in keys}
        rx=attrs.get('r',attrs.get('rx'));ry=attrs.get('r',attrs.get('ry'))
        bounds=[[attrs['cx']-rx,attrs['cy']-ry],[attrs['cx']+rx,attrs['cy']+ry]];tag=kind
    else:
        attrs={k:num(g[k],k) for k in {'x1','y1','x2','y2'}}
        a=[attrs['x1'],attrs['y1']];b=[attrs['x2'],attrs['y2']];length=math.dist(a,b)
        if length<1e-8:reject('PRIMITIVE_DEGENERATE','line endpoints coincide')
        bounds=[a,b];tag='line'
        if kind=='arrow':
            head=num(g['head_length'],'head length',.1,length/2)
            dx,dy=(b[0]-a[0])/length,(b[1]-a[1])/length
            h=[[b[0]-head*dx+head*.5*dy,b[1]-head*dy-head*.5*dx],b,[b[0]-head*dx-head*.5*dy,b[1]-head*dy+head*.5*dx]]
            extra=h;bounds+=h
    if kind in {'line','polyline','arrow'} and s['stroke'] in {'none','transparent'}:reject('PRIMITIVE_INVISIBLE','open shape requires stroke')
    inside(bounds,box,s['strokeWidth']/2 if s['stroke'] not in {'none','transparent'} else 0)
    return {'kind':kind,'tag':tag,'attrs':attrs,'style':s,'view_box':box,'arrowhead':extra}


def compile_shape_element(element):
    eid,props,acc,src,rsn=require_type(element,'shape');g=shape_geometry(props)
    alt=text_value(acc.get('alt'),'shape alt',maximum=2000)
    name=component_name('Shape',eid)
    source=f'''import React from "react";
type ShapeGeometry = {{kind:string;tag:string;attrs:Record<string,number|string>;style:{{fill:string;stroke:string;strokeWidth:number;opacity:number}};view_box:number[];arrowhead:number[][]}};
const geometry: ShapeGeometry = {jsx(g)};
export const {name}: React.FC = () => <svg data-bie-element-id={{{jsx(eid)}}} data-bie-shape-kind={{{jsx(g['kind'])}}}
  role="img" aria-label={{{literal_js_string(alt)}}} viewBox={{geometry.view_box.join(" ")}}
  style={{{{width:"100%",height:"100%",display:"block"}}}}>
  <title>{{{literal_js_string(alt)}}}</title>
  {{React.createElement(geometry.tag, {{...geometry.attrs,...geometry.style,strokeLinejoin:"round"}})}}
  {{geometry.arrowhead.length>0 ? <polyline points={{geometry.arrowhead.map(p=>p.join(",")).join(" ")}}
    fill="none" stroke={{geometry.style.stroke}} strokeWidth={{geometry.style.strokeWidth}} opacity={{geometry.style.opacity}} strokeLinejoin="round"/> : null}}
</svg>;
'''
    return compile_result(eid,'shape',name,source)
