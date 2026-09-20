from .element_compiler_common import *
from .vector_geometry import vector_geometry

def compile_vector_element(element):
    eid, props, acc, src, rsn = require_type(element, "vector")
    data = vector_geometry(props)
    comp = component_name("Vector", eid)
    source = f'''import React from "react";
const vector = {jsx(data)};
export const {comp}: React.FC = () => (
  <svg viewBox="0 0 400 320" width="100%" height="100%" role="img" aria-label={{{jsx(acc.get("alt") or props.get("label") or "vector")}}}>
    <title>{{"components: " + vector.components.join(", ") + " " + vector.units + "; " + vector.projection_label}}</title>
    <defs><marker id="arrow-{comp}" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="currentColor" /></marker></defs>
    <line x1={{70}} y1={{145}} x2={{330}} y2={{145}} stroke="currentColor" strokeOpacity={{0.3}} />
    <line x1={{200}} y1={{35}} x2={{200}} y2={{255}} stroke="currentColor" strokeOpacity={{0.3}} />
    {{vector.is_zero ? <circle cx={{200}} cy={{145}} r={{4}} fill="currentColor" /> : <line x1={{200}} y1={{145}} x2={{vector.endpoint[0]}} y2={{vector.endpoint[1]}} stroke="currentColor" strokeWidth={{3}} markerEnd="url(#arrow-{comp})" />}}
    <text x={{8}} y={{274}} fontSize={{12}}>{{vector.label + " (" + vector.components.join(", ") + ") " + vector.units}}</text>
    <text x={{8}} y={{291}} fontSize={{11}}>{{vector.projection_label}}</text>
    <text x={{8}} y={{309}} fontSize={{10}}>{{"View scale: " + vector.scale_px_per_unit + " px/unit (individual vector)"}}</text>
  </svg>
);
'''
    return compile_result(eid, "vector", comp, source)
