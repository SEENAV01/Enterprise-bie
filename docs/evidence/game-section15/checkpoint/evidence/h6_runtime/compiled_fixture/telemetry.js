export const telemetryProgram = { "consent_required": true, "events": ["challenge_completed", "game_started", "mechanic_completed"], "local_sink_only": true, "payload_allowlist": ["event", "game_id", "level_id", "challenge_id", "attempt_number", "outcome_code", "mechanic_id", "duration_bucket", "objective_id", "adaptation_id"], "product_accepted": false, "raw_text_allowed": false, "remote_endpoint": null, "schema_version": "bie.game.telemetry-program/1", "sequence_ids_required": true };
export function sanitizeTelemetry(input) { const out = {}; for (const key of telemetryProgram.payload_allowlist) {
    if (key in input)
        out[key] = input[key];
} return out; }
