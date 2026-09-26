import {studioLevels, renderGameRuntime, hydrateSemanticPrimitives, applySemanticState} from "./react-runtime";
import {createRuntimeController} from "./runtime-controller";
import {stateMachine} from "./state-machine";
import {ruleMetadata} from "./rules";
import {interactionProgram} from "./interactions";
import {scoringProgram} from "./scoring";
import {feedbackProgram} from "./feedback";
import {adaptationMetadata} from "./adaptation";
import {telemetryProgram, sanitizeTelemetry} from "./telemetry";
export function bootstrap(React: {createElement: (...args: any[]) => any}, mount: (node: any) => HTMLElement): any {
if(!studioLevels.length)throw new Error("GAME_NO_LEVELS");const levelId=studioLevels[0].level_id;const node=renderGameRuntime(React,levelId);const root=mount(node);hydrateSemanticPrimitives(levelId);const controller=createRuntimeController(levelId);controller.bind(root);applySemanticState(controller.getState(),levelId);return controller;}
export const runtimeBindings={stateMachine,ruleMetadata,interactionProgram,scoringProgram,feedbackProgram,adaptationMetadata,telemetryProgram,sanitizeTelemetry} as const;
