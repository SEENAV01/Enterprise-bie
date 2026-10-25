// The toolbox block registry (Task 046a). The core block library (index.tsx) draws a layer of type "block" by asking
// this registry for the component named in the layer; the toolbox bundle (blocks/toolbox/*) registers the components.
// Kept free of heavy imports, so the core preview bundle stays small and a spec that needs a toolbox block fails
// loudly in the core bundle instead of drawing nothing.
import type React from "react";

export type BlockProps = {
  data: any;                 // the block's own data (from a BIE compute adapter or the director)
  at: number;                // the frame the layer appears on (frame numbers below are relative to the scene)
  until?: number;
  width: number;             // pixel size of the layer's box
  height: number;
  id: string;
};

const blocks = new Map<string, React.FC<BlockProps>>();

export function registerBlock(name: string, component: React.FC<BlockProps>) {
  blocks.set(name, component);
}

export function getBlock(name: string): React.FC<BlockProps> | undefined {
  return blocks.get(name);
}

export const blockNames = () => Array.from(blocks.keys()).sort();
