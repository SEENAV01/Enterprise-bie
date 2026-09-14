"""Authored context fixtures using actual canonical KI/PR/MATH/RE/PED functions.

Source extraction and scored responses are supplied test data. This harness is
not a PDF extractor, authenticated assessment system or live teaching benchmark.
"""
from dataclasses import asdict
import hashlib
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid5, NAMESPACE_URL
from bie.infrastructure.artifact_store import ArtifactCatalog, FileSystemCAS
from bie.director.director_artifacts import DirectorArtifactIO, canonical
from bie.director.director_inputs import (TeachingBinding, publish_source_catalog, load_source_catalog,
    publish_reasoning, publish_pedagogy, load_director_inputs)
from bie.director.teaching_context import (SourceExcerpt, KnowledgeConcept, GroundedPrerequisite,
    GroundedDerivation, publish_teaching_context)
from bie.director.context_bridges import derivation_decision_value
from bie.director.qa_contract import SourceCatalog, SourcePage, SourcePassage
from bie.director.source_grounding_qa import SourceBytes
from bie.reasoning.decision_contracts import ReasoningDecision, EvidenceRef
from bie.reasoning.teaching_order import Candidate, decide as reasoning_order
from bie.prerequisite_intelligence.graph import Edge
from bie.math_intelligence.derivation_step import make_step
from bie.pedagogy.learning_objective_generator import generate_objective
from bie.pedagogy.teaching_mode_selection import select_teaching_mode
from bie.pedagogy.assessment_blueprint import AssessmentCell, build_assessment_blueprint
from bie.pedagogy.pedagogy_plan_contract import PedagogyDecision, build_pedagogy_plan


SPECS = {
    'science': {
        'title': 'From moving charge to current in copper',
        'concepts': (
            ('charge', 'electric current', 'Electric current is a flow of electric charge.'),
            ('copper', 'conduction in solid copper', 'In solid copper, mobile electrons carry electric current while the copper ions remain near their lattice positions.')),
        'condition': 'This explanation applies to solid copper, not to every copper compound.',
        'link': 'Understanding electric current as moving charge is a prerequisite for explaining conduction in solid copper.'},
    'economics': {
        'title': 'From direct barter to an accepted medium of exchange',
        'concepts': (
            ('barter', 'double coincidence of wants', 'The double coincidence of wants means that each trader must want what the other offers.'),
            ('money', 'medium of exchange', 'An accepted medium of exchange lets a seller receive money and buy from a different person later.')),
        'condition': 'The medium must be accepted by the people involved; universal acceptance is not established.',
        'link': 'Understanding the double coincidence of wants is a prerequisite for explaining how money separates selling from buying.'},
    'math': {
        'title': 'Explain each supplied algebraic transformation',
        'concepts': (('algebra', 'combining like terms', 'For a real number x, combining like terms preserves the value of an expression.'),),
        'condition': 'These transformations concern real numbers and do not establish a rule about arbitrary mathematical objects.',
        'link': 'The supplied chain is x + x to 2*x by collecting like terms because two equal terms add to twice the term. '
                'It continues from 2*x to x*2 by commutativity of multiplication because changing the factor order preserves the product.'},
}


def scored_event(f, *, concept_id=None, score=.9, reliability=1., learner_key='fixture-learner', age_steps=0, **changes):
    data = {'schema_version': 'bie.ped.reported_assessment/1.0.0', 'source_catalog_ref': asdict(f.source_ref),
        'learner_key': learner_key, 'concept_id': concept_id or f.concepts[0].concept_id,
        'item_id': 'reported-item:' + str(len(f.io.catalog.records)), 'response_text': 'Authored reported answer fixture',
        'score': score, 'reliability': reliability, 'age_steps': age_steps,
        'score_origin': 'controlled-fixture-reported-score', **changes}
    return f.io.derive('evidence.pedagogy_assessment', f.run_id, (f.source_ref,), data,
        stage_id='PEDAGOGY', metadata={'requires_review': True, 'accepted': False})


def publish_context(f, *, concepts=None, prerequisites=None, derivations=None, observation_refs=(), **kwargs):
    return publish_teaching_context(f.io, f.run_id, f.source_ref,
        f.concepts if concepts is None else concepts,
        f.prerequisites if prerequisites is None else prerequisites,
        f.derivations if derivations is None else derivations, observation_refs, **kwargs)


def rebind(f, context_ref, *, bindings=None, plan=None, objectives=None, reasoning_ref=None):
    re_ref = reasoning_ref or f.reasoning_ref
    ped_ref = publish_pedagogy(f.io, f.run_id, f.source_ref, re_ref, plan or f.plan,
        f.objectives if objectives is None else objectives, f.bindings if bindings is None else bindings,
        teaching_context_ref=context_ref)
    inputs = load_director_inputs(f.io, re_ref, ped_ref, run_id=f.run_id, **f.config)
    return ped_ref, inputs


def context_upstream(root, case_id='science', *, scores=(), ped_dependency=True, math_steps=None):
    spec = SPECS[case_id]; root = Path(root); root.mkdir(parents=True, exist_ok=True)
    run_id = str(uuid5(NAMESPACE_URL, 'bie-dir-context-fixture/1/' + case_id))
    io = DirectorArtifactIO(ArtifactCatalog(FileSystemCAS(root / 'cas')))
    link = spec['link'] if math_steps is None else ' '.join('The supplied step is %s to %s by %s because %s.' % row for row in math_steps)
    text = ' '.join([c[2] for c in spec['concepts']] + [spec['condition'], link])
    data = text.encode(); sha = 'sha256:' + hashlib.sha256(data).hexdigest()
    page = SourcePage('page:' + case_id, 'source:' + case_id, sha, 1, text, 'authored-context/1')
    passage = SourcePassage('evidence:' + case_id, page.page_id, page.fingerprint(), 'body', 0, len(text), text)
    source_ref = publish_source_catalog(io, run_id, SourceCatalog((page,), (passage,)),
        (SourceBytes(page.source_id, data, 'text/plain; charset=utf-8'),))
    _, _, _, source_refs, _ = load_source_catalog(io, source_ref)
    evidence = (EvidenceRef(source_refs[passage.evidence_id].artifact_id, 'primary', .95),)
    def excerpt(quote):
        start = text.index(quote)
        return SourceExcerpt(passage.evidence_id, start, start + len(quote), quote)
    concepts = tuple(KnowledgeConcept('concept:' + cid, label, (excerpt(definition),),
        (excerpt(spec['condition']),) if i == len(spec['concepts']) - 1 else ())
        for i, (cid, label, definition) in enumerate(spec['concepts']))
    prerequisites = (GroundedPrerequisite(Edge(concepts[0].concept_id, concepts[1].concept_id, .95),
        (passage.evidence_id,)),) if len(concepts) > 1 else ()
    derivations = ()
    if case_id == 'math':
        supplied = math_steps if math_steps is not None else (
            ('x + x', '2*x', 'collecting like terms', 'two equal terms add to twice the term'),
            ('2*x', 'x*2', 'commutativity of multiplication', 'changing the factor order preserves the product'))
        steps = tuple(make_step(*row, passage.evidence_id) for row in supplied)
        derivations = (GroundedDerivation('derivation:algebra', 'reasoning:algebra', concepts[0].concept_id, steps, ('x',)),)
    objectives = tuple(generate_objective(c.concept_id, c.label, (passage.evidence_id,)) for c in concepts)
    actual_order = reasoning_order(tuple(Candidate(c.concept_id, i, i, .9) for i, c in enumerate(concepts)))
    reasoning = []; decisions = []; bindings = []
    for i, objective in enumerate(objectives):
        cid = objective.concept_id.split(':')[-1]; rid = 'reasoning:' + cid; did = 'pedagogy:' + cid
        value = derivation_decision_value(derivations[0]) if derivations else canonical({'ordered_concepts': actual_order})
        reasoning.append(ReasoningDecision(rid, 'mathematical_derivation' if derivations else 'teaching_order',
            objective.concept_id, 'Which supplied reasoning supports this teaching decision?', value,
            'Controlled source-bound result; interpretation remains reviewable.', .95, list(evidence), requires_review=True))
        mode = select_teaching_mode(objective_level='UNDERSTAND', prerequisite_readiness=.8,
            mathematical_density=.9 if derivations else .1, dynamic_system=False, source_supports_derivation=bool(derivations))
        cell = AssessmentCell(objective.objective_id, objective.concept_id, 'UNDERSTAND', None, False,
            ('assessment:' + cid,), objective.evidence_ids)
        blueprint = build_assessment_blueprint(((objective.objective_id, objective.concept_id, 'UNDERSTAND', False),), (cell,))
        parents = (decisions[-1].decision_id,) if i and ped_dependency else ()
        decisions.append(PedagogyDecision(did, 'teaching_mode', 'mode:' + cid, objective.evidence_ids,
            parent_decision_ids=parents, requires_review=True))
        lesson = 'lesson:' + case_id if i == len(objectives) - 1 else 'earlier:' + case_id
        bindings.append(TeachingBinding(did, lesson, (objective.objective_id,), (rid,), mode, blueprint.cells))
    reasoning_ref = publish_reasoning(io, run_id, source_ref, tuple(reasoning), ())
    plan = build_pedagogy_plan(plan_id='ped-plan:' + case_id, source_id=page.source_id,
        objective_ids=tuple(o.objective_id for o in objectives), lesson_ids=tuple(b.lesson_id for b in bindings),
        decisions=tuple(decisions), policy_version='canonical-context-fixture/1')
    f = SimpleNamespace(root=root, case_id=case_id, run_id=run_id, io=io, source_ref=source_ref,
        concepts=concepts, prerequisites=prerequisites, derivations=derivations, objectives=objectives,
        reasoning=tuple(reasoning), reasoning_ref=reasoning_ref, bindings=tuple(bindings), plan=plan,
        config={'lesson_id': 'lesson:' + case_id, 'title': spec['title'], 'language': 'en'}, text=text)
    f.observation_refs = tuple(scored_event(f, score=score) for score in scores)
    f.context_ref = publish_context(f, observation_refs=f.observation_refs)
    f.pedagogy_ref, f.inputs = rebind(f, f.context_ref)
    return f
