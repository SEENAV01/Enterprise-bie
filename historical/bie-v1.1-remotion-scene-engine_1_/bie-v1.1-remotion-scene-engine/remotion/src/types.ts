export type Scene = {
  scene_id: string; title?: string; purpose: string; duration_frames: number;
  content_refs: string[]; source_refs: string[];
  visual: {type: string; layout?: string; formula?: string; [key:string]: unknown};
  narration: {mode: string; key_points: string[]};
  timeline: {start:number; duration:number; action:string}[];
};
export type SceneDSL = {lesson_id:string; scenes:Scene[]};
