"""Real registered execution/repair/consumer path over authored protocol fixtures."""
import argparse,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests/director'))
from context_fixtures import context_upstream as upstream
from teaching_fixtures import TeachingProtocolFixture, ContextAnnotationFixture
from directing_fixtures import executor,orchestrator
from annotation_review_fixtures import runtime
from annotation_fixtures import AnnotationProtocolFixture
from repair_fixtures import intents
from bie.director.director_artifacts import fingerprint
from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import RevisionError


def run_case(case):
    with tempfile.TemporaryDirectory(prefix='bie-repair-') as tmp:
        f=upstream(tmp,case,scores=(0.,1.) if case=='economics' else ())
        broken=runtime(annotator=ContextAnnotationFixture(lambda p,v,n:{}))
        e,g,c,s=executor(f,generator=TeachingProtocolFixture(),annotations=broken)
        try:
            o=orchestrator(f,e);assert o.run_until_blocked_or_complete()==[]
            old=o.state.stages['DIRECTOR'].current
            base=f.io.load(old.evidence_refs[0]);saved=base.payload['result']['execution']
            generated_before=len(g.requests)
            key=s.db.execute('SELECT key FROM claims').fetchone()[0]
            e.annotations=runtime(annotator=ContextAnnotationFixture());o.configuration['director_repair']={'previous_idempotency_key':key}
            o.retry_failed('DIRECTOR');assert o.resume()==['DIRECTOR']
            current=o.state.stages['DIRECTOR'].current;output=f.io.load(current.output_artifact_refs[0])
            result=f.io.load(current.evidence_refs[0]).payload['result']
            assert len(g.requests)==generated_before
            assert result['execution']['snapshot']==saved['snapshot'] and result['execution']['pauses']==saved['pauses']
            consumer=DirectorConsumers(f.io,e.revisions);_,execution=consumer._director(output.to_ref())
            visuals,animations=intents(execution)
            timing=consumer.timing(output.to_ref());visual=consumer.visual(output.to_ref(),visuals)
            animation=consumer.animation(output.to_ref(),visual,animations);game=consumer.game_handoff(output.to_ref())
            candidates=(timing,visual,animation,game)
            before=[consumer.read_current(ref).artifact_type for ref in candidates]
            evidence=e.revisions.invalidate_inputs(f.io,f.run_id,(f.context_ref,),'Grounded context superseded after preview')
            stale=[]
            for ref in candidates:
                try:consumer.read_current(ref)
                except RevisionError:stale.append(ref.artifact_type)
                else:raise AssertionError('stale candidate was consumed')
            assert before==stale and len(evidence)==1
            return {'context_ref':f.context_ref.artifact_id, 'context':f.inputs.teaching_context.model_data(),
                    'bridge_decision_ids':list(f.inputs.teaching_context.bridge_decision_ids),
                    'teaching_obligations':[o.obligation_id for o in f.inputs.teaching_context.obligations],
                    'case_id':case,'initial_failure':old.diagnostics,'final_stage_attempt':current.attempt,
                    'generator_calls':len(g.requests),'generator_calls_during_repair':0,
                    'factual_calls':len(c.requests),'failed_annotator_calls':len(broken.annotator.requests),
                    'repaired_annotator_calls':len(e.annotations.annotator.requests),
                    'reviewer_calls':len(e.annotations.reviewer.requests),
                    'narration_preserved':True,'assessment_pauses_preserved':True,
                    'consumer_candidates':before,'stale_candidates_rejected':stale,
                    'result_fingerprint':fingerprint(result),'execution_result':result,
                    'status':'REVIEW_REQUIRED','accepted':False,'release_ready':False}
        finally:s.close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'verification/contextual_director.json');args=parser.parse_args()
    cases=[run_case(case) for case in ('science','economics','math')]
    report={'schema_version':'bie.dir.context_walkthrough/1.0.0','cases':cases,
            'scope':'Actual source-bound KI/PR/MATH/PED context, existing registered DIR teaching/annotation/repair and original consumer functions on authored fixtures.',
            'live_models_executed':False,'real_book_pipeline_executed':False,'audio_video_rendered':False,
            'playable_game_executed':False,'accepted':False,
            'limitations':['Fixtures establish bounded execution and failure behavior, not live teaching quality.',
                           'Consumers produce timing/sync/game-handoff planning candidates, not media or game runtimes.',
                           'Context covers grounded definitions/conditions, explicit prerequisites and a bounded supplied algebraic chain; broad codecs, long-context segmentation, broader teaching, scene-local repair and catalog recovery remain open.']}
    report['report_fingerprint']=fingerprint(report);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cases':3,'generator_calls':sum(c['generator_calls'] for c in cases),
        'repair_generator_calls':0,'factual_calls':sum(c['factual_calls'] for c in cases),
        'bridge_obligations':sum(sum(o.startswith('bridge:') for o in c['teaching_obligations']) for c in cases),
        'math_step_obligations':sum(sum(o.startswith('math:') for o in c['teaching_obligations']) for c in cases),
        'consumer_candidates':sum(len(c['consumer_candidates']) for c in cases),
        'stale_candidates_rejected':sum(len(c['stale_candidates_rejected']) for c in cases),
        'report_fingerprint':report['report_fingerprint'],'accepted':False}))


if __name__=='__main__':main()
