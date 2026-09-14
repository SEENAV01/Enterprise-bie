"""Authored large-source protocol fixtures; no real PDF extraction or quality claim."""
from dataclasses import asdict
import copy, hashlib, json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid5, NAMESPACE_URL
from bie.infrastructure.artifact_store import ArtifactCatalog, FileSystemCAS
from bie.director.director_artifacts import DirectorArtifactIO, canonical
from bie.director.director_inputs import (TeachingBinding, publish_source_catalog, load_source_catalog,
    publish_reasoning, publish_pedagogy, load_director_inputs)
from bie.director.qa_contract import SourceCatalog, SourcePage, SourcePassage
from bie.director.source_grounding_qa import SourceBytes
from bie.director.teaching_context import SourceExcerpt, KnowledgeConcept, GroundedPrerequisite, publish_teaching_context
from bie.prerequisite_intelligence.graph import Edge
from bie.reasoning.decision_contracts import ReasoningDecision, EvidenceRef
from bie.reasoning.teaching_order import Candidate, decide
from bie.pedagogy.learning_objective_generator import generate_objective
from bie.pedagogy.teaching_mode_selection import select_teaching_mode
from bie.pedagogy.assessment_blueprint import AssessmentCell, build_assessment_blueprint
from bie.pedagogy.pedagogy_plan_contract import PedagogyDecision, build_pedagogy_plan


def long_upstream(root, *, units=8, page_characters=5200, dependencies='pairs'):
    root=Path(root); root.mkdir(parents=True,exist_ok=True)
    run_id=str(uuid5(NAMESPACE_URL,'bie-window-fixture/1/'+str(units)+'/'+str(page_characters)+'/'+dependencies))
    io=DirectorArtifactIO(ArtifactCatalog(FileSystemCAS(root/'cas')))
    passages=[]; pages=[]; sources=[]; concepts=[]; definitions=[]; conditions=[]
    for i in range(units):
        label='archive comparison '+str(i+1)
        definition='In '+label+', the earlier recorded event precedes the later recorded event.'
        condition='These recorded dates establish temporal order; they do not establish causation without additional evidence.'
        paragraph='The authored archive case '+str(i+1)+' distinguishes the order recorded by dates from a causal explanation. A sequence can be described while the explanation remains unresolved. '
        text=definition+'\n'+paragraph*max(1,page_characters//len(paragraph))+'\n'+condition
        data=text.encode(); source_id='source:archive:'+str(i+1)
        page=SourcePage('page:archive:'+str(i+1),source_id,'sha256:'+hashlib.sha256(data).hexdigest(),1,text,'authored-window-fixture/1')
        passage=SourcePassage('evidence:archive:'+str(i+1),page.page_id,page.fingerprint(),'body',0,len(text),text)
        pages.append(page); passages.append(passage); sources.append(SourceBytes(source_id,data,'text/plain; charset=utf-8'))
        def excerpt(quote):
            at=text.index(quote); return SourceExcerpt(passage.evidence_id,at,at+len(quote),quote)
        concepts.append(KnowledgeConcept('concept:archive:'+str(i+1),label,(excerpt(definition),),(excerpt(condition),)))
        definitions.append(definition); conditions.append(condition)
    source_ref=publish_source_catalog(io,run_id,SourceCatalog(tuple(pages),tuple(passages)),tuple(sources))
    _,_,_,refs,_=load_source_catalog(io,source_ref)
    objectives=tuple(generate_objective(c.concept_id,c.label,(p.evidence_id,)) for c,p in zip(concepts,passages))
    ordered=decide(tuple(Candidate(c.concept_id,0,i,.9) for i,c in enumerate(concepts)))
    reasoning=[]; decisions=[]; bindings=[]; prerequisites=[]
    mode=select_teaching_mode(objective_level='UNDERSTAND',prerequisite_readiness=.8,mathematical_density=0.,
        dynamic_system=False,source_supports_derivation=False)
    for i,(concept,objective,passage) in enumerate(zip(concepts,objectives,passages)):
        did='pedagogy:archive:'+str(i+1); rid='reasoning:archive:'+str(i+1)
        parent=(decisions[i-1].decision_id,) if i and (dependencies=='chain' or dependencies=='pairs' and i%2) else ()
        # Dependencies are controlled curriculum signals, not claimed empirical
        # prerequisite discoveries. They stay grounded and review-required.
        if parent: prerequisites.append(GroundedPrerequisite(Edge(concepts[i-1].concept_id,concept.concept_id,.8),
            (passages[i-1].evidence_id,passage.evidence_id)))
        evidence=EvidenceRef(refs[passage.evidence_id].artifact_id,'primary',.9)
        reasoning.append(ReasoningDecision(rid,'teaching_order',concept.concept_id,'Which authored case should be explained?',
            canonical({'ordered_concepts':ordered}),'Original teaching_order on authored candidates.',.9,[evidence],requires_review=True))
        cell=AssessmentCell(objective.objective_id,concept.concept_id,'UNDERSTAND',None,False,
            ('assessment:archive:'+str(i+1),),objective.evidence_ids)
        blueprint=build_assessment_blueprint(((objective.objective_id,concept.concept_id,'UNDERSTAND',False),),(cell,))
        decisions.append(PedagogyDecision(did,'teaching_mode','mode:archive:'+str(i+1),objective.evidence_ids,parent_decision_ids=parent,requires_review=True))
        bindings.append(TeachingBinding(did,'lesson:archive',(objective.objective_id,),(rid,),mode,blueprint.cells))
    reasoning_ref=publish_reasoning(io,run_id,source_ref,tuple(reasoning),())
    plan=build_pedagogy_plan(plan_id='ped-plan:archive',source_id=pages[0].source_id,
        objective_ids=tuple(o.objective_id for o in objectives),lesson_ids=('lesson:archive',),
        decisions=tuple(decisions),policy_version='authored-large-source/1')
    context_ref=publish_teaching_context(io,run_id,source_ref,tuple(concepts),tuple(prerequisites))
    pedagogy_ref=publish_pedagogy(io,run_id,source_ref,reasoning_ref,plan,objectives,tuple(bindings),teaching_context_ref=context_ref)
    config={'lesson_id':'lesson:archive','title':'Read a sequence of authored archive cases carefully','language':'en'}
    inputs=load_director_inputs(io,reasoning_ref,pedagogy_ref,run_id=run_id,**config)
    return SimpleNamespace(root=root,case_id='archive',run_id=run_id,io=io,source_ref=source_ref,reasoning_ref=reasoning_ref,
        pedagogy_ref=pedagogy_ref,context_ref=context_ref,inputs=inputs,config=config,concepts=tuple(concepts),
        objectives=objectives,bindings=tuple(bindings),reasoning=tuple(reasoning),plan=plan,
        source_texts=tuple(p.text for p in pages),definitions=tuple(definitions),conditions=tuple(conditions))
