export type TimelineBeat={start:number;duration:number;action:string};
export type Scene={scene_id:string;module?:string;title?:string;purpose:string;duration_frames:number;content_refs:string[];source_refs:string[];visual:{type:string;layout?:string;formula?:string;objects?:string[];parameters?:string[];[key:string]:unknown};narration:{mode:string;key_points:string[]};timeline:TimelineBeat[]};
export type SceneDSL={lesson_id:string;scenes:Scene[]};
