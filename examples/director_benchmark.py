"""Executable engineering benchmark; extractive adapter is NOT final BIE intelligence.

Uses real canonical PED objects and existing DIR producers. The adapter accepts
only the source/PED request and never opens the fixture or its oracle. It is
intentionally a controlled integration reference, not autonomous book planning.
"""
from dataclasses import asdict, replace
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from bie.director.director_benchmark import (DirectorRequest, DirectorExecution, DirectorBenchmarkCase,
    DirectorBenchmarkSuite, NarrativeExpectation, CandidateIdentity, run_director_benchmark, validate_request)
from bie.director.qa_contract import SourcePage, SourcePassage, SourceCatalog, ScriptClaim, snapshot_script, bind_span
from bie.director.source_grounding_qa import SourceBytes
from bie.director.script_plan import ScriptSegment, build_script_plan
from bie.director.voiceover_generation import generate_voiceover
from bie.director.lesson_architecture_contract import LessonSceneIntent, build_lesson_architecture
from bie.director.game_handoff import build_game_handoff
from bie.director.script_coherence_qa import DiscourseBeat
from bie.director.speech_timing import estimate_speech
from bie.director.pause_timing import build_pause_timing
from bie.director.emphasis_timing import build_emphasis_timing
from bie.director.scene_duration_fit import fit_scene_durations
from bie.director.pacing_qa import PacingBeat
from bie.pedagogy.learning_objective_generator import generate_objective
from bie.pedagogy.pedagogy_plan_contract import PedagogyDecision, build_pedagogy_plan


def controlled_director(request):
    passages=validate_request(request)
    objectives={o.objective_id:o for o in request.objectives}
    remaining={d.decision_id:d for d in request.pedagogy.decisions}
    ordered=[]; done=set()
    while remaining:
        ready=[d for d in remaining.values() if set(d.parent_decision_ids)<=done]
        if not ready: raise ValueError("cyclic PED decision sequence")
        for d in sorted(ready,key=lambda d:d.decision_id):
            if d.kind!="EXPLAIN" or d.payload_id not in objectives: raise ValueError("controlled adapter needs objective explanation decisions")
            ordered.append(d); done.add(d.decision_id); del remaining[d.decision_id]
    if len(request.pedagogy.lesson_ids)!=1: raise ValueError("controlled adapter covers one lesson")
    lesson=request.pedagogy.lesson_ids[0]
    segments=[]; scenes=[]; drafts=[]
    for d in ordered:
        o=objectives[d.payload_id]; sid="scene:"+d.decision_id; uid="utterance:"+d.decision_id
        parents=tuple("scene:"+p for p in d.parent_decision_ids)
        scenes.append(LessonSceneIntent(sid,"EXPLAIN",(o.objective_id,),o.evidence_ids,parents,request.pedagogy.requires_review))
        segments.append(ScriptSegment(uid,sid,"EXPLAIN",o.statement,o.evidence_ids,(o.objective_id,)))
        quotes=tuple(passages[e].quote for e in o.evidence_ids)
        draft=generate_voiceover(uid,quotes,{q:tuple(e for e in o.evidence_ids if passages[e].quote==q) for q in quotes})
        drafts.append(replace(draft,requires_review=draft.requires_review or request.pedagogy.requires_review))
    script=build_script_plan(lesson,segments,"controlled-clear")
    snapshot=snapshot_script(script,tuple(drafts),tuple(s.segment_id for s in segments),request.language)
    architecture=build_lesson_architecture(lesson,request.title,scenes,request.pedagogy.objective_ids,
        tuple(sorted({p.source_id for p in request.catalog.pages})),"controlled-ped-dir/1")
    claims=tuple(ScriptClaim("claim:"+u.utterance_id,bind_span(snapshot,u.utterance_id),"FACT",u.evidence_ids) for u in snapshot.utterances)
    beats=[]; pacing=[]
    for u,d in zip(snapshot.utterances,ordered):
        o=objectives[d.payload_id]
        required=tuple(objectives[next(x.payload_id for x in ordered if x.decision_id==p)].concept_id for p in d.parent_decision_ids)
        beats.append(DiscourseBeat(u.utterance_id,u.fingerprint(),(o.concept_id,),required))
        pacing.append(PacingBeat("pace:"+d.decision_id,bind_span(snapshot,u.utterance_id),"EXPLAIN",(o.concept_id,),u.evidence_ids,u.objective_ids))
    handoff=build_game_handoff(lesson,request.pedagogy.objective_ids,tuple(o.concept_id for o in request.objectives),(),
        tuple("mastery:"+o.objective_id for o in request.objectives),tuple(sorted({e for o in request.objectives for e in o.evidence_ids})))
    speech=estimate_speech(snapshot.utterances); pauses=build_pause_timing(speech); emphasis=build_emphasis_timing(speech)
    return DirectorExecution(snapshot,architecture,handoff,speech,pauses,emphasis,
        fit_scene_durations(speech,pauses,emphasis),claims,tuple(beats),tuple(pacing))


def load_suite(path=ROOT/'benchmarks/director_controlled_v1.json'):
    data=json.loads(path.read_text()); cases=[]; artifacts=[]
    for item in data['cases']:
        cid=item['id']; text="\n".join(f['text'] for f in item['facts']); raw=text.encode('utf-8'); sid="source:"+cid
        page=SourcePage("page:"+cid,sid,"sha256:"+hashlib.sha256(raw).hexdigest(),1,text,"controlled-utf8/1")
        artifacts.append(SourceBytes(sid,raw,"text/plain; charset=utf-8"))
        passages=[]; objectives=[]; decisions=[]; start=0
        for i,fact in enumerate(item['facts']):
            eid=f"e:{cid}:{i}"; stop=start+len(fact['text'])
            passages.append(SourcePassage(eid,page.page_id,page.fingerprint(),f"paragraph:{i}",start,stop,fact['text']))
            objective=generate_objective(fact['concept'],fact['concept'],(eid,)); objectives.append(objective)
            # Reverse lexical names deliberately: dependency order is authoritative.
            did=f"decision:{99-i}"; parents=(f"decision:{100-i}",) if i else ()
            decisions.append(PedagogyDecision(did,"EXPLAIN",objective.objective_id,(eid,),parents))
            start=stop+1
        plan=build_pedagogy_plan(plan_id="ped:"+cid,source_id=sid,objective_ids=tuple(o.objective_id for o in objectives),
            lesson_ids=("lesson:"+cid,),decisions=decisions,policy_version="controlled-ped/1")
        request=DirectorRequest("request:"+cid,cid,"en",SourceCatalog((page,),tuple(passages)),plan,tuple(objectives))
        expected=tuple(NarrativeExpectation(c['id'],c['kind'],tuple(c['phrases']),tuple(p.evidence_id for p in passages),
            "Independent source expectation in engineering fixture; no semantic generalization claimed") for c in item['checks'])
        cases.append(DirectorBenchmarkCase(cid,item['domain'],request,expected))
    suite=DirectorBenchmarkSuite(data['suite_id'],data['version'],data['provenance'],data['oracle_author'],data['oracle_method'],
        tuple(data['required_domains']),tuple(cases))
    return suite,tuple(artifacts)


def candidate_identity():
    # Hash all executing production/adapter files, not just a version label.
    files=sorted((ROOT/'bie').rglob('*.py'))+[Path(__file__).resolve()]
    payload=json.dumps([(str(p.relative_to(ROOT)),hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],separators=(',',':')).encode()
    return CandidateIdentity("controlled-extractive-PED-DIR-adapter","1.0.0","sha256:"+hashlib.sha256(payload).hexdigest(),
        "sha256:"+hashlib.sha256(b'controlled-ped-dir-default-config/1').hexdigest())


def run():
    suite,artifacts=load_suite(); result=run_director_benchmark(suite,controlled_director,artifacts,candidate_identity())
    return {**asdict(result),"checks_passed":result.checks_passed,"qa_status":result.qa_status,
        "passed_case_fraction":result.passed_case_fraction,"accepted":False,"real_book_executed":False,
        "actual_media_or_game_executed":False,"scope":"Six authored engineering cases across three domains; controlled PED to DIR execution",
        "report_fingerprint":result.fingerprint()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path); args=parser.parse_args()
    result=run()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({k:result[k] for k in ('checks_passed','qa_status','accepted','case_results','domain_results','report_fingerprint')}))
    else: print(json.dumps(result,indent=2,ensure_ascii=False))
    raise SystemExit(0 if result['checks_passed'] else 1)
