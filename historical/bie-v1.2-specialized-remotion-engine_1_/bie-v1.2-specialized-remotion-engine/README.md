# BIE v1.2 — Specialized Remotion Engine

The real Electricity & Magnetism Scene DSL is now connected to reusable Remotion visual primitives:
Equation, Graph, CircuitDiagram, FieldLines, ParticleFlow, Comparison, plus a dispatcher.

The AI/pedagogy layer chooses `visual.type`; the renderer chooses the deterministic React component. Animations are frame-driven with Remotion interpolation rather than CSS animation.

Run:
`cd remotion && npm install && npm run start`

Then select S01–S18 in Studio.

Render only when desired:
`npx remotion render src/index.ts S08 out/scene.mp4`

This milestone is the specialized renderer foundation. Audio/captions, richer physics simulation, precise typesetting, transitions, and full-lesson rendering are the next layer.
