"""H5-002: exact local-origin policy. No proxying, fallback files or eval CSP."""
from pathlib import PurePosixPath
from urllib.parse import urlsplit
from ...models import BenchmarkError
from ..contracts import MIME,path
CSP=("default-src 'none'; script-src 'self'; script-src-attr 'none'; "
     "style-src 'self'; img-src 'self'; font-src 'self'; connect-src 'self'; "
     "object-src 'none'; base-uri 'none'; form-action 'none'; frame-src 'none'; "
     "worker-src 'none'; frame-ancestors 'none'")
HEADERS={'Content-Security-Policy':CSP,'X-Content-Type-Options':'nosniff',
         'Cache-Control':'no-store','Referrer-Policy':'no-referrer',
         'Cross-Origin-Resource-Policy':'same-origin','X-Frame-Options':'DENY',
         'Permissions-Policy':'camera=(), microphone=(), geolocation=(), payment=()'}

def request_path(raw):
    if type(raw) is not str or len(raw)>1024 or not raw.startswith('/') or raw.startswith('//'):
        raise BenchmarkError('HTTP_PATH_REJECTED')
    # Reject alternate encodings rather than guessing browser/server normalization.
    if any(c in raw for c in ('%','?','#','\\','\x00','\r','\n')):raise BenchmarkError('HTTP_PATH_REJECTED')
    try:return path(raw[1:])
    except BenchmarkError as exc:raise BenchmarkError('HTTP_PATH_REJECTED') from exc

def route_path(url,origin,method,manifest_names):
    try:
        u=urlsplit(url); o=urlsplit(origin)
        if method!='GET' or u.scheme!='http' or u.netloc!=o.netloc or u.username or u.password or u.query or u.fragment:
            raise BenchmarkError('HTTP_ROUTE_DENIED')
        name=request_path(u.path)
        if name not in manifest_names:raise BenchmarkError('HTTP_ROUTE_DENIED')
        return name
    except (ValueError,TypeError) as exc:raise BenchmarkError('HTTP_ROUTE_DENIED') from exc

def headers(name,raw):
    from hashlib import sha256
    return {**HEADERS,'Content-Type':MIME[PurePosixPath(name).suffix.lower()],
            'Content-Length':str(len(raw)),'ETag':'"'+sha256(raw).hexdigest()+'"'}
