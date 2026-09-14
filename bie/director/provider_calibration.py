"""Independent benchmark release and external-provider calibration boundary.

This module closes the executable *harness* gap.  It cannot manufacture an
expert oracle, provider deployment, real-source corpus or product acceptance.
When no candidate is supplied the only truthful state is NOT_RUN.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib

from .contract_validation import finite, nonblank
from .director_artifacts import canonical, fingerprint
from .director_benchmark import (CandidateIdentity, DirectorBenchmarkReport,
    DirectorBenchmarkSuite, run_director_benchmark, validate_suite)
from .director_model import model_identity
from .semantic_execution import EvaluatorIdentity
from .source_grounding_qa import SourceBytes


def _instant(value, name):
    nonblank(value, name)
    try: result=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as error: raise ValueError('invalid '+name) from error
    if result.tzinfo is None: raise ValueError(name+' must include timezone')
    return result.astimezone(timezone.utc)


def source_receipts(suite, artifacts):
    validate_suite(suite)
    if type(artifacts) is not tuple or any(not isinstance(a,SourceBytes) or type(a.data) is not bytes for a in artifacts):
        raise ValueError('immutable benchmark source bytes required')
    needed={}
    for case in suite.cases:
        for page in case.request.catalog.pages:
            if page.source_id in needed and needed[page.source_id]!=page.source_sha256:
                raise ValueError('conflicting benchmark source revisions')
            needed[page.source_id]=page.source_sha256
    if len({a.source_id for a in artifacts})!=len(artifacts) or {a.source_id for a in artifacts}!=set(needed):
        raise ValueError('benchmark sources must exactly cover the suite')
    result=[]
    for source in sorted(artifacts,key=lambda a:a.source_id):
        nonblank(source.media_type,'source media type')
        digest='sha256:'+hashlib.sha256(source.data).hexdigest()
        if digest!=needed[source.source_id]:raise ValueError('benchmark source bytes changed')
        result.append((source.source_id,digest,source.media_type,len(source.data)))
    return tuple(result)


@dataclass(frozen=True)
class ProviderStackIdentity:
    generator: EvaluatorIdentity
    critic: EvaluatorIdentity
    annotator: EvaluatorIdentity
    reviewer: EvaluatorIdentity
    candidate: CandidateIdentity
    execution_mode: str
    deployment_environment: str

    def validate(self):
        for identity in (self.generator,self.critic,self.annotator,self.reviewer):model_identity(identity)
        if (self.annotator.provider,self.annotator.model)==(self.reviewer.provider,self.reviewer.model):
            raise ValueError('independent annotation reviewer identity required')
        for value in (self.candidate.name,self.candidate.version,self.candidate.code_sha256,
                      self.candidate.configuration_sha256,self.deployment_environment):nonblank(value,'provider stack identity')
        for value in (self.candidate.code_sha256,self.candidate.configuration_sha256):
            if not value.startswith('sha256:') or len(value)!=71:raise ValueError('candidate digest required')
        if self.execution_mode not in ('CONTROLLED_PROTOCOL','EXTERNAL_CONFIGURED_PROVIDER'):
            raise ValueError('known provider execution mode required')

    def fingerprint(self):self.validate();return fingerprint(asdict(self))


@dataclass(frozen=True)
class SignedBenchmarkRelease:
    release_id:str
    authority:str
    key_id:str
    suite_fingerprint:str
    oracle_author:str
    oracle_method:str
    source_byte_receipts:tuple[tuple[str,str,str,int],...]
    issued_at_utc:str
    signature:bytes

    def signed_payload(self):
        return {key:value for key,value in asdict(self).items() if key!='signature'}


@dataclass(frozen=True)
class VerifiedBenchmarkIdentity:
    authority:str
    key_id:str
    release_id:str
    verified_at_utc:str
    assurance:str


@dataclass(frozen=True)
class CalibrationPolicy:
    version:str='bie-dir-provider-calibration/1.0.0'
    repetitions:int=2
    minimum_case_fraction:float=1.0
    maximum_unstable_cases:int=0
    required_assurance:str='INDEPENDENT_BENCHMARK_AUTHORITY'

    def validate(self):
        if self.version!='bie-dir-provider-calibration/1.0.0':raise ValueError('unsupported calibration policy')
        if type(self.repetitions) is not int or self.repetitions<2 or self.repetitions>20:raise ValueError('bounded repeated calibration required')
        finite(self.minimum_case_fraction,'minimum case fraction',high=1)
        if type(self.maximum_unstable_cases) is not int or self.maximum_unstable_cases<0:raise ValueError('unstable-case budget required')
        nonblank(self.required_assurance,'benchmark assurance')


@dataclass(frozen=True)
class ProviderCalibrationReport:
    calibration_id:str
    status:str
    suite_fingerprint:str
    source_byte_receipts:tuple[tuple[str,str,str,int],...]
    provider_stack_fingerprint:str
    provider_stack:ProviderStackIdentity
    policy:CalibrationPolicy
    benchmark_release_fingerprint:str|None
    verification_identity:VerifiedBenchmarkIdentity|None
    benchmark_report:DirectorBenchmarkReport|None
    gates:tuple[tuple[str,bool],...]
    reason:str|None
    limitations:tuple[str,...]

    @property
    def eligible_for_acceptance_review(self):
        return self.status=='EXECUTED' and bool(self.gates) and all(value for _,value in self.gates)

    @property
    def accepted(self):return False

    def fingerprint(self):return fingerprint(asdict(self))


LIMITATIONS=(
    'A verified benchmark release authenticates its declared oracle payload; it does not prove the oracle is pedagogically sufficient.',
    'Provider stack identity and execution mode are retained provenance, not remote-code attestation.',
    'Benchmark success is evidence for governed human acceptance review, never automatic product acceptance.',
    'Real PDFs, representative learners, rendered media and playable-game outcomes require separate empirical evidence.',)


def planned_calibration(calibration_id,suite,artifacts,stack,reason,policy=CalibrationPolicy()):
    nonblank(calibration_id,'calibration identity');nonblank(reason,'calibration not-run reason')
    if not isinstance(stack,ProviderStackIdentity) or not isinstance(policy,CalibrationPolicy):raise ValueError('typed calibration inputs required')
    stack.validate();policy.validate();receipts=source_receipts(suite,artifacts)
    return ProviderCalibrationReport(calibration_id,'NOT_RUN',suite.fingerprint(),receipts,stack.fingerprint(),stack,policy,
        None,None,None,(('EXTERNAL_PROVIDER_EXECUTED',False),),reason,LIMITATIONS)


def _verify_release(suite,receipts,release,verifier,now_utc,policy):
    if not isinstance(release,SignedBenchmarkRelease):raise ValueError('signed benchmark release required')
    for value in (release.release_id,release.authority,release.key_id,release.oracle_author,release.oracle_method):nonblank(value,'benchmark release field')
    _instant(release.issued_at_utc,'benchmark release time');_instant(now_utc,'benchmark verification time')
    if type(release.signature) is not bytes or not 16<=len(release.signature)<=8192:raise ValueError('bounded benchmark signature required')
    if (release.suite_fingerprint,release.oracle_author,release.oracle_method,release.source_byte_receipts)!=(
            suite.fingerprint(),suite.oracle_author,suite.oracle_method,receipts):
        raise ValueError('benchmark release does not bind the exact suite and sources')
    if not callable(getattr(verifier,'verify_benchmark',None)):raise ValueError('configured benchmark authority verifier required')
    identity=verifier.verify_benchmark(canonical(release.signed_payload()).encode(),release.signature,
        release.authority,release.key_id,now_utc)
    if not isinstance(identity,VerifiedBenchmarkIdentity):raise ValueError('typed benchmark verification identity required')
    if (identity.authority,identity.key_id,identity.release_id)!=(release.authority,release.key_id,release.release_id):
        raise ValueError('benchmark verification identity mismatch')
    if identity.assurance!=policy.required_assurance:raise ValueError('insufficient benchmark authority assurance')
    _instant(identity.verified_at_utc,'benchmark identity verification time')
    return identity


def run_provider_calibration(calibration_id,suite,artifacts,stack,candidate,release,verifier,*,now_utc,
                             policy=CalibrationPolicy()):
    nonblank(calibration_id,'calibration identity')
    if not isinstance(stack,ProviderStackIdentity) or not isinstance(policy,CalibrationPolicy):raise ValueError('typed calibration inputs required')
    stack.validate();policy.validate();receipts=source_receipts(suite,artifacts)
    identity=_verify_release(suite,receipts,release,verifier,now_utc,policy)
    report=run_director_benchmark(suite,candidate,artifacts,stack.candidate,repetitions=policy.repetitions)
    gates=(('SIGNED_ORACLE_VERIFIED',True),('SOURCE_BYTES_PINNED',report.source_byte_receipts==receipts),
        ('ALL_CASE_CHECKS_PASSED',report.checks_passed),('MINIMUM_CASE_FRACTION',report.passed_case_fraction>=policy.minimum_case_fraction),
        ('REPLAY_STABLE',len(report.unstable_cases)<=policy.maximum_unstable_cases),
        ('NO_QA_BLOCKER',report.qa_status!='BLOCKED'),
        ('EXTERNAL_PROVIDER_EXECUTED',stack.execution_mode=='EXTERNAL_CONFIGURED_PROVIDER'))
    release_fingerprint=fingerprint({**release.signed_payload(),
        'signature_sha256':'sha256:'+hashlib.sha256(release.signature).hexdigest()})
    return ProviderCalibrationReport(calibration_id,'EXECUTED',suite.fingerprint(),receipts,stack.fingerprint(),stack,policy,
        release_fingerprint,identity,report,gates,None,LIMITATIONS)
