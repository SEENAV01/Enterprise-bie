"""Registered windowed DIR with exact-base repair and original consumers.

Source text and provider responses are authored fixtures. No live-model, PDF,
rendering, scoring or playable-runtime acceptance is implied.
"""
import argparse,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests/director'))
from window_fixtures import long_upstream
from context_fixtures import context_upstream
from windowed_directing_fixtures import WindowProtocolFixture,windowed_base
from teaching_fixtures import ContextAnnotationFixture
from directing_fixtures import executor,orchestrator
from annotation_review_fixtures import runtime
from repair_fixtures import intents
from bie.director.context_windows import WindowedDirectingPolicy
from bie.director.director_model import DirectingPolicy,DirectingFailure
from bie.director.grounded_directing import model_context
from bie.director.director_artifacts import canonical,fingerprint
from bie.director.recovery_codec import grounded_record
from bie.director.narration_annotations import verify_base
from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import RevisionError


def request_size(request):
    return sum(len(m['content']) for m in request.messages)+len(canonical(request.response_schema))


def run_case(case):
    with tempfile.TemporaryDirectory(prefix='bie-windows-') as tmp:
        f=(context_upstream(tmp,'math') if case=='supplied-algebra'
           else long_upstream(tmp,units=8,page_characters=5200) if case=='eight-source-units'
           else long_upstream(tmp,units=4,page_characters=13000))
        context_size=len(canonical(model_context(f.inputs)))
        old_failure=None;old=WindowProtocolFixture()
        if context_size>DirectingPolicy().maximum_request_characters:
            try:windowed_base(f,old,DirectingPolicy())
            except DirectingFailure as failure:old_failure=failure.code
            else:raise AssertionError('oversized single request unexpectedly executed')
            assert old_failure=='DIRECTOR_CONTEXT_BUDGET_EXCEEDED' and not old.requests
        broken=runtime(annotator=ContextAnnotationFixture(lambda p,v,n:{}))
        policy=WindowedDirectingPolicy()
        e,g,c,s=executor(f,generator=WindowProtocolFixture(),policy=policy,annotations=broken)
        try:
            o=orchestrator(f,e);assert o.run_until_blocked_or_complete()==[]
            prior=o.state.stages['DIRECTOR'].current
            saved=f.io.load(prior.evidence_refs[0]).payload['result'];base=grounded_record(saved)
            verify_base(f.io,f.inputs,base);generated_before=len(g.requests)
            key=s.db.execute('SELECT key FROM claims').fetchone()[0]
            e.annotations=runtime(annotator=ContextAnnotationFixture())
            o.configuration['director_repair']={'previous_idempotency_key':key}
            o.retry_failed('DIRECTOR');assert o.resume()==['DIRECTOR']
            current=o.state.stages['DIRECTOR'].current
            result=f.io.load(current.evidence_refs[0]).payload['result']
            assert len(g.requests)==generated_before
            assert result['base_result']['narrated_scenes']==saved['narrated_scenes']
            assert result['base_result']['window_execution']==saved['window_execution']
            assert result['execution']['snapshot']==saved['execution']['snapshot']
            assert result['execution']['pauses']==saved['execution']['pauses']
            consumer=DirectorConsumers(f.io,e.revisions);ref=current.output_artifact_refs[0]
            _,execution=consumer._director(ref);visuals,animations=intents(execution)
            timing=consumer.timing(ref);visual=consumer.visual(ref,visuals)
            candidates=(timing,visual,consumer.animation(ref,visual,animations),consumer.game_handoff(ref))
            types=[consumer.read_current(r).artifact_type for r in candidates]
            evidence=e.revisions.invalidate_inputs(f.io,f.run_id,(f.context_ref,),'Grounded context superseded after window preview')
            stale=[]
            for candidate in candidates:
                try:consumer.read_current(candidate)
                except RevisionError:stale.append(candidate.artifact_type)
                else:raise AssertionError('stale windowed candidate consumed')
            assert types==stale and len(evidence)==1
            pages={p.fingerprint() for p in f.inputs.catalog.pages}
            source_ids={p['evidence_id'] for p in model_context(f.inputs)['source_passages']}
            windows=base.window_execution.windows
            assert {p for w in windows for p in w.page_fingerprints}==pages
            assert {p for w in windows for p in w.evidence_ids}==source_ids
            sizes=[request_size(r) for r in g.requests];assert max(sizes)<=policy.maximum_request_characters
            return {'case_id':case,'full_model_context_characters':context_size,
                'source_characters':sum(len(p.text) for p in f.inputs.catalog.pages),'source_pages':len(pages),
                'single_request_failure':old_failure,'single_request_provider_calls':len(old.requests),
                'window_count':len(windows),'window_decision_counts':[len(w.decision_ids) for w in windows],
                'complete_source_evidence_coverage':True,'complete_source_page_coverage':True,
                'scene_count':len(base.plan.scenes),'retained_narrated_scenes':len(base.narrated_scenes),
                'request_character_sizes':sizes,'maximum_request_characters':policy.maximum_request_characters,
                'peak_request_characters':max(sizes),'all_request_fingerprints_reconstructed':True,
                'teaching_obligations':[o.obligation_id for o in f.inputs.teaching_context.obligations],
                'initial_failure':prior.diagnostics,'final_stage_attempt':current.attempt,
                'generator_calls':len(g.requests),'generator_calls_during_repair':len(g.requests)-generated_before,
                'factual_calls':len(c.requests),'failed_annotator_calls':len(broken.annotator.requests),
                'repaired_annotator_calls':len(e.annotations.annotator.requests),'reviewer_calls':len(e.annotations.reviewer.requests),
                'narration_preserved':True,'assessment_pauses_preserved':True,
                'consumer_candidates':types,'stale_candidates_rejected':stale,
                'result_fingerprint':fingerprint(result),'execution_result':result,
                'status':'REVIEW_REQUIRED','accepted':False,'release_ready':False}
        finally:s.close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'verification/windowed_director.json');args=parser.parse_args()
    cases=[run_case(case) for case in ('eight-source-units','four-larger-pages','supplied-algebra')]
    report={'schema_version':'bie.dir.window_walkthrough/1.0.0','cases':cases,
        'scope':'Actual window requests, original full-scope DIR validators, registered execution, exact-base repair, annotation/review and four planning consumers over authored fixtures.',
        'live_models_executed':False,'real_book_pipeline_executed':False,'audio_video_rendered':False,'playable_game_executed':False,'accepted':False,
        'limitations':['Authored fixture outcomes establish execution and failure behavior, not live teaching quality.',
            'Whole-page, prerequisite-closure and supplied-chain windows are bounded; indivisible oversized units fail explicitly.',
            'Earlier narration is retained in full by the host; generation receives exact recent scenes and a complete identity/coverage ledger, not full earlier speech.',
            'Annotation/reviewer full-context budgets and factual complete-page budgets remain unchanged and unsegmented.',
            'Global discourse retrieval, richer codecs/teaching, scene-local repair, catalog recovery and full product/runtime adoption remain implementation work.']}
    report['report_fingerprint']=fingerprint(report);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cases':len(cases),'windows':sum(c['window_count'] for c in cases),
        'scenes':sum(c['scene_count'] for c in cases),'generator_calls':sum(c['generator_calls'] for c in cases),
        'repair_generator_calls':sum(c['generator_calls_during_repair'] for c in cases),
        'factual_calls':sum(c['factual_calls'] for c in cases),'peak_request_characters':max(c['peak_request_characters'] for c in cases),
        'consumer_candidates':sum(len(c['consumer_candidates']) for c in cases),
        'stale_candidates_rejected':sum(len(c['stale_candidates_rejected']) for c in cases),
        'report_fingerprint':report['report_fingerprint'],'accepted':False}))


if __name__=='__main__':main()
