"""RATER-003: signed, scoped human review; roles and identity are operator-owned."""
from ..models import BenchmarkError,digest,exact_fields,ident
from .contracts import context,pinned,make_assessment
from .judgement import rubric as check_rubric,grade
from .auth import verify

def assignment(ctx,rubric,*,reviewer_id,candidate_author_id):
    ctx=context(ctx);check_rubric(rubric);pinned(rubric,ctx['rubric_sha256'])
    ident(reviewer_id);ident(candidate_author_id)
    if reviewer_id in {candidate_author_id,rubric['owner_id']}:
        raise BenchmarkError('HUMAN_REVIEW_CONFLICT_OF_INTEREST')
    row={'context':ctx,'reviewer_id':reviewer_id,'candidate_author_id':candidate_author_id,
         'rubric_sha256':digest(rubric),'rubric_unit_ids':sorted(r['id'] for r in rubric['units'])}
    row['assignment_sha256']=digest(row);return row

def execute(ctx,rubric,token,*,trust,authenticated_subject,candidate_author_id,now,production=False):
    a=assignment(ctx,rubric,reviewer_id=authenticated_subject,candidate_author_id=candidate_author_id)
    p=verify(token,trust,kind='HUMAN_REVIEW',scope_sha256=a['assignment_sha256'],now=now,production=production)
    if p['subject_id']!=authenticated_subject:raise BenchmarkError('HUMAN_AUTHENTICATED_IDENTITY_MISMATCH')
    exact_fields(p['claims'],{'units','conflicts_declared'})
    if p['claims']['conflicts_declared'] is not False:raise BenchmarkError('HUMAN_DECLARED_CONFLICT')
    value,reasons=grade(rubric,p['claims']['units'])
    return make_assessment(ctx,authenticated_subject,'HUMAN',value,reasons=reasons,
        evidence={'assignment_sha256':a['assignment_sha256'],'attestation_sha256':digest(token),'attestation':token,
                  'key_id':p['key_id'],'reviewer_expertise_independently_verified':False},
        execution='FIXTURE' if trust[p['key_id']]['fixture_only'] else 'HUMAN_ATTESTATION')
