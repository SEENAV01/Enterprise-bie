"""H4-008: canonical dist-layout adapter. Layout is NOT native-run provenance.
Contract read at a68e054...: bie/game_engine/build_runtime_engine/browser_runtime.py
(blob f526d00761ab8c3ca19aaa1af7e8c1d0f860da06). Browser profile executes actual
canonical-layout smoke-bundle bytes in Chromium; ES module/native boot is unverified.
"""
from .contracts import candidate,CANDIDATE_SCHEMA,BrowserLimits
from ..models import BenchmarkError,digest
CANONICAL_COMMIT='a68e054025b8fe7756a71e998d9e9103dad8e0f4'
BROWSER_RUNTIME_BLOB='f526d00761ab8c3ca19aaa1af7e8c1d0f860da06'

def map_dist(expected_files,*,expected_manifest_sha256,limits=BrowserLimits()):
    if digest(expected_files)!=expected_manifest_sha256:raise BenchmarkError('GAME_DIST_MANIFEST_PIN_MISMATCH')
    names={r.get('path') for r in expected_files} if type(expected_files) is list and all(type(x) is dict for x in expected_files) else set()
    if not {'runtime/index.html','runtime/smoke-bundle.js','runtime/security-headers.json'}.issubset(names):
        raise BenchmarkError('GAME_DIST_REQUIRED_FILES_MISSING')
    return candidate({'schema_version':CANDIDATE_SCHEMA,'entrypoint':'runtime/index.html',
        'files':expected_files,'origin_kind':'CANONICAL_LAYOUT_UNVERIFIED','load_mode':'CANONICAL_SMOKE_BUNDLE'},limits)
