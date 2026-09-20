from __future__ import annotations
import json
from .react_emitter_common import *

TYPE_MAP={"string":"string","number":"number","boolean":"boolean","string[]":"string[]","number[]":"number[]","unknown":"unknown"}

def emit_props(*, interface_name="BieSceneProps", fields=(), defaults=None):
    interface_name=ts_identifier(interface_name,"interface_name")
    normalized=[]
    seen=set()
    for raw in fields:
        f=dict(raw)
        name=ts_identifier(f.get("name"),"field name")
        if name in seen: raise ReactEmitterError("duplicate prop field")
        seen.add(name)
        kind=f.get("type")
        if kind not in TYPE_MAP: raise ReactEmitterError("unsupported prop type")
        normalized.append((name,TYPE_MAP[kind],bool(f.get("optional",False))))
    normalized.sort()
    defaults=dict(defaults or {})
    if set(defaults)-seen: raise ReactEmitterError("default references unknown prop")
    lines=[f"export interface {interface_name} {{"]
    for name,kind,optional in normalized:
        lines.append(f"  {name}{'?' if optional else ''}: {kind};")
    lines.append("}")
    lines.append("")
    lines.append(f"export const defaultSceneProps: Partial<{interface_name}> = {json.dumps(defaults,sort_keys=True,ensure_ascii=False)};")
    return emitted_file("src/props.ts","\n".join(lines)+"\n")
