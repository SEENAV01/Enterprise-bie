"""Shared immutable byte/binding validation; uses existing QA stores and reports."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from fractions import Fraction
import math
from ..native_quality_v2.common import (Binding, Finding, Report, require, fields, items,
    text, unique, read_json, report, approved, Review, ReviewVerifier, SnapshotStore,
    ArtifactRef, ContractError, canonical_bytes, digest, integer, token, binding_matches)
from ..math_v2.expression import rational, qtext, bounded

SCHEMA='bie.qa.domain-quality-input/1'

def native_digest(value):
    """Lossless typed fingerprint for native float-bearing observations.

    Does not loosen the inherited float-free release contract, round observations,
    or confuse an integer with a float. Tags on *every* node avoid marker collisions.
    Python hexadecimal floats retain the exact observed finite binary value.
    """
    count=0
    def encode(v,depth=0):
        nonlocal count
        count+=1;require(depth<=32 and count<=50000,'H4_NATIVE_DIGEST_BUDGET')
        if v is None:return ['none']
        if type(v)is bool:return ['bool',v]
        if type(v)is int:return ['int',v]
        if type(v)is str:return ['str',v]
        if type(v)is float:
            require(math.isfinite(v),'H4_NONFINITE_NATIVE_VALUE')
            return ['float_hex',v.hex()]
        if type(v)in (list,tuple):return ['sequence',[encode(x,depth+1)for x in v]]
        require(type(v)is dict and all(type(k)is str for k in v),'H4_NATIVE_DIGEST_TYPE')
        return ['map',[[k,encode(v[k],depth+1)]for k in sorted(v)]]
    return digest({'encoding':'bie.qa.lossless-native-tree/1','value':encode(value)})

def ids(values, name, minimum=1):
    require(type(values) in (list,tuple) and minimum<=len(values)<=1024,name+'_COUNT')
    for x in values: token(x,name)
    require(len(set(values))==len(values),name+'_DUPLICATE')
    return tuple(values)

def read_input(root, ref, binding, policy, task, extra):
    require(type(binding) is Binding and binding.policy_digest==policy.content_digest,'H4_POLICY_BINDING')
    require(type(ref) is ArtifactRef,'H4_ARTIFACT_REF')
    with SnapshotStore(root) as store: data=read_json(store,ref)
    fields(data,('schema_version','task_id','binding',*extra),'H4_INPUT_FIELDS')
    require(data['schema_version']==SCHEMA and data['task_id']==task,'H4_INPUT_SCHEMA_TASK')
    binding_matches(data['binding'],binding)
    return data

def finish(task,binding,findings,refs,details):
    # This layer validates finite structured evidence, never establishes its natural-
    # language interpretation, operational provenance or end-to-end media coverage.
    findings.append(Finding('CONTEXTUAL_AND_NATIVE_E2E_REVIEW_REQUIRED',task))
    return report(task,binding,findings,refs,{'lossless_details_digest':native_digest(details)}), details

def verify_sources(root,refs):
    require(type(refs) is tuple and bool(refs) and all(type(r)is ArtifactRef for r in refs),'H4_SOURCE_REFS')
    ids([r.artifact_id for r in refs],'SOURCE')
    require(len({r.path for r in refs})==len(refs),'H4_SOURCE_PATH_ALIAS')
    with SnapshotStore(root) as store:
        return {r.artifact_id:store.read(r).decode('utf-8',errors='strict') for r in refs}

@dataclass(frozen=True)
class Limits:
    max_records: int=256
    max_age: int=86400
    def __post_init__(self):
        integer(self.max_records,'records',1,1024);integer(self.max_age,'age',1,604800)

class PolicyDigest:
    @property
    def content_digest(self):return digest(asdict(self))
