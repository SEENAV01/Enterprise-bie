"use strict";
// state-machine.js
const stateMachine = { "deterministic": true, "games": [{ "game_id": "game:motion", "levels": [{ "level_id": "level:1", "reset_policy": "level", "state_ids": ["attempts", "x"], "variables": [{ "id": "x", "initial": 1.0, "max": 10, "min": 0, "role": "position", "type": "number", "units": "m" }, { "id": "attempts", "initial": 0, "max": 10, "min": 0, "role": "attempt_count", "type": "integer", "units": null }] }] }], "product_accepted": false, "schema_version": "bie.game.state-machine/1" };
function cloneState(s) { return { ...s }; }

// rules.js
function rule_rule_move(state) { return Boolean((Number(state["x"]) < 2)); }
const ruleMetadata = { "product_accepted": false, "rules": [{ "effects": [{ "kind": "set", "target": "x", "value": 2.0 }], "explanation": "Moving changes the position.", "function_name": "rule_rule_move", "grounding_refs": ["source:book"], "level_id": "level:1", "priority": 10, "rule_id": "rule:move" }], "schema_version": "bie.game.rule-program/2", "uses_eval": false };

// interactions.js
const interactionProgram = { "actions_and_events": [{ "accessible_label": "Move the object", "action_id": "drag:mover", "keyboard_equivalent": "Arrow keys adjust position", "kind": "drag", "level_id": "level:1", "target": "entity:mover" }, { "accessible_label": "Submit answer", "action_id": "submit", "keyboard_equivalent": null, "kind": "submit", "level_id": "level:1", "target": "entity:mover" }, { "causal": true, "mechanic_id": "mechanic:parameter", "motion_ids": ["motion:value"], "pedagogical_purpose": "Show the parameter change and its causal effect.", "receipt_id": "mechanic:b886deb9383a81da925777ef", "semantic_event_id": "event:586df05607278a09ab2c8184", "state_after": "sha256:fbc786c7adbdd0614ade02569b7a42f1f52be7af1c7a5f50995f95242288dbe6", "state_before": "sha256:3a7d647740ec6f86b72e0bf3948ab456551e07e9605e3a2785de1c66842ebb48" }], "decorative_only_forbidden": true, "keyboard_parity_required": true, "product_accepted": false, "schema_version": "bie.game.interaction-program/1" };

// scoring.js
const scoringProgram = { "games": { "game:motion": { "correct_points": 10, "floor": 0, "hint_cost": 1, "incorrect_points": 0, "mastery_weighted": true, "policy_id": "policy:score:v1", "speed_pressure": false } }, "product_accepted": false, "schema_version": "bie.game.scoring-program/1" };

// feedback.js
const feedbackProgram = { "feedback": [{ "challenge_id": "challenge:motion", "explanation": "Changing x changes the object position represented by the semantic visual.", "failure": "Not yet. Compare the current position with the target.", "misconceptions": [{ "message": "Check which direction moves x toward the target.", "misconception_id": "mis:direction" }], "reveal_answer_on_failure": false, "success": "Correct. The object reached the target because the state changed to x equals 2." }], "product_accepted": false, "schema_version": "bie.game.feedback-program/1" };

// adaptation.js
function adapt_adapt_hint(state) { return Boolean((Number(state["attempts"]) >= 2)); }
const adaptationMetadata = { "deterministic_priority": true, "product_accepted": false, "rules": [{ "action": "unlock_hint", "adaptation_id": "adapt:hint", "function_name": "adapt_adapt_hint", "level_id": "level:1", "priority": 1, "target_id": "hint:2" }], "schema_version": "bie.game.adaptation-program/2" };

// telemetry.js
const telemetryProgram = { "events": ["challenge_completed", "game_started", "mechanic_completed"], "payload_allowlist": ["event", "game_id", "level_id", "challenge_id", "attempt_number", "outcome_code", "mechanic_id", "duration_bucket"], "product_accepted": false, "raw_text_allowed": false, "remote_endpoint": null, "schema_version": "bie.game.telemetry-program/1" };
function sanitizeTelemetry(input) { const out = {}; for (const key of telemetryProgram.payload_allowlist) {
    if (key in input)
        out[key] = input[key];
} return out; }

// react-runtime.js
const studioLevels = [{ "camera": [{ "duration_ms": 800, "id": "camera:focus", "kind": "focus", "purpose": "Keep learner attention on the changing object", "start_ms": 0, "target": "entity:mover" }], "game_id": "game:motion", "level_id": "level:1", "motion": [{ "duration_ms": 800, "id": "motion:move", "kind": "move", "purpose": "Show the state change caused by learner manipulation", "start_ms": 0, "target": "entity:mover" }], "purpose": "Build intuitive displacement understanding", "title": "Motion Lab", "visual_entities": [{ "accessible_label": "A movable object", "id": "entity:mover", "kind": "object", "semantic_role": "manipulated_object", "state_bindings": ["x"] }, { "accessible_label": "Target at x equals 2", "id": "entity:target", "kind": "label", "semantic_role": "target_marker", "state_bindings": [] }] }];
function renderGameRuntime(React, activeLevelId) {
    const level = studioLevels.find((x) => x.level_id === activeLevelId);
    if (!level)
        throw new Error("GAME_LEVEL_NOT_FOUND");
    const entityNodes = level.visual_entities.map((e) => React.createElement("div", { key: e.id, "data-entity-id": e.id, "data-semantic-role": e.semantic_role, "aria-label": e.accessible_label }));
    return React.createElement("main", { role: "application", "aria-label": level.title, "data-studio-grade": "true", "data-slide-deck": "false" }, ...entityNodes);
}

// bootstrap.js








function bootstrap(React, mount) {
    if (!studioLevels.length)
        throw new Error("GAME_NO_LEVELS");
    const levelId = studioLevels[0].level_id;
    const node = renderGameRuntime(React, levelId);
    mount(node);
}
const runtimeBindings = { stateMachine, ruleMetadata, interactionProgram, scoringProgram, feedbackProgram, adaptationMetadata, telemetryProgram, sanitizeTelemetry };

// entry.js

const React = {
  createElement(tag, props = {}, ...children) {
    const el = document.createElement(tag);
    for (const [key, value] of Object.entries(props || {})) {
      if (key === "key" || value === undefined || value === null) continue;
      if (key === "className") el.setAttribute("class", String(value));
      else el.setAttribute(key, String(value));
    }
    for (const child of children.flat(Infinity)) {
      if (child instanceof Node) el.appendChild(child);
      else if (child !== undefined && child !== null) el.appendChild(document.createTextNode(String(child)));
    }
    return el;
  }
};
function mount(node) {
  const root = document.getElementById("bie-game-root");
  if (!root) throw new Error("GAME_BUILD_ROOT_MISSING");
  if (!(node instanceof HTMLElement)) throw new Error("GAME_BUILD_ROOT_INVALID");
  node.id = "bie-game-root";
  root.replaceWith(node);
}
bootstrap(React, mount);
globalThis.__BIE_GAME_RUNTIME__ = Object.freeze({booted:true,bindingKeys:Object.keys(runtimeBindings).sort()});
