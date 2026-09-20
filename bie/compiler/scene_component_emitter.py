from __future__ import annotations
import json
from .react_emitter_common import *

def emit_scene_component(*, scene_name="Scene", layers=(), background="white"):
    scene_name=ts_identifier(scene_name,"scene_name")
    normalized=[]
    imports={}
    for raw in layers:
        item=dict(raw)
        layer_id=nonblank(item.get("layer_id"),"layer_id")
        component=ts_identifier(item.get("component_name"),"component_name")
        import_path=nonblank(item.get("import_path"),"import_path")
        start=item.get("from_frame",0)
        duration=item.get("duration_in_frames")
        if isinstance(start,bool) or not isinstance(start,int) or start<0:
            raise ReactEmitterError("from_frame invalid")
        if isinstance(duration,bool) or not isinstance(duration,int) or duration<1:
            raise ReactEmitterError("duration_in_frames invalid")
        props=item.get("props",{})
        if not isinstance(props,dict):
            raise ReactEmitterError("props must be object")
        normalized.append((start,layer_id,component,import_path,duration,props))
        imports[(component,import_path)]=True
    normalized.sort(key=lambda x:(x[0],x[1]))

    import_lines=['import React from "react";','import {AbsoluteFill, Sequence} from "remotion";']
    for component,import_path in sorted(imports):
        import_lines.append(f'import {{{component}}} from {js_string(import_path)};')

    body=[]
    for start,layer_id,component,import_path,duration,props in normalized:
        pj=json.dumps(props,sort_keys=True,ensure_ascii=False)
        body.append(
          f'      <Sequence name={{{js_string(layer_id)}}} from={{{start}}} durationInFrames={{{duration}}}>\n'
          f'        <{component} {{...({pj})}} />\n'
          f'      </Sequence>'
        )
    layers_text="\n".join(body)
    content=(
        "\n".join(import_lines)
        + f'\n\nexport const {scene_name}: React.FC = () => {{\n'
        + '  return (\n'
        + f'    <AbsoluteFill name="Scene" style={{{{backgroundColor: {js_string(background)}}}}}>\n'
        + layers_text + '\n'
        + '    </AbsoluteFill>\n'
        + '  );\n'
        + '};\n'
    )
    return emitted_file("src/Scene.tsx",content)
