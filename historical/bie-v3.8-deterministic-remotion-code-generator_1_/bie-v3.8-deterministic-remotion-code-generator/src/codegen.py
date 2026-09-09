def ts_literal(x):
    if isinstance(x,str): return '"' + x.replace('"','\\"') + '"'
    if x is None: return "undefined"
    if isinstance(x,bool): return "true" if x else "false"
    if isinstance(x,(int,float)): return str(x)
    if isinstance(x,list): return "["+", ".join(ts_literal(v) for v in x)+"]"
    if isinstance(x,dict): return "{"+", ".join(f"{k}: {ts_literal(v)}" for k,v in x.items())+"}"
    return "undefined"

def generate_component(ir):
    lines=[
      'import React from "react";',
      'import {AbsoluteFill, Audio, Sequence} from "remotion";',
      '',
      f'export const Scene_{ir["scene_id"]}: React.FC = () => {{',
      '  return (',
      '    <AbsoluteFill>'
    ]
    for layer in ir.get("layers",[]):
        key=layer["key"]
        primitive=layer["primitive"]
        props=ts_literal(layer["props"])
        lines.append(f'      <div key={"{key}"} data-primitive={"{primitive}"} data-props={{{props}}} />')
    lines += ['    </AbsoluteFill>','  );','};','']
    return "\n".join(lines)

def generate_root(compositions):
    lines=['import React from "react";','import {Composition} from "remotion";']
    for c in compositions:
        lines.append(f'import {{ Scene_{c["scene_id"]} }} from "./Scene_{c["scene_id"]}";')
    lines += ['','export const Root: React.FC = () => (','  <>']
    for c in compositions:
        lines.append(f'    <Composition id="{c["scene_id"]}" component={{Scene_{c["scene_id"]}}} durationInFrames={{900}} fps={30} width={1920} height={1080} />')
    lines += ['  </>',');','']
    return "\n".join(lines)
