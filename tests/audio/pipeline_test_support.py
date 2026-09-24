"""H5 synthetic fixtures: actual canonical native output, ephemeral test keys only."""
from functools import lru_cache
from dataclasses import asdict
from pathlib import Path
import copy,json,tempfile,time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from bie.audio.pipeline_profile import probe_profile
from bie.audio.pipeline_contract import build_request,SCOPE
from bie.audio.pipeline_evidence import issue_execution,verify_receipt,DOMAIN
from bie.audio.acoustic_contract import canonical
KEY='TEST_ONLY_H5_DO_NOT_APPROVE_IN_PRODUCTION'
RUN='01952504-3824-4000-8000-000000000005'
ROOT=Path(__file__).resolve().parents[2]

def clone(value):return copy.deepcopy(value)

@lru_cache(maxsize=1)
def context():
    profile=probe_profile();key=Ed25519PrivateKey.generate();now=int(time.time())
    source=json.loads((ROOT/'examples/audio_h5/english.json').read_text())
    request=build_request(source,profile_fingerprint=profile['fingerprint'],run_id=RUN,job_id='synthetic-h5',revision='r1',key_id=KEY)
    trust={'schema_version':'bie.audio.pipeline-trust/1','revision':'TEST_ONLY_EPHEMERAL','scope':SCOPE,
        'max_age_seconds':3600,'max_future_skew_seconds':30,'issuers':[{'key_id':KEY,'role':'audio-pipeline-executor',
        'public_key_hex':key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex(),
        'profile_fingerprints':[profile['fingerprint']],'not_before':now-3600,'not_after':now+86400,'revoked':False}]}
    return {'profile':profile,'key':key,'source':source,'request':request,'trust':trust}


def request(**kwargs):
    c=context();options=dict(profile_fingerprint=c['profile']['fingerprint'],run_id=RUN,job_id='synthetic-h5',revision='r1',key_id=KEY)
    source=kwargs.pop('source',c['source']);options.update(kwargs)
    return build_request(source,**options)

@lru_cache(maxsize=1)
def actual():
    c=context()
    with tempfile.TemporaryDirectory() as td:
        return issue_execution(c['request'],c['profile'],c['trust'],c['key'],lock_root=Path(td)/'slots')


def verify(receipt=None,files=None,request_value=None,profile=None,trust=None,now=None):
    c=context();f,r=actual()
    return verify_receipt(r if receipt is None else receipt,f if files is None else files,
        c['request'] if request_value is None else request_value,c['profile'] if profile is None else profile,
        c['trust'] if trust is None else trust,now=now)


def resign(receipt):
    r=clone(receipt);r['signature_ed25519_hex']=context()['key'].sign(DOMAIN+canonical(r['payload'])).hex();return r


def store_actual(root):
    from bie.audio.pipeline_durable import PipelineArtifactStore,PipelineCoordinator
    c=context();files,receipt=actual();store=PipelineArtifactStore(Path(root)/'artifacts',profile=c['profile'])
    ref=store.put(c['request'],files,receipt,c['trust']);jobs=PipelineCoordinator(Path(root)/'jobs')
    return store,ref,jobs
