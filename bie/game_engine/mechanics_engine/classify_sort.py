from .common import *
from .input_contracts import ClassificationItem
def define(ctx):return make_definition(ctx,'mechanic:classify-sort',MechanicKind.CLASSIFY_SORT,'Learner groups evidence-bearing items by an explicit conceptual criterion.',(action('place:category',ActionKind.PLACE,'Place item in category','Arrow keys then Enter','category:bins'),),(motion('motion:group',MotionSemantic.GROUP,'category:bins','Show conceptual grouping caused by classification.','classification'),),('semantic_motion','keyboard_input','state_machine'))
def execute(ctx,state,items,assignments,allowed_categories):
 d=define(ctx)
 typed=tuple(ClassificationItem.from_mapping(x) for x in items)
 if not typed:raise MechanicError('GAME_MECH_CLASSIFY_ITEMS')
 ids=[x.item_id for x in typed]
 if len(ids)!=len(set(ids)) or set(assignments)!=set(ids):raise MechanicError('GAME_MECH_CLASSIFY_COVERAGE')
 if any(c not in allowed_categories for c in assignments.values()):raise MechanicError('GAME_MECH_CLASSIFY_CATEGORY')
 expected={x.item_id:x.category for x in typed};correct={i:assignments[i]==expected[i] for i in ids};groups={c:tuple(sorted(i for i in ids if assignments[i]==c)) for c in sorted(allowed_categories)}
 after={**state,'groups':tuple((k,v) for k,v in groups.items()),'all_correct':all(correct.values())};out={'correctness':tuple(sorted(correct.items())),'groups':groups};return after,out,receipt(d,state,after,{'assignments':assignments},out)
