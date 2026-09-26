export const studioLevels = [{ "actions": [{ "action_id": "drag:mover", "label": "Move the object", "target": "entity:mover" }, { "action_id": "submit", "label": "Submit answer", "target": "entity:mover" }], "audio": [{ "asset_ref": "audio:probe", "caption": "\u06cc\u06c1 \u062d\u0631\u06a9\u062a \u06a9\u0627 \u062a\u062c\u0631\u0628\u06c1 \u06c1\u06d2\u06d4", "cue_id": "cue:narration:1", "duck_narration": false, "end_ms": 100, "kind": "narration", "start_ms": 0, "text_ref": "text:narration", "trigger_event": "level_start" }], "camera": [{ "duration_ms": 800, "id": "camera:focus", "kind": "focus", "purpose": "Keep learner attention on the changing object", "start_ms": 0, "target": "entity:mover" }], "challenges": [{ "challenge_id": "challenge:motion", "title": "Move to target" }, { "challenge_id": "challenge:second", "title": "Second challenge" }], "game_id": "game:motion", "level_id": "level:1", "motion": [{ "duration_ms": 800, "id": "motion:move", "kind": "move", "purpose": "Show the state change caused by learner manipulation", "start_ms": 0, "target": "entity:mover" }], "purpose": "Build intuitive displacement understanding", "title": "Motion Lab", "visual_entities": [{ "accessible_label": "A movable object", "glyph": "\u25cf", "id": "entity:mover", "kind": "object", "semantic_role": "manipulated_object", "state_bindings": ["x"] }, { "accessible_label": "Target at x equals 2", "glyph": "\u25c6", "id": "entity:target", "kind": "label", "semantic_role": "target_marker", "state_bindings": [] }] }];
export const runtimeExperience = { "attributions": [{ "asset_ref": "audio:probe", "attribution": "Generated verification tone", "license_id": "CC0-1.0", "rights_ref": "rights:probe", "source_ref": "source:probe" }], "audio_max_sync_drift_ms": 120, "direction": "rtl", "locale": "ur-IN", "messages": { "ui.actions": "Actions", "ui.attribution": "\u0645\u0627\u062e\u0630 \u0627\u0648\u0631 \u062d\u0642\u0648\u0642", "ui.audio_play": "\u0628\u06cc\u0627\u0646 \u0686\u0644\u0627\u0626\u06cc\u06ba", "ui.challenge_select": "Choose challenge", "ui.ready": "\u062a\u06cc\u0627\u0631" } };
export function renderGameRuntime(React, activeLevelId) {
    const level = studioLevels.find((x) => x.level_id === activeLevelId);
    if (!level)
        throw new Error("GAME_LEVEL_NOT_FOUND");
    const nodes = level.visual_entities.map((e) => { const primary = level.actions.find((a) => a.target === e.id); const tag = primary ? "button" : "figure"; const props = { key: e.id, "data-entity-id": e.id, "data-entity-kind": e.kind, "data-semantic-role": e.semantic_role, "data-state-bindings": e.state_bindings.join(","), "aria-label": e.accessible_label }; if (tag === "button") {
        props.type = "button";
        props["data-action-id"] = primary.action_id;
    } return React.createElement(tag, props, React.createElement("span", { "aria-hidden": "true" }, e.glyph + " "), React.createElement("span", { "data-entity-label": "true" }, e.accessible_label)); });
    const extraActions = level.actions.filter((a) => level.actions.find((first) => first.target === a.target)?.action_id !== a.action_id).map((a) => React.createElement("button", { key: a.action_id, type: "button", "data-action-id": a.action_id, "aria-label": a.label }, a.label));
    const actionControls = extraActions.length ? React.createElement("section", { "aria-label": runtimeExperience.messages["ui.actions"] }, ...extraActions) : null;
    const challengeControl = level.challenges.length > 1 ? React.createElement("select", { "data-challenge-control": "select", "aria-label": runtimeExperience.messages["ui.challenge_select"], defaultValue: level.challenges[0].challenge_id }, ...level.challenges.map((c) => React.createElement("option", { key: c.challenge_id, value: c.challenge_id }, c.title))) : null;
    const audioButton = level.audio.length ? React.createElement("button", { type: "button", "data-audio-control": "play", "aria-label": runtimeExperience.messages["ui.audio_play"] }, runtimeExperience.messages["ui.audio_play"]) : null;
    const rights = runtimeExperience.attributions.length ? React.createElement("footer", { "data-rights-attribution": "true", "aria-label": runtimeExperience.messages["ui.attribution"] }, ...runtimeExperience.attributions.map((r) => React.createElement("p", { "data-rights-ref": r.rights_ref }, r.attribution + " — " + r.license_id))) : React.createElement("footer", { "data-rights-attribution": "true", "aria-label": runtimeExperience.messages["ui.attribution"] }, runtimeExperience.messages["ui.attribution"]);
    return React.createElement("main", { role: "application", lang: runtimeExperience.locale, dir: runtimeExperience.direction, "aria-label": level.title, "data-level-id": level.level_id, "data-studio-grade": "true", "data-slide-deck": "false" }, React.createElement("header", {}, React.createElement("h2", {}, level.title), React.createElement("p", {}, level.purpose)), React.createElement("section", { "aria-label": "Interactive semantic scene", "data-scene": "semantic" }, ...nodes), actionControls, challengeControl, audioButton, React.createElement("output", { id: "bie-game-feedback", "aria-live": "polite", "aria-atomic": "true" }, runtimeExperience.messages["ui.ready"]), React.createElement("div", { id: "bie-game-captions", "aria-live": "polite", "data-caption-region": "true" }, ""), rights);
}
export function hydrateSemanticPrimitives(activeLevelId) {
    const level = studioLevels.find((x) => x.level_id === activeLevelId);
    if (!level)
        throw new Error("GAME_LEVEL_NOT_FOUND");
    const NS = "http:" + "//www.w3.org/2000/svg";
    for (const e of level.visual_entities) {
        if (e.kind === "label")
            continue;
        const host = document.querySelector(`[data-entity-id="${e.id}"]`);
        if (!host)
            continue;
        if (host.querySelector('[data-semantic-svg]'))
            continue;
        const svg = document.createElementNS(NS, "svg");
        svg.setAttribute("data-semantic-svg", "true");
        svg.setAttribute("viewBox", "0 0 180 96");
        svg.setAttribute("width", "180");
        svg.setAttribute("height", "96");
        svg.setAttribute("role", "img");
        svg.setAttribute("aria-label", e.accessible_label);
        const line = (x1, y1, x2, y2) => { const n = document.createElementNS(NS, "line"); n.setAttribute("x1", String(x1)); n.setAttribute("y1", String(y1)); n.setAttribute("x2", String(x2)); n.setAttribute("y2", String(y2)); n.setAttribute("stroke", "currentColor"); n.setAttribute("stroke-width", "3"); svg.appendChild(n); };
        const circle = (cx, cy, r) => { const n = document.createElementNS(NS, "circle"); n.setAttribute("cx", String(cx)); n.setAttribute("cy", String(cy)); n.setAttribute("r", String(r)); n.setAttribute("fill", "none"); n.setAttribute("stroke", "currentColor"); n.setAttribute("stroke-width", "3"); svg.appendChild(n); };
        if (e.kind === "vector") {
            line(18, 48, 150, 48);
            const p = document.createElementNS(NS, "polygon");
            p.setAttribute("points", "150,38 170,48 150,58");
            p.setAttribute("fill", "currentColor");
            svg.appendChild(p);
        }
        else if (e.kind === "graph") {
            line(24, 78, 24, 18);
            line(24, 78, 162, 78);
            const poly = document.createElementNS(NS, "polyline");
            poly.setAttribute("points", "28,70 60,58 92,62 126,32 158,24");
            poly.setAttribute("fill", "none");
            poly.setAttribute("stroke", "currentColor");
            poly.setAttribute("stroke-width", "3");
            svg.appendChild(poly);
        }
        else if (e.kind === "map") {
            const r = document.createElementNS(NS, "rect");
            r.setAttribute("x", "20");
            r.setAttribute("y", "16");
            r.setAttribute("width", "140");
            r.setAttribute("height", "64");
            r.setAttribute("fill", "none");
            r.setAttribute("stroke", "currentColor");
            svg.appendChild(r);
            circle(60, 46, 6);
            circle(126, 58, 6);
            line(66, 48, 120, 56);
        }
        else if (e.kind === "timeline") {
            line(18, 48, 162, 48);
            circle(48, 48, 6);
            circle(90, 48, 6);
            circle(136, 48, 6);
        }
        else if (e.kind === "equation") {
            const t = document.createElementNS(NS, "text");
            t.setAttribute("x", "24");
            t.setAttribute("y", "56");
            t.setAttribute("font-size", "24");
            t.textContent = "x = f(state)";
            svg.appendChild(t);
        }
        else if (e.kind === "particle") {
            circle(90, 48, 20);
        }
        else if (e.kind === "field") {
            circle(90, 48, 18);
            circle(90, 48, 34);
            circle(90, 48, 46);
        }
        else if (e.kind === "flow") {
            circle(36, 48, 10);
            circle(90, 48, 10);
            circle(144, 48, 10);
            line(46, 48, 80, 48);
            line(100, 48, 134, 48);
        }
        else if (e.kind === "bio_structure") {
            circle(90, 48, 34);
            circle(78, 44, 8);
            circle(108, 54, 6);
        }
        else {
            const r = document.createElementNS(NS, "rect");
            r.setAttribute("x", "34");
            r.setAttribute("y", "20");
            r.setAttribute("width", "112");
            r.setAttribute("height", "56");
            r.setAttribute("rx", "12");
            r.setAttribute("fill", "none");
            r.setAttribute("stroke", "currentColor");
            r.setAttribute("stroke-width", "3");
            svg.appendChild(r);
        }
        host.appendChild(svg);
    }
}
export function applySemanticState(state, activeLevelId) {
    const level = studioLevels.find((x) => x.level_id === activeLevelId);
    if (!level)
        throw new Error("GAME_LEVEL_NOT_FOUND");
    const reduced = globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true;
    for (const e of level.visual_entities) {
        const node = document.querySelector(`[data-entity-id="${e.id}"]`);
        if (!node)
            continue;
        const values = e.state_bindings.map((k) => [k, state[k]]);
        node.dataset.stateValue = JSON.stringify(values);
        const cue = level.motion.find((m) => m.target === e.id);
        if (cue) {
            node.dataset.motionKind = cue.kind;
            if (!reduced && typeof node.animate === "function") {
                const numeric = values.find((x) => typeof x[1] === "number");
                const distance = numeric ? Math.max(-120, Math.min(120, Number(numeric[1]) * 16)) : 24;
                node.animate([{ transform: "translateX(0px)", opacity: .8 }, { transform: `translateX(${distance}px)`, opacity: 1 }], { duration: Math.max(120, cue.duration_ms), fill: "forwards", easing: "ease" });
            }
        }
    }
    const cam = level.camera[0];
    const root = document.querySelector('main[role="application"]');
    if (root && cam) {
        root.dataset.cameraKind = cam.kind;
        if (cam.target)
            root.dataset.cameraTarget = cam.target;
        const target = cam.target ? document.querySelector(`[data-entity-id="${cam.target}"]`) : null;
        if (target && !reduced && typeof target.animate === "function")
            target.animate([{ transform: "scale(1)" }, { transform: "scale(1.04)" }], { duration: Math.max(120, cam.duration_ms), direction: "alternate", iterations: 2, easing: "ease-in-out" });
    }
}
export function renderedGeometry(activeLevelId) { const level = studioLevels.find((x) => x.level_id === activeLevelId); if (!level)
    throw new Error("GAME_LEVEL_NOT_FOUND"); return level.visual_entities.map((e) => { const n = document.querySelector(`[data-entity-id="${e.id}"]`); const r = n?.getBoundingClientRect(); return { id: e.id, width: r?.width || 0, height: r?.height || 0, text: (n?.textContent || "").trim() }; }); }
