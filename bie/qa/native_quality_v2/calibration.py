"""HARD010: held-out calibration and criterion floors, not fabricated quality scores."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from fractions import Fraction
from .common import *

@dataclass(frozen=True,slots=True)
class CriterionFloor:
    criterion_id: str
    minimum_score: int
    critical: bool
    def __post_init__(self):
        token(self.criterion_id,'criterion');integer(self.minimum_score,'minimum_score',0,1000000)
        require(type(self.critical) is bool,'CRITICAL_TYPE')

@dataclass(frozen=True,slots=True)
class RaterIdentity:
    rater_id: str
    model_version: str
    principal: str
    independence_group: str
    def __post_init__(self):
        for field in ('rater_id','model_version','principal','independence_group'):token(getattr(self,field),field)

@dataclass(frozen=True,slots=True)
class CalibrationPolicy:
    criteria: tuple[CriterionFloor,...]
    raters: tuple[RaterIdentity,...]
    domain: str
    language: str
    minimum_positive_per_criterion: int = 2
    minimum_negative_per_criterion: int = 2
    minimum_accuracy_ppm: int = 900000
    minimum_agreement_ppm: int = 900000
    max_age_seconds: int = 86400
    def __post_init__(self):
        require(type(self.criteria) is tuple and bool(self.criteria) and all(type(c) is CriterionFloor for c in self.criteria),'CALIBRATION_CRITERIA')
        require(len({c.criterion_id for c in self.criteria})==len(self.criteria),'CALIBRATION_DUPLICATE_CRITERION')
        require(type(self.raters) is tuple and 2<=len(self.raters)<=8 and all(type(r) is RaterIdentity for r in self.raters),'CALIBRATION_RATERS')
        for f in ('rater_id','principal','independence_group'):
            require(len({getattr(r,f) for r in self.raters})==len(self.raters),'RATERS_NOT_INDEPENDENT')
        token(self.domain,'domain');token(self.language,'language')
        for f in ('minimum_positive_per_criterion','minimum_negative_per_criterion'):integer(getattr(self,f),f,1,100000)
        for f in ('minimum_accuracy_ppm','minimum_agreement_ppm'):integer(getattr(self,f),f,1,1000000)
        integer(self.max_age_seconds,'max_age_seconds',1,604800)
    @property
    def content_digest(self):return digest(asdict(self))


def evaluate_calibration(corpus_ref: ArtifactRef,predictions_ref: ArtifactRef,root,binding: Binding,
                         policy: CalibrationPolicy,*,review: Review | None=None,verifier: ReviewVerifier | None=None,
                         now: int) -> tuple[Report,dict]:
    require(binding.policy_digest==policy.content_digest,'CALIBRATION_POLICY_BINDING')
    verifier=verifier or ReviewVerifier();findings=[]
    with SnapshotStore(root) as store:
        corpus=read_json(store,corpus_ref);pred=read_json(store,predictions_ref)
    fields(corpus,('schema_version','corpus_id','domain','language','rubric_digest','created_at','training_source_hashes','cases','provenance_mode'))
    require(corpus['schema_version']=='bie.qa.calibration-corpus/1','CALIBRATION_SCHEMA')
    token(corpus['corpus_id'],'corpus_id');integer(corpus['created_at'],'created_at')
    if (corpus['domain'],corpus['language'],corpus['rubric_digest'])!=(policy.domain,policy.language,policy.content_digest):findings.append(Finding('CALIBRATION_SCOPE_MISMATCH','corpus','BLOCKER'))
    if not 0<=now-corpus['created_at']<=policy.max_age_seconds:findings.append(Finding('CALIBRATION_STALE','corpus','BLOCKER'))
    require(corpus['provenance_mode'] in ('diagnostic','independent'),'CALIBRATION_PROVENANCE')
    train=items(corpus['training_source_hashes'],'TRAINING_HASHES');require(len(set(train))==len(train),'DUPLICATE_TRAINING_HASH')
    for value in train:sha256(value,'training_hash')
    cases=items(corpus['cases'],'CASES',1);by_id=unique(cases,'case_id','CALIBRATION_CASE_DUPLICATE')
    criteria={c.criterion_id:c for c in policy.criteria};holdout=[];hashes=set()
    for c in cases:
        fields(c,('case_id','source_sha256','input_sha256','split','labels','blind_id'))
        token(c['case_id'],'case_id');token(c['blind_id'],'blind_id');sha256(c['source_sha256'],'source_sha');sha256(c['input_sha256'],'input_sha')
        require(c['split'] in ('train','holdout'),'CALIBRATION_SPLIT')
        require(type(c['labels']) is dict and set(c['labels'])==set(criteria) and all(type(v) is bool for v in c['labels'].values()),'CALIBRATION_LABELS')
        if c['split']=='holdout':
            if c['source_sha256'] in train or c['input_sha256'] in hashes:findings.append(Finding('CALIBRATION_HOLDOUT_LEAKAGE',c['case_id'],'BLOCKER'))
            hashes.add(c['input_sha256']);holdout.append(c)
    all_train={c['source_sha256'] for c in cases if c['split']=='train'}|set(train)
    train_inputs={c['input_sha256'] for c in cases if c['split']=='train'}
    if any(c['source_sha256'] in all_train or c['input_sha256'] in train_inputs for c in holdout):findings.append(Finding('CALIBRATION_HOLDOUT_LEAKAGE','corpus','BLOCKER'))
    require(bool(holdout),'CALIBRATION_HOLDOUT_EMPTY')
    require(len({c['blind_id'] for c in cases})==len(cases),'BLIND_ID_DUPLICATE')
    fields(pred,('schema_version','corpus_sha256','policy_digest','raters','predictions'))
    require(pred['schema_version']=='bie.qa.calibration-predictions/1' and pred['corpus_sha256']==corpus_ref.sha256 and pred['policy_digest']==policy.content_digest,'PREDICTION_BINDING')
    require(pred['raters']==[asdict(r) for r in policy.raters],'RATER_IDENTITY_MISMATCH')
    rows=items(pred['predictions'],'PREDICTIONS',1,MAX_ITEMS*8)
    rater_ids={r.rater_id for r in policy.raters};hold_ids={c['case_id'] for c in holdout}
    values={}
    for p in rows:
        fields(p,('case_id','rater_id','scores'))
        key=(p['case_id'],p['rater_id']);require(key not in values,'PREDICTION_DUPLICATE')
        require(p['case_id'] in hold_ids and p['rater_id'] in rater_ids,'PREDICTION_UNKNOWN_ID')
        require(type(p['scores']) is dict and set(p['scores'])==set(criteria),'PREDICTION_CRITERION_COVERAGE')
        for score in p['scores'].values():integer(score,'score',0,1000000)
        values[key]=p['scores']
    require(set(values)=={(c,r) for c in hold_ids for r in rater_ids},'PREDICTION_CASE_COVERAGE')
    metrics={}
    for cid,floor in criteria.items():
        positive=sum(c['labels'][cid] for c in holdout);negative=len(holdout)-positive
        if positive<policy.minimum_positive_per_criterion or negative<policy.minimum_negative_per_criterion:
            findings.append(Finding('CALIBRATION_CLASS_COVERAGE',cid,'BLOCKER'))
        correct=0;false_clear=0;agreement=0
        for c in holdout:
            decisions=[values[(c['case_id'],r.rater_id)][cid]>=floor.minimum_score for r in policy.raters]
            correct+=sum(d==c['labels'][cid] for d in decisions)
            false_clear+=sum(d and not c['labels'][cid] for d in decisions)
            agreement+=len(set(decisions))==1
        total=len(holdout)*len(policy.raters)
        accuracy=Fraction(correct,max(total,1));agree=Fraction(agreement,max(len(holdout),1))
        metrics[cid]=dict(positives=positive,negatives=negative,correct=correct,total=total,false_clear=false_clear,accuracy=str(accuracy),agreement=str(agree))
        if accuracy*1_000_000<policy.minimum_accuracy_ppm:findings.append(Finding('CALIBRATION_ACCURACY_FLOOR',cid,'BLOCKER'))
        if agree*1_000_000<policy.minimum_agreement_ppm:findings.append(Finding('CALIBRATION_RATER_DISAGREEMENT',cid,'BLOCKER'))
        if floor.critical and false_clear:findings.append(Finding('CRITICAL_DEFECT_FALSE_CLEAR',cid,'BLOCKER'))
    bound=digest(dict(binding=asdict(binding),corpus=asdict(corpus_ref),predictions=asdict(predictions_ref)))
    authorization=approved(review,verifier,subject=corpus['corpus_id'],purpose='calibration',request_digest=bound,
        policy_digest=policy.content_digest,now=now,evidence_ids=(corpus_ref.artifact_id,predictions_ref.artifact_id),max_age=policy.max_age_seconds)
    if authorization!='VERIFIED':findings.append(Finding('CALIBRATION_AUTHORITY_REQUIRED','corpus','BLOCKER' if authorization=='BLOCKED' else 'REVIEW'))
    if corpus['provenance_mode']=='diagnostic':findings.append(Finding('DIAGNOSTIC_CALIBRATION_NOT_EMPIRICAL','corpus'))
    details=dict(metrics=metrics,calibration_request_digest=bound,authority=authorization,learning_efficacy_established=False)
    return report('BIE-QA-HARD-010',binding,findings,(corpus_ref,predictions_ref),details),details


def evaluate_quality(scores: dict[str,dict[str,int]],policy: CalibrationPolicy,calibration_report: Report) -> dict:
    """Each rater and each criterion has a floor; style cannot average away content."""
    require(type(calibration_report) is Report and calibration_report.task_id=='BIE-QA-HARD-010','QUALITY_CALIBRATION_REQUIRED')
    require(calibration_report.binding.policy_digest==policy.content_digest,'QUALITY_POLICY_BINDING')
    require(type(scores) is dict and set(scores)=={r.rater_id for r in policy.raters},'QUALITY_RATER_COVERAGE')
    failures=[];disagreements=[]
    for r,row in scores.items():
        require(type(row) is dict and set(row)=={c.criterion_id for c in policy.criteria},'QUALITY_CRITERION_COVERAGE')
        for v in row.values():integer(v,'quality_score',0,1_000_000)
    for c in policy.criteria:
        votes=[row[c.criterion_id]>=c.minimum_score for row in scores.values()]
        if not all(votes):failures.append(c.criterion_id)
        if len(set(votes))>1:disagreements.append(c.criterion_id)
    status='BLOCKED' if failures or calibration_report.status=='BLOCKED' else 'REVIEW_REQUIRED' if calibration_report.status!='LOCAL_CHECKS_CLEAR' else 'LOCAL_CHECKS_CLEAR'
    return dict(status=status,failed_criteria=failures,disagreements=disagreements,product_accepted=False,release_authorized=False)
