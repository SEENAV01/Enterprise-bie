from __future__ import annotations
import re
from .errors import GameBuildError
_REL=re.compile(r'(from\s+["\'])(\./[^"\']+)(["\'])')
def link_browser_esm(source):
    if not isinstance(source,str):raise GameBuildError('GAME_BUILD_LINK_SOURCE')
    def repl(m):
        spec=m.group(2)
        if spec.endswith('.js') or spec.endswith('.json'):return m.group(0)
        return m.group(1)+spec+'.js'+m.group(3)
    out=_REL.sub(repl,source)
    if re.search(r'from\s+["\']\./[^"\']+(?<!\.js)(?<!\.json)["\']',out):raise GameBuildError('GAME_BUILD_UNLINKED_IMPORT')
    return out
