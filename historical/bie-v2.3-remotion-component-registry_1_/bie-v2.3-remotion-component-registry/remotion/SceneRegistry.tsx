import React from "react";
import { AbsoluteFill, Sequence } from "remotion";

export type SceneSpec = {
  scene_id: string;
  type: string;
  duration_ms: number;
  objective: string;
  visual: { type: string; instructions?: string; assets?: string[] };
  narration: string;
  on_screen_text?: string[];
  equations?: string[];
  animation?: { enter?: string; exit?: string; actions?: string[] };
  camera?: { mode?: string };
  transition?: string;
  emphasis?: string[];
  evidence_refs?: string[];
  checkpoint?: unknown;
};

const Base: React.FC<{scene: SceneSpec}> = ({scene}) => (
  <AbsoluteFill style={{padding:80, fontFamily:"Arial", justifyContent:"center"}}>
    <div style={{fontSize:28, opacity:.65}}>{scene.type}</div>
    <div style={{fontSize:58, fontWeight:700, marginTop:24}}>{scene.objective}</div>
    {scene.on_screen_text?.map((x,i)=><div key={i} style={{fontSize:34,marginTop:20}}>{x}</div>)}
    {scene.equations?.map((x,i)=><div key={i} style={{fontSize:42,marginTop:25}}>{x}</div>)}
  </AbsoluteFill>
);

export const DefinitionScene = Base;
export const ProcessScene = Base;
export const EquationScene = Base;
export const DiagramScene = Base;
export const ChartScene = Base;
export const TableScene = Base;
export const ApplicationScene = Base;
export const WorkedExampleScene = Base;
export const CheckpointScene = Base;
export const RecapScene = Base;

export const REGISTRY: Record<string, React.FC<{scene:SceneSpec}>> = {
  definition: DefinitionScene,
  process_animation: ProcessScene,
  derivation: EquationScene,
  diagram_explanation: DiagramScene,
  chart: ChartScene,
  table: TableScene,
  application: ApplicationScene,
  worked_example: WorkedExampleScene,
  checkpoint: CheckpointScene,
  recap: RecapScene,
  causal_explanation: ProcessScene,
  comparison: TableScene
};

export function RenderScene({scene}:{scene:SceneSpec}) {
  const C = REGISTRY[scene.type] ?? Base;
  return <C scene={scene}/>;
}

export function RenderTimeline({scenes}:{scenes:SceneSpec[]}) {
  let from=0;
  return <>
    {scenes.map(scene=>{
      const duration=Math.max(1,Math.round(scene.duration_ms*30/1000));
      const node=<Sequence key={scene.scene_id} from={from} durationInFrames={duration}><RenderScene scene={scene}/></Sequence>;
      from += duration;
      return node;
    })}
  </>;
}
