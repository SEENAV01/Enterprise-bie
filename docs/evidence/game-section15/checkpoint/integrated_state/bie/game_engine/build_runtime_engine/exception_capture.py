from __future__ import annotations
import hashlib,json
from functools import lru_cache
from .contracts import ExceptionEvidence,BuildPolicy
from .process import run_bounded
from .toolchain import discover_toolchain
from .errors import GameBuildError
from .sandbox import sandboxed_chromium,sandbox_evidence

def _stack_hash(stack):return hashlib.sha256(stack.encode()).hexdigest()
@lru_cache(maxsize=8)
def capture_node_exception(policy=BuildPolicy()):
    node=next(x for x in discover_toolchain()[0] if x.name=='node');script='try { throw new Error("BIE_RUNTIME_FIXTURE") } catch (e) { console.log(JSON.stringify({name:e.name,code:e.message,stack:String(e.stack||"")})) }';r=run_bounded([node.path,'-e',script],timeout=policy.process_timeout_seconds,cpu_seconds=policy.process_cpu_seconds,memory_bytes=policy.process_memory_bytes,max_processes=policy.process_max_processes,max_open_files=policy.process_max_open_files)
    if r.returncode!=0:raise GameBuildError('GAME_BUILD_NODE_EXCEPTION_HARNESS')
    d=json.loads(r.stdout);return ExceptionEvidence('node',d['name'],d['code'],_stack_hash(d['stack']),True,False,False).validate()
@lru_cache(maxsize=8)
def capture_browser_exception(dist,policy=BuildPolicy()):
    errors=[]
    with sandboxed_chromium(policy) as (ctx,profile,manifest):
        page=ctx.pages[0] if ctx.pages else ctx.new_page();page.on('pageerror',lambda err:errors.append(str(err)));page.set_content('<!doctype html><html><body></body></html>');page.evaluate('setTimeout(() => { throw new Error("BIE_BROWSER_FIXTURE") }, 0)');page.wait_for_timeout(150);sandbox_evidence(profile,manifest)
    if not errors or 'BIE_BROWSER_FIXTURE' not in errors[0]:raise GameBuildError('GAME_BUILD_BROWSER_EXCEPTION_NOT_CAPTURED')
    stack=errors[0];return ExceptionEvidence('browser','Error','BIE_BROWSER_FIXTURE',_stack_hash(stack),True,False,False).validate()
