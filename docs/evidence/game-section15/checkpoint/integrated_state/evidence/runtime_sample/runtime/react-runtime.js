export const studioLevels = [{ "camera": [{ "duration_ms": 800, "id": "camera:focus", "kind": "focus", "purpose": "Keep learner attention on the changing object", "start_ms": 0, "target": "entity:mover" }], "game_id": "game:motion", "level_id": "level:1", "motion": [{ "duration_ms": 800, "id": "motion:move", "kind": "move", "purpose": "Show the state change caused by learner manipulation", "start_ms": 0, "target": "entity:mover" }], "purpose": "Build intuitive displacement understanding", "title": "Motion Lab", "visual_entities": [{ "accessible_label": "A movable object", "id": "entity:mover", "kind": "object", "semantic_role": "manipulated_object", "state_bindings": ["x"] }, { "accessible_label": "Target at x equals 2", "id": "entity:target", "kind": "label", "semantic_role": "target_marker", "state_bindings": [] }] }];
export function renderGameRuntime(React, activeLevelId) {
    const level = studioLevels.find((x) => x.level_id === activeLevelId);
    if (!level)
        throw new Error("GAME_LEVEL_NOT_FOUND");
    const entityNodes = level.visual_entities.map((e) => React.createElement("div", { key: e.id, "data-entity-id": e.id, "data-semantic-role": e.semantic_role, "aria-label": e.accessible_label }));
    return React.createElement("main", { role: "application", "aria-label": level.title, "data-studio-grade": "true", "data-slide-deck": "false" }, ...entityNodes);
}
