import { studioLevels, renderGameRuntime } from "./react-runtime.js";
import { stateMachine } from "./state-machine.js";
import { ruleMetadata } from "./rules.js";
import { interactionProgram } from "./interactions.js";
import { scoringProgram } from "./scoring.js";
import { feedbackProgram } from "./feedback.js";
import { adaptationMetadata } from "./adaptation.js";
import { telemetryProgram, sanitizeTelemetry } from "./telemetry.js";
export function bootstrap(React, mount) {
    if (!studioLevels.length)
        throw new Error("GAME_NO_LEVELS");
    const levelId = studioLevels[0].level_id;
    const node = renderGameRuntime(React, levelId);
    mount(node);
}
export const runtimeBindings = { stateMachine, ruleMetadata, interactionProgram, scoringProgram, feedbackProgram, adaptationMetadata, telemetryProgram, sanitizeTelemetry };
