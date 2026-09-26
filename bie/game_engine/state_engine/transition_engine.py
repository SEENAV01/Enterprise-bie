from __future__ import annotations
from ..document import GameLevelContract
from ..errors import GameContractError
from .contracts import ActionCommand
from .manipulables import normalize_command
from .expression_runtime import evaluate_typed
from .effects import apply_effects
from .snapshots import make_snapshot
from .receipts import make_transition_receipt,transition_receipt_id

def execute_rule(level:GameLevelContract,snapshot,command:ActionCommand,rule_id:str):
    level.validate();snapshot.validate();norm=normalize_command(level,command)
    if command.expected_snapshot_id is not None and command.expected_snapshot_id!=snapshot.snapshot_id:raise GameContractError('GAME_STATE_STALE_COMMAND')
    rules={r.rule_id:r for r in level.interaction.rules}
    if rule_id not in rules:raise GameContractError('GAME_STATE_UNKNOWN_RULE',rule_id)
    rule=rules[rule_id];state=snapshot.as_dict();ok=evaluate_typed(rule.condition,state,level.state.type_map())
    if type(ok) is not bool or not ok:raise GameContractError('GAME_STATE_RULE_NOT_ELIGIBLE',rule_id)
    updated,deltas=apply_effects(level.state,state,rule.effects)
    impl={'rule':rule,'normalized_command':norm}
    rid=transition_receipt_id(command.command_id,rule_id,snapshot,deltas,impl)
    after=make_snapshot(level.state,updated,snapshot.tick+1,snapshot.snapshot_id,rid)
    receipt=make_transition_receipt(command.command_id,rule_id,snapshot,after,deltas,impl)
    if after.transition_receipt_id!=receipt.receipt_id:raise GameContractError('GAME_STATE_RECEIPT_BINDING')
    return after,receipt
