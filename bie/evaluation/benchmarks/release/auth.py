"""Operator-held HMAC attestations. Never embed production keys in packages.

Shared-secret verification authenticates the configured service, not a person's
real-world identity or expertise. The deployment must establish that binding.
"""
import hmac,hashlib
from ..models import BenchmarkError,canonical_json,digest,digest_string,exact_fields,ident
from ..domains.structured import choice,unique_ids
from .contracts import bounded_int
FIELDS={'schema_version','kind','subject_id','key_id','issued_at','expires_at','nonce','scope_sha256','claims'}

def sign(payload,key):
    if type(key) is not bytes or len(key)<32:raise BenchmarkError('WEAK_ATTESTATION_KEY')
    _body(payload)
    return {'payload':payload,'signature':hmac.new(key,canonical_json(payload).encode(),hashlib.sha256).hexdigest()}

def _body(p):
    exact_fields(p,FIELDS);choice(p['schema_version'],{'1.0.0'})
    for k in ['kind','subject_id','key_id','nonce']:ident(p[k])
    digest_string(p['scope_sha256']);bounded_int(p['issued_at']);bounded_int(p['expires_at'])
    if not 0<p['expires_at']-p['issued_at']<=604800:raise BenchmarkError('INVALID_ATTESTATION_TTL')
    canonical_json(p['claims'])

def verify(token,trust,*,kind,scope_sha256,now,production=False):
    exact_fields(token,{'payload','signature'});p=token['payload'];_body(p);digest_string(token['signature'])
    bounded_int(now);digest_string(scope_sha256);ident(kind)
    if type(production) is not bool:raise BenchmarkError('INVALID_PRODUCTION_MODE')
    if type(trust) is not dict or p['key_id'] not in trust:raise BenchmarkError('UNKNOWN_ATTESTATION_KEY')
    k=trust[p['key_id']]
    exact_fields(k,{'secret','subject_id','roles','not_before','expires_at','revoked','fixture_only'})
    if type(k['secret']) is not bytes or len(k['secret'])<32:raise BenchmarkError('WEAK_ATTESTATION_KEY')
    ident(k['subject_id']);unique_ids(k['roles']);bounded_int(k['not_before']);bounded_int(k['expires_at'])
    if type(k['revoked']) is not bool or type(k['fixture_only']) is not bool:raise BenchmarkError('INVALID_KEY_STATE')
    expected=hmac.new(k['secret'],canonical_json(p).encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,token['signature']):raise BenchmarkError('BAD_ATTESTATION_SIGNATURE')
    if k['revoked'] or p['subject_id']!=k['subject_id'] or kind not in k['roles']:
        raise BenchmarkError('UNAUTHORIZED_ATTESTOR')
    if p['kind']!=kind or p['scope_sha256']!=scope_sha256:raise BenchmarkError('ATTESTATION_SCOPE_MISMATCH')
    if not k['not_before']<=p['issued_at']<=now<p['expires_at']<=k['expires_at']:
        raise BenchmarkError('ATTESTATION_EXPIRED_OR_FUTURE')
    if production and k['fixture_only']:raise BenchmarkError('FIXTURE_KEY_NOT_PRODUCTION')
    return p
