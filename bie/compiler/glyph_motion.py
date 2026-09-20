"""Explicit equal-outline glyph correspondence; not algebra or arbitrary path morph.

Source-reviewed pairs move identical glyph outlines using affine placement.
Unmatched glyphs crossfade. All source/destination strokes remain represented.
No inferred mathematical equivalence or semantic symbol matching is claimed.
"""
from __future__ import annotations
import math,re
from .qa_common import digest
from .specialized_motion import fail

IDENTITY=[1.,0.,0.,1.,0.,0.]

def multiply(a,b):
    return [a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5]]

def transform(text):
    if text is None:return IDENTITY[:]
    result=IDENTITY[:];pos=0
    for m in re.finditer(r'(translate|scale|matrix)\s*\(([^)]*)\)',text):
        if text[pos:m.start()].strip():fail('GLYPH_TRANSFORM_UNSUPPORTED','unsupported affine syntax')
        try:v=[float(x) for x in re.split(r'[,\s]+',m[2].strip())]
        except ValueError:fail('GLYPH_TRANSFORM_UNSUPPORTED','non-numeric transform')
        if not all(math.isfinite(x) and abs(x)<1e7 for x in v):fail('GLYPH_TRANSFORM_UNSUPPORTED','non-finite or excessive placement')
        if m[1]=='translate' and len(v) in (1,2):a=[1,0,0,1,v[0],v[1] if len(v)==2 else 0]
        elif m[1]=='scale' and len(v) in (1,2):a=[v[0],0,0,v[-1],0,0]
        elif m[1]=='matrix' and len(v)==6:a=v
        else:fail('GLYPH_TRANSFORM_UNSUPPORTED','affine arity')
        result=multiply(result,a);pos=m.end()
    if text[pos:].strip():fail('GLYPH_TRANSFORM_UNSUPPORTED','unconsumed transform')
    return result

def flatten_layout(layout):
    tree=layout['tree'];defs={}
    def collect(n):
        if isinstance(n,dict):
            if 'id' in n['attrs']:defs[n['attrs']['id']]=n
            for c in n['children']:collect(c)
    collect(tree);out=[]
    def walk(n,parent,style,depth=0):
        if not isinstance(n,dict) or depth>32:fail('GLYPH_TREE_UNSUPPORTED','bounded SVG tree required')
        tag=n['tag'];a=n['attrs'];m=multiply(parent,transform(a.get('transform')));st={**style,**a.get('style',{})}
        for k in ('fill','stroke','strokeWidth'): 
            if k in a:st[k]=a[k]
        if tag=='defs':return
        if tag=='use':
            ref=a.get('href','');node=defs.get(ref[1:]) if ref.startswith('#') else None
            if node is None or node['tag']!='path':fail('GLYPH_REFERENCE_UNSUPPORTED','local path definition required')
            placement=[1,0,0,1,float(a.get('x',0)),float(a.get('y',0))]
            walk(node,multiply(m,placement),st,depth+1);return
        if tag in {'path','rect'}:
            if st.get('fill')=='none' and st.get('stroke','none')=='none':return
            if tag=='path':d=a['d']
            else:
                x,y,w,h=[float(a.get(k,0)) for k in ('x','y','width','height')]
                d=f'M {x} {y} h {w} v {h} h {-w} Z'
            if len(out)>=1024:fail('GLYPH_BUDGET','at most 1024 visible paths per equation')
            shape={'d':d,'style':st};out.append({'shape':shape,'shape_sha256':digest(shape),'matrix':m});return
        if tag not in {'svg','g'}:fail('GLYPH_TREE_UNSUPPORTED',tag)
        for c in n['children']:walk(c,m,st,depth+1)
    walk(tree,IDENTITY,{})
    if not out:fail('GLYPH_EMPTY','no visible glyphs')
    return out

def glyph_layout_plan(layouts,pairs):
    if not isinstance(pairs,(list,tuple)) or len(pairs)!=len(layouts)-1:fail('GLYPH_PAIR_COVERAGE','one reviewed map per state transition')
    sizes=[l['view_box'] for l in layouts];width=max(x[2] for x in sizes);height=max(x[3] for x in sizes)
    atoms=[]
    for l,box in zip(layouts,sizes):
        offset=[1,0,0,1,(width-box[2])/2-box[0],(height-box[3])/2-box[1]]
        atoms.append([{**a,'matrix':multiply(offset,a['matrix'])} for a in flatten_layout(l)])
    checked=[]
    for i,rows in enumerate(pairs):
        if not isinstance(rows,(list,tuple)) or not 1<=len(rows)<=1024:fail('GLYPH_PAIR_INVALID','at least one explicit equal-outline pair per transition')
        src=set();dst=set();result=[]
        for row in rows:
            if not isinstance(row,(list,tuple)) or len(row)!=2 or any(type(v)is not int for v in row):fail('GLYPH_PAIR_INVALID','integer source/destination indices required')
            a,b=row
            if a in src or b in dst or not 0<=a<len(atoms[i]) or not 0<=b<len(atoms[i+1]):fail('GLYPH_PAIR_INVALID','out-of-range or duplicate glyph correspondence')
            if atoms[i][a]['shape_sha256']!=atoms[i+1][b]['shape_sha256']:fail('GLYPH_OUTLINE_MISMATCH','different glyphs cannot be presented as identical moving symbols')
            src.add(a);dst.add(b);result.append([a,b])
        checked.append(result)
    return {'states':atoms,'pairs':checked,'width':width,'height':height,'mode':'glyph-matched-affine','semantic_equivalence':'NOT_VERIFIED','accepted':False}

def compile_glyph_component(c,element,layouts):
    from .animation_compiler_common import component_name,compile_result,jsx
    from .specialized_camera import progress_source
    plan=glyph_layout_plan(layouts,c.parameters['glyph_pairs']);name=component_name('EquationGlyphs',c.track_id)
    src=f'''import React from "react";
import {{useCurrentFrame,useVideoConfig}} from "remotion";
const states={jsx(c.parameters['states'])};
const plan={jsx(plan)};
const sideConditions:string[]={jsx(element['props'].get('side_conditions',[]))};
type Atom={{shape:{{d:string;style:Record<string,unknown>}};shape_sha256:string;matrix:number[]}};
export const evaluateGlyphMorph=(frame:number,fps:number)=>{{
 {progress_source(c)}
 const location=progress*(states.length-1),lower=Math.min(states.length-1,Math.floor(location)),upper=Math.min(states.length-1,lower+1);
 const t=lower===upper?0:Math.max(0,Math.min(1,(location-lower-(1-{c.parameters['transition_fraction']}))/{c.parameters['transition_fraction']}));
 const from=plan.states[lower] as Atom[],to=plan.states[upper] as Atom[];
 const pairs=lower===upper?[]:plan.pairs[lower];
 const usedFrom=new Set(pairs.map(p=>p[0])),usedTo=new Set(pairs.map(p=>p[1]));
 const paths:{{atom:Atom;opacity:number;kind:string}}[]=[];
 for(const [a,b] of pairs){{const x=from[a],y=to[b];paths.push({{atom:{{...x,matrix:x.matrix.map((v,k)=>v+(y.matrix[k]-v)*t)}},opacity:1,kind:"matched"}})}}
 for(let i=0;i<from.length;i++)if(!usedFrom.has(i))paths.push({{atom:from[i],opacity:1-t,kind:"departing"}});
 if(upper!==lower)for(let i=0;i<to.length;i++)if(!usedTo.has(i))paths.push({{atom:to[i],opacity:t,kind:"arriving"}});
 return {{lower,upper,progress:t,paths}};
}};
export const {name}:React.FC<React.PropsWithChildren>=()=>{{const frame=useCurrentFrame(),{{fps}}=useVideoConfig();const state=evaluateGlyphMorph(frame,fps);
return <div data-bie-element-id={{{jsx(c.element_id)}}} data-bie-track-id={{{jsx(c.track_id)}}} data-bie-action="morph" data-bie-transition-mode="glyph-matched-affine" role="math" aria-label={{states[state.lower].alt}} style={{{{width:"100%",height:"100%",display:"flex",flexDirection:"column",minWidth:0}}}}>
<svg viewBox={{`0 0 ${{plan.width}} ${{plan.height}}`}} width="100%" height="100%" preserveAspectRatio="xMidYMid meet" style={{{{flex:1,minHeight:0}}}} data-bie-state-index={{state.lower}} data-bie-state-expression={{states[state.lower].expression}}>
{{state.paths.map((p,i)=><path key={{i}} d={{p.atom.shape.d}} style={{p.atom.shape.style as React.CSSProperties}} opacity={{p.opacity}} transform={{`matrix(${{p.atom.matrix.join(" ")}})`}} data-bie-glyph-kind={{p.kind}}/>)}}
</svg>{{sideConditions.length>0?<div aria-label="side conditions">{{sideConditions.join(", ")}}</div>:null}}</div>;
}};
'''
    return compile_result(c.track_id,c.action,f'src/animations/{name}.tsx',src)
