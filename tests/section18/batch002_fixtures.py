"""Explicit synthetic native-contract artifacts, never real-book evidence."""
from dataclasses import asdict, replace
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from bie.reasoning.decision_contracts import ReasoningDecision,EvidenceRef,DecisionAlternative
from bie.pedagogy.book_scale_curriculum_optimizer import CurriculumUnit,CurriculumDependency,optimize_book_curriculum
from bie.director.lesson_architecture_contract import LessonSceneIntent,build_lesson_architecture
from bie.director.script_plan import ScriptSegment,build_script_plan
from bie.pedagogy.pedagogy_plan_contract import PedagogyDecision,build_pedagogy_plan
from bie.scene_ir.unified_scene_ir_contract import UnifiedElement,UnifiedTrack,UnifiedSceneIRDocument
from bie.game_engine.director_engine.fixtures import director_context
from bie.game_engine.director_engine.planner import plan_experience
from bie.game_engine.director_engine.contracts import plan_fingerprint
from bie.game_engine.provenance import EvidenceRef as GameEvidence,ProvenanceBundle
from bie.game_engine.codec import encode

def documents(body):
    ref='source-'+body['native_job_id'][4:];source=body['source_id'];sha=body['source_hash']
    d=ReasoningDecision('decision-a','example_selection','concept-a','Why does the synthetic example apply?',
        'worked-example','A cited synthetic premise supports the selected example.',.85,[EvidenceRef(ref,'primary',.9)],
        [DecisionAlternative('other','Different example',.2,'Not relevant to this premise')],['Assume the stated conditions.'],[],[],[],[],False,[])
    b=replace(d,decision_id='decision-b',depends_on_decisions=['decision-a'],requires_review=True,confidence=.45,
        uncertainty=['Additional independent semantic review is required.'])
    reasoning=dict(decisions=[asdict(d),asdict(b)],statuses={'decision-a':'RESOLVED','decision-b':'ABSTAINED'})
    units=[CurriculumUnit('unit-a',0,.8,.4,.6,.3,8),CurriculumUnit('unit-b',1,.7,.5,.4,.3,10)]
    deps=[CurriculumDependency('unit-a','unit-b','prerequisite')]
    curr=dict(units=[asdict(u)|dict(title=u.unit_id+' synthetic unit',objective_ids=['objective-a'],evidence_refs=[ref]) for u in units],
              dependencies=[asdict(x) for x in deps],plan=asdict(optimize_book_curriculum(units,deps)),max_lesson_minutes=45.,max_lesson_load=2.2)
    arch=build_lesson_architecture('lesson-a','Synthetic causal lesson',[
        LessonSceneIntent('scene-a','Explain then probe the conditions.',('objective-a',),(ref,)),
        LessonSceneIntent('scene-b','Transfer the synthetic rule.',('objective-a',),(ref,),('scene-a',))],
        ['objective-a'],[source],'ped-policy/1')
    ped=build_pedagogy_plan(plan_id='ped-a',source_id=source,objective_ids=['objective-a'],lesson_ids=['lesson-a'],
        decisions=[PedagogyDecision('ped-d1','example','payload-a',(ref,))],policy_version='ped-policy/1')
    lesson=dict(architecture=asdict(arch),sections=[dict(section_id='section-a',scene_id='scene-a',start_ms=0,end_ms=60000,purpose='Explain'),
        dict(section_id='section-b',scene_id='scene-b',start_ms=60000,end_ms=120000,purpose='Transfer')],
        assessments=[dict(assessment_id='assess-a',objective_id='objective-a',prompt='Predict the next synthetic state.',
            success_criteria=['Identify the rule and justify the prediction.'],evidence_refs=[ref])],pedagogy=asdict(ped))
    script=build_script_plan('lesson-a',[ScriptSegment('segment-a','scene-a','Explain','Realize the cited rule.',(ref,),('objective-a',)),
        ScriptSegment('segment-b','scene-b','Probe','Ask for a justified prediction.',(ref,),('objective-a',))],'configured-voice')
    director=dict(architecture=asdict(arch),script_plan=asdict(script),timings=[dict(scene_id='scene-a',start_ms=0,end_ms=60000,
        narration_refs=['segment-a'],visual_refs=[ref]),dict(scene_id='scene-b',start_ms=60000,end_ms=120000,
        narration_refs=['segment-b'],visual_refs=[ref])])
    element=UnifiedElement('element-a','shape',{'fill':'green'},(ref,),('decision-a',),{'label':'Source-linked rectangle'},
        {'x':.1,'y':.2,'width':.4,'height':.3})
    track=UnifiedTrack('track-a','element-a','translate',0,1000,{},(ref,),('decision-a',))
    scene=UnifiedSceneIRDocument('scene-a','1.0.0','Synthetic spatial plan',1500,(element,),(track,),(ref,),('decision-a',))
    ir=dict(document=scene.to_dict(),fps=30,viewport={'width':1920,'height':1080})
    plan=plan_experience(director_context())
    # Rebind the labelled synthetic producer's evidence to the actual persisted
    # source CAS. No production generation or learner outcome is claimed.
    def prov(p):return ProvenanceBundle(tuple(GameEvidence(ref,r.locator,sha,r.role) for r in p.refs),p.inherited_from)
    plan=replace(plan,objective_assignments=tuple(replace(x,provenance=prov(x.provenance)) for x in plan.objective_assignments),
        mechanic_assignments=tuple(replace(x,provenance=prov(x.provenance)) for x in plan.mechanic_assignments),
        misconception_assignments=tuple(replace(x,provenance=prov(x.provenance)) for x in plan.misconception_assignments))
    material=dict(strategy=plan.selected_strategy.value,objectives=plan.objective_assignments,mechanics=plan.mechanic_assignments,
        misconceptions=plan.misconception_assignments,mastery=plan.mastery_targets,levels=plan.levels,difficulty=plan.difficulty,
        feedback=plan.feedback,hints=plan.hints,scoring=plan.scoring,adaptations=plan.adaptations,strategy_fingerprint=plan.strategy_fingerprint)
    plan=replace(plan,plan_fingerprint=plan_fingerprint(material));plan.validate()
    return dict(reasoning=reasoning,curriculum=curr,lesson=lesson,director=director,scene_ir=ir,game_plan=encode(plan))
