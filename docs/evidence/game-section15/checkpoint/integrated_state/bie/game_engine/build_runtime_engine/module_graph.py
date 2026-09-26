from __future__ import annotations
from pathlib import Path
import re
from ..canonical import fingerprint
from .errors import GameBuildError
_IMPORT=re.compile(r'from\s+["\'](\./[^"\']+)["\']')
_DYNAMIC=re.compile(r'\bimport\s*\(')
def verify_module_graph(runtime:Path):
    runtime=Path(runtime);nodes=sorted(p.name for p in runtime.glob('*.js'));node_set=set(nodes);edges=[]
    for p in sorted(runtime.glob('*.js')):
        src=p.read_text()
        if _DYNAMIC.search(src):raise GameBuildError('GAME_BUILD_DYNAMIC_IMPORT_FORBIDDEN',p.name)
        for spec in _IMPORT.findall(src):
            target=spec[2:]
            if target not in node_set:raise GameBuildError('GAME_BUILD_DANGLING_IMPORT',p.name+'->'+target)
            edges.append((p.name,target))
    if 'entry.js' not in node_set or 'bootstrap.js' not in node_set:raise GameBuildError('GAME_BUILD_MODULE_ENTRY_MISSING')
    return {'nodes':tuple(nodes),'edges':tuple(sorted(edges)),'graph_fingerprint':fingerprint({'nodes':nodes,'edges':sorted(edges)}),'passed':True,'product_accepted':False}
