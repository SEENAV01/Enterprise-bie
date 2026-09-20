"""H9 source-faithful finite SVG geometry. No code/URL/style-string execution."""
from __future__ import annotations
from collections.abc import Mapping
import math,re
from .hardening_contracts import finite_number,text_value,known_properties,sequence,reject


def fields(value,required,optional=()):
    if not isinstance(value,Mapping) or not set(required)<=set(value) or set(value)-set(required)-set(optional):
        reject('PRIMITIVE_FIELDS_INVALID','expected '+','.join(sorted(required))+'; no ignored properties')


def num(value,name,low=-1e6,high=1e6):
    n=finite_number(value,name)
    if not low<=n<=high:reject('PRIMITIVE_NUMBER_BOUNDS',name+' outside bounds')
    return n


def viewbox(value):
    v=sequence(value,'view_box',minimum=4,maximum=4)
    x,y=num(v[0],'view x'),num(v[1],'view y')
    w,h=num(v[2],'view width',.01,100000),num(v[3],'view height',.01,100000)
    return [x,y,w,h]


def color(value,name='color'):
    if not isinstance(value,str) or not (re.fullmatch(r'(?:#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6})',value) or value in {'none','currentColor','black','white','red','green','blue','yellow','orange','purple','gray','transparent'}):
        reject('PRIMITIVE_COLOR_UNSAFE',name+' must be a named or RGB color; use explicit opacity, never CSS/URL markup')
    return value


def style(value):
    fields(value,set(),{'fill','stroke','stroke_width','opacity'})
    s={'fill':color(value.get('fill','none')),'stroke':color(value.get('stroke','currentColor')),
       'strokeWidth':num(value.get('stroke_width',2),'stroke width',.1,100),
       'opacity':num(value.get('opacity',1),'opacity',0,1)}
    if s['opacity']==0 or s['fill'] in {'none','transparent'} and s['stroke'] in {'none','transparent'}:
        reject('PRIMITIVE_INVISIBLE','required primitive may not be silently invisible')
    return s


def point(value):
    return [num(v,'point') for v in sequence(value,'point',minimum=2,maximum=2)]


def inside(points,box,margin=0):
    x,y,w,h=box
    for a,b in points:
        if a-margin<x-1e-8 or b-margin<y-1e-8 or a+margin>x+w+1e-8 or b+margin>y+h+1e-8:
            reject('PRIMITIVE_OUTSIDE_VIEWBOX','source geometry/stroke exceeds its declared viewport')


def area(points):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))/2


def simple_polygon(points):
    def orient(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def on(a,b,c):return abs(orient(a,b,c))<1e-9 and min(a[0],b[0])-1e-9<=c[0]<=max(a[0],b[0])+1e-9 and min(a[1],b[1])-1e-9<=c[1]<=max(a[1],b[1])+1e-9
    for i,(a,b) in enumerate(zip(points,points[1:]+points[:1])):
        for j,(c,d) in enumerate(zip(points,points[1:]+points[:1])):
            if j<=i or j==i+1 or (i==0 and j==len(points)-1):continue
            if orient(a,b,c)*orient(a,b,d)<0 and orient(c,d,a)*orient(c,d,b)<0 or any((on(a,b,c),on(a,b,d),on(c,d,a),on(c,d,b))):
                reject('PRIMITIVE_SELF_INTERSECTION','polygon must be simple and non-self-touching')
    if abs(area(points))<1e-8:reject('PRIMITIVE_DEGENERATE','zero-area polygon')


def rect_boundary(node,toward):
    cx=node['x']+node['width']/2;cy=node['y']+node['height']/2
    dx,dy=toward[0]-cx,toward[1]-cy
    if abs(dx)+abs(dy)<1e-9:reject('DIAGRAM_EDGE_DEGENERATE','coincident node centres')
    k=min(node['width']/2/abs(dx) if dx else math.inf,node['height']/2/abs(dy) if dy else math.inf)
    return [cx+dx*k,cy+dy*k]
