from scene_graph import scene,node
from components import component_ref,component_graph
from assets import bind_assets
from animation import animation_graph
from timeline import timeline
from remotion import composition_spec,remotion_component,generate_component_source
from validation import validate_scene_graph,validate_composition

def compile_scene(scene_id,duration_seconds,fps=30,visual_refs=None,
                  audio_ref=None,cues=None,assets=None,animations=None):
    sg=scene(scene_id,visual_refs=visual_refs or [],audio_refs=[audio_ref] if audio_ref else [])
    tl=timeline(scene_id,duration_seconds,fps,audio_ref,cues)
    frames=max(1,round(duration_seconds*fps))
    component_name="Scene_"+scene_id.replace("-","_")
    body=("export const "+component_name+
          " = ({children}) => <AbsoluteFill>{children}</AbsoluteFill>;")
    rc=remotion_component(component_name,["React","{AbsoluteFill} from 'remotion'"],body)
    comp=composition_spec(scene_id,component_name,frames,fps)
    checks=[validate_scene_graph(sg),validate_composition(comp)]
    errors=[e for c in checks for e in c["errors"]]
    return {"schema_version":"5.25","scene_graph":sg,"timeline":tl,
            "assets":bind_assets(assets or []),
            "animations":animation_graph(animations or []),
            "component":rc,"composition":comp,
            "component_source":generate_component_source(rc),
            "quality_gate":{"valid":not errors,"errors":errors}}
