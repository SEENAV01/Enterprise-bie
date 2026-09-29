"""Closed-world integer-only JSON. Trust is never decoded from a request."""
from dataclasses import fields
from ..release_v2.contracts import ArtifactRef, ContractError
from ..source_v2.codec import loads,request_from_dict as source_from_dict
from ..source_v2.models import Policy as SourcePolicy
from .models import (PrerequisiteRule,LearningEvent,MasteryEvidence,Statement,InferenceStep,Argument,
                     EvidenceLink,SourceLineage,CalibrationArtifact,ConfidenceDecision,ReasoningRequest,ReasoningPolicy)
from .logic import Expr
from .attestation import Review

def shape(data,cls):
    if type(data) is not dict or set(data)!={f.name for f in fields(cls)}:raise ContractError('REASONING_FIELDS_MISMATCH',cls.__name__)
    return dict(data)

def array(value,limit=4096):
    if type(value) is not list or len(value)>limit:raise ContractError('INVALID_REASONING_ARRAY')
    return tuple(value)

def expression(data,depth=1):
    if depth>16:raise ContractError('EXPRESSION_RESOURCE_LIMIT')
    d=shape(data,Expr);d['args']=tuple(expression(x,depth+1) for x in array(d['args'],2));return Expr(**d)

def simple(data,cls,tuples=()):
    d=shape(data,cls)
    for f in tuples:d[f]=array(d[f])
    if 'artifact' in d:d['artifact']=ArtifactRef(**shape(d['artifact'],ArtifactRef))
    return cls(**d)

def request_from_dict(data):
    d=shape(data,ReasoningRequest);d['source']=source_from_dict(d['source'])
    for f,cls,ts in (('events',LearningEvent,('claim_ids',)),('masteries',MasteryEvidence,()),
       ('steps',InferenceStep,('premise_ids',)),('arguments',Argument,('statement_ids','premise_ids','step_ids','assumption_ids')),
       ('evidence',EvidenceLink,('citation_ids',)),('calibrations',CalibrationArtifact,()),
       ('decisions',ConfidenceDecision,('disclosure_claim_ids',))):
        d[f]=tuple(simple(x,cls,ts) for x in array(d[f]))
    statements=[]
    for raw in array(d['statements']):
        s=shape(raw,Statement);s['expression']=expression(s['expression']);statements.append(Statement(**s))
    d['statements']=tuple(statements);return ReasoningRequest(**d)

def policy_from_dict(data):
    d=shape(data,ReasoningPolicy);d['source']=simple(d['source'],SourcePolicy,('expected_output_ids',))
    for f in ('concepts','target_concepts','expected_argument_ids'):d[f]=array(d[f])
    d['prerequisites']=tuple(simple(x,PrerequisiteRule) for x in array(d['prerequisites']))
    d['lineages']=tuple(simple(x,SourceLineage) for x in array(d['lineages']))
    return ReasoningPolicy(**d)

def load_request(data):return request_from_dict(loads(data))
def load_policy(data):return policy_from_dict(loads(data))
def load_reviews(data):return tuple(simple(x,Review,('evidence_ids',)) for x in array(loads(data),8192))
