"""Strict, bounded operator inputs and local deployment identity."""
from dataclasses import dataclass
from pathlib import Path
import hashlib, hmac, json, os, re, time

MAX_PDF_BYTES = 25 * 1024 * 1024
MAX_NODES, MAX_EDGES = 200, 800
ID = re.compile(r'[A-Za-z0-9_-]{1,100}\Z', re.ASCII)
HASH = re.compile(r'[a-f0-9]{64}\Z', re.ASCII)
PERMISSIONS = frozenset({'read','source','create','control','retry','publish','worker',
                         'admin_read','admin_config','admin_recover'})

class OperatorError(ValueError):
    def __init__(self, code, status=409):
        self.code, self.status = code, status
        super().__init__(code)

def require(condition, code, status=409):
    if not condition: raise OperatorError(code, status)

def ident(value):
    require(type(value) is str and bool(ID.fullmatch(value)), 'invalid_identifier', 400)
    return value

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()

def digest(value): return hashlib.sha256(canonical(value)).hexdigest()

def strict_json(raw, max_bytes=16*1024):
    require(len(raw) <= max_bytes, 'payload_too_large', 413)
    def pairs(rows):
        result = {}
        for k,v in rows:
            require(k not in result, 'duplicate_json_key', 400)
            result[k] = v
        return result
    try:
        return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError()))
    except (ValueError,UnicodeError,TypeError) as e:
        if isinstance(e,OperatorError): raise
        raise OperatorError('invalid_json',400) from None

def private_path(root, *parts):
    from bie.infrastructure.path_confinement import confined_path
    root = Path(os.path.abspath(root))
    target = root.joinpath(*parts)
    for p in (target,)+tuple(target.parents):
        require(not p.is_symlink(), 'storage_link_rejected')
    require(target == confined_path(root,target), 'storage_path_rejected')
    return target

@dataclass(frozen=True)
class Principal:
    actor: str
    tenant: str
    permissions: frozenset[str]
    expires_at: float
    def __post_init__(self):
        ident(self.actor); ident(self.tenant)
        require(self.permissions <= PERMISSIONS, 'invalid_permission_configuration')

class Credentials:
    """Process-provisioned bearer credentials; no token is persisted or returned.

    This is local operator access control, NOT enterprise SSO or public IAM.
    Revocation/expiry are checked on each operation, including worker dispatch.
    """
    def __init__(self): self._grants = {}
    def grant(self, token, principal):
        require(type(token) is str and 32 <= len(token) <= 256 and token.isascii() and not any(c.isspace() for c in token),
                'invalid_credential_configuration')
        require(type(principal) is Principal, 'invalid_principal')
        self._grants[hashlib.sha256(token.encode()).hexdigest()] = principal
    def revoke(self, token): self._grants.pop(hashlib.sha256(token.encode()).hexdigest(),None)
    def authenticate(self, token):
        require(type(token) is str and 32 <= len(token) <= 256, 'unauthorized', 401)
        hashed = hashlib.sha256(token.encode()).hexdigest()
        principal = next((v for k,v in self._grants.items() if hmac.compare_digest(k,hashed)),None)
        require(principal is not None and principal.expires_at > time.time(), 'unauthorized', 401)
        return principal
    def check(self, principal, permission):
        require(principal in self._grants.values() and principal.expires_at > time.time(), 'unauthorized', 401)
        require(permission in principal.permissions, 'forbidden', 403)

    def access_binding(self,token,principal):
        require(self.authenticate(token)==principal,'unauthorized',401)
        return hashlib.sha256(token.encode()).hexdigest()

    def check_binding(self,binding,principal,permission):
        require(self._grants.get(binding)==principal,'unauthorized',401)
        self.check(principal,permission)

def run_options(options):
    require(type(options) is dict and set(options) <= {'profile','outputs','locale','model_policy'}, 'invalid_config',400)
    profile = options.get('profile','native_pdf_inspection_v1')
    require(profile == 'native_pdf_inspection_v1', 'engine_profile_unavailable',409)
    outputs = options.get('outputs',['video','game'])
    require(type(outputs) is list and len(outputs) in (1,2) and
            all(type(v) is str and v in ('video','game') for v in outputs) and len(set(outputs)) == len(outputs),
            'invalid_outputs',400)
    locale = options.get('locale','en')
    require(locale in ('en','hi'), 'unsupported_locale',400)
    policy = options.get('model_policy','offline_only')
    require(policy == 'offline_only', 'live_provider_not_configured',409)
    return dict(profile=profile, outputs=sorted(outputs), locale=locale, model_policy=policy)
