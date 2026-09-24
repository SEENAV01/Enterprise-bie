"""H4-R1 synthetic integration fixtures. Keys are ephemeral and never exported.

Real espeak media and the actual canonical kernel operation are cached per test
process. Mutated/resigned evidence is ONLY for negative contract tests.
"""
from functools import lru_cache
from pathlib import Path
from dataclasses import asdict
import copy
import tempfile
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from bie.audio.acoustic_contract import SCOPE,build_job,canonical
from bie.audio.acoustic_runtime import probe_local_runtime
from bie.audio.kernel_profile import KERNEL_SCOPE,probe_profile
from bie.audio.kernel_evidence import DOMAIN,issue_kernel_evaluation
from bie.audio.kernel_durable import build_kernel_request
from .qa_test_support import native

KEY_ID='TEST_ONLY_H4R1_DO_NOT_TRUST_IN_PRODUCTION'
RUN_ID='01952504-3824-4000-8000-000000000004'

def clone(x):return copy.deepcopy(x)

@lru_cache(maxsize=1)
def context():
    sync,mixed,stems=native()
    runtime=probe_local_runtime();profile=probe_profile(runtime);job=build_job(mixed,sync)
    key=Ed25519PrivateKey.generate();now=int(time.time())
    trust={'schema_version':'bie.audio.kernel-trust/1','revision':'TEST_ONLY_EPHEMERAL',
        'scope':KERNEL_SCOPE,'profile_fingerprints':[profile['fingerprint']],
        'evaluator_trust':{'schema_version':'bie.audio.evaluator-trust/1',
        'revision':'TEST_ONLY_EPHEMERAL','scope':SCOPE,'max_age_seconds':3600,
        'max_future_skew_seconds':30,'issuers':[{'key_id':KEY_ID,'role':'acoustic-evaluator',
        'public_key_hex':key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex(),
        'runtime_fingerprints':[runtime['fingerprint']],'not_before':now-3600,
        'not_after':now+86400,'revoked':False}]}}
    request=build_kernel_request(job,profile=profile,runtime=runtime,run_id=RUN_ID,
        job_id='synthetic-kernel-fixture',revision='H4R1-r1',key_id=KEY_ID)
    return {'sync':sync,'mixed':mixed,'stems':stems,'job':job,'runtime':runtime,
        'profile':profile,'key':key,'trust':trust,'request':request}

@lru_cache(maxsize=1)
def actual_receipt():
    c=context()
    with tempfile.TemporaryDirectory(prefix='bie-h4r-fixture-') as td:
        return issue_kernel_evaluation(c['job'],c['mixed'].wav_bytes,c['runtime'],c['profile'],
            c['trust'],c['key'],KEY_ID,lock_root=Path(td)/'slots',
            request_fingerprint=c['request']['fingerprint'])

def resign(receipt,key=None):
    r=clone(receipt);key=context()['key'] if key is None else key
    r['signature_ed25519_hex']=key.sign(DOMAIN+canonical(r['payload'])).hex()
    return r

def verify(receipt=None,trust=None,profile=None,now=None,request_fingerprint=None):
    from bie.audio.kernel_evidence import verify_kernel_receipt
    c=context()
    return verify_kernel_receipt(actual_receipt() if receipt is None else receipt,c['job'],c['runtime'],
        c['profile'] if profile is None else profile,c['trust'] if trust is None else trust,
        now=now,request_fingerprint=request_fingerprint)

def pipeline(root,**overrides):
    from bie.audio.kernel_durable import evaluate_kernel_durable
    c=context();options=dict(root=root,run_id=RUN_ID,job_id='synthetic-kernel-fixture',revision='H4R1-r1',
        runtime=c['runtime'],profile=c['profile'],trust=c['trust'],signer=c['key'],key_id=KEY_ID)
    options.update(overrides)
    return evaluate_kernel_durable(c['mixed'],c['sync'],**options)
