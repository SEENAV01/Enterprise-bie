from .animation_compiler_common import *

EASING_PRESETS={
    "linear":"Easing.linear",
    "gentle":"Easing.bezier(0.16, 1, 0.3, 1)",
    "emphasize":"Easing.bezier(0.34, 1.56, 0.64, 1)",
    "decelerate":"Easing.bezier(0.0, 0.0, 0.2, 1)",
    "accelerate":"Easing.bezier(0.4, 0.0, 1, 1)",
    "standard":"Easing.bezier(0.4, 0.0, 0.2, 1)",
}

def easing_expression(intent):
    if not isinstance(intent,str) or not intent.strip():
        raise AnimationCompilerError("semantic easing intent required")
    key=intent.strip()
    if key not in EASING_PRESETS:
        raise AnimationCompilerError("unsupported semantic easing intent")
    return EASING_PRESETS[key]

def compile_semantic_easing_module(intents):
    intents=tuple(sorted(set(intents)))
    if not intents:
        raise AnimationCompilerError("at least one easing intent required")
    mapping={intent:easing_expression(intent) for intent in intents}
    lines=['import {Easing} from "remotion";',"","export const semanticEasing = {"]
    for intent in intents:
        lines.append(f"  {jsx(intent)}: {mapping[intent]},")
    lines.append("} as const;")
    lines.append("")
    lines.append("export type SemanticEasingIntent = keyof typeof semanticEasing;")
    source="\n".join(lines)+"\n"
    return compile_result("semantic-easing","semantic_easing","src/animations/semantic-easing.ts",source)
