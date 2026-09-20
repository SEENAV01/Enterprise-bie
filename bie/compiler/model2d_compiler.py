from .element_compiler_common import *
from .model2d_geometry import model2d_geometry

def compile_model2d_element(element):
    eid, props, acc, src, rsn = require_type(element, "model2d")
    geometry = model2d_geometry(props)
    comp = component_name("Model2D", eid)
    source = f'''import React from "react";
const vertices: ReadonlyArray<readonly [number, number]> = {jsx(geometry["vertices"])};
const edges: ReadonlyArray<readonly [number, number]> = {jsx(geometry["edges"])};
export const {comp}: React.FC = () => (
  <svg viewBox="0 0 400 300" width="100%" height="100%" role="img" aria-label={{{jsx(acc.get("alt") or "2D model")}}}>
    {{edges.map(([a,b], index) => <line key={{index}} x1={{8 + vertices[a][0] * 384}} y1={{8 + vertices[a][1] * 284}} x2={{8 + vertices[b][0] * 384}} y2={{8 + vertices[b][1] * 284}} stroke="currentColor" strokeWidth={{2}} />)}}
    {{vertices.map(([x,y], index) => <circle key={{index}} cx={{8 + x * 384}} cy={{8 + y * 284}} r={{3}} fill="currentColor"><title>{{"vertex " + index}}</title></circle>)}}
  </svg>
);
'''
    return compile_result(eid, "model2d", comp, source)
