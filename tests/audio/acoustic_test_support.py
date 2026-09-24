"""H2 tests: ephemeral test-only keys; native results are distinguished from mutations."""
from functools import lru_cache
from dataclasses import asdict
import copy
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from bie.audio.common import fingerprint
from bie.audio.acoustic_contract import BOUNDARIES,SCOPE,canonical,build_job
from bie.audio.acoustic_runtime import probe_local_runtime,run_native
from .qa_test_support import native,change_pcm
NOW=1_800_000_000
KEY_ID='test-only-not-production-H2'

def clone(value):return copy.deepcopy(value)
def rehash(value):
    value.pop('fingerprint',None);value['fingerprint']=fingerprint(value);return value

@lru_cache(maxsize=1)
def context():
    s,m,stems=native();job=build_job(m,s);runtime=probe_local_runtime()
    result=run_native(job,m.wav_bytes,runtime)
    key=Ed25519PrivateKey.generate()
    trust={'schema_version':'bie.audio.evaluator-trust/1','revision':'TEST_ONLY_NEVER_ADOPT',
           'scope':SCOPE,'max_age_seconds':3600,'max_future_skew_seconds':30,
           'issuers':[{'key_id':KEY_ID,'role':'acoustic-evaluator',
               'public_key_hex':key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex(),
               'runtime_fingerprints':[runtime['fingerprint']], 'not_before':NOW-3600,
               'not_after':NOW+86400,'revoked':False}]}
    return s,m,job,runtime,result,key,trust

def sign_test_payload(payload,key=None):
    key=context()[5] if key is None else key
    return {'schema_version':'bie.audio.signed-evaluation/1','payload':payload,
        'signature_ed25519_hex':key.sign(b'BIE-AUDIO-EVALUATOR-V1\0'+canonical(payload)).hex()}

def receipt(job=None,result=None,issued=NOW):
    c=context();job=c[2] if job is None else job;result=c[4] if result is None else result
    return sign_test_payload({'schema_version':'bie.audio.evaluator-payload/1','key_id':KEY_ID,
        'scope':SCOPE,'issued_at':issued,'expires_at':issued+600,'job_fingerprint':job['fingerprint'],
        'binding':clone(job['binding']),'measurement':clone(result),**BOUNDARIES})

@lru_cache(maxsize=1)
def silent_context():
    s,m,j,r,result,key,trust=context()
    silent=change_pcm(m,lambda a,c:a.fill(0))
    job=build_job(silent,s);res=run_native(job,silent.wav_bytes,r)
    return silent,job,res,receipt(job,res)
