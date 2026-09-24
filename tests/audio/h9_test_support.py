from __future__ import annotations
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from bie.audio.common import fingerprint
from bie.audio.evaluator_capability import AccentBinding, EvaluatorProfile, EvaluationRequirements
from bie.audio.evaluator_contract import EvaluationTarget, request_from_targets, EvaluatedTarget, EvaluationReport
from bie.audio.acoustic_calibration import CalibrationCase, CalibrationDataset, CalibrationPolicy, calibrate
from bie.audio.evaluator_authority import AuthorityPayload, AuthorityTrust, sign_authority

MEDIA='1'*64
RUNTIME='sha256:'+'2'*64
PLAN='sha256:'+'3'*64
CLOCK='sha256:'+'4'*64
TARGET1='sha256:'+'5'*64
TARGET2='sha256:'+'6'*64
VOICE='sha256:'+'7'*64
NOW=1_800_000_000

def profile(*, ipa=True,oov=True,code=True,languages=('en-US','hi-IN')):
    accents=tuple(AccentBinding(l,a,(f'evidence:{l}:{a}',)) for l,a in ((languages[0],'general'),))
    return EvaluatorProfile('eval-1','provider-1','model-1','r1',RUNTIME,tuple(languages),accents,'IPA',
        ('word_boundaries','phone_sequence','deviation_score','uncertainty'),ipa,oov,code,100,600,('model-card:1',))

def requirements(*,languages=('en-US',),accents=(('en-US','general'),),count=2,seconds=5,ipa=True,oov=True,code=False):
    return EvaluationRequirements(tuple(languages),tuple(accents),count,seconds,ipa,oov,code)

def targets(count=2):
    rows=[EvaluationTarget(TARGET1,'seg-1',0,'en-US','general','charge','tʃɑɹdʒ',True,0,100,('source:1',),VOICE),
          EvaluationTarget(TARGET2,'seg-1',1,'en-US','general','force',None,False,100,200,('source:2',),VOICE)]
    return tuple(rows[:count])

def request(prof=None,req=None,targs=None):
    prof=prof or profile(); targs=targs or targets(); req=req or requirements(count=len(targs))
    return request_from_targets(media_sha256=MEDIA,sample_rate=16000,total_samples=80000,plan_fingerprint=PLAN,
        clock_fingerprint=CLOCK,profile=prof,targets=targs,requirements=req)

def report(req=None,prof=None,scores=(100_000,120_000),uncertainties=(50_000,60_000),statuses=None):
    prof=prof or profile(); req=req or request(prof=prof)
    statuses=statuses or tuple('MEASURED' for _ in req.targets)
    rows=[]
    for i,t in enumerate(req.targets):
        measured=statuses[i]=='MEASURED'
        rows.append(EvaluatedTarget(t.target_fingerprint,statuses[i],scores[i] if measured else None,uncertainties[i] if measured else None,
            ('tʃ','ɑ','ɹ','dʒ') if measured and t.expected_ipa else (('f','ɔɹ','s') if measured else ()),
            t.start_sample if measured else None,t.end_sample if measured else None,t.is_oov if measured else False,()))
    return EvaluationReport(req.fingerprint(),prof.evaluator_id,prof.provider_id,prof.model_id,prof.model_revision,prof.runtime_fingerprint,
        prof.fingerprint(),req.media_sha256,tuple(rows))

def dataset(prof=None,*,scope='HELD_OUT_INDEPENDENT',held=True,independent=True,uncertain=0):
    prof=prof or profile(); rows=[]
    for i in range(20):
        rows.append(CalibrationCase(f'c{i}',fingerprint({'c':i}),f'{i+10:064x}','en-US','general','CORRECT',50_000+i*1000,
            500_000 if i<uncertain else 50_000,prof.fingerprint(),(f'label:{i}',)))
    for i in range(20):
        rows.append(CalibrationCase(f'e{i}',fingerprint({'e':i}),f'{i+100:064x}','en-US','general','PRONUNCIATION_ERROR',700_000+i*1000,
            50_000,prof.fingerprint(),(f'label:e{i}',)))
    return CalibrationDataset('ds-1','r1',prof.fingerprint(),tuple(rows),held,independent,scope,('dataset-card:1',))

def calibration(prof=None,ds=None):
    prof=prof or profile(); ds=ds or dataset(prof)
    return calibrate(ds,CalibrationPolicy())

def authority(prof=None,cal=None,*,production=True,custody='EXTERNAL_KMS_HSM',allow=True,role=None):
    prof=prof or profile(); cal=cal or calibration(prof)
    key=Ed25519PrivateKey.generate(); pub=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    role=role or ('PRODUCTION_RELEASE_AUTHORITY' if production else 'TEST_ONLY')
    payload=AuthorityPayload('issuer-1',role,'key-1',custody,prof.fingerprint(),cal.fingerprint(),'prod' if production else 'test',NOW,NOW+3600,('approval:1',))
    signed=sign_authority(payload,key); trust=AuthorityTrust('key-1','issuer-1',base64.b64encode(pub).decode(),allow)
    return signed,trust
