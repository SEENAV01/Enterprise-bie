from __future__ import annotations
from .provenance_adapter import all_refs
from html import escape
from .contracts import *
from .security import csp_value,validate_generated_source
def compile_html_runtime(ctx:CompilerContext):
    ctx.validate();exp=ctx.document.experiences[0];level=exp.levels[0]
    html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="'+escape(csp_value(),quote=True)+'"><title>'+escape(exp.title)+'</title></head><body><main id="bie-game-root" role="application" aria-label="'+escape(exp.title)+'" data-studio-grade="true" data-slide-deck="false" data-level-id="'+escape(level.level_id)+'"></main><script type="module" src="./bootstrap.js"></script></body></html>'
    validate_generated_source(html,allow_imports=True);refs=all_refs(ctx.document.provenance);return artifact(ArtifactKind.HTML_RUNTIME,'runtime/index.html','text/html',html,refs)
