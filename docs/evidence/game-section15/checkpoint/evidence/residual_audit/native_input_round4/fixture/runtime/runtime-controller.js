import { stateMachine, cloneState } from "./state-machine.js";
import { ruleMetadata, ruleFunctions, challengeFunctions } from "./rules.js";
import { interactionProgram } from "./interactions.js";
import { scoringProgram } from "./scoring.js";
import { feedbackProgram } from "./feedback.js";
import { adaptationMetadata, adaptationFunctions } from "./adaptation.js";
import { telemetryProgram, sanitizeTelemetry } from "./telemetry.js";
import { applySemanticState, studioLevels, runtimeExperience } from "./react-runtime.js";
function cueRows(levelId) { return studioLevels.find((x) => x.level_id === levelId)?.audio || []; }
let activeNarration = null;
const playingAudio = new Set();
function playCue(levelId, trigger) { const cue = cueRows(levelId).find((x) => x.trigger_event === trigger || x.trigger_event === "mechanic_completed"); if (!cue)
    return false; const caption = document.getElementById("bie-game-captions"); if (caption) {
    caption.textContent = cue.caption || "";
    caption.dataset.cueId = cue.cue_id;
    caption.dataset.expectedStartMs = String(cue.start_ms || 0);
    caption.dataset.expectedEndMs = String(cue.end_ms || 0);
} if (!cue.asset_ref)
    return true; const url = globalThis.__BIE_GAME_ASSETS__?.[cue.asset_ref]; if (!url)
    return false; const audio = new Audio(url); playingAudio.add(audio); audio.addEventListener("ended", () => playingAudio.delete(audio), { once: true }); audio.preload = "auto"; const expected = Math.max(0, Number(cue.end_ms || 0) - Number(cue.start_ms || 0)); audio.addEventListener("loadedmetadata", () => { if (expected > 0 && Number.isFinite(audio.duration)) {
    const drift = Math.abs(audio.duration * 1000 - expected);
    audio.dataset.syncDriftMs = String(drift);
    if (drift > Number(runtimeExperience.audio_max_sync_drift_ms || 120))
        throw new Error("GAME_AUDIO_SYNC_DRIFT");
} }); if (cue.kind === "narration")
    activeNarration = audio; const prior = activeNarration && activeNarration !== audio ? activeNarration : null; if (cue.duck_narration && prior) {
    prior.volume = .35;
    audio.addEventListener("ended", () => { prior.volume = 1; }, { once: true });
} void audio.play().catch(() => { }); return true; }
function levelState(levelId) { const levels = stateMachine.games.flatMap((g) => g.levels); const level = levels.find((x) => x.level_id === levelId); if (!level)
    throw new Error("GAME_RUNTIME_LEVEL_STATE_MISSING"); const out = {}; for (const v of level.variables)
    out[v.id] = v.initial; return out; }
function numericEffectValue(value) { if (typeof value !== "number" || !Number.isFinite(value))
    throw new Error("GAME_RUNTIME_EFFECT_NUMERIC"); return value; }
function applyEffects(levelId, state, effects) { const next = cloneState(state); for (const e of effects) {
    const cur = next[e.target];
    if (e.kind === "set")
        next[e.target] = e.value;
    else if (e.kind === "add")
        next[e.target] = numericEffectValue(cur) + numericEffectValue(e.value);
    else if (e.kind === "sub")
        next[e.target] = numericEffectValue(cur) - numericEffectValue(e.value);
    else if (e.kind === "mul")
        next[e.target] = numericEffectValue(cur) * numericEffectValue(e.value);
    else if (e.kind === "div") {
        if (numericEffectValue(e.value) === 0)
            throw new Error("GAME_RUNTIME_DIV_ZERO");
        next[e.target] = numericEffectValue(cur) / numericEffectValue(e.value);
    }
    else if (e.kind === "toggle") {
        if (typeof cur !== "boolean")
            throw new Error("GAME_RUNTIME_EFFECT_TOGGLE_BOOL");
        next[e.target] = !cur;
    }
    else
        throw new Error("GAME_RUNTIME_EFFECT_UNSUPPORTED");
    validateState(levelId, next);
} return next; }
function validateState(levelId, state) {
    const level = stateMachine.games.flatMap((g) => g.levels).find((l) => l.level_id === levelId);
    if (!level)
        throw new Error("GAME_RUNTIME_LEVEL_STATE_MISSING");
    if (Object.keys(state).length !== level.variables.length)
        throw new Error("GAME_RUNTIME_STATE_COVERAGE");
    for (const spec of level.variables) {
        const value = state[spec.id];
        if (!Object.prototype.hasOwnProperty.call(state, spec.id))
            throw new Error("GAME_RUNTIME_STATE_COVERAGE");
        if (spec.type === "number" || spec.type === "integer") {
            if (typeof value !== "number" || !Number.isFinite(value) || (spec.type === "integer" && !Number.isSafeInteger(value)))
                throw new Error("GAME_RUNTIME_STATE_TYPE");
            if ((spec.min !== null && value < spec.min) || (spec.max !== null && value > spec.max))
                throw new Error("GAME_RUNTIME_STATE_RANGE");
        }
        else if (spec.type === "boolean" && typeof value !== "boolean" || spec.type === "string" && typeof value !== "string")
            throw new Error("GAME_RUNTIME_STATE_TYPE");
        else if (spec.type === "enum" && !spec.enum_values.includes(value))
            throw new Error("GAME_RUNTIME_STATE_ENUM");
    }
}
export function createRuntimeController(levelId) {
    let disposed = false, bound = false, telemetrySequence = 0;
    const disposers = [];
    function on(target, type, listener) { target.addEventListener(type, listener); disposers.push(() => target.removeEventListener(type, listener)); }
    function dispose() { if (disposed)
        return; disposed = true; for (const remove of disposers)
        remove(); disposers.length = 0; for (const audio of playingAudio)
        audio.pause(); playingAudio.clear(); activeNarration = null; }
    let state = levelState(levelId), score = 0, attempts = 0, lastFeedback = "Ready";
    const completedChallenges = new Set();
    validateState(levelId, state);
    const telemetry = [];
    const actions = interactionProgram.actions_and_events.filter((x) => x.level_id === levelId && x.action_id);
    function dispatch(actionId, payload = {}) {
        if (disposed)
            throw new Error("GAME_RUNTIME_DISPOSED");
        const action = actions.find((x) => x.action_id === actionId);
        if (!action)
            throw new Error("GAME_RUNTIME_ACTION_UNKNOWN");
        if (action.mechanic_id === "reset") {
            state = levelState(levelId);
            applySemanticState(state, levelId);
            return { applied: true, action_id: actionId, rule_id: null, mechanic_id: action.mechanic_id, state: cloneState(state), score, feedback: "Reset", adaptations: [], telemetry: {} };
        }
        const meta = ruleMetadata.rules.find((x) => x.rule_id === action.rule_id && x.level_id === levelId);
        if (!meta)
            throw new Error("GAME_RUNTIME_RULE_ROUTE_MISSING");
        const predicate = ruleFunctions[meta.function_name];
        if (!predicate)
            throw new Error("GAME_RUNTIME_RULE_FUNCTION_MISSING");
        if (!predicate(state))
            return { applied: false, action_id: actionId, rule_id: action.rule_id, mechanic_id: action.mechanic_id, state: cloneState(state), score, feedback: lastFeedback, adaptations: [], telemetry: {} };
        const ids = action.challenge_ids || [];
        const selected = payload.challenge_id;
        const challengeId = typeof selected === "string" && ids.includes(selected) ? selected : ids.length === 1 && selected === undefined ? ids[0] : null;
        if (!challengeId)
            throw new Error("GAME_RUNTIME_CHALLENGE_ROUTE_AMBIGUOUS");
        const challenge = challengeFunctions[JSON.stringify([levelId, challengeId])];
        if (!challenge)
            throw new Error("GAME_RUNTIME_CHALLENGE_MISSING");
        const nextState = applyEffects(levelId, state, meta.effects);
        const failed = challenge.failure(nextState);
        const succeeded = !failed && challenge.success(nextState);
        state = nextState;
        attempts++;
        const gameId = stateMachine.games.find((g) => g.levels.some((l) => l.level_id === levelId))?.game_id;
        const scoring = scoringProgram.games[gameId];
        if (scoring) {
            const points = succeeded && !completedChallenges.has(challengeId) ? Number(scoring.correct_points) : failed ? Number(scoring.incorrect_points) : 0;
            score = Math.max(Number(scoring.floor), score + points);
        }
        if (succeeded)
            completedChallenges.add(challengeId);
        const fb = feedbackProgram.feedback.find((x) => x.challenge_id === challengeId && x.level_id === levelId);
        lastFeedback = succeeded ? (fb?.success || "Correct") : failed ? (fb?.failure || "Not yet") : "In progress";
        const fired = [];
        for (const a of adaptationMetadata.rules) {
            if (a.level_id !== levelId)
                continue;
            const fn = adaptationFunctions[a.function_name];
            if (fn && fn(state))
                fired.push(a.action + ":" + (a.target_id || ""));
        }
        const event = sanitizeTelemetry({ event: "mechanic_completed", game_id: gameId, level_id: levelId, challenge_id: challengeId, attempt_number: attempts, outcome_code: succeeded ? "succeeded" : failed ? "failed" : "in_progress", mechanic_id: action.mechanic_id, objective_id: (action.objective_ids || [])[(action.challenge_ids || []).indexOf(challengeId)] || "", adaptation_id: fired[0] || "" });
        if (telemetryProgram.events.includes("mechanic_completed")) {
            telemetry.push(event);
            const cfg = window.__BIE_GAME_TELEMETRY_CONFIG__;
            if (cfg?.enabled && window.__BIE_GAME_TELEMETRY_SINK__) {
                telemetrySequence++;
                window.__BIE_GAME_TELEMETRY_SINK__({ ...event, session_id: cfg.session_id, sequence_id: telemetrySequence, policy_id: cfg.policy_id });
            }
        }
        playCue(levelId, "mechanic_completed");
        applySemanticState(state, levelId);
        const out = document.getElementById("bie-game-feedback");
        if (out)
            out.textContent = lastFeedback;
        return { applied: true, action_id: actionId, rule_id: action.rule_id, mechanic_id: action.mechanic_id, state: cloneState(state), score, feedback: lastFeedback, adaptations: fired, telemetry: event };
    }
    function bind(root) {
        if (disposed || bound)
            throw new Error("GAME_RUNTIME_BIND_LIFECYCLE");
        const targets = actions.map((action) => { const node = root.querySelector(`[data-action-id="${action.action_id}"]`); if (!node)
            throw new Error("GAME_RUNTIME_ACTION_TARGET_MISSING"); return { action, node }; });
        const chooser = root.querySelector('[data-challenge-control="select"]');
        bound = true;
        const audioControl = root.querySelector('[data-audio-control="play"]');
        if (audioControl)
            on(audioControl, "click", () => playCue(levelId, "level_start"));
        for (const { action, node } of targets) {
            let suppressPointerClick = false;
            const invoke = (payload = {}) => dispatch(action.action_id, chooser ? { ...payload, challenge_id: chooser.value } : payload);
            on(node, "click", (ev) => { if (suppressPointerClick && ev.detail > 0) {
                suppressPointerClick = false;
                return;
            } suppressPointerClick = false; invoke({}); });
            on(node, "keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") {
                ev.preventDefault();
                suppressPointerClick = false;
                invoke({});
            }
            else if (action.kind === "adjust" && (ev.key === "ArrowRight" || ev.key === "ArrowUp")) {
                ev.preventDefault();
                invoke({ delta: 1 });
            }
            else if (action.kind === "adjust" && (ev.key === "ArrowLeft" || ev.key === "ArrowDown")) {
                ev.preventDefault();
                invoke({ delta: -1 });
            } });
            if (action.kind === "drag" || action.kind === "drop" || action.kind === "place")
                on(node, "pointerup", (ev) => { if (ev.button !== 0)
                    return; suppressPointerClick = true; invoke({ x: ev.clientX, y: ev.clientY }); });
        }
    }
    return Object.freeze({ dispatch, bind, dispose, playNarration: () => playCue(levelId, "level_start"), getState: () => cloneState(state), getScore: () => score, getFeedback: () => lastFeedback, getTelemetry: () => telemetry.slice(), actionIds: () => actions.map((x) => x.action_id), audioRuntimeAvailable: true, reducedMotionSupported: true });
}
