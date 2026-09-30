"""H5-001: trusted HTTP policy; reuse the bounded H4 behavioral contract."""
from ..contracts import BrowserLimits, snapshot, path, target, bounded_text
from ...models import BenchmarkError, exact_fields, digest, ident
SCHEMA='browser-http-reference-1'
LOAD_MODE='HTTP_MODULE_APP'
PROFILES={'BIE-EVAL-METRIC-014':'http-module-game-behavior-1',
          'BIE-EVAL-METRIC-015':'http-module-accessibility-1'}

def reference(value, metric_id=None, limits=BrowserLimits()):
    from ..contracts import reference as legacy
    r=snapshot(value)
    if type(r) is not dict or r.get('schema_version')!=SCHEMA:
        raise BenchmarkError('HTTP_REFERENCE_SCHEMA')
    if 'http_policy' not in r: raise BenchmarkError('HTTP_POLICY_REQUIRED')
    policy=r['http_policy'];base={k:v for k,v in r.items() if k!='http_policy'}
    base['schema_version']='browser-reference-1'
    legacy(base,metric_id,limits)
    exact_fields(policy,{'ready','required_assets','ax_checks','max_requests','max_response_bytes'})
    exact_fields(policy['ready'],{'target','text'});target(policy['ready']['target'])
    bounded_text(policy['ready']['text'])
    assets=policy['required_assets']
    if type(assets) is not list or not 1<=len(assets)<=limits.max_files:
        raise BenchmarkError('HTTP_REQUIRED_ASSETS_INVALID')
    for asset in assets: path(asset)
    if len(set(assets))!=len(assets):raise BenchmarkError('HTTP_DUPLICATE_REQUIRED_ASSET')
    if type(policy['max_requests']) is not int or not 1<=policy['max_requests']<=2000:
        raise BenchmarkError('HTTP_REQUEST_LIMIT_INVALID')
    if type(policy['max_response_bytes']) is not int or not 1024<=policy['max_response_bytes']<=256_000_000:
        raise BenchmarkError('HTTP_RESPONSE_LIMIT_INVALID')
    ax=policy['ax_checks'];all_ids={c['id'] for s in r['steps'] for c in s['checks']}
    if type(ax) is not list or not 1<=len(ax)<=100:raise BenchmarkError('HTTP_AX_CHECKS_REQUIRED')
    if any(i.startswith('http-') for i in all_ids):raise BenchmarkError('HTTP_RESERVED_BEHAVIOR_ID')
    seen=set()
    for row in ax:
        exact_fields(row,{'id','target','role','name'});ident(row['id']);target(row['target'])
        if row['id'] in seen or row['id'] in all_ids or row['id'].startswith('http-') or row['id'] in ('runtime-health','fresh-context-replay'):
            raise BenchmarkError('HTTP_DUPLICATE_AX_CHECK')
        seen.add(row['id']);bounded_text(row['name']);bounded_text(row['role'],64)
        if not row['role']:raise BenchmarkError('HTTP_AX_ROLE_REQUIRED')
    return r

def binding(ref,cand):
    if cand['load_mode']!=LOAD_MODE:raise BenchmarkError('HTTP_LOAD_MODE_MISMATCH')
    names={r['path'] for r in cand['files']}
    if not set(ref['http_policy']['required_assets'])<=names:
        raise BenchmarkError('HTTP_REQUIRED_ASSET_UNDECLARED')
    if cand['entrypoint'] not in ref['http_policy']['required_assets']:
        raise BenchmarkError('HTTP_ENTRYPOINT_NOT_REQUIRED')
    return True
