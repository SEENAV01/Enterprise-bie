from __future__ import annotations
from .game_ir import compile_game_ir
from .react_runtime import compile_react_runtime
from .html_runtime import compile_html_runtime
from .state_machine import compile_state_machine
from .rule_compiler import compile_rules
from .interaction_compiler import compile_interactions
from .scoring_compiler import compile_scoring
from .feedback_compiler import compile_feedback
from .adaptation_compiler import compile_adaptation
from .telemetry_compiler import compile_telemetry
from .source_map import build_source_map
from .asset_manifest import compile_asset_manifest
from .runtime_controller import compile_runtime_controller
from .bootstrap import compile_bootstrap
from .manifest import build_manifest
from .receipts import make_receipt
from .contracts import *
from .security import validate_generated_source

def compile_game(ctx:CompilerContext)->CompiledBundle:
    ctx.validate();arts=[compile_game_ir(ctx),compile_react_runtime(ctx),compile_html_runtime(ctx),compile_state_machine(ctx),compile_rules(ctx),compile_interactions(ctx),compile_scoring(ctx),compile_feedback(ctx),compile_adaptation(ctx),compile_telemetry(ctx),compile_asset_manifest(ctx),compile_runtime_controller(ctx),compile_bootstrap(ctx),build_source_map(ctx)]
    for a in arts:
        if a.media_type.startswith('text/') or 'typescript' in a.media_type or a.media_type=='application/javascript':validate_generated_source(a.content,allow_imports=True)
    arts.append(build_manifest(ctx,arts));receipt=make_receipt(ctx,arts);return CompiledBundle(tuple(sorted(arts,key=lambda x:x.path)),receipt,False).validate()
