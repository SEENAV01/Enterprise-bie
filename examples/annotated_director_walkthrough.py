"""Controlled annotation + independent review execution, not live-model quality."""
import argparse,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests/director'))
from input_fixtures import upstream
from directing_fixtures import executor,orchestrator
from annotation_review_fixtures import runtime
from bie.director.director_artifacts import fingerprint
from bie.director.qa_contract import coverage


def run_case(case):
    with tempfile.TemporaryDirectory(prefix='bie-annotations-') as tmp:
        f=upstream(tmp,case);rt=runtime();e,g,c,s=executor(f,annotations=rt)
        try:
            o=orchestrator(f,e);executed=o.run_until_blocked_or_complete()
            if executed!=['DIRECTOR']:raise RuntimeError('controlled annotated stage failed')
            stage=o.state.stages['DIRECTOR'].current;output=f.io.load(stage.output_artifact_refs[0]);ev=f.io.load(stage.evidence_refs[0])
            result=ev.payload['result'];a=result['annotation_production']['annotations']
            assert result['execution']['snapshot']==result['base_result']['execution']['snapshot']
            assert result['execution']['pauses']==result['base_result']['execution']['pauses']
            graph=f.io.load_graph((output.to_ref(),))
            findings=[f['code'] for q in result['qa_reports'] for f in q['findings']]
            assert 'DISCOURSE_ANNOTATION_MISSING' not in findings and 'PACING_ANNOTATION_INCOMPLETE' not in findings
            return {'case_id':case,'run_id':f.run_id,'stage_state':stage.state,'schema_version':output.payload['schema_version'],
                'scene_count':len(result['base_result']['plan']['scenes']),'utterances':len(result['execution']['snapshot']['utterances']),
                'claims':len(a['claims']),'discourse_beats':len(a['discourse']),'terms':len(a['terms']),
                'emphasis_anchors':len(a['emphasis']),'pacing_beats':len(a['pacing']),
                'generator_calls':len(g.requests),'annotator_calls':len(rt.annotator.requests),
                'annotation_reviewer_calls':len(rt.reviewer.requests),'factual_critic_calls':len(c.requests),
                'artifact_ancestry_count':len(graph),'output_id':output.artifact_id,'execution_evidence_id':ev.artifact_id,
                'result_fingerprint':ev.payload['result_fingerprint'],'narration_unchanged':True,'assessment_pauses_unchanged':True,
                'base_duration_ms':sum(scene['duration_ms'] for scene in result['base_result']['execution']['timeline']['scenes']),
                'annotated_duration_ms':sum(scene['duration_ms'] for scene in result['execution']['timeline']['scenes']),'status':output.metadata['status'],
                'accepted':False,'release_ready':False,'result':result}
        finally:s.close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'verification/annotated_director.json');args=parser.parse_args()
    cases=[run_case(c) for c in ('science','economics','history')]
    report={'schema_version':'bie.dir.annotated_walkthrough/1.0.0','cases':cases,
        'scope':'Actual canonical artifact, registered DIR, annotation/reviewer provider-protocol, factual/structural QA and estimated timing execution on authored fixtures.',
        'live_models_executed':False,'real_book_pipeline_executed':False,'audio_video_rendered':False,
        'playable_game_executed':False,'accepted':False,
        'limitations':['Annotator and reviewer responses are explicit protocol fixtures; no live annotation or teaching quality is established.',
            'Unknown curriculum audience and uncalibrated model policy retain review. No learner questionnaire or age inference was used.',
            'Narration and assessment pauses are unchanged; emphasis affects estimated timing only, not an audio waveform.',
            'Broader upstream codecs, selective repair/invalidation, actual consumer gates and product acceptance remain open.']}
    report['report_fingerprint']=fingerprint(report);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cases':len(cases),'claims':[c['claims'] for c in cases],'generator_calls':sum(c['generator_calls'] for c in cases),
        'annotator_calls':sum(c['annotator_calls'] for c in cases),'reviewer_calls':sum(c['annotation_reviewer_calls'] for c in cases),
        'factual_calls':sum(c['factual_critic_calls'] for c in cases),'statuses':[c['status'] for c in cases],
        'report_fingerprint':report['report_fingerprint'],'accepted':False}))


if __name__=='__main__':main()
