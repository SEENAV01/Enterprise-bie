"""H5-003. Source-reviewed typeset equation steps, explicitly a crossfade not proof."""
from .animation_compiler_common import component_name, compile_result, jsx
from .specialized_motion import specialized_contract, fail
from .specialized_camera import progress_source
from .equation_typesetting import typeset_latex
from .hardening_contracts import literal_js_string


def compile_specialized_equation(track, element, *, typesetter=None):
    c = specialized_contract(track)
    from .specialized_motion import validate_element_source
    from .animation_compiler_common import normalize_track
    fields = normalize_track(track)
    if element is None: fail('SPECIALIZED_TARGET_REQUIRED', 'source element required')
    validate_element_source(c, element, fields[6], fields[7])
    if c.action != 'morph': fail('SPECIALIZED_ACTION_MISMATCH', 'morph action required')
    if element is None or element.get('element_type') != 'equation':
        fail('EQUATION_MORPH_TARGET_UNSUPPORTED', 'equation element required')
    p = c.parameters; props = element['props']; name = component_name('EquationSteps', c.track_id)
    render = typesetter or typeset_latex
    layouts = [render(s['expression'], element_id=(c.element_id if i == 0 else c.element_id+':'+c.track_id+':state:'+str(i)),
                      font_size=props.get('font_size', 32)) for i, s in enumerate(p['states'])]
    if p['mode']=='glyph-matched-affine':
        from .glyph_motion import compile_glyph_component
        return compile_glyph_component(c,element,layouts)
    source = f'''import React from "react";
import {{useCurrentFrame, useVideoConfig}} from "remotion";
type EquationNode = {{tag:string; attrs:Record<string, unknown>; children:(EquationNode|string)[]}};
const states = {jsx(p['states'])};
const layouts = {jsx(layouts)};
const sideConditions: string[] = {jsx(props.get('side_conditions', []))};
const draw = (node: EquationNode|string, key: string): React.ReactNode => {{
  if (typeof node === "string") return node;
  return React.createElement(node.tag, {{...node.attrs,key}}, ...node.children.map((child,i)=>draw(child,key+"-"+i)));
}};
export const evaluateEquationSteps = (frame: number, fps: number) => {{
  {progress_source(c)}
  const location = progress*(states.length-1);
  const lower = Math.min(states.length-1, Math.floor(location));
  const upper = Math.min(states.length-1, lower+1);
  const upperOpacity = lower===upper ? 0 : Math.max(0,Math.min(1,(location-lower-(1-{p['transition_fraction']}))/{p['transition_fraction']}));
  return {{lower,upper,upperOpacity,lowerOpacity:1-upperOpacity}};
}};
export const {name}: React.FC<React.PropsWithChildren> = () => {{
  const frame = useCurrentFrame(); const {{fps}} = useVideoConfig();
  const state = evaluateEquationSteps(frame,fps);
  return <div data-bie-element-id={{{jsx(c.element_id)}}} data-bie-track-id={{{jsx(c.track_id)}}}
    data-bie-action="morph" data-bie-transition-mode="typeset-state-crossfade" role="math"
    aria-label={{states[state.lower].alt}} style={{{{width:"100%",height:"100%",display:"flex",flexDirection:"column",minWidth:0}}}}>
    <div style={{{{flex:1,minHeight:0,width:"100%",display:"grid"}}}}>
      <div data-bie-state-index={{state.lower}} data-bie-state-expression={{states[state.lower].expression}}
        style={{{{gridArea:"1 / 1",display:"grid",placeItems:"center",minWidth:0,minHeight:0,opacity:state.lowerOpacity}}}}>
        {{draw(layouts[state.lower].tree as EquationNode, "state-"+state.lower)}}
      </div>
      {{state.upperOpacity > 0 && state.upper !== state.lower ? <div data-bie-state-index={{state.upper}}
        data-bie-state-expression={{states[state.upper].expression}}
        style={{{{gridArea:"1 / 1",display:"grid",placeItems:"center",minWidth:0,minHeight:0,opacity:state.upperOpacity}}}}>
        {{draw(layouts[state.upper].tree as EquationNode, "state-"+state.upper)}}
      </div> : null}}
    </div>
    {{sideConditions.length > 0 ? <div aria-label="side conditions">{{sideConditions.join(", ")}}</div> : null}}
  </div>;
}};
'''
    return compile_result(c.track_id, c.action, f'src/animations/{name}.tsx', source)
