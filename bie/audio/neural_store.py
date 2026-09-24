"""H1-004: response+alignment cache, using the existing lock/directory helpers.

HMAC binds local process-produced response records. It is NOT an ElevenLabs
signature, trusted phonetic evaluation, or protection from the service owner.
The key must live outside the cache entries, in a private service-owned file.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import asdict
import hashlib, hmac, json, os, stat, tempfile, shutil
from .common import AudioError, fingerprint, strict_json
from .tts_cache import safe_directory, read_regular, key_lock
from .neural_transport import HTTPReply


def load_seal_key(path, *, create=False):
    p=Path(path).absolute()
    if any(a.is_symlink() for a in (p,*p.parents)): raise AudioError('NEURAL_KEY_PATH')
    if create and not p.exists():
        p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        try:
            fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'wb') as f:f.write(os.urandom(32));f.flush();os.fsync(f.fileno())
        except FileExistsError: pass
    data=read_regular(p,32);st=p.stat()
    if len(data)!=32 or (stat.S_IMODE(st.st_mode)&0o077) or st.st_uid!=os.getuid():
        raise AudioError('NEURAL_KEY_PERMISSION_OR_LENGTH')
    return data


def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


class NeuralResponseStore:
    def __init__(self,root,*,key):
        if type(key)is not bytes or len(key)!=32: raise AudioError('NEURAL_SEAL_KEY_REQUIRED')
        self.root=safe_directory(root);self.entries=safe_directory(self.root/'entries');self.locks=safe_directory(self.root/'locks');self._key=key
    def __repr__(self):return 'NeuralResponseStore(<private key omitted>)'
    def lock(self,request,*,timeout,cancellation=None):
        return key_lock(self.locks/(request.fingerprint()[7:]+'.lock'),timeout=timeout,cancellation=cancellation)
    def load(self,request,*,payload_hash,scope,maximum):
        folder=self.entries/request.fingerprint()[7:]
        if not folder.exists() and not folder.is_symlink(): return None
        if folder.is_symlink() or not folder.is_dir() or {p.name for p in folder.iterdir()}!={'response.json','seal.json'}:
            raise AudioError('NEURAL_RESPONSE_CACHE_INCOMPLETE')
        body=read_regular(folder/'response.json',maximum)
        row=strict_json(read_regular(folder/'seal.json',16000).decode())
        if type(row)is not dict or set(row)!={'record','hmac_sha256'}: raise AudioError('NEURAL_SEAL_SCHEMA')
        r=row['record']
        if type(r)is not dict: raise AudioError('NEURAL_SEAL_SCHEMA')
        if type(row['hmac_sha256'])is not str or not hmac.compare_digest(row['hmac_sha256'],hmac.new(self._key,canonical(r),hashlib.sha256).hexdigest()):
            raise AudioError('NEURAL_RESPONSE_SEAL_MISMATCH')
        expected={'schema_version':'bie.audio.neural-response/1','request':request.fingerprint(),
                  'runtime':request.voice.runtime_fingerprint,'payload_sha256':payload_hash,'response_sha256':hashlib.sha256(body).hexdigest(),
                  'scope':scope,'status':200,'request_id':r.get('request_id')}
        if r!=expected or type(r['request_id'])is not str: raise AudioError('NEURAL_RESPONSE_CACHE_BINDING')
        return HTTPReply(200,body,r['request_id'],scope)
    def put(self,request,reply,*,payload_hash):
        folder=self.entries/request.fingerprint()[7:]
        if folder.exists() or folder.is_symlink(): raise AudioError('NEURAL_RESPONSE_CONCURRENT_CONFLICT')
        r={'schema_version':'bie.audio.neural-response/1','request':request.fingerprint(),'runtime':request.voice.runtime_fingerprint,
           'payload_sha256':payload_hash,'response_sha256':hashlib.sha256(reply.body).hexdigest(),
           'scope':reply.evidence_scope,'status':reply.status,'request_id':reply.request_id}
        envelope={'record':r,'hmac_sha256':hmac.new(self._key,canonical(r),hashlib.sha256).hexdigest()}
        temporary=Path(tempfile.mkdtemp(prefix='.pending-',dir=self.entries))
        try:
            for name,value in (('response.json',reply.body),('seal.json',canonical(envelope))):
                with (temporary/name).open('xb') as f: f.write(value);f.flush();os.fsync(f.fileno())
            os.rename(temporary,folder)
            fd=os.open(self.entries,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(fd)
            finally:os.close(fd)
        finally:
            if temporary.exists():shutil.rmtree(temporary)
