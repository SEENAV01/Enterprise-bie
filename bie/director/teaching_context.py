"""BIE-DIR-HARD-CONTEXT-001: source-bound adapters over existing KI/PR/MATH/PED.

This wraps supplied structured extraction and scored events; it does not claim
to extract a book, authenticate a learner, prove algebra or grade a response.
"""
from dataclasses import asdict, dataclass
import ast
from .director_artifacts import canonical, parse_json, fields, fingerprint, reference
from .contract_validation import ids, nonblank, finite, acyclic
from .recovery_codec import decode
from bie.bie_core.artifact_contracts import ArtifactRef
from bie.knowledge_intelligence.knowledge_graph_build import build as build_knowledge_graph
from bie.knowledge_intelligence.knowledge_graph_validate import validate as validate_knowledge_graph
from bie.knowledge_intelligence.concept_definitions import attach as attach_definitions
from bie.knowledge_intelligence.applicability_conditions import make as make_condition
from bie.prerequisite_intelligence.graph import Edge, build_graph
from bie.prerequisite_intelligence.teaching_order import teaching_order
from bie.math_intelligence.derivation_step import DerivationStep, make_step
from bie.math_intelligence.derivation_chain import Step, validate_chain
from bie.math_intelligence.symbolic_equivalence import equivalent, _eval
from bie.math_intelligence.teachable_math import plan_step
from bie.pedagogy.uncertainty_aware_mastery import MasteryObservation, infer_knowledge_state


@dataclass(frozen=True)
class SourceExcerpt:
    evidence_id: str
    start_char: int
    end_char: int
    quote: str


@dataclass(frozen=True)
class KnowledgeConcept:
    concept_id: str
    label: str
    definitions: tuple[SourceExcerpt, ...]
    conditions: tuple[SourceExcerpt, ...] = ()


@dataclass(frozen=True)
class GroundedPrerequisite:
    edge: Edge
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class GroundedDerivation:
    derivation_id: str
    reasoning_decision_id: str
    concept_id: str
    steps: tuple[DerivationStep, ...]
    variables: tuple[str, ...]


@dataclass(frozen=True)
class TeachingContextPolicy:
    version: str = 'bie-dir-teaching-context/1.0.0'
    maximum_concepts: int = 2048
    maximum_edges: int = 8192
    maximum_math_steps: int = 1024
    maximum_observations: int = 4096

    def validate(self):
        nonblank(self.version, 'context version')
        for value in (self.maximum_concepts, self.maximum_edges, self.maximum_math_steps, self.maximum_observations):
            if type(value) is not int or value < 1:
                raise ValueError('positive context resource budget required')


@dataclass(frozen=True)
class TeachingContext:
    context_ref: ArtifactRef
    source_catalog_ref: ArtifactRef
    concepts: tuple[KnowledgeConcept, ...]
    prerequisites: tuple[GroundedPrerequisite, ...]
    derivations: tuple[GroundedDerivation, ...]
    compiled_json: str
    review_reasons: tuple[str, ...]

    def model_data(self):
        return parse_json(self.compiled_json)


def _rich_records(value):
    """Decode only the compiled-in rich teaching records and SourceExcerpt fields."""
    from .rich_teaching import (GroundedWorkedExample, GroundedDemonstration, GroundedInquiry,
        GroundedMisconception, GroundedNotation)
    known = {kind.__name__: kind for kind in (GroundedWorkedExample, GroundedDemonstration,
        GroundedInquiry, GroundedMisconception, GroundedNotation)}
    result = []
    for row in value:
        if type(row) is not dict or set(row) != {'type', 'value'} or row['type'] not in known:
            raise ValueError('known rich teaching record required')
        kind = known[row['type']]; raw = fields(row['value'], kind.__dataclass_fields__, row['type'])
        def excerpt(item):
            return SourceExcerpt(**fields(item, SourceExcerpt.__dataclass_fields__, 'rich source excerpt'))
        if kind is GroundedWorkedExample:
            item = kind(raw['example_id'], raw['concept_id'], excerpt(raw['setup']),
                tuple(excerpt(step) for step in raw['steps']), excerpt(raw['outcome']))
        elif kind is GroundedDemonstration:
            item = kind(raw['demonstration_id'], raw['concept_id'], excerpt(raw['setup']),
                excerpt(raw['action']), excerpt(raw['observation']), excerpt(raw['interpretation']))
        elif kind is GroundedInquiry:
            item = kind(raw['inquiry_id'], raw['concept_id'], excerpt(raw['claim']), excerpt(raw['evidence']),
                excerpt(raw['misconception']) if raw['misconception'] is not None else None)
        elif kind is GroundedMisconception:
            item = kind(raw['misconception_id'], raw['concept_id'], excerpt(raw['belief']),
                excerpt(raw['counterevidence']), excerpt(raw['replacement']))
        else:
            item = kind(raw['notation_id'], raw['concept_id'], excerpt(raw['symbol']),
                raw['spoken_form'], excerpt(raw['meaning']))
        result.append(item)
    return tuple(result)


def _rich_json(records):
    return [{'type': type(record).__name__, 'value': asdict(record)} for record in records]


def excerpt_text(catalog, excerpt):
    passages = {p.evidence_id: p for p in catalog.passages}
    if excerpt.evidence_id not in passages:
        raise ValueError('unresolved context excerpt')
    text = passages[excerpt.evidence_id].quote
    if (type(excerpt.start_char) is not int or type(excerpt.end_char) is not int
            or not 0 <= excerpt.start_char < excerpt.end_char <= len(text)
            or text[excerpt.start_char:excerpt.end_char] != excerpt.quote or not excerpt.quote.strip()):
        raise ValueError('context quote/offset mismatch')
    return excerpt.quote


def _expression(text, variables):
    # Bound the existing numerical probe tool before calling it. No calls,
    # attributes, containers, huge integers or compound exponents are admitted.
    if not isinstance(text, str) or not text.strip() or len(text) > 256:
        raise ValueError('bounded algebraic expression required')
    tree = ast.parse(text.replace('^', '**'), mode='eval')
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div,
               ast.Pow, ast.USub, ast.UAdd, ast.Load, ast.Name, ast.Constant)
    nodes = list(ast.walk(tree))
    if len(nodes) > 128 or any(not isinstance(n, allowed) for n in nodes):
        raise ValueError('unsupported expression structure')
    for node in nodes:
        if isinstance(node, ast.Name) and node.id not in variables:
            raise ValueError('unbound math symbol')
        if isinstance(node, ast.Constant):
            finite(node.value, 'math constant', low=-1000000, high=1000000)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            if not isinstance(node.right, ast.Constant) or type(node.right.value) is not int or not 0 <= node.right.value <= 12:
                raise ValueError('bounded literal exponent required')
            if not isinstance(node.left, (ast.Name, ast.Constant)):
                raise ValueError('compound exponent base requires a different math adapter')


def _observations(io, refs, source_ref, concepts, policy):
    if len(refs) > policy.maximum_observations:
        raise ValueError('mastery observation resource budget')
    observations = []; learner = None; authenticated = 0
    for ref in refs:
        event = io.load(ref)
        if event.artifact_type == 'evidence.pedagogy_assessment.authenticated':
            from .authenticated_assessment import validate_authenticated_assessment
            data = validate_authenticated_assessment(io, event, source_ref); authenticated += 1
        else:
            if event.artifact_type != 'evidence.pedagogy_assessment' or event.schema_version != '1.0.0':
                raise ValueError('explicit scored assessment event required')
            data = fields(event.payload, ('schema_version', 'source_catalog_ref', 'learner_key', 'concept_id',
                'item_id', 'response_text', 'score', 'reliability', 'age_steps', 'score_origin'), 'assessment event')
            if data['schema_version'] != 'bie.ped.reported_assessment/1.0.0' or reference(data['source_catalog_ref']) != source_ref:
                raise ValueError('unsupported or stale scored event')
        if source_ref not in event.parent_refs or event.run_id != io.load(source_ref).run_id:
            raise ValueError('assessment source/run ancestry mismatch')
        for name in ('learner_key', 'concept_id', 'item_id', 'response_text', 'score_origin'):
            nonblank(data[name], name)
        if data['concept_id'] not in concepts or learner is not None and learner != data['learner_key']:
            raise ValueError('unknown concept or mixed learners')
        learner = data['learner_key']
        finite(data['score'], 'reported score', high=1); finite(data['reliability'], 'reported reliability', high=1)
        if type(data['age_steps']) is not int or data['age_steps'] < 0:
            raise ValueError('observation age must be a nonnegative integer')
        # The actual persisted event is the evidence, not a book passage posing
        # as evidence that this learner answered an assessment.
        observations.append(MasteryObservation(event.artifact_id, data['concept_id'], data['score'],
            data['reliability'], data['age_steps'], (event.artifact_id,)))
    return tuple(observations), authenticated


def _compile_context(io, source_ref, concepts, prerequisites, derivations, observation_refs, policy,
                     rich_teaching=()):
    from .director_inputs import load_source_catalog
    policy.validate()
    _, catalog, _, evidence_refs, _ = load_source_catalog(io, source_ref)
    if not concepts or len(concepts) > policy.maximum_concepts or len(prerequisites) > policy.maximum_edges:
        raise ValueError('nonempty context within configured resource budgets required')
    ids(tuple(c.concept_id for c in concepts), 'context concepts')
    concept_ids = {c.concept_id for c in concepts}; nodes = []
    for concept in concepts:
        nonblank(concept.label, 'concept label')
        if not concept.definitions:
            raise ValueError('each supplied concept needs grounded definition evidence')
        definitions = [{'text': excerpt_text(catalog, d), 'anchor_id': evidence_refs[d.evidence_id].artifact_id,
                        'confidence': 1.0} for d in concept.definitions]
        # Confidence here is exact quote binding, not semantic interpretation.
        conditions = [make_condition(concept.concept_id, excerpt_text(catalog, d),
            (evidence_refs[d.evidence_id].artifact_id,), 1.0) for d in concept.conditions]
        nodes.append({'concept_id': concept.concept_id, 'label': concept.label,
                      **attach_definitions(concept.concept_id, definitions), 'conditions': conditions})
    edges = []; pairs = set(); incoming = {c: [] for c in concept_ids}
    for row in prerequisites:
        edge = row.edge; finite(edge.confidence, 'prerequisite confidence', high=1)
        ids(row.evidence_ids, 'prerequisite evidence')
        if not set(row.evidence_ids) <= evidence_refs.keys():
            raise ValueError('prerequisite evidence outside source')
        pair = (edge.prerequisite, edge.dependent)
        if pair in pairs or set(pair) - concept_ids or pair[0] == pair[1]:
            raise ValueError('duplicate, self or dangling prerequisite')
        pairs.add(pair); incoming[edge.dependent].append(edge.prerequisite)
        edges.append({'source': edge.prerequisite, 'target': edge.dependent, 'type': 'PREREQUISITE',
                      'confidence': edge.confidence, 'evidence_ids': list(row.evidence_ids)})
    acyclic(incoming)
    pr_graph = build_graph(concept_ids, tuple(row.edge for row in prerequisites))
    order = teaching_order(pr_graph.nodes, list(pairs))
    knowledge = build_knowledge_graph(nodes, edges); kg_qa = validate_knowledge_graph(knowledge)
    if not kg_qa['passed']:
        raise ValueError('canonical knowledge graph validation failed')
    ids(tuple(d.derivation_id for d in derivations), 'derivation IDs', required=False)
    ids(tuple(d.reasoning_decision_id for d in derivations), 'derivation RE bindings', required=False)
    if sum(len(d.steps) for d in derivations) > policy.maximum_math_steps:
        raise ValueError('math context resource budget')
    math = []
    for derivation in derivations:
        if derivation.concept_id not in concept_ids or not derivation.steps:
            raise ValueError('derivation concept/steps missing')
        variables = ids(derivation.variables, 'math variables', required=False)
        if len(variables) > 8 or any(not v.isidentifier() or v.startswith('_') for v in variables):
            raise ValueError('bounded named math variables required')
        probes = []; teaching = []
        for step in derivation.steps:
            if make_step(step.before, step.after, step.rule, step.justification, step.source) != step:
                raise ValueError('noncanonical derivation step')
            if step.source not in evidence_refs:
                raise ValueError('derivation lacks actual source evidence')
            quote = next(p.quote for p in catalog.passages if p.evidence_id == step.source)
            if any(part not in quote for part in (step.before, step.after, step.rule, step.justification)):
                raise ValueError('derivation expressions/rule/justification absent from cited source')
            _expression(step.before, variables); _expression(step.after, variables)
            for point in (-2.0, -.5, 1.0, 3.0):
                env = {v: point + i * .37 for i, v in enumerate(variables)}
                try:
                    samples = (_eval(step.before, env), _eval(step.after, env))
                except ZeroDivisionError:
                    continue
                for sample in samples: finite(sample, 'finite math probe result', low=-float('inf'))
            result = equivalent(step.before, step.after, variables)
            if not result.equivalent:
                raise ValueError('existing math probes found disagreement or no valid probes')
            probes.append(asdict(result))
            teaching.append(asdict(plan_step(step.after, len(variables), True, False)))
        chain = validate_chain([Step(s.before, s.after) for s in derivation.steps])
        if not chain.valid:
            raise ValueError('disconnected source derivation chain')
        math.append({'derivation': asdict(derivation), 'chain': asdict(chain), 'numerical_probes': probes,
                     'teaching_steps': teaching, 'proof_status': 'NOT_PROVEN_REVIEW_REQUIRED'})
    observations, authenticated = _observations(io, observation_refs, source_ref, concept_ids, policy)
    states = tuple(infer_knowledge_state(c, observations) for c in sorted(concept_ids))
    result = {'knowledge_graph': knowledge, 'knowledge_graph_checks': kg_qa,
            'prerequisite_order': order, 'math': math, 'mastery_states': [asdict(s) for s in states],
            'mastery_interpretation': ('IDENTITY_AND_GRADE_RECEIPT_AUTHENTICATED; LEARNING_INFERENCE_STILL_UNCALIBRATED; NEVER_WAIVE_PREREQUISITES'
                if authenticated else 'REPORTED_OBSERVATIONS_NOT_AUTHENTICATED_OR_CALIBRATED; NEVER_WAIVE_PREREQUISITES'),
            'review_reasons': ['CONTEXT_SEMANTICS_REVIEW_REQUIRED'] +
                (['NUMERICAL_PROBES_ARE_NOT_PROOF'] if math else []) +
                (['AUTHENTICATED_GRADE_STILL_REQUIRES_CALIBRATION_REVIEW'] if authenticated else
                 (['REPORTED_MASTERY_REQUIRES_REVIEW'] if observations else ['MASTERY_UNKNOWN_NO_OBSERVATIONS']))}
    if rich_teaching:
        from .rich_teaching import compile_rich_teaching
        result['rich_teaching'] = compile_rich_teaching(rich_teaching, concept_ids,
            lambda excerpt: excerpt_text(catalog, excerpt))
        result['review_reasons'].append('RICH_TEACHING_EFFECTIVENESS_REQUIRES_REVIEW')
    return result


def publish_teaching_context(io, run_id, source_ref, concepts, prerequisites=(), derivations=(),
                             observation_refs=(), policy=TeachingContextPolicy(), *, rich_teaching=()):
    concepts = decode(tuple[KnowledgeConcept, ...], parse_json(canonical([asdict(c) for c in concepts])))
    prerequisites = decode(tuple[GroundedPrerequisite, ...], parse_json(canonical([asdict(p) for p in prerequisites])))
    derivations = decode(tuple[GroundedDerivation, ...], parse_json(canonical([asdict(d) for d in derivations])))
    refs = tuple(observation_refs); ids(tuple(r.artifact_id for r in refs), 'observation refs', required=False)
    rich_teaching = _rich_records(parse_json(canonical(_rich_json(tuple(rich_teaching)))))
    compiled = _compile_context(io, source_ref, concepts, prerequisites, derivations, refs, policy, rich_teaching)
    schema = 'bie.dir.teaching_context/1.1.0' if rich_teaching else 'bie.dir.teaching_context/1.0.0'
    payload = {'schema_version': schema, 'source_catalog_ref': asdict(source_ref),
         'concepts': [asdict(c) for c in concepts], 'prerequisites': [asdict(p) for p in prerequisites],
         'derivations': [asdict(d) for d in derivations], 'observation_refs': [asdict(r) for r in refs],
         'policy': asdict(policy), 'compiled': compiled}
    if rich_teaching: payload['rich_teaching'] = _rich_json(rich_teaching)
    return io.derive('pedagogy.teaching_context', run_id, (source_ref,) + refs,
        payload, stage_id='PEDAGOGY',
        metadata={'requires_review': True, 'accepted': False, 'release_ready': False})


def load_teaching_context(io, ref, source_ref):
    artifact = io.load(ref)
    if any(a.run_id != artifact.run_id for a in io.load_graph((artifact.to_ref(),)).values()):
        raise ValueError('cross-run teaching context ancestry')
    if artifact.artifact_type != 'pedagogy.teaching_context' or artifact.schema_version != '1.0.0':
        raise ValueError('typed teaching context required')
    version = artifact.payload.get('schema_version') if type(artifact.payload) is dict else None
    expected_fields = ('schema_version', 'source_catalog_ref', 'concepts', 'prerequisites',
        'derivations', 'observation_refs', 'policy', 'compiled') + (('rich_teaching',) if version == 'bie.dir.teaching_context/1.1.0' else ())
    p = fields(artifact.payload, expected_fields, 'teaching context')
    if p['schema_version'] not in ('bie.dir.teaching_context/1.0.0', 'bie.dir.teaching_context/1.1.0') or reference(p['source_catalog_ref']) != source_ref:
        raise ValueError('stale context/source pairing')
    concepts = decode(tuple[KnowledgeConcept, ...], p['concepts'])
    prerequisites = decode(tuple[GroundedPrerequisite, ...], p['prerequisites'])
    derivations = decode(tuple[GroundedDerivation, ...], p['derivations'])
    refs = tuple(reference(r) for r in p['observation_refs'])
    ids(tuple(r.artifact_id for r in refs), 'observation refs', required=False)
    if artifact.parent_refs != [source_ref, *refs]:
        raise ValueError('teaching context parent coverage mismatch')
    rich_teaching = _rich_records(p['rich_teaching']) if version == 'bie.dir.teaching_context/1.1.0' else ()
    expected = _compile_context(io, source_ref, concepts, prerequisites, derivations, refs,
        decode(TeachingContextPolicy, p['policy']), rich_teaching)
    if (canonical(expected) != canonical(p['compiled']) or artifact.metadata.get('requires_review') is not True
            or artifact.metadata.get('accepted') is not False or artifact.metadata.get('release_ready') is not False):
        raise ValueError('context tool output edited or review removed')
    return TeachingContext(artifact.to_ref(), source_ref, concepts, prerequisites, derivations,
                           canonical(expected), tuple(expected['review_reasons']))
