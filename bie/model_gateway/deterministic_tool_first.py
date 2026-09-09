
class ToolFirstError(ValueError):pass
DETERMINISTIC={"arithmetic","unit_conversion","schema_validation","hashing","sorting","graph_cycle_check"}
def route(task_kind,tool_available):
 if not task_kind:raise ToolFirstError("task kind")
 if task_kind in DETERMINISTIC and tool_available:return "TOOL"
 return "MODEL"
