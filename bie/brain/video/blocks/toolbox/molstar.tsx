// protein_3d through Mol* (Task 046a): the Protein Data Bank's own viewer, for detailed cartoons and surfaces.
// Mol*'s own animation loop is paused; every video frame sets the camera and draws once, synchronously.
import React, { useLayoutEffect, useRef, useState } from "react";
import { PluginContext } from "molstar/lib/mol-plugin/context";
import { DefaultPluginSpec } from "molstar/lib/mol-plugin/spec";
import { Color } from "molstar/lib/mol-util/color";
import { continueRender, delayRender } from "remotion";
import { registerBlock, BlockProps } from "../registry";
import { Title, Badge, assetUrl, ramp, useAsset, useFrameHold, useRel } from "./common";

async function startPlugin(holder: HTMLDivElement, pdb: string, format: string) {
  const plugin = new PluginContext(DefaultPluginSpec());
  await plugin.init();
  const canvas = document.createElement("canvas");
  canvas.style.width = "100%";
  canvas.style.height = "100%";
  holder.appendChild(canvas);
  if (!(await plugin.initViewerAsync(canvas, holder))) throw new Error("Mol* could not start WebGL");
  // Water molecules (HOH) are crystal water, not the protein: left out so the fold reads clearly.
  const clean = format === "pdb" ? pdb.split("\n").filter((l) => !(l.startsWith("HETATM") && l.slice(17, 20) === "HOH")).join("\n") : pdb;
  const data = await plugin.builders.data.rawData({ data: clean, label: "structure" });
  const trajectory = await plugin.builders.structure.parseTrajectory(data, format as any);
  await plugin.builders.structure.hierarchy.applyPreset(trajectory, "default");
  const c3d = plugin.canvas3d!;
  // Software WebGL: screen-space occlusion and outlines cost seconds per frame, so they are off; the axes helper too.
  c3d.setProps({ transparentBackground: true, renderer: { backgroundColor: Color(0x06121c) } as any,
    trackball: { animate: { name: "off", params: {} } } as any,
    postprocessing: { occlusion: { name: "off", params: {} }, outline: { name: "off", params: {} }, shadow: { name: "off", params: {} } } as any,
    camera: { helper: { axes: { name: "off", params: {} } } } as any } as any);
  c3d.requestCameraReset({ durationMs: 0 });
  c3d.commit(true);
  c3d.tick(performance.now() as any, { isSynchronous: true, manualDraw: true });
  c3d.pause();
  const base = { ...c3d.camera.getSnapshot() };
  return { plugin, base };
}

const MolstarProtein: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, frame, fps } = useRel(at);
  const pdb = useAsset<string>(`pdb:${data.src}`, async () => (await fetch(assetUrl(data.src))).text());
  const holder = useRef<HTMLDivElement>(null);
  const [view, setView] = useState<{ plugin: PluginContext; base: any } | null>(null);
  const starting = useRef(false);
  const release = useFrameHold(frame);
  useLayoutEffect(() => {
    if (!pdb || !holder.current || starting.current) return;
    starting.current = true;
    const handle = delayRender("molstar start");
    startPlugin(holder.current, pdb, data.format || "pdb").then((v) => { setView(v); continueRender(handle); },
      (e) => { continueRender(handle); throw e; });
  }, [pdb]);
  useLayoutEffect(() => {
    if (!view) return;
    const c3d = view.plugin.canvas3d!;
    const { position, target, up } = view.base;
    const angle = (((data.turn_degrees ?? 200) * Math.PI) / 180) * ramp(rel, 0, (data.seconds ?? 5) * fps, (t: number) => t);
    const dx = position[0] - target[0], dz = position[2] - target[2];
    const zoom = data.zoom ?? 0.85;
    const rotated = [target[0] + (dx * Math.cos(angle) + dz * Math.sin(angle)) * zoom, target[1] + (position[1] - target[1]) * zoom,
                     target[2] + (-dx * Math.sin(angle) + dz * Math.cos(angle)) * zoom];
    c3d.camera.setState({ ...view.base, position: rotated as any, up, target }, 0);
    c3d.tick(performance.now() as any, { isSynchronous: true, manualDraw: true });
    release();
  });
  return (
    <>
      <div ref={holder} style={{ position: "absolute", inset: 0, width, height }} />
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 30, bottom: 24 }} /> : null}
    </>
  );
};

registerBlock("protein_molstar", MolstarProtein);
