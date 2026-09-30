"""H3-001: explicit versioned AV profiles, never silent legacy upgrades."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from ..models import BenchmarkError,canonical_json,strict_loads,digest,digest_string,ident,text,version_tuple
from ..av.custody import Limits,exact_fields,integer
from ..av.service import validate_policy
from ..metrics.common import indexed

SCHEMA = 'metric-av-reference-3'
CANDIDATE_SCHEMA = 'metric-av-candidate-3'
METRICS = ('BIE-EVAL-METRIC-012','BIE-EVAL-METRIC-013','BIE-EVAL-METRIC-015')
REF_FIELDS = {'schema_version','metric_id','rubric_id','version','reference_owner_id','evidence_grade',
              'source_refs','av_policy','limits_sha256','frame_reference','a11y_reference'}

@dataclass(frozen=True)
class ExecutionContext:
    # Must come from the trusted evaluator/operator, never the submitted JSON.
    artifact_root: str | Path
    limits: Limits = Limits()
    def __post_init__(self):
        if not isinstance(self.artifact_root,(str,Path)) or type(self.limits) is not Limits:
            raise BenchmarkError('AV_EXECUTION_CONTEXT_INVALID')

def snapshot(value: Any) -> Any:
    return strict_loads(canonical_json(value))

def validate_reference(value, metric_id):
    r=snapshot(value);exact_fields(r,REF_FIELDS)
    if r['schema_version']!=SCHEMA or metric_id not in METRICS or r['metric_id']!=metric_id:
        raise BenchmarkError('AV_PROFILE_METRIC_MISMATCH')
    for k in ('rubric_id','reference_owner_id'):ident(r[k])
    version_tuple(r['version'])
    if r['evidence_grade'] not in ('AUTHORED_DIAGNOSTIC','REFERENCE_CANDIDATE'):
        raise BenchmarkError('AV_REFERENCE_GRADE_INVALID')
    for row in indexed(r['source_refs'],{'id','locator','basis_sha256'},lower=1).values():
        text(row['locator']);digest_string(row['basis_sha256'])
    validate_policy(r['av_policy']);digest_string(r['limits_sha256'])
    if metric_id==METRICS[1]:
        exact_fields(r['frame_reference'],{'decoded_sha256','frame_chain_sha256','ffmpeg_sha256'})
        for v in r['frame_reference'].values():digest_string(v)
    elif r['frame_reference'] is not None:raise BenchmarkError('UNUSED_FRAME_REFERENCE')
    if metric_id==METRICS[2]:
        if type(r['a11y_reference']) is not dict:raise BenchmarkError('STATIC_ACCESSIBILITY_REFERENCE_REQUIRED')
        if not r['av_policy']['require_captions'] or not r['av_policy']['require_audio']:
            raise BenchmarkError('ACCESSIBILITY_AV_POLICY_INCOMPLETE')
    elif r['a11y_reference'] is not None:raise BenchmarkError('UNUSED_ACCESSIBILITY_REFERENCE')
    return r

def relative_path(value):
    # Portable strict subset; reject alternate separators, drive names and controls.
    if type(value) is not str or not value or len(value)>1024 or any(ord(c)<32 or ord(c)==127 for c in value):
        raise BenchmarkError('ADOPTION_PATH_UNSAFE')
    if value.startswith('/') or '\\' in value or ':' in value or any(x in ('','.','..') for x in value.split('/')):
        raise BenchmarkError('ADOPTION_PATH_UNSAFE')
    return value

def artifact(value, maximum):
    exact_fields(value,{'path','sha256','size_bytes'})
    relative_path(value['path']);digest_string(value['sha256']);integer(value['size_bytes'],1,maximum)
    return value

def validate_candidate(value, metric_id, limits):
    c=snapshot(value);exact_fields(c,{'schema_version','media','captions','caption_format','a11y_candidate'})
    if c['schema_version']!=CANDIDATE_SCHEMA:raise BenchmarkError('AV_CANDIDATE_SCHEMA_INVALID')
    artifact(c['media'],limits.max_input_bytes)
    if c['captions'] is not None:
        artifact(c['captions'],1_000_000)
        if c['captions']['path']==c['media']['path']:raise BenchmarkError('DUPLICATE_ARTIFACT_PATH')
        if c['caption_format'] not in ('srt','vtt'):raise BenchmarkError('UNSUPPORTED_CAPTION_FORMAT')
    elif c['caption_format'] is not None:raise BenchmarkError('UNUSED_CAPTION_FORMAT')
    if metric_id==METRICS[2]:
        if type(c['a11y_candidate']) is not dict:raise BenchmarkError('STATIC_ACCESSIBILITY_CANDIDATE_REQUIRED')
    elif c['a11y_candidate'] is not None:raise BenchmarkError('UNUSED_ACCESSIBILITY_CANDIDATE')
    return c

def content_identity(candidate):
    # Paths cannot create a second attempt for identical content in one campaign.
    def row(v):return None if v is None else {k:v[k] for k in ('sha256','size_bytes')}
    return digest({'media':row(candidate['media']),'captions':row(candidate['captions']),
        'caption_format':candidate['caption_format'],'a11y_candidate':candidate['a11y_candidate']})
