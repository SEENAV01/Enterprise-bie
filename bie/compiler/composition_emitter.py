from __future__ import annotations
import json
from .react_emitter_common import *

def emit_composition(*, composition_id, scene_component="Scene", scene_import="./Scene", width, height, fps, duration_in_frames, default_props=None):
    composition_id=nonblank(composition_id,"composition_id")
    scene_component=ts_identifier(scene_component,"scene_component")
    scene_import=nonblank(scene_import,"scene_import")
    for n,v in (("width",width),("height",height),("fps",fps),("duration_in_frames",duration_in_frames)):
        if isinstance(v,bool) or not isinstance(v,int) or v<1:
            raise ReactEmitterError(f"{n} must be positive int")
    props_json=json.dumps(default_props or {},sort_keys=True,ensure_ascii=False)
    content=(
        'import React from "react";\n'
        'import {Composition} from "remotion";\n'
        f'import {{{scene_component}}} from {js_string(scene_import)};\n\n'
        f'const defaultProps = {props_json} as const;\n\n'
        'export const BieComposition: React.FC = () => {\n'
        '  return (\n'
        '    <Composition\n'
        f'      id={{{js_string(composition_id)}}}\n'
        f'      component={{{scene_component}}}\n'
        f'      width={{{width}}}\n'
        f'      height={{{height}}}\n'
        f'      fps={{{fps}}}\n'
        f'      durationInFrames={{{duration_in_frames}}}\n'
        '      defaultProps={{...defaultProps}}\n'
        '    />\n'
        '  );\n'
        '};\n'
    )
    return emitted_file("src/Composition.tsx",content)
