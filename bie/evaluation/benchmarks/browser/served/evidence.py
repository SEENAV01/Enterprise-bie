"""H5-007: cross-check native response bodies against custody/server evidence.
A hash is integrity, not a trust signature. Missing runtime stays BLOCKED.
"""
from collections import Counter
from fractions import Fraction
from pathlib import PurePosixPath
from ...models import BenchmarkError,digest
from ..contracts import MIME
from ..scoring import grade as behavior_grade
from .origin import HEADERS

def validate(reference,candidate,observed):
    if (type(observed) is not dict or observed.get('status')!='COLLECTED' or
        observed.get('transport')!='REAL_LOOPBACK_HTTP_MODULE_APP' or
        observed.get('hostile_code_sandbox_verified') is not False or
        observed.get('trusted_fixture_execution_only') is not True):
        raise BenchmarkError('HTTP_EVIDENCE_INCOMPLETE')
    if type(observed.get('runs')) is not list or len(observed['runs'])!=reference['replay_count']:raise BenchmarkError('HTTP_REPLAY_INCOMPLETE')
    manifest={r['path']:r for r in candidate['files']};policy=reference['http_policy']
    for index,run in enumerate(observed['runs']):
      try:
        if type(run['fresh_context_index']) is not int or run['fresh_context_index']!=index or not run['readiness'] or any(v.get('ready') is not True or
            v.get('target')!=policy['ready']['target'] or v.get('observed_text')!=policy['ready']['text'] for v in run['readiness']):
            raise BenchmarkError('HTTP_READINESS_EVIDENCE_INVALID')
        wire=run['http_responses'];server=run['http_server'];received=Counter();sent=Counter();size=0
        if type(wire) is not list or type(server) is not list or not wire or len(wire)>policy['max_requests'] or len(server)>policy['max_requests']:
            raise BenchmarkError('HTTP_TRANSCRIPT_INCOMPLETE')
        for row in wire:
            if type(row['size_bytes']) is not int or type(row['status']) is not int:raise BenchmarkError('HTTP_WIRE_TYPE_INVALID')
            name=row['path'];m=manifest.get(name);size+=row['size_bytes']
            if m is None or row['method']!='GET' or row['status']!=200 or row['size_bytes']!=m['size_bytes'] or row['sha256']!=m['sha256']:
                raise BenchmarkError('HTTP_RESPONSE_BINDING_MISMATCH')
            h={k.lower():v for k,v in row['headers'].items()}
            if (any(h.get(k.lower())!=v for k,v in HEADERS.items()) or
                h.get('content-type')!=MIME[PurePosixPath(name).suffix.lower()] or
                h.get('content-length')!=str(m['size_bytes'])):raise BenchmarkError('HTTP_RESPONSE_HEADERS_MISMATCH')
            received[(name,row['sha256'],row['size_bytes'])]+=1
        if size>policy['max_response_bytes']:raise BenchmarkError('HTTP_RESPONSE_BYTE_LIMIT')
        for row in server:
            if row['status']!=200 or row['method']!='GET' or not row['response_completed']:
                raise BenchmarkError('HTTP_SERVER_TRANSCRIPT_FAILED')
            sent[(row['path'],row['sha256'],row['size_bytes'])]+=1
        if received!=sent:raise BenchmarkError('HTTP_WIRE_SERVER_MISMATCH')
        if candidate['entrypoint'] not in {v['path'] for v in wire}:raise BenchmarkError('HTTP_ENTRYPOINT_UNOBSERVED')
        if set(run['ax'])!={v['id'] for v in policy['ax_checks']}:raise BenchmarkError('HTTP_AX_EVIDENCE_MISSING')
      except BenchmarkError:raise
      except (KeyError,TypeError,ValueError) as exc:raise BenchmarkError('HTTP_EVIDENCE_MALFORMED') from exc
    try:
        account=observed['server_accounting'];records=[row for run in observed['runs'] for row in run['http_server']]
        if (account['records']!=records or account['limit_exceeded'] is not False or
            type(account['requests']) is not int or account['requests']!=len(records) or account['requests']>policy['max_requests'] or
            type(account['response_bytes_reserved']) is not int or account['response_bytes_reserved']!=sum(v['size_bytes'] for v in records) or
            account['response_bytes_reserved']>policy['max_response_bytes']):raise BenchmarkError('HTTP_ACCOUNTING_MISMATCH')
    except BenchmarkError:raise
    except (KeyError,TypeError,ValueError) as exc:raise BenchmarkError('HTTP_ACCOUNTING_MALFORMED') from exc
    return True

def grade(reference,observed):
    base=behavior_grade(reference,observed);units=base['units'];policy=reference['http_policy']
    for asset in policy['required_assets']:
        ok=all(asset in {x['path'] for x in run['http_responses']} for run in observed['runs'])
        units.append({'id':'http-asset-'+digest(asset)[:16],'weight':'1','credit':'1' if ok else '0',
                      'reasons':[] if ok else ['HTTP_REQUIRED_ASSET_NOT_LOADED']})
    for row in policy['ax_checks']:
        ok=all(run['ax'][row['id']].get('present') is True and run['ax'][row['id']].get('ignored') is False and
               run['ax'][row['id']].get('role')==row['role'] and run['ax'][row['id']].get('name')==row['name']
               for run in observed['runs'])
        units.append({'id':row['id'],'weight':'1','credit':'1' if ok else '0','reasons':[] if ok else ['NATIVE_AX_CHECK_MISMATCH']})
    n=sum(Fraction(u['credit']) for u in units);d=len(units)
    base.update(score_exact=str(n/d),earned_weight=str(n),total_weight=str(d),outcome='PASS' if n==d else 'FAIL')
    return base
