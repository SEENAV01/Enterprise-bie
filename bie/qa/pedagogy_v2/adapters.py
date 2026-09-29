"""Exercise preserved native PED interfaces, without laundering their PASS flags."""
from dataclasses import dataclass
import math
from ..release_v2.contracts import ContractError
from ..source_v2.models import Request
from bie.pedagogy.learning_objective_generator import LearningObjective
from bie.pedagogy.assessment_blueprint import AssessmentBlueprintReport,build_assessment_blueprint
from bie.pedagogy.cognitive_load_qa import cognitive_load_qa
from bie.pedagogy.multi_constraint_sequencer import SequencingResult,sequence_curriculum
from .models import ObjectiveRequirement,Objective

@dataclass(frozen=True,slots=True)
class NativeInspection:
    component:str
    native_checks_passed:bool
    disposition:str='REVIEW_REQUIRED'
    product_accepted:bool=False

def import_objective(native,requirement,source,*,statement_claim_ids,citation_ids,level):
    if type(native) is not LearningObjective or type(requirement) is not ObjectiveRequirement or type(source) is not Request:raise ContractError('INVALID_NATIVE_OBJECTIVE_INPUT')
    if (native.objective_id,native.concept_id)!=(requirement.objective_id,requirement.concept_id):raise ContractError('NATIVE_OBJECTIVE_IDENTITY_MISMATCH')
    claims={c.claim_id:c for c in source.claims};cites={c.citation_id:c for c in source.citations}
    if type(statement_claim_ids) is not tuple or type(citation_ids) is not tuple or not statement_claim_ids or not citation_ids:raise ContractError('NATIVE_OBJECTIVE_BINDINGS_REQUIRED')
    if any(c not in claims for c in statement_claim_ids) or any(c not in cites for c in citation_ids):raise ContractError('NATIVE_OBJECTIVE_LINK_MISSING')
    if native.statement!=' '.join(claims[c].text for c in statement_claim_ids):raise ContractError('NATIVE_OBJECTIVE_TEXT_MISMATCH')
    if set(native.evidence_ids)!=set(citation_ids):raise ContractError('NATIVE_OBJECTIVE_EVIDENCE_MISMATCH')
    if level not in requirement.allowed_levels:raise ContractError('NATIVE_OBJECTIVE_LEVEL_MISMATCH')
    return Objective(native.objective_id,native.concept_id,level,statement_claim_ids,tuple(c.criterion_id for c in requirement.criteria),citation_ids,requirement.mastery_threshold_ppm)

def inspect_blueprint(actual,requirements,cells):
    if type(actual) is not AssessmentBlueprintReport:raise ContractError('INVALID_NATIVE_BLUEPRINT')
    expected=build_assessment_blueprint(requirements,cells)
    if actual!=expected:raise ContractError('EDITED_NATIVE_BLUEPRINT')
    return NativeInspection('assessment_blueprint',expected.passed)

def inspect_load(values,*,max_load,max_jump):
    if type(values) is not tuple or not values:raise ContractError('EMPTY_NATIVE_LOAD_SCOPE')
    ids=[]
    for row in values:
        if type(row) is not tuple or len(row)!=2 or type(row[0]) is not str or not row[0].strip() or type(row[1]) not in (int,float) or not math.isfinite(row[1]):raise ContractError('INVALID_NATIVE_LOAD_VALUE')
        ids.append(row[0])
    if len(set(ids))!=len(ids):raise ContractError('DUPLICATE_NATIVE_LOAD_ID')
    if type(max_load) not in (int,float) or type(max_jump) not in (int,float):raise ContractError('INVALID_NATIVE_LOAD_LIMIT')
    report=cognitive_load_qa(values,max_load=max_load,max_jump=max_jump)
    return NativeInspection('cognitive_load_qa',report.passed)

def inspect_sequence(actual,nodes,constraints,*,max_adjacent_load):
    if type(actual) is not SequencingResult:raise ContractError('INVALID_NATIVE_SEQUENCE')
    expected=sequence_curriculum(nodes,constraints,max_adjacent_load=max_adjacent_load)
    if actual!=expected:raise ContractError('EDITED_NATIVE_SEQUENCE')
    return NativeInspection('multi_constraint_sequencer',not expected.violated_soft_constraints)
