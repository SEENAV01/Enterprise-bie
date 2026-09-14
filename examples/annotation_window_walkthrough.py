"""Registered source-scoped annotation/review with whole-lesson reconciliation."""
import argparse,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests/director'))
from window_fixtures import long_upstream
from windowed_directing_fixtures import windowed_base,WindowProtocolFixture
from annotation_window_fixtures import WindowAnnotationFixture,window_runtime,production
from teaching_fixtures import ContextAnnotationFixture
from annotation_fixtures import ANNOTATOR
from annotation_review_fixtures import ReviewProtocolFixture,REVIEWER
from directing_fixtures import executor,context,orchestrator
from repair_fixtures import retry_context,intents
from bie.director.context_windows import WindowedDirectingPolicy
from bie.director.narration_annotations import produce_annotations,AnnotationPolicy
from bie.director.annotation_review import review_annotations,AnnotationReviewPolicy
from bie.director.annotation_window_context import WindowedAnnotationReviewPolicy
from bie.director.director_artifacts import canonical,fingerprint
from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import RevisionError
from bie.director.director_model import DirectingFailure


def request_size(request):return sum(len(m['content']) for m in request.messages)+len(canonical(request.response_schema))


def run_case(case,units,page_characters,repair=False):
    with tempfile.TemporaryDirectory(prefix='bie-annotation-windows-') as tmp:
        f=long_upstream(tmp,units=units,page_characters=page_characters)
        baseline=windowed_base(f);old_annotator=ContextAnnotationFixture();old_annotation_failure=None
        try:produce_annotations(f.io,f.inputs,baseline,old_annotator,ANNOTATOR,AnnotationPolicy())
        except DirectingFailure as error:old_annotation_failure=error.code
        if case=='eight-large-pages':
            assert old_annotation_failure=='DIRECTOR_CONTEXT_BUDGET_EXCEEDED' and not old_annotator.requests
        scoped=production(f,baseline);old_reviewer=ReviewProtocolFixture()
        old_review=review_annotations(f.inputs,baseline,scoped,old_reviewer,REVIEWER,AnnotationReviewPolicy())
        if case=='eight-large-pages':assert old_review.failures==('DIRECTOR_CONTEXT_BUDGET_EXCEEDED',) and not old_reviewer.requests
        broken=window_runtime(annotator=WindowAnnotationFixture(lambda p,v,n:{})) if repair else None
        e,g,c,s=executor(f,generator=WindowProtocolFixture(),policy=WindowedDirectingPolicy(),annotations=broken or window_runtime())
        try:
            if repair:
                o=orchestrator(f,e);assert o.run_until_blocked_or_complete()==[];prior=o.state.stages['DIRECTOR'].current
                generated_before=len(g.requests);factual_before=len(c.requests);key=s.db.execute('SELECT key FROM claims').fetchone()[0]
                e.annotations=window_runtime();o.configuration['director_repair']={'previous_idempotency_key':key}
                o.retry_failed('DIRECTOR');assert o.resume()==['DIRECTOR'];current=o.state.stages['DIRECTOR'].current
                assert len(g.requests)==generated_before;result_ref=current.output_artifact_refs[0]
                repair_calls={'generator':0,'factual':len(c.requests)-factual_before}
            else:
                prior=None;stage=e(context(f));result_ref=stage.output_artifact_refs[0];repair_calls={'generator':0,'factual':0}
            output=f.io.load(result_ref);evidence=f.io.load(output.payload['execution_evidence_ref']['artifact_id']);record=evidence.payload['result']
            annotation=record['annotation_production'];review=record['annotation_review']
            self_scopes=annotation['window_calls'];review_scopes=review['review_windows']
            assert len(self_scopes)==units and len(review_scopes)==units+1
            consumer=DirectorConsumers(f.io,e.revisions);_,execution=consumer._director(result_ref);visuals,animations=intents(execution)
            timing=consumer.timing(result_ref);visual=consumer.visual(result_ref,visuals)
            candidates=(timing,visual,consumer.animation(result_ref,visual,animations),consumer.game_handoff(result_ref))
            types=[consumer.read_current(x).artifact_type for x in candidates]
            invalidated=e.revisions.invalidate_inputs(f.io,f.run_id,(f.context_ref,),'Context superseded after annotation-window preview')
            stale=[]
            for candidate in candidates:
                try:consumer.read_current(candidate)
                except RevisionError:stale.append(candidate.artifact_type)
                else:raise AssertionError('stale candidate consumed')
            all_pages={p.page_id for p in f.inputs.catalog.pages};seen=set()
            for request in e.annotations.annotator.requests:
                payload=json.loads(request.messages[1]['content'])
                if payload['operation']=='ANNOTATE_SCENE':seen.update(p['page_id'] for p in payload['inputs']['source_pages'])
                else:
                    assert payload['operation']=='RECONCILE_DISCOURSE'
                    assert [u['text'] for u in payload['utterances']]==[u.text for u in execution.snapshot.utterances]
            assert seen==all_pages and types==stale and len(invalidated)==1
            sizes={'generation':[request_size(x) for x in g.requests],
                'annotation':[request_size(x) for x in e.annotations.annotator.requests],
                'review':[request_size(x) for x in e.annotations.reviewer.requests]}
            return {'case_id':case,'source_pages':units,'source_characters':sum(len(x) for x in f.source_texts),
                'single_annotation_failure':old_annotation_failure,'single_annotation_provider_calls':len(old_annotator.requests),
                'single_review_failures':list(old_review.failures),'single_review_provider_calls':len(old_reviewer.requests),
                'generation_windows':len(record['base_result']['window_execution']['windows']),
                'annotation_source_scopes':len(self_scopes),'global_reconciliation_scopes':1,
                'review_source_scopes':len(review_scopes)-1,'global_review_scopes':1,
                'complete_source_page_coverage':True,'complete_spoken_lesson_reconciled':True,
                'utterances':len(execution.snapshot.utterances),'scene_count':len({u.scene_id for u in execution.snapshot.utterances}),
                'generation_calls':len(g.requests),'annotation_calls':len(e.annotations.annotator.requests),
                'review_calls':len(e.annotations.reviewer.requests),'factual_calls':len(c.requests),
                'repair_calls':repair_calls,'request_character_sizes':sizes,
                'peak_request_characters':{k:max(v) for k,v in sizes.items()},
                'window_records_persisted_and_revalidated_by_consumer':True,
                'consumer_candidates':types,'stale_candidates_rejected':stale,
                'initial_failure':prior.diagnostics if prior else [],'result_fingerprint':fingerprint(record),
                'status':'REVIEW_REQUIRED','accepted':False,'release_ready':False}
        finally:s.close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'verification/annotation_window_walkthrough.json');args=parser.parse_args()
    cases=[run_case('eight-large-pages',8,7000,True),run_case('four-large-pages',4,13000),run_case('three-scene-continuity',3,500)]
    report={'schema_version':'bie.dir.annotation_window_walkthrough/1.0.0','cases':cases,
        'scope':'Registered DIR execution over authored source/provider fixtures with complete-scene source annotation, whole-spoken-lesson reconciliation, scoped independent review, repair and original consumers.',
        'live_models_executed':False,'real_book_pipeline_executed':False,'audio_video_rendered':False,'playable_game_executed':False,'accepted':False,
        'limitations':['Authored fixtures establish bounded execution and explicit failure behavior, not annotation correctness or teaching quality.',
            'Every source scene and all speech are covered; an indivisible oversized scene/source/support or complete global discourse request still fails explicitly.',
            'Global discourse omits full source pages and cannot establish factual truth; source scopes and existing per-claim factual QA retain those roles.',
            'Production provider token calibration, global retrieval for arbitrarily long spoken lessons, multilingual/audience evidence and real textbook validation remain open.']}
    report['report_fingerprint']=fingerprint(report);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cases':len(cases),'annotation_source_scopes':sum(c['annotation_source_scopes'] for c in cases),
        'review_source_scopes':sum(c['review_source_scopes'] for c in cases),'global_annotation_scopes':3,'global_review_scopes':3,
        'generation_calls':sum(c['generation_calls'] for c in cases),'annotation_calls':sum(c['annotation_calls'] for c in cases),
        'review_calls':sum(c['review_calls'] for c in cases),'factual_calls':sum(c['factual_calls'] for c in cases),
        'repair_generation_calls':sum(c['repair_calls']['generator'] for c in cases),'consumer_candidates':sum(len(c['consumer_candidates']) for c in cases),
        'stale_candidates_rejected':sum(len(c['stale_candidates_rejected']) for c in cases),'report_fingerprint':report['report_fingerprint'],'accepted':False}))


if __name__=='__main__':main()
