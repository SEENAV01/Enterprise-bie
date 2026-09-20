from __future__ import annotations
from .react_emitter_common import *

def emit_state_bindings(*, bindings=()):
    normalized=[]
    seen=set()
    for raw in bindings:
        b=dict(raw)
        bid=nonblank(b.get("binding_id"),"binding_id")
        if bid in seen: raise ReactEmitterError("duplicate binding_id")
        seen.add(bid)
        state_path=nonblank(b.get("state_path"),"state_path")
        target_id=nonblank(b.get("target_id"),"target_id")
        prop=nonblank(b.get("property_name"),"property_name")
        transform=b.get("transform","identity")
        if transform not in {"identity","bool","number","string","percent","clamp01"}:
            raise ReactEmitterError("unsupported state transform")
        normalized.append((bid,state_path,target_id,prop,transform))
    normalized.sort()

    cases=[]
    for bid,state_path,target_id,prop,transform in normalized:
        expr={
          "identity":"value",
          "bool":"Boolean(value)",
          "number":"Number(value)",
          "string":"String(value)",
          "percent":"`${Number(value) * 100}%`",
          "clamp01":"Math.max(0, Math.min(1, Number(value)))",
        }[transform]
        cases.append(
          f'  {{bindingId: {js_string(bid)}, statePath: {js_string(state_path)}, targetId: {js_string(target_id)}, '
          f'propertyName: {js_string(prop)}, transform: (value: unknown) => {expr}}},'
        )
    content=(
        'export type StateBindingRuntime = {\n'
        '  bindingId: string;\n'
        '  statePath: string;\n'
        '  targetId: string;\n'
        '  propertyName: string;\n'
        '  transform: (value: unknown) => unknown;\n'
        '};\n\n'
        'export const stateBindings: StateBindingRuntime[] = [\n'
        + "\n".join(cases)
        + '\n];\n\n'
        'export const resolveStateBinding = (bindingId: string, value: unknown): unknown => {\n'
        '  const binding = stateBindings.find((item) => item.bindingId === bindingId);\n'
        '  if (!binding) {\n'
        '    throw new Error(`Unknown state binding: ${bindingId}`);\n'
        '  }\n'
        '  return binding.transform(value);\n'
        '};\n'
    )
    return emitted_file("src/state-bindings.ts",content)
