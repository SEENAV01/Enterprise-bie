// ThreeCanvas with @remotion/three's name and props, for the preview harness (Task 046a). A React Three Fiber canvas
// that never renders on its own clock: every time the video frame changes, the scene is drawn once, synchronously,
// and the frame is held (delayRender) until that draw is done, so a screenshot always shows exactly this frame.
// In a real Remotion project the import "@remotion/three" gives Remotion's own ThreeCanvas instead.
import React, { useLayoutEffect, useRef } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { continueRender, delayRender, useCurrentFrame } from "remotion";

type Props = React.ComponentProps<typeof Canvas> & { width: number; height: number };

const FrameSync: React.FC<{ frame: number; done: () => void }> = ({ frame, done }) => {
  const advance = useThree((s) => s.advance);
  useLayoutEffect(() => {
    advance(performance.now());
    done();
  }, [frame, advance, done]);
  return null;
};

// The canvas takes the size it is told, as Remotion's ThreeCanvas does, never the measured one: inside a scaled stage
// (a 720p output of the 1920 × 1080 composition, Task 046) the measured rectangle is the scaled one.
const SizeSync: React.FC<{ width: number; height: number }> = ({ width, height }) => {
  const setSize = useThree((s) => s.setSize);
  const size = useThree((s) => s.size);
  useLayoutEffect(() => {
    if (size.width !== width || size.height !== height) setSize(width, height);
  }, [width, height, setSize, size.width, size.height]);
  return null;
};

export const ThreeCanvas: React.FC<Props> = ({ width, height, children, style, gl, ...rest }) => {
  const frame = useCurrentFrame();
  const handle = useRef<{ frame: number; id: number } | null>(null);
  if (!handle.current || handle.current.frame !== frame) {
    if (handle.current) continueRender(handle.current.id);
    handle.current = { frame, id: delayRender(`three frame ${frame}`) };
  }
  const done = React.useCallback(() => {
    if (handle.current) continueRender(handle.current.id);
  }, []);
  return (
    <Canvas frameloop="never" dpr={(rest as any).dpr ?? 1} style={{ width, height, ...style }} resize={{ offsetSize: true, scroll: false, debounce: 0 }}
      gl={{ preserveDrawingBuffer: true, antialias: true, ...(gl as object) }} {...rest}>
      <SizeSync width={width} height={height} />
      {children}
      <FrameSync frame={frame} done={done} />
    </Canvas>
  );
};
