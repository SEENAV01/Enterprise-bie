from __future__ import annotations
from ..errors import GameContractError
from ..canonical import fingerprint

def verify_receipt_chain(initial_snapshot,receipts,final_snapshot):
    current=initial_snapshot.snapshot_id;commands=set()
    for r in receipts:
        r.validate()
        if r.command_id in commands:raise GameContractError('GAME_STATE_REPLAY_DUPLICATE_COMMAND')
        commands.add(r.command_id)
        if r.before_snapshot_id!=current:raise GameContractError('GAME_STATE_REPLAY_CHAIN_BREAK')
        current=r.after_snapshot_id
    if current!=final_snapshot.snapshot_id:raise GameContractError('GAME_STATE_REPLAY_FINAL_MISMATCH')
    return {'receipt_count':len(tuple(receipts)),'final_snapshot_id':current,'chain_fingerprint':fingerprint(tuple(receipts)),'product_accepted':False}
