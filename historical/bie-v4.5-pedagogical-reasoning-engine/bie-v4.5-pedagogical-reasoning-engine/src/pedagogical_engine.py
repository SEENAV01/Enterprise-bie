from importance import score_importance,classify_importance
from prerequisites import prerequisite_order
from explanation_strategy import build_strategy
from learning_sequence import build_learning_sequence
from lesson_units import make_teaching_unit

def plan(items, nodes, edges):
    for item in items:
        item["importance_score"]=score_importance(item)
        item["importance_class"]=classify_importance(item["importance_score"])
    order=prerequisite_order(nodes,edges)
    strategies=build_strategy(items)
    strategy_map={x["item_id"]:x for x in strategies}
    sequence=build_learning_sequence(items,order["order"])
    units=[make_teaching_unit(x,strategy_map[x["id"]]) for x in sequence]
    return {
      "schema_version":"4.5",
      "importance":items,
      "dependency_order":order,
      "strategies":strategies,
      "teaching_units":units,
      "policy":{
        "prerequisites_before_dependents":True,
        "importance_affects_depth":True,
        "derivations_are_stepwise":True,
        "applications_are_explicit":True
      }
    }
