from __future__ import annotations
from .react_emitter_common import *

def emit_root(*, root_component="RemotionRoot", composition_component="BieComposition", composition_import="./Composition"):
    root_component=ts_identifier(root_component,"root_component")
    composition_component=ts_identifier(composition_component,"composition_component")
    composition_import=nonblank(composition_import,"composition_import")
    content=(
        'import React from "react";\n'
        f'import {{{composition_component}}} from {js_string(composition_import)};\n\n'
        f'export const {root_component}: React.FC = () => {{\n'
        f'  return <{composition_component} />;\n'
        f'}};\n'
    )
    return emitted_file("src/Root.tsx",content)
