export function rule_rule_move(state) { return Boolean((Number(state["x"]) < 2)); }
export const ruleMetadata = { "product_accepted": false, "rules": [{ "effects": [{ "kind": "set", "target": "x", "value": 2.0 }], "explanation": "Moving changes the position.", "function_name": "rule_rule_move", "grounding_refs": ["source:book"], "level_id": "level:1", "priority": 10, "rule_id": "rule:move" }], "schema_version": "bie.game.rule-program/2", "uses_eval": false };
export const ruleFunctions = { "rule:move": rule_rule_move };
