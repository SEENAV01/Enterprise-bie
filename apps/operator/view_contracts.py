"""Bounded projections of canonical artifacts. No engine, generation or acceptance.

Producer ports accept canonical documents; display projections are derived only
after native validation. Unknown fields fail closed rather than leaking raw JSON.
"""
from dataclasses import asdict, fields, is_dataclass
from enum import Enum
import math, re
from .contracts import require, canonical, OperatorError
from bie.reasoning import decision_contracts as re_contract
from bie.reasoning.reasoning_status_semantics import normalize_status
from bie.pedagogy import book_scale_curriculum_optimizer as curriculum
from bie.pedagogy.pedagogy_plan_contract import PedagogyDecision, build_pedagogy_plan
from bie.director.lesson_architecture_contract import LessonSceneIntent, build_lesson_architecture, validate_lesson_architecture
from bie.director.script_plan import ScriptSegment, build_script_plan, validate_script_plan
from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
from bie.scene_ir.schema_validation import validate_schema_shape
from bie.scene_ir.temporal_validation import validate_temporal
from bie.scene_ir.spatial_validation import validate_spatial
from bie.scene_ir.accessibility_validation import validate_accessibility
from bie.game_engine.director_engine import contracts as game
from bie.game_engine.provenance import ProvenanceBundle, EvidenceRef as GameEvidence
from bie.game_engine.codec import encode

KINDS=('reasoning','curriculum','lesson','director','scene_ir','game_plan')
MAX_DOCUMENT=512*1024
MAX_ITEMS=200

def ident(value):
    # Canonical semantic IDs use namespaces (e.g. concept:coulomb). They are
    # dictionary identifiers, never filesystem paths or shell arguments.
    require(type(value) is str and value not in ('.','..') and re.fullmatch(r'[A-Za-z0-9_.:-]{1,160}',value,re.ASCII) is not None,
            'view_identifier_invalid',400)
    return value

def shape(value, required, optional=()):
    require(type(value) is dict and set(required)<=set(value)<=set(required)|set(optional),'view_schema_invalid',400)
    return value

def seq(value, allow_empty=False):
    require(type(value) in (list,tuple) and (allow_empty or len(value)>0) and len(value)<=MAX_ITEMS,'view_collection_invalid',400)
    return list(value)

def text(value, maximum=2000):
    require(type(value) is str and 0<len(value.strip())<=maximum and not any(ord(c)<32 and c not in '\n\t' for c in value),
            'view_text_invalid',400)
    # Data is rendered literally, never HTML. Credentials/private paths are not
    # legitimate teaching fields. This is defense-in-depth, not a secret scanner.
    require(not re.search(r'(?i)(?:sk-proj-|AKIA[0-9A-Z]{12}|-----BEGIN .*PRIVATE KEY|Bearer\s+\S{20}|[A-Z]:[\\/]|/home/|/Users/)',value),
            'private_data_rejected',400)
    return value

def number(value, low=0, high=86400000, integer=False):
    require(type(value) is int if integer else type(value) in (int,float),'view_number_invalid',400)
    require(math.isfinite(value) and low<=value<=high,'view_number_invalid',400)
    return value

def ids(value, allow_empty=False):
    values=[ident(v) for v in seq(value,allow_empty)]
    require(len(values)==len(set(values)),'view_duplicate_identifier',400)
    return values

def lesson_architecture(raw):
    shape(raw,('lesson_id','title','scenes','objective_ids','source_ids','policy_version','requires_review'))
    ident(raw['lesson_id']);text(raw['title']);text(raw['policy_version'],200)
    scenes=[]
    for row in seq(raw['scenes']):
        shape(row,('scene_id','purpose','objective_ids','evidence_ids','parent_scene_ids','requires_review'))
        ident(row['scene_id']);text(row['purpose']);ids(row['objective_ids']);ids(row['evidence_ids']);ids(row['parent_scene_ids'],True)
        require(type(row['requires_review']) is bool,'view_review_invalid',400)
        scenes.append(LessonSceneIntent(**{**row,**{k:tuple(row[k]) for k in ('objective_ids','evidence_ids','parent_scene_ids')}}))
    value=build_lesson_architecture(raw['lesson_id'],raw['title'],scenes,ids(raw['objective_ids']),ids(raw['source_ids']),raw['policy_version'])
    validate_lesson_architecture(value)
    require(canonical(asdict(value))==canonical(raw),'view_noncanonical',400)
    return value

def reasoning(raw, body):
    shape(raw,('decisions','statuses'))
    decisions=[]; nodes=[]; refs=set()
    rows=seq(raw['decisions'])
    require(type(raw['statuses']) is dict and set(raw['statuses'])=={r['decision_id'] for r in rows},'view_status_inventory',400)
    for row in rows:
        shape(row,tuple(f.name for f in fields(re_contract.ReasoningDecision)))
        for k in ('decision_id','subject_id'):ident(row[k])
        for k in ('question','selected_option','rationale_summary'):text(row[k])
        for k in ('premises','constraints','uncertainty','downstream_effects','policy_tags'):
            for value in seq(row[k],True):text(value)
        ids(row['depends_on_decisions'],True);number(row['confidence'],0,1)
        require(type(row['requires_review']) is bool,'view_review_invalid',400)
        ev=[]
        for e in seq(row['evidence_refs']):
            shape(e,('artifact_id','role','strength','note'));ident(e['artifact_id']);number(e['strength'],0,1)
            if e['note'] is not None:text(e['note'])
            ev.append(re_contract.EvidenceRef(**e));refs.add(e['artifact_id'])
        alternatives=[]
        for a in seq(row['alternatives'],True):
            shape(a,('option_id','description','score','rejected_reason'));ident(a['option_id']);text(a['description'])
            if a['score'] is not None:number(a['score'],0,1)
            if a['rejected_reason'] is not None:text(a['rejected_reason'])
            alternatives.append(re_contract.DecisionAlternative(**a))
        d=re_contract.ReasoningDecision(**dict(row,evidence_refs=ev,alternatives=alternatives))
        d.validate();decisions.append(d)
        status=normalize_status(raw['statuses'][d.decision_id])
        require(not status.requires_review or d.requires_review,'view_review_required',400)
        nodes.append(dict(id=d.decision_id,label=d.question,decision_type=d.decision_type,subject=d.subject_id,
            selected_option=d.selected_option,rationale=d.rationale_summary,confidence=d.confidence,
            assumptions=d.premises,constraints=d.constraints,uncertainty=d.uncertainty,evidence_refs=[asdict(e) for e in ev],
            status=status.status,requires_review=d.requires_review,alternatives=[asdict(a) for a in alternatives]))
    re_contract.ReasoningDecisionGraph(decisions).validate()
    require(sum(len(d.depends_on_decisions) for d in decisions)<=800,'view_dependency_limit',400)
    return dict(nodes=nodes,edges=[dict(source=p,target=d.decision_id,type='depends_on') for d in decisions for p in d.depends_on_decisions],
                semantic_correctness_claimed=False),refs

def curriculum_view(raw, body):
    shape(raw,('units','dependencies','plan','max_lesson_minutes','max_lesson_load'))
    units=[];display={};refs=set()
    native_fields=tuple(f.name for f in fields(curriculum.CurriculumUnit))
    for row in seq(raw['units']):
        shape(row,native_fields+('title','objective_ids','evidence_refs'))
        ident(row['unit_id']);text(row['title']);ids(row['objective_ids']);refs.update(ids(row['evidence_refs']))
        number(row['source_order'],0,100000,True)
        for k in ('objective_priority','cognitive_load','review_weight','misconception_risk'):number(row[k],0,1)
        number(row['estimated_minutes'],.01,10000)
        units.append(curriculum.CurriculumUnit(**{k:row[k] for k in native_fields}));display[row['unit_id']]=row
    deps=[]
    for row in seq(raw['dependencies'],True):
        shape(row,tuple(f.name for f in fields(curriculum.CurriculumDependency)))
        ident(row['before']);ident(row['after']);text(row['kind'],100);number(row['strength'],0,1)
        require(type(row['hard']) is bool,'view_dependency_invalid',400)
        deps.append(curriculum.CurriculumDependency(**row))
    value=curriculum.optimize_book_curriculum(units,deps,max_lesson_minutes=number(raw['max_lesson_minutes'],.01,10000),
                                            max_lesson_load=number(raw['max_lesson_load'],.01,200))
    require(canonical(asdict(value))==canonical(raw['plan']),'curriculum_plan_tampered',400)
    return dict(units=[display[i] for i in value.order],dependencies=raw['dependencies'],order=value.order,
                lesson_groups=value.lesson_groups,review_after_unit=value.review_after_unit,total_minutes=value.total_minutes,
                violated_soft_constraints=value.violated_soft_constraints,timing_basis='PLANNED_NOT_MEASURED'),refs

def lesson_view(raw, body):
    shape(raw,('architecture','sections','assessments','pedagogy'))
    arch=lesson_architecture(raw['architecture'])
    require(body['source_id'] in arch.source_ids,'view_source_reference_invalid',400)
    refs={e for s in arch.scenes for e in s.evidence_ids};known={s.scene_id:s for s in arch.scenes};section_ids=[]
    sections=[]
    for row in seq(raw['sections']):
        shape(row,('section_id','scene_id','start_ms','end_ms','purpose'))
        section_ids.append(ident(row['section_id']));text(row['purpose']);require(row['scene_id'] in known,'view_scene_unknown',400)
        start=number(row['start_ms'],integer=True);end=number(row['end_ms'],integer=True)
        require(end>start,'view_timing_invalid',400);sections.append(row)
    require(len(set(section_ids))==len(section_ids) and {s['scene_id'] for s in sections}==set(known),'view_section_coverage',400)
    ordered=sorted(sections,key=lambda r:(r['start_ms'],r['section_id']))
    require(all(a['end_ms']<=b['start_ms'] for a,b in zip(ordered,ordered[1:])),'view_timing_overlap',400)
    for scene in arch.scenes:
        starts=[s['start_ms'] for s in sections if s['scene_id']==scene.scene_id]
        for parent in scene.parent_scene_ids:
            require(max(s['end_ms'] for s in sections if s['scene_id']==parent)<=min(starts),
                    'view_prerequisite_timing_invalid',400)
    assessments=[]
    for row in seq(raw['assessments']):
        shape(row,('assessment_id','objective_id','prompt','success_criteria','evidence_refs'))
        ident(row['assessment_id']);require(row['objective_id'] in arch.objective_ids,'view_objective_unknown',400)
        text(row['prompt']);[text(x) for x in seq(row['success_criteria'])];refs.update(ids(row['evidence_refs']));assessments.append(row)
    require(len({r['assessment_id'] for r in assessments})==len(assessments) and
            {r['objective_id'] for r in assessments}==set(arch.objective_ids),'view_assessment_coverage',400)
    ped=raw['pedagogy'];shape(ped,('plan_id','source_id','objective_ids','lesson_ids','decisions','policy_version','requires_review'))
    ds=[]
    for d in seq(ped['decisions']):
        shape(d,tuple(f.name for f in fields(PedagogyDecision)))
        for k in ('decision_id','kind','payload_id'):text(d[k],200)
        ids(d['evidence_ids']);ids(d['parent_decision_ids'],True);number(d['confidence'],0,1)
        ds.append(PedagogyDecision(**d));refs.update(d['evidence_ids'])
    built=build_pedagogy_plan(**{k:v for k,v in ped.items() if k!='requires_review'} | {'decisions':ds})
    require(canonical(asdict(built))==canonical(ped) and built.source_id==body['source_id'] and
        arch.lesson_id in built.lesson_ids and set(arch.objective_ids)<=set(built.objective_ids),'view_pedagogy_binding',400)
    return dict(architecture=asdict(arch),sections=ordered,assessments=assessments,pedagogy=asdict(built),
                duration_ms=max(s['end_ms'] for s in ordered),timing_basis='PLANNED_NOT_MEASURED'),refs

def director_view(raw, body):
    shape(raw,('architecture','script_plan','timings'))
    arch=lesson_architecture(raw['architecture']);require(body['source_id'] in arch.source_ids,'view_source_reference_invalid',400)
    script=raw['script_plan'];shape(script,('lesson_id','segments','voice_profile'));text(script['voice_profile'],200)
    segments=[];refs={e for s in arch.scenes for e in s.evidence_ids}
    for s in seq(script['segments']):
        shape(s,tuple(f.name for f in fields(ScriptSegment)))
        ident(s['segment_id']);text(s['purpose']);text(s['text_intent']);ids(s['objective_ids']);refs.update(ids(s['evidence_ids']))
        require(s['scene_id'] in {v.scene_id for v in arch.scenes} and
                set(s['objective_ids'])<=set(next(v for v in arch.scenes if v.scene_id==s['scene_id']).objective_ids),
                'view_script_binding',400)
        segments.append(ScriptSegment(**s))
    plan=build_script_plan(script['lesson_id'],segments,script['voice_profile']);validate_script_plan(plan)
    require(plan.lesson_id==arch.lesson_id and canonical(asdict(plan))==canonical(script),'view_script_binding',400)
    scenes=[];last=0
    for row in seq(raw['timings']):
        shape(row,('scene_id','start_ms','end_ms','narration_refs','visual_refs'))
        ident(row['scene_id']);start=number(row['start_ms'],integer=True);end=number(row['end_ms'],integer=True)
        require(start>=last and end>start,'view_timing_invalid',400);last=end
        require(set(ids(row['narration_refs']))<={s.segment_id for s in plan.segments if s.scene_id==row['scene_id']},
                'view_narration_binding',400)
        refs.update(ids(row['visual_refs']));scenes.append(row)
    require(len({s['scene_id'] for s in scenes})==len(scenes) and {s['scene_id'] for s in scenes}=={s.scene_id for s in arch.scenes},
            'view_scene_coverage',400)
    by_scene={s['scene_id']:s for s in scenes}
    for scene in arch.scenes:
        for parent in scene.parent_scene_ids:
            require(by_scene[parent]['end_ms']<=by_scene[scene.scene_id]['start_ms'],'view_prerequisite_timing_invalid',400)
    require({ref for s in scenes for ref in s['narration_refs']}=={s.segment_id for s in plan.segments},'view_narration_coverage',400)
    return dict(architecture=asdict(arch),script_plan=asdict(plan),timings=scenes,duration_ms=last,
                compiled=False,rendered=False,timing_basis='PLANNED_NOT_MEASURED'),refs

def scene_view(raw, body):
    shape(raw,('document','fps','viewport'))
    fps=number(raw['fps'],1,120,True);shape(raw['viewport'],('width','height'))
    for v in raw['viewport'].values():number(v,1,8192,True)
    doc=decode_scene_ir(raw['document']);wire=doc.to_dict()
    for validate in (validate_schema_shape,validate_temporal,validate_spatial,validate_accessibility):
        require(validate(wire).passed,'scene_ir_validation_failed',400)
    refs=set(doc.source_refs)
    asset_refs=[]
    for e in doc.elements:
        refs.update(e.source_refs)
        if 'asset_ref' in e.props:asset_refs.append(ident(e.props['asset_ref']));refs.add(e.props['asset_ref'])
    for t in doc.tracks:refs.update(t.source_refs)
    for ref in refs:ident(ref)
    # Only display identity/type/geometry/accessibility. Never execute props,
    # state bindings, assets, compiler capabilities or embedded scripts.
    def frame(ms):return ms*fps//1000
    elements=[dict(id=e.element_id,type=e.element_type,source_refs=e.source_refs,reasoning_refs=e.reasoning_refs,
        box=dict(e.normalized_box) if e.normalized_box else None,
        accessibility={k:text(v) if type(v) is str else v for k,v in dict(e.accessibility).items()
                       if k in ('alt','label','reduced_motion_variant','color_independent_encoding')}) for e in doc.elements]
    tracks=[dict(id=t.track_id,element_id=t.element_id,action=t.action,start_ms=t.start_ms,end_ms=t.end_ms,
                 start_frame=frame(t.start_ms),end_frame_exclusive=math.ceil(t.end_ms*fps/1000)) for t in doc.tracks]
    for e in elements:text(e['id'],200);text(e['type'],100)
    return dict(scene_id=doc.scene_id,title=text(doc.title),duration_ms=doc.duration_ms,fps=fps,viewport=raw['viewport'],
                elements=elements,tracks=tracks,asset_refs=sorted(set(asset_refs)),review_required=True,accepted=False,compiled=False,rendered=False),refs

# Fixed canonical dataclass vocabulary; never imports a class named by data.
GAME_TYPES={c.__name__:c for c in (game.DirectorPlan,game.ObjectiveAssignment,game.MechanicAssignment,
    game.MisconceptionAssignment,game.MasteryTarget,game.LevelNode,game.DifficultyPoint,game.FeedbackDesign,
    game.HintStep,game.ScoringPolicy,game.AdaptationRule,ProvenanceBundle,GameEvidence)}
GAME_ENUMS={c.__name__:c for c in (game.StrategyKind,game.MechanicKind,game.LevelRole,game.HintMode,game.AdaptAction)}

def game_decode(v):
    if type(v) is list:return [game_decode(x) for x in v]
    if type(v) is not dict:return v
    if '$type' in v:
        cls=GAME_TYPES.get(v['$type']);require(cls is not None,'game_plan_type_invalid',400)
        shape(v,('$type',)+tuple(f.name for f in fields(cls)))
        return cls(**{k:game_decode(x) for k,x in v.items() if k!='$type'})
    if '$enum' in v:
        shape(v,('$enum','value'));cls=GAME_ENUMS.get(v['$enum']);require(cls is not None,'game_plan_enum_invalid',400)
        return cls(v['value'])
    if '$tuple' in v:shape(v,('$tuple',));return tuple(game_decode(x) for x in seq(v['$tuple'],True))
    require(False,'game_plan_wire_invalid',400)

def game_view(raw, body):
    plan=game_decode(raw);require(type(plan) is game.DirectorPlan,'game_plan_type_invalid',400);plan.validate()
    material=dict(strategy=plan.selected_strategy.value,objectives=plan.objective_assignments,mechanics=plan.mechanic_assignments,
        misconceptions=plan.misconception_assignments,mastery=plan.mastery_targets,levels=plan.levels,difficulty=plan.difficulty,
        feedback=plan.feedback,hints=plan.hints,scoring=plan.scoring,adaptations=plan.adaptations,strategy_fingerprint=plan.strategy_fingerprint)
    require(game.plan_fingerprint(material)==plan.plan_fingerprint,'game_plan_fingerprint_invalid',400)
    refs=set()
    for seqs in (plan.objective_assignments,plan.mechanic_assignments,plan.misconception_assignments):
        for item in seqs:
            for r in item.provenance.refs:ident(r.artifact_id);refs.add(r.artifact_id)
    return dict(plan_id=plan.plan_id,strategy=plan.selected_strategy.value,
        objectives=[dict(objective_id=x.objective_id,level_id=x.level_id,concept_ids=x.concept_ids,required_interaction=x.required_interaction) for x in plan.objective_assignments],
        levels=[dict(level_id=x.level_id,role=x.role.value,objectives=x.objective_ids,mechanic=x.mechanic.value,
                     estimated_seconds=x.estimated_seconds,prerequisites=x.prerequisite_level_ids,purpose=text(x.pedagogical_purpose)) for x in plan.levels],
        feedback=[asdict(x) for x in plan.feedback],misconceptions=[dict(id=x.misconception_id,objective=x.objective_id,
            feedback=x.feedback_ref,remediation_level=x.remediation_level_id) for x in plan.misconception_assignments],
        mastery_targets=[asdict(x) for x in plan.mastery_targets],scoring=asdict(plan.scoring),
        adaptations=[dict(rule=x.rule_id,objective=x.objective_id,condition=text(x.condition),action=x.action.value,
                         target=x.target_level_id,rationale=text(x.rationale)) for x in plan.adaptations],
        playable=False,built=False,product_accepted=False),refs

def validate_view(kind,payload,body):
    require(kind in KINDS,'view_kind_unavailable',404)
    require(len(canonical(payload))<=MAX_DOCUMENT,'view_size_limit',413)
    # Iterative complexity guard before invoking recursive native validators.
    stack=[(payload,0)];count=0
    while stack:
        v,depth=stack.pop();count+=1
        require(count<=20000 and depth<=32,'view_complexity_limit',400)
        if type(v) is dict:
            require(len(v)<=100 and all(type(k) is str for k in v),'view_complexity_limit',400)
            stack.extend((x,depth+1) for x in v.values())
        elif type(v) in (list,tuple):
            require(len(v)<=MAX_ITEMS,'view_collection_invalid',400);stack.extend((x,depth+1) for x in v)
        elif type(v) is str:text(v,10000)
        elif type(v) is float:require(math.isfinite(v),'view_number_invalid',400)
        elif v is not None:require(type(v) in (int,bool),'view_type_invalid',400)
    validator={'reasoning':reasoning,'curriculum':curriculum_view,'lesson':lesson_view,'director':director_view,
               'scene_ir':scene_view,'game_plan':game_view}[kind]
    try:return validator(payload,body)
    except OperatorError:raise
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError):
        raise OperatorError('canonical_view_contract_failed',400) from None
