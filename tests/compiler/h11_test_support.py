"""H11 local image/video fixtures, real file bytes; not textbooks or acceptance."""
from pathlib import Path
from dataclasses import replace
from copy import deepcopy
import json
from bie.compiler.qa_scene_compile import CompilerQATarget
ROOT=Path(__file__).resolve().parents[2]
FIX=ROOT/'fixtures/comp_h11'
ASSET_ROOT=FIX/'asset_root'
T=replace(CompilerQATarget(),compiler_version='1.3.0-comp-h3',width=640,height=360,fps=12)
def scene(name='full-image'):
    return json.loads((FIX/(name+'.json')).read_text())
def asset(p):return p['metadata']['compiler_media_v1']['assets'][0]
def path(p):return ASSET_ROOT/asset(p)['public_path']
def copy_assets(destination,p):
    d=destination/asset(p)['public_path'];d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(path(p).read_bytes());return d

def diagnostic(raw,frames):
    import subprocess,tempfile
    from bie.compiler.hardened_scene_compile import compile_h3_scene
    c=compile_h3_scene(raw,target=T)
    if not c.receipt.source_gate_passed:raise AssertionError(c.receipt.findings)
    request={'files':{f.path:f.content for f in c.codegen.files},'frames':list(frames),'fps':T.fps,'width':T.width,'height':T.height}
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'request.json';p.write_text(json.dumps(request));r=__import__('subprocess').run(['node',str(ROOT/'bie/compiler/qa_support/media_bridge.cjs'),str(p)],capture_output=True,text=True,timeout=35)
        if r.returncode:raise AssertionError(r.stderr)
        return json.loads(r.stdout)

def nodes(tree):
    if isinstance(tree,list):
        for n in tree:yield from nodes(n)
    elif isinstance(tree,dict):
        yield tree
        for n in tree.get('children',[]):yield from nodes(n)
