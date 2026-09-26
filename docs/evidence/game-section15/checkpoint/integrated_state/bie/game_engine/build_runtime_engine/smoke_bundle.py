from __future__ import annotations
from pathlib import Path
import hashlib,re
from .errors import GameBuildError
_ORDER=('state-machine.js','rules.js','interactions.js','scoring.js','feedback.js','adaptation.js','telemetry.js','react-runtime.js','runtime-controller.js','bootstrap.js','entry.js')
_IMPORT=re.compile(r'^\s*import\s+.*?;\s*$',re.M)
_EXPORT=re.compile(r'\bexport\s+(?=(?:const|let|var|function|class)\b)')

def build_smoke_bundle(runtime_dir:Path):
    runtime_dir=Path(runtime_dir);parts=[]
    for name in _ORDER:
        p=runtime_dir/name
        if not p.is_file():raise GameBuildError('GAME_BUILD_SMOKE_MODULE_MISSING',name)
        src=p.read_text();src=_IMPORT.sub('',src);src=_EXPORT.sub('',src);parts.append('// '+name+'\n'+src)
    bundle='"use strict";\n'+ '\n'.join(parts)
    if re.search(r'(^|\n)\s*import\s',bundle) or re.search(r'\bexport\s+(?:const|let|var|function|class)',bundle):raise GameBuildError('GAME_BUILD_SMOKE_BUNDLE_MODULE_SYNTAX')
    return bundle,hashlib.sha256(bundle.encode()).hexdigest()
