export type CaptionWord = {
  text: string;
  startFrame: number;
  endFrame: number;
};

export type Narration = {
  mode: string;
  key_points: string[];
  script?: string;
  estimated_duration_frames?: number;
  audio_asset?: string | null;
  caption_asset?: string | null;
};

export type Scene = {
  scene_id: string;
  module?: string;
  title?: string;
  purpose: string;
  duration_frames: number;
  content_refs: string[];
  source_refs: string[];
  visual: { type: string; layout?: string; formula?: string; objects?: string[]; [key:string]: unknown };
  narration: Narration;
  timeline: { start:number; duration:number; action:string }[];
};

export type Lesson = { lesson_id:string; scenes:Scene[] };
