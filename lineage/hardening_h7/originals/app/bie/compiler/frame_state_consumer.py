"""H6-002: deterministic state-at-frame and actual JSX consumers.

No useEffect/useState, handler evaluation, random access history, implicit casts or
mutable playback cursor. Reading frame N before frame 0 has identical semantics.
"""
from __future__ import annotations
from copy import deepcopy
from .frame_runtime_contract import integer, transformed, fail
from .element_compiler_common import jsx, component_name
from .react_emitter_common import emitted_file


def runtime_at(plan, frame):
    integer(frame, 0, plan['frame_count'] - 1, 'render frame')
    state = deepcopy(plan['initial_state']); events = []
    for e in plan['events']:
        if e['frame'] > frame:
            break
        state[e['state_path']] = e['value']; events.append(e['event_id'])
    values = {}
    for b in plan['bindings']:
        values.setdefault(b['target_id'], {})[b['property_name']] = transformed(state[b['state_path']], b['property_name'], b['transform'])
    cue = next((c for c in plan['narration'] if c['start_frame'] <= frame < c['end_frame']), None)
    return {'frame': frame, 'state': state, 'targets': values, 'applied_event_ids': events,
            'active_cue_ids': [] if cue is None else [cue['cue_id']], 'caption_text': '' if cue is None else cue['text']}


def emit_runtime(plan):
    source = '''// BIE H6: pure frame evaluation; generated only from a validated plan.
export type Scalar = string | number | boolean;
export type Event = {event_id:string; frame:number; at_ms:number; state_path:string; value:Scalar; target_ids:string[]; source_refs:string[]; reasoning_refs:string[]};
export type Binding = {binding_id:string; state_path:string; target_id:string; property_name:string; transform:string; source_refs:string[]; reasoning_refs:string[]};
export type Cue = {cue_id:string; start_frame:number; end_frame:number; start_ms:number; end_ms:number; text_ref:string; text:string; narration_revision:number; target_ids:string[]; asset_id:string; public_path:string; trim_before_frames:number; volume:number; source_refs:string[]; reasoning_refs:string[]};
export const initialState: Record<string, Scalar> = INITIAL;
export const events: Event[] = EVENTS;
export const bindings: Binding[] = BINDINGS;
export const cues: Cue[] = CUES;
export const FRAME_COUNT = COUNT;
export const EXPECTED_FPS = FPS;
export const atFrame = (frame:number) => {
  if (!Number.isInteger(frame) || frame < 0 || frame >= FRAME_COUNT) throw new Error("FRAME_RUNTIME_FRAME_INVALID");
  const state: Record<string, Scalar> = {...initialState};
  const applied_event_ids: string[] = [];
  for (const e of events) {
    if (e.frame > frame) break;
    state[e.state_path] = e.value; applied_event_ids.push(e.event_id);
  }
  const targets: Record<string, Record<string, Scalar>> = {};
  for (const b of bindings) {
    const value = state[b.state_path];
    if (!Object.prototype.hasOwnProperty.call(targets, b.target_id)) targets[b.target_id] = {};
    targets[b.target_id][b.property_name] = b.transform === "clamp01" ? Math.max(0, Math.min(1, value as number)) : value;
  }
  const cue = cues.find(c => c.start_frame <= frame && frame < c.end_frame);
  return {frame, state, targets, applied_event_ids, active_cue_ids:cue ? [cue.cue_id] : [], caption_text:cue ? cue.text : ""};
};
'''
    values = {'INITIAL':plan['initial_state'], 'EVENTS':plan['events'], 'BINDINGS':plan['bindings'],
              'CUES':plan['narration'], 'COUNT':plan['frame_count'], 'FPS':plan['fps']}
    # Exact token replacement once, before user data is inserted; strings may contain token names.
    import re
    source = re.sub(r'\b(INITIAL|EVENTS|BINDINGS|CUES|COUNT|FPS)\b', lambda m: jsx(values[m.group()]), source)
    return emitted_file('src/runtime/frame-runtime.ts', source)


def text_style(element):
    style = {'whiteSpace':'pre-wrap', 'overflowWrap':'anywhere'}
    if 'compiler_layout' in element['props']:
        from .layout_repair_contracts import presentation
        p = presentation('text', element['props']['compiler_layout'])
        style.update(boxSizing='border-box',width='100%',minWidth=0,fontSize=p['font_px'],lineHeight=p['line_height'],padding=p['padding_px'])
    return style


def emit_bound_layer(plan, element):
    eid = element['element_id']; bs = [b for b in plan['bindings'] if b['target_id'] == eid]
    caption = plan['caption_target_id'] == eid
    if not bs and not caption:
        return None
    props = {b['property_name'] for b in bs}
    replace_text = 'text' in props or caption
    name = component_name('RuntimeLayer', eid)
    inner = '{children}'
    if replace_text:
        expr = 'value.caption_text' if caption else 'bound.text as string'
        inner = (f'<div role="text" dir="auto" data-bie-text-id={{{jsx(eid+":text")}}} '
                 f'aria-label={{{expr}}} data-role={{{jsx(element["props"].get("role","body"))}}} '
                 f'style={{{jsx(text_style(element))}}}>{{{expr}}}</div>')
    # The wrapper preserves fixed layout; CSS visibility does not delete its geometry.
    style = '{opacity: (bound.opacity as number | undefined) ?? 1, visibility: bound.visible === false ? "hidden" : "visible", width:"100%", height:"100%"}'
    source = f'''import React from "react";
import {{useCurrentFrame, useVideoConfig}} from "remotion";
import {{atFrame, EXPECTED_FPS}} from "../runtime/frame-runtime";
export const {name}: React.FC<React.PropsWithChildren> = ({{children}}) => {{
  const frame = useCurrentFrame();
  if (useVideoConfig().fps !== EXPECTED_FPS) throw new Error("FRAME_RUNTIME_FPS_MISMATCH");
  const value = atFrame(frame); const bound = value.targets[{jsx(eid)}] ?? {{}};
  return <div data-bie-runtime-target={{{jsx(eid)}}} data-bie-active-cues={{value.active_cue_ids.join(",")}} style={{{style}}}>{inner}</div>;
}};
'''
    return emitted_file('src/runtime-layers/' + name + '.tsx', source), name
