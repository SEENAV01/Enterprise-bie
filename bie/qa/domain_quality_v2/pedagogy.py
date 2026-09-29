"""HARD013: native architecture/assessment bindings and observed route checks.

An independent route/assessment inventory cannot be shrunk by submitted traces.
Native contracts are executed, not inferred from a serialized 'passed' field.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from ...director.lesson_architecture_contract import LessonArchitecture,validate_lesson_architecture
from ...pedagogy.assessment_blueprint import AssessmentCell, build_assessment_blueprint
from .common import *

@dataclass(frozen=True)
class RoutePolicy(PolicyDigest):
    routes: tuple[tuple[str,tuple[str,...]],...]
    assessment_requirements: tuple[tuple[str,str,str,bool],...]
    item_answers: tuple[tuple[str,str],...]
    remediation: tuple[tuple[str,str],...]=()
    min_response_ms: int=1000
    max_age: int=86400
    def __post_init__(self):
        require(type(self.routes)is tuple and 1<=len(self.routes)<=128,'PED_ROUTES')
        ids([r for r,p in self.routes],'ROUTE')
        for r,p in self.routes:ids(p,'ROUTE_SCENES')
        require(type(self.assessment_requirements)is tuple and 0<len(self.assessment_requirements)<=128,'PED_REQUIREMENTS')
        require(len(set(self.assessment_requirements))==len(self.assessment_requirements),'PED_REQUIREMENT_DUPLICATE')
        for o,c,l,t in self.assessment_requirements:token(o,'objective');token(c,'concept');text(l,'level');require(type(t)is bool,'PED_TRANSFER')
        require(type(self.item_answers)is tuple,'PED_ANSWERS');ids([i for i,a in self.item_answers],'ANSWER_ITEM')
        for i,a in self.item_answers:text(a,'answer')
        require(type(self.remediation)is tuple and len(set(self.remediation))==len(self.remediation),'PED_REMEDIATION')
        for i,s in self.remediation:require(i in dict(self.item_answers),'PED_REMEDIATION_ITEM');token(s,'scene')
        integer(self.min_response_ms,'response',1,600000);integer(self.max_age,'age',1,604800)

def evaluate_pedagogy(architecture,cells,ref,source_refs,root,binding,policy,*,now):
    require(type(architecture)is LessonArchitecture,'PED_NATIVE_ARCHITECTURE');validate_lesson_architecture(architecture)
    require(type(cells)is tuple and all(type(c)is AssessmentCell for c in cells),'PED_NATIVE_CELLS')
    native=build_assessment_blueprint(policy.assessment_requirements,cells)
    sources=verify_sources(root,source_refs);allowed=set(sources);scenes={s.scene_id:s for s in architecture.scenes}
    require(all(set(s.evidence_ids)<=allowed for s in architecture.scenes)and all(set(c.evidence_ids)<=allowed for c in cells),'PED_SOURCE_BINDING')
    data=read_input(root,ref,binding,policy,'BIE-QA-HARD-013',('native_digest','mode','captured_at','routes'))
    require(data['native_digest']==digest(dict(architecture=asdict(architecture),cells=[asdict(c)for c in cells])),'PED_NATIVE_DIGEST')
    integer(now,'now');integer(data['captured_at'],'captured_at');require(0<=now-data['captured_at']<=policy.max_age,'PED_STALE_OBSERVATION')
    require(data['mode']in ('diagnostic','observed'),'PED_OBSERVATION_MODE')
    findings=[]
    if not native.passed:findings.append(Finding('NATIVE_ASSESSMENT_REQUIREMENT_MISSING','blueprint','BLOCKER'))
    submitted=unique(items(data['routes'],'PED_OBSERVED_ROUTES',1,128),'route_id','PED_ROUTE_DUPLICATE')
    require(set(submitted)==set(dict(policy.routes)),'PED_OBSERVED_ROUTE_CENSUS')
    answers=dict(policy.item_answers);all_item_ids={i for c in cells for i in c.item_ids}
    require(set(answers)==all_item_ids,'PED_ITEM_INVENTORY')
    for rid,expected in policy.routes:
        require(set(expected)<=set(scenes),'PED_UNKNOWN_SCENE')
        row=submitted[rid];fields(row,('route_id','scene_order','events'))
        if row['scene_order']!=list(expected):findings.append(Finding('NONDEFAULT_ROUTE_MISMATCH',rid,'BLOCKER'))
        seen=set()
        for sid in row['scene_order']:
            require(sid in scenes,'PED_TRACE_UNKNOWN_SCENE')
            if not set(scenes[sid].parent_scene_ids)<=seen:findings.append(Finding('OBSERVED_PREREQUISITE_ORDER',rid+':'+sid,'BLOCKER'))
            seen.add(sid)
        events=items(row['events'],'PED_EVENTS',1,4096);ids([e.get('event_id')for e in events],'PED_EVENT')
        last=-1;active={};completed=set();errors={};assessment_seen=set()
        for e in events:
            fields(e,('event_id','kind','item_id','scene_id','at_ms','text','correct'))
            integer(e['at_ms'],'event_time',0,86400000);require(e['at_ms']>=last,'PED_EVENT_TIME_ORDER');last=e['at_ms']
            require(e['scene_id']in row['scene_order'],'PED_EVENT_SCENE');text(e['text'],'event_text');require(e['correct']is None or type(e['correct'])is bool,'PED_EVENT_CORRECT')
            require(e['kind']in ('prompt','response','feedback','display','remediation'),'PED_EVENT_KIND')
            item=e['item_id'];require(item in answers,'PED_EVENT_ITEM')
            if e['kind']=='prompt':
                require(item not in active and item not in completed,'PED_DUPLICATE_PROMPT');active[item]=e['at_ms'];assessment_seen.add(item)
            elif e['kind']=='response':
                require(item in active and item not in completed,'PED_RESPONSE_WITHOUT_PROMPT')
                if e['at_ms']-active[item]<policy.min_response_ms:findings.append(Finding('RESPONSE_WINDOW_TOO_SHORT',rid+':'+item,'BLOCKER'))
                completed.add(item);require(type(e['correct'])is bool,'PED_RESPONSE_CORRECT_REQUIRED')
                if not e['correct']:errors[item]=e['at_ms']
            elif e['kind']=='feedback'and item not in completed:findings.append(Finding('FEEDBACK_BEFORE_RESPONSE',rid+':'+item,'BLOCKER'))
            # Any observed display, even tagged as another item, can leak a pending answer.
            if e['kind']!='response':
                for pending in set(active)-completed:
                    if answers[pending] in e['text']:findings.append(Finding('OBSERVED_ANSWER_LEAKAGE',rid+':'+pending,'BLOCKER'))
        if assessment_seen!=all_item_ids or completed!=all_item_ids:findings.append(Finding('OBSERVED_ASSESSMENT_COVERAGE',rid,'BLOCKER'))
        for item,scene in policy.remediation:
            if item in errors and not any(e['kind']=='remediation'and e['item_id']==item and e['scene_id']==scene and e['at_ms']>=errors[item]for e in events):findings.append(Finding('MISCONCEPTION_REMEDIATION_MISSING',rid+':'+item,'BLOCKER'))
    findings.append(Finding('OBSERVED_RUNTIME_ATTESTATION_REQUIRED','lesson'))
    return finish('BIE-QA-HARD-013',binding,findings,(ref,*source_refs),dict(native_blueprint_executed=True,native_coverage=native.passed,routes=len(submitted),observed_mastery=False))
