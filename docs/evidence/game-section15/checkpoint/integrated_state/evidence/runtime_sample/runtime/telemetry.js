export const telemetryProgram = { "events": ["challenge_completed", "game_started", "mechanic_completed"], "payload_allowlist": ["event", "game_id", "level_id", "challenge_id", "attempt_number", "outcome_code", "mechanic_id", "duration_bucket"], "product_accepted": false, "raw_text_allowed": false, "remote_endpoint": null, "schema_version": "bie.game.telemetry-program/1" };
export function sanitizeTelemetry(input) { const out = {}; for (const key of telemetryProgram.payload_allowlist) {
    if (key in input)
        out[key] = input[key];
} return out; }
