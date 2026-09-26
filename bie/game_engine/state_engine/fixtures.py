from __future__ import annotations
from ..fixtures import sample_document
from ..expressions import *
from ..interaction import *
from .contracts import ActionCommand
from .snapshots import initial_snapshot,make_snapshot
from .reachability import *
from .invariants import StateInvariant

def sample_level():return sample_document().experiences[0].levels[0]
def sample_snapshot():return initial_snapshot(sample_level().state)
def drag_command(seq=1,expected=None):return ActionCommand('cmd:drag:'+str(seq),seq,'drag:mover','actor:learner',tuple(sorted({'x':2.0,'y':0.0}.items())),expected)
def submit_command(seq=2,expected=None):return ActionCommand('cmd:submit:'+str(seq),seq,'submit','actor:learner',(),expected)
def invariant_bounds():return (StateInvariant('inv:x:nonnegative',Compare(CompareOp.GE,Variable('x'),Literal(0)),'Position remains within lower bound'),)
def sample_transition_system():
    nodes=(StateNode('s0','sha256:'+'0'*64),StateNode('s1','sha256:'+'1'*64),StateNode('s2','sha256:'+'2'*64,True),StateNode('dead','sha256:'+'3'*64))
    edges=(StateEdge('e01','s0','s1','transition:t1'),StateEdge('e12','s1','s2','transition:t2'),StateEdge('e1d','s1','dead','transition:td'))
    return TransitionSystem(nodes,edges,100,False)
