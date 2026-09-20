# Primary API references used for H5

Consulted 2026-09-18. These references guide API use; they are not evidence of an installed-version render.

- Remotion `useCurrentFrame`: https://www.remotion.dev/docs/use-current-frame — frame zero and Sequence-relative behavior. This batch does not claim arbitrary nested Sequence timing.
- Remotion `interpolate`: https://www.remotion.dev/docs/interpolate — frame-indexed, explicit interpolation. H5 emits bounded scalar arithmetic with the inherited endpoint convention.
- Remotion `Sequence`: https://www.remotion.dev/docs/sequence — composition-relative behavior; actual installed dependency execution remains blocked.
- W3C SVG2 paths: https://www.w3.org/TR/SVG2/paths.html — path geometry and pathLength contract.
- W3C SVG2 stroke dashing: https://www.w3.org/TR/SVG2/painting.html#StrokeDashing — dash offset and normalized path length.

Render scope in this delivery: real Chromium executing generated markup through explicitly labelled React/Remotion API doubles, not the Remotion renderer. Font files are not distributed.
