"""Explicit v1 → v2 migration for the representable subset.

Unsupported semantic features fail closed. The exact normalized legacy payload
and all enrichment inputs travel with the candidate; migration is not acceptance.
"""
from dataclasses import dataclass, asdict
import hashlib

from .canonical import canonical_json
from .codec import dumps, loads, encode
from .document import GameDocument
from .errors import GameContractError
from .expressions import Expr, validate_expr
from .legacy_codec import load_legacy, dump_legacy
from .provenance import EvidenceRef
from .validation import validate_game_document

def _sha(data):
    return hashlib.sha256(data).hexdigest()

def _same(a, b, code):
    if canonical_json(a) != canonical_json(b):
        raise GameContractError(code)

@dataclass(frozen=True)
class ExpressionEnrichment:
    legacy_expression: str
    typed_expression: Expr
    reasoning_evidence: EvidenceRef

    def validate(self):
        self.reasoning_evidence.validate()
        validate_expr(self.typed_expression)
        digest = _sha(canonical_json({'legacy_expression': self.legacy_expression,
                                     'typed_expression': encode(self.typed_expression)}))
        if self.reasoning_evidence.role != 'reasoning' or self.reasoning_evidence.content_sha256 != digest:
            raise GameContractError('GAME_MIGRATION_EXPRESSION_EVIDENCE')

@dataclass(frozen=True)
class MigrationEnrichment:
    legacy_sha256: str
    candidate: GameDocument
    text_catalog: dict[str, str]
    expressions: tuple[ExpressionEnrichment, ...]
    mechanic_modes: dict[str, str]
    policy_evidence: tuple[EvidenceRef, ...]
    review_evidence: EvidenceRef

@dataclass(frozen=True)
class MigrationResult:
    candidate_wire: bytes
    legacy_wire: bytes
    enrichment_wire: bytes
    receipt_wire: bytes

    def document(self):
        # A new object on each access; callers cannot mutate a sealed result.
        return loads(self.candidate_wire)

def enrichment_bytes(enrichment):
    return canonical_json({'text_catalog': enrichment.text_catalog,
        'expressions': [{'legacy_expression': x.legacy_expression, 'typed_expression': encode(x.typed_expression),
                         'reasoning_evidence': asdict(x.reasoning_evidence)} for x in enrichment.expressions],
        'mechanic_modes': enrichment.mechanic_modes, 'policy_evidence': enrichment.policy_evidence})

def review_binding(enrichment):
    """The exact payload a policy reviewer must bind; does not grant approval."""
    return canonical_json({'legacy_sha256': enrichment.legacy_sha256,
        'candidate_sha256': _sha(dumps(enrichment.candidate)),
        'enrichment_sha256': _sha(enrichment_bytes(enrichment))})

def migrate_legacy(data, enrichment: MigrationEnrichment):
    if type(enrichment) is not MigrationEnrichment:
        raise GameContractError('GAME_MIGRATION_EXPLICIT_ENRICHMENT_REQUIRED')
    legacy = load_legacy(data)
    legacy_wire = dump_legacy(legacy)
    if enrichment.legacy_sha256 != _sha(legacy_wire):
        raise GameContractError('GAME_MIGRATION_STALE_SOURCE')
    candidate = enrichment.candidate
    if type(candidate) is not GameDocument or candidate.game_ir_version != '2.0.0':
        raise GameContractError('GAME_MIGRATION_TARGET_VERSION')
    validate_game_document(candidate)
    _same(legacy.document_id, candidate.document_id, 'GAME_MIGRATION_DOCUMENT_ID')
    refs = {(r.role, r.artifact_id) for r in candidate.provenance.refs}
    for role, values in (('source', legacy.source_artifact_refs), ('reasoning', legacy.reasoning_decision_refs)):
        if any((role, value) not in refs for value in values):
            raise GameContractError('GAME_MIGRATION_PROVENANCE_LOSS')
    expressions = {}
    for item in enrichment.expressions:
        item.validate()
        if item.legacy_expression in expressions:
            raise GameContractError('GAME_MIGRATION_DUPLICATE_EXPRESSION')
        expressions[item.legacy_expression] = item.typed_expression
    used = set()

    def expression(old, new):
        if old not in expressions or expressions[old] != new:
            raise GameContractError('GAME_MIGRATION_EXPRESSION_UNRESOLVED')
        used.add(old)

    def text(old, ref):
        if enrichment.text_catalog.get(ref) != old:
            raise GameContractError('GAME_MIGRATION_TEXT_LOSS')

    policies = {p.artifact_id: p for p in enrichment.policy_evidence}
    if len(policies) != len(enrichment.policy_evidence):
        raise GameContractError('GAME_MIGRATION_DUPLICATE_POLICY')
    used_policies = set()
    used_mechanics = set()
    if len(legacy.experiences) != len(candidate.experiences):
        raise GameContractError('GAME_MIGRATION_EXPERIENCE_COVERAGE')
    for old_game, new_game in zip(legacy.experiences, candidate.experiences):
        _same((old_game.game_id, old_game.title), (new_game.game_id, new_game.title), 'GAME_MIGRATION_GAME_IDENTITY')
        if old_game.telemetry_events or old_game.compiler_capabilities:
            raise GameContractError('GAME_MIGRATION_RUNTIME_EXTENSIONS_UNSUPPORTED')
        for original, ref in ((old_game.scoring_policy, new_game.scoring_policy_ref), (old_game.mastery_policy, new_game.mastery_policy_ref)):
            evidence = policies.get(ref)
            if evidence is None:
                raise GameContractError('GAME_MIGRATION_POLICY_EVIDENCE_REQUIRED')
            evidence.validate()
            if evidence.role != 'policy' or evidence.content_sha256 != _sha(canonical_json(original)):
                raise GameContractError('GAME_MIGRATION_POLICY_HASH')
            used_policies.add(ref)
        if len(old_game.levels) != len(new_game.levels):
            raise GameContractError('GAME_MIGRATION_LEVEL_COVERAGE')
        for old, new in zip(old_game.levels, new_game.levels):
            _same((old.level_id, old.title, old.purpose), (new.level_id, new.title, new.purpose), 'GAME_MIGRATION_LEVEL_IDENTITY')
            level_refs = refs | {(r.role, r.artifact_id) for c in new.challenges for r in c.learning.provenance.refs}
            if any(('reasoning', ref) not in level_refs for ref in old.reasoning_decision_refs):
                raise GameContractError('GAME_MIGRATION_LEVEL_PROVENANCE_LOSS')
            if not set(old.learning_objective_refs).issubset({c.learning.objective_id for c in new.challenges}):
                raise GameContractError('GAME_MIGRATION_LEVEL_OBJECTIVE_LOSS')
            if old.adaptations:
                raise GameContractError('GAME_MIGRATION_LEGACY_ADAPTATION_UNSUPPORTED')
            old_states = [asdict(x) for x in old.state_variables]
            new_states = [{**asdict(x), 'value_type': x.value_type.value, 'enum_values': list(x.enum_values)} for x in new.state.variables]
            _same(old_states, new_states, 'GAME_MIGRATION_STATE_LOSS')
            entities = {e.entity_id: e for e in new.visual.entities}
            actions = {a.action_id: a for a in new.interaction.actions}
            for obj in old.manipulables:
                target = entities.get(obj.object_id)
                if target is None or target.accessible_description != obj.accessibility_label:
                    raise GameContractError('GAME_MIGRATION_ENTITY_LOSS')
                _same(obj.object_type, target.kind.value, 'GAME_MIGRATION_ENTITY_KIND')
                if set(obj.bindings.values()) != set(target.state_bindings) or obj.semantic_role != target.semantic_role:
                    raise GameContractError('GAME_MIGRATION_ENTITY_BINDING')
                if obj.properties:
                    raise GameContractError('GAME_MIGRATION_OBJECT_PROPERTIES_UNSUPPORTED')
                for action in obj.allowed_actions:
                    if action not in actions or actions[action].target_entity_id != obj.object_id:
                        raise GameContractError('GAME_MIGRATION_ACTION_LOSS')
            if len(old.rules) != len(new.interaction.rules):
                raise GameContractError('GAME_MIGRATION_RULE_COVERAGE')
            op_map = {'set': 'set', 'add': 'add', 'subtract': 'sub', 'multiply': 'mul', 'divide': 'div', 'toggle': 'toggle'}
            for rule, target in zip(old.rules, new.interaction.rules):
                _same((rule.rule_id, rule.explanation, rule.priority), (target.rule_id, target.explanation, target.priority), 'GAME_MIGRATION_RULE_IDENTITY')
                expression(rule.trigger_expression, target.condition)
                if len(rule.effects) != len(target.effects):
                    raise GameContractError('GAME_MIGRATION_EFFECT_COVERAGE')
                for effect, mapped in zip(rule.effects, target.effects):
                    if effect.operation not in op_map or effect.expression is not None:
                        raise GameContractError('GAME_MIGRATION_EFFECT_UNSUPPORTED')
                    _same((effect.target_variable_id, op_map[effect.operation], effect.value),
                          (mapped.target_variable_id, mapped.kind.value, mapped.value), 'GAME_MIGRATION_EFFECT_LOSS')
                if not set(rule.evidence_refs + rule.concept_refs).issubset(target.grounding_refs):
                    raise GameContractError('GAME_MIGRATION_RULE_GROUNDING_LOSS')
            if len(old.challenges) != len(new.challenges):
                raise GameContractError('GAME_MIGRATION_CHALLENGE_COVERAGE')
            for challenge, mapped in zip(old.challenges, new.challenges):
                _same((challenge.challenge_id, challenge.title, challenge.mastery_weight, challenge.difficulty),
                      (mapped.challenge_id, mapped.title, mapped.mastery_weight, mapped.difficulty), 'GAME_MIGRATION_CHALLENGE_IDENTITY')
                if challenge.hints or challenge.compiler_capabilities:
                    raise GameContractError('GAME_MIGRATION_CHALLENGE_EXTENSION_UNSUPPORTED')
                if enrichment.mechanic_modes.get(challenge.mechanic) != mapped.mode.value:
                    raise GameContractError('GAME_MIGRATION_MECHANIC_UNRESOLVED')
                used_mechanics.add(challenge.mechanic)
                text(challenge.mission_prompt, mapped.mission_prompt_ref)
                text(challenge.feedback.success_message, mapped.feedback.success_message_ref)
                text(challenge.feedback.failure_message, mapped.feedback.failure_message_ref)
                for misconception, message in challenge.feedback.misconception_messages.items():
                    text(message, dict(mapped.feedback.misconception_feedback).get(misconception))
                if challenge.feedback.explanation_artifact_refs and challenge.feedback.explanation_artifact_refs != [mapped.feedback.explanation_ref]:
                    raise GameContractError('GAME_MIGRATION_EXPLANATION_LOSS')
                expression(challenge.success_condition, mapped.success_condition)
                if len(challenge.failure_conditions) != len(mapped.failure_conditions):
                    raise GameContractError('GAME_MIGRATION_FAILURE_COVERAGE')
                for condition, typed in zip(challenge.failure_conditions, mapped.failure_conditions):
                    expression(condition, typed)
                for before, after in ((challenge.concept_refs, mapped.learning.concept_ids),
                                      (challenge.prerequisite_refs, mapped.learning.prerequisite_ids),
                                      (challenge.misconception_refs, mapped.learning.misconception_ids),
                                      (challenge.learning_objective_refs, (mapped.learning.objective_id,))):
                    if not set(before).issubset(after):
                        raise GameContractError('GAME_MIGRATION_LEARNING_LOSS')
                learning_refs = {(r.role, r.artifact_id) for r in mapped.learning.provenance.refs}
                for role, values in (('source', challenge.source_artifact_refs), ('reasoning', challenge.reasoning_decision_refs)):
                    if any((role, value) not in learning_refs for value in values):
                        raise GameContractError('GAME_MIGRATION_LEARNING_PROVENANCE_LOSS')
                if not set(challenge.allowed_actions).issubset(actions):
                    raise GameContractError('GAME_MIGRATION_ACTION_LOSS')
    if used != set(expressions) or used_policies != set(policies) or used_mechanics != set(enrichment.mechanic_modes):
        raise GameContractError('GAME_MIGRATION_UNUSED_ENRICHMENT')
    candidate_wire = dumps(candidate)
    enrichment_wire = enrichment_bytes(enrichment)
    review = enrichment.review_evidence
    review.validate()
    binding = {'legacy_sha256': _sha(legacy_wire), 'candidate_sha256': _sha(candidate_wire), 'enrichment_sha256': _sha(enrichment_wire)}
    if review.role != 'policy' or review.content_sha256 != _sha(canonical_json(binding)):
        raise GameContractError('GAME_MIGRATION_REVIEW_BINDING')
    receipt = {**binding, 'review_evidence': asdict(review), 'schema_version': 'bie.game.legacy-migration/1',
               'status': 'EXPLICIT_ENRICHED_CANDIDATE', 'semantic_review_supplied': True,
               'independent_semantic_equivalence_proven': False, 'runtime_verified': False, 'product_accepted': False}
    return MigrationResult(candidate_wire, legacy_wire, enrichment_wire, canonical_json(receipt))
