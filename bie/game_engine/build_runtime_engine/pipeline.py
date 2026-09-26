from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from ..compiler_engine.provenance_adapter import all_refs
from .contracts import BuildPolicy
from .workspace import build_workspace
from .browser_runtime import browser_smoke
from .deployment import deployment_smoke
from .interaction_simulation import simulate
from .deterministic_replay import verify_deterministic_replay
from .exception_capture import capture_node_exception,capture_browser_exception
from .receipts import make_receipt
@dataclass(frozen=True)
class RuntimeBuildResult:
    manifest:object;browser:object;interaction:object;replay:object;exceptions:tuple;receipts:tuple;product_accepted:bool=False;deployment:object|None=None

def build_runtime_package(ctx,asset_blobs,root:Path,policy=BuildPolicy()):
    ws=build_workspace(ctx,asset_blobs,root,policy);refs=all_refs(ctx.document.provenance);browser=browser_smoke(root/'dist',policy);deployment=deployment_smoke(root/'dist',policy);interaction=simulate(ctx,ws.compiler_bundle);replay=verify_deterministic_replay(ctx);exceptions=(capture_node_exception(policy),capture_browser_exception(root/'dist',policy))
    outs=(ws.manifest,browser,interaction,replay,exceptions)
    tasks=('BIE-GAME-BUILD-001','BIE-GAME-BUILD-002','BIE-GAME-BUILD-003','BIE-GAME-BUILD-004','BIE-GAME-BUILD-005')
    receipts=tuple(make_receipt(t,ctx,o,ws.toolchain_fingerprint,refs) for t,o in zip(tasks,outs))
    return RuntimeBuildResult(ws.manifest,browser,interaction,replay,exceptions,receipts,False,deployment)
