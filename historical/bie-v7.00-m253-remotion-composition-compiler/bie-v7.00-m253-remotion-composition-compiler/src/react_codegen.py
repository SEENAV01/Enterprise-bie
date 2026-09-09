def generate_react_source(comp, layers):
    lines=[
      'import React from "react";',
      'import { AbsoluteFill } from "remotion";',
      '',
      'export const GeneratedEducationalScene: React.FC = () => (',
      '  <AbsoluteFill>'
    ]
    for layer in layers:
        lid=layer["id"]
        lines.append(f'    <div data-layer="{lid}">{lid}</div>')
    lines += ['  </AbsoluteFill>', ');']
    return "\n".join(lines)

def validate_react_source(source):
    required=["import React","AbsoluteFill","GeneratedEducationalScene"]
    errors=[x for x in required if x not in source]
    return {"valid":not errors,"errors":errors}
