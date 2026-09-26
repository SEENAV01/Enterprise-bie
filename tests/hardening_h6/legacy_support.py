from dataclasses import asdict, replace
import hashlib
from bie.game_engine import contracts as v1
from bie.game_engine.fixtures import sample_document
from bie.game_engine.canonical import canonical_json
from bie.game_engine.codec import encode
from bie.game_engine.legacy_codec import dump_legacy
from bie.game_engine.legacy_migration import ExpressionEnrichment, MigrationEnrichment, review_binding
from bie.game_engine.provenance import EvidenceRef

def fixture():
    candidate = sample_document()
    game = candidate.experiences[0]
    level = game.levels[0]
    rule = level.interaction.rules[0]
    challenge = level.challenges[0]
    states = [v1.StateVariable(x.variable_id, x.value_type.value, x.initial_value,
              x.min_value, x.max_value, list(x.enum_values), x.units, x.semantic_role) for x in level.state.variables]
    obj = v1.Manipulable('entity:mover', 'Mover', 'object', {'x': 'x'}, ['drag:mover'],
                        'manipulated_object', accessibility_label='A movable object')
    old_rule = v1.Rule('rule:move', 'x < 2', [v1.Effect('x', 'set', 2.0)], rule.explanation,
                       rule.priority, ['source:book'])
    old_challenge = v1.Challenge(challenge.challenge_id, challenge.title, 'Move to the target',
        'manipulate_parameter', 'x == 2', ['drag:mover'], [], v1.FeedbackPolicy('Success', 'Retry'),
        challenge.mastery_weight, challenge.difficulty, concept_refs=['concept:motion'],
        prerequisite_refs=['pre:position'], learning_objective_refs=['obj:motion'],
        misconception_refs=['mis:direction'], reasoning_decision_refs=['reason:game'],
        source_artifact_refs=['source:book'], failure_conditions=['attempts > 3'])
    old_level = v1.GameLevel(level.level_id, level.title, level.purpose, states, [obj], [old_rule], [old_challenge])
    old_game = v1.GameExperience(game.game_id, game.title, 'manipulation', [old_level], {'correct': 10}, {'threshold': .8})
    old = v1.GameDocument('1.0.0', candidate.document_id, [old_game], ['source:book'], ['reason:game'], {'historical_note': 'preserved'})
    wire = dump_legacy(old)
    expression_rows = []
    for index, (text, expr) in enumerate([('x < 2', rule.condition), ('x == 2', challenge.success_condition), ('attempts > 3', challenge.failure_conditions[0])]):
        digest = hashlib.sha256(canonical_json({'legacy_expression': text, 'typed_expression': encode(expr)})).hexdigest()
        expression_rows.append(ExpressionEnrichment(text, expr, EvidenceRef('migration:expr:' + str(index), 'review:expression', digest, 'reasoning')))
    policies = tuple(EvidenceRef(ref, 'review:policy', hashlib.sha256(canonical_json(value)).hexdigest(), 'policy')
                     for ref, value in ((game.scoring_policy_ref, old_game.scoring_policy), (game.mastery_policy_ref, old_game.mastery_policy)))
    enrichment = MigrationEnrichment(hashlib.sha256(wire).hexdigest(), candidate,
        {challenge.mission_prompt_ref: 'Move to the target', challenge.feedback.success_message_ref: 'Success', challenge.feedback.failure_message_ref: 'Retry'},
        tuple(expression_rows), {'manipulate_parameter': 'manipulation'}, policies,
        EvidenceRef('migration:review', 'review:fixture', '0' * 64, 'policy'))
    return wire, seal(enrichment)

def seal(enrichment):
    return replace(enrichment, review_evidence=replace(enrichment.review_evidence,
        content_sha256=hashlib.sha256(review_binding(enrichment)).hexdigest()))
