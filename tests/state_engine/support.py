from dataclasses import replace
from bie.game_engine.state_engine.fixtures import *
from bie.game_engine.state_engine.snapshots import make_snapshot,initial_snapshot

def snapshot_values(**changes):
    l=sample_level();base=initial_snapshot(l.state).as_dict();base.update(changes);return make_snapshot(l.state,base)
