from .common import *
from .input_contracts import TimelineEvent
def define(ctx):return make_definition(ctx,'mechanic:timeline',MechanicKind.TIMELINE_RECONSTRUCTION,'Learner reconstructs temporal order from evidence-backed anchors and explicit partial-order constraints.',(action('order:events',ActionKind.ORDER,'Reorder events','Arrow keys and Enter','timeline:events'),),(motion('motion:timeline',MotionSemantic.REORDER,'timeline:events','Make temporal relationships visible as learner order changes.','timeline_order'),),('semantic_motion','keyboard_input','state_machine'))
def execute(ctx,state,events,learner_order):
 d=define(ctx)
 if not isinstance(events,(tuple,list)) or len(events)<2:raise MechanicError('GAME_MECH_TIMELINE_INPUT')
 typed=tuple(TimelineEvent.from_mapping(e) for e in events);ids=[e.event_id for e in typed]
 if len(ids)!=len(set(ids)) or set(learner_order)!=set(ids):raise MechanicError('GAME_MECH_TIMELINE_COVERAGE')
 anchors={e.event_id:e.time for e in typed}
 if any(v is None for v in anchors.values()):raise MechanicError('GAME_MECH_TIMELINE_ANCHOR')
 expected=tuple(sorted(ids,key=lambda x:(anchors[x],x)));valid=tuple(learner_order)==expected
 after={**state,'timeline_order':tuple(learner_order),'valid':valid};out={'expected_order':expected,'valid':valid,'tie_break':'event_id'};return after,out,receipt(d,state,after,{'learner_order':tuple(learner_order)},out)
