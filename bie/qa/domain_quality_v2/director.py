"""HARD016: native-script rubric and source-conditioned multilingual checks.

Fixed literal/route/rubric checks do not replace contextual reviewers or measured
speech. Supplied style scores cannot compensate for critical academic failures.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
import unicodedata
from ...director.script_plan import ScriptPlan,validate_script_plan
from .common import *

@dataclass(frozen=True)
class DirectorPolicy(PolicyDigest):
    segment_ids: tuple[str,...]
    required_objectives: tuple[str,...]
    conditions: tuple[tuple[str,str,str],...]
    hooks: tuple[tuple[str,str],...] # hook segment, explanatory payoff segment
    terminology: tuple[tuple[str,str,str],...] # segment, language, exact displayed term
    rubric_floors: tuple[tuple[str,int],...]
    languages: tuple[str,...]=('en','hi')
    max_codepoints_per_second: int=40
    max_age: int=86400
    def __post_init__(self):
        ids(self.segment_ids,'DIR_SEGMENT');ids(self.required_objectives,'DIR_OBJECTIVE');ids(self.languages,'DIR_LANGUAGE')
        require(type(self.rubric_floors)is tuple,'DIR_RUBRIC');ids([r for r,f in self.rubric_floors],'RUBRIC_CRITERION')
        require({'academic','explanation','source_fidelity'}<=set(dict(self.rubric_floors)),'DIR_CRITICAL_FLOORS_REQUIRED')
        for r,f in self.rubric_floors:integer(f,'rubric_floor',1,1000000)
        for coll in (self.conditions,self.hooks,self.terminology):require(type(coll)is tuple and len(coll)<=1024,'DIR_POLICY_ROWS')
        for sid,src,frag in self.conditions:require(sid in self.segment_ids,'DIR_CONDITION_SUBJECT');token(src,'source');text(frag,'condition')
        for hook,payoff in self.hooks:require(hook in self.segment_ids and payoff in self.segment_ids and hook!=payoff,'DIR_HOOK_PAIR')
        for sid,lang,term in self.terminology:require(sid in self.segment_ids and lang in self.languages,'DIR_TERM_SCOPE');text(term,'term')
        integer(self.max_codepoints_per_second,'text_rate',1,200);integer(self.max_age,'age',1,604800)

def evaluate_director(native,ref,source_refs,root,binding,policy,*,now):
    require(type(native)is ScriptPlan,'DIR_NATIVE_SCRIPT');validate_script_plan(native)
    segments={s.segment_id:s for s in native.segments};require(set(segments)==set(policy.segment_ids),'DIR_NATIVE_SEGMENT_CENSUS')
    source=verify_sources(root,source_refs);findings=[]
    require(all(set(s.evidence_ids)<=set(source)for s in native.segments),'DIR_NATIVE_SOURCE_BINDING')
    if not set(policy.required_objectives)<={o for s in native.segments for o in s.objective_ids}:findings.append(Finding('DIRECTOR_OBJECTIVE_MISSING','script','BLOCKER'))
    data=read_input(root,ref,binding,policy,'BIE-QA-HARD-016',('native_digest','timeline','ratings','rated_at','provenance_mode'))
    require(data['native_digest']==digest(asdict(native)),'DIR_NATIVE_DIGEST');integer(now,'now');integer(data['rated_at'],'rated_at')
    require(0<=now-data['rated_at']<=policy.max_age,'DIR_STALE_RATING')
    require(data['provenance_mode']in ('diagnostic','observed'),'DIR_PROVENANCE')
    rows=unique(items(data['timeline'],'DIR_TIMELINE',1,1024),'segment_id','DIR_TIMELINE_DUPLICATE')
    require(set(rows)==set(segments),'DIR_TIMELINE_CENSUS')
    for sid,row in rows.items():
        fields(row,('segment_id','language','start_ms','end_ms','role'))
        require(row['language']in policy.languages,'DIR_UNKNOWN_LANGUAGE');require(row['role']in ('hook','explanation','recap','transition'),'DIR_ROLE')
        integer(row['start_ms'],'start',0,86400000);integer(row['end_ms'],'end',1,86400000);require(row['end_ms']>row['start_ms'],'DIR_TIMING')
        s=segments[sid].text_intent
        if any(unicodedata.category(ch)=='Cc'and ch not in '\n\t'for ch in s)or any(ch in s for ch in ('\u202e','\u202d','\u2066','\u2067','\u2068','\u2069')):findings.append(Finding('SCRIPT_HIDDEN_CONTROL',sid,'BLOCKER'))
        if len(s)*1000>policy.max_codepoints_per_second*(row['end_ms']-row['start_ms']):findings.append(Finding('MULTILINGUAL_TIMING_BUDGET',sid,'BLOCKER'))
    for sid,src,fragment in policy.conditions:
        require(src in source and fragment in source[src],'DIR_CONDITION_NOT_IN_SOURCE')
        if fragment not in segments[sid].text_intent:findings.append(Finding('SOURCE_CONDITION_DROPPED',sid,'BLOCKER'))
    for hook,payoff in policy.hooks:
        if rows[hook]['role']!='hook'or rows[payoff]['role']!='explanation'or rows[payoff]['start_ms']<rows[hook]['end_ms']:findings.append(Finding('HOOK_WITHOUT_EXPLANATORY_PAYOFF',hook,'BLOCKER'))
        if segments[hook].text_intent==segments[payoff].text_intent:findings.append(Finding('REPEATED_HOOK_NOT_EXPLANATION',hook,'BLOCKER'))
    for sid,lang,term in policy.terminology:
        if rows[sid]['language']!=lang or term not in segments[sid].text_intent:findings.append(Finding('MULTILINGUAL_TERM_MISSING',sid,'BLOCKER'))
    require(type(data['ratings'])is dict and set(data['ratings'])==set(dict(policy.rubric_floors)),'DIR_RUBRIC_CENSUS')
    for criterion,floor in policy.rubric_floors:
        score=data['ratings'][criterion];integer(score,'criterion_score',0,1000000)
        if score<floor:findings.append(Finding('RUBRIC_HARD_FLOOR_FAILED',criterion,'BLOCKER'))
    findings.append(Finding('INDEPENDENT_SCRIPT_RUBRIC_AND_SPEECH_REQUIRED','script'))
    return finish('BIE-QA-HARD-016',binding,findings,(ref,*source_refs),dict(native_script_executed=True,segment_count=len(segments),all_floors_independent=True,actual_speech_measured=False))
