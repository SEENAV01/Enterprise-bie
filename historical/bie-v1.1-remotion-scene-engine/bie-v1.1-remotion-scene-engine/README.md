# BIE v1.1 — Real Scene Intelligence + Remotion Bridge

This stage converts the real Electricity & Magnetism lesson plan into a source-grounded Scene DSL.

18 scenes cover:
- charge and electric field
- conductors/insulators
- circuits/current/ammeter
- potential/voltmeter
- Ohm's law
- resistance/resistivity
- series/parallel
- Joule heating
- safety
- AC/DC
- electromagnets
- motor/generator
- magnetic field lines
- worked numerical
- adaptive assessment

Every scene has source_refs. Visual type is selected from the learning purpose rather than arbitrary decoration.

The Remotion folder is a renderer bridge. It creates one Composition per scene and keeps the Scene DSL separate from React/Remotion rendering.

Run validation:
`python scene_engine/validate.py examples/electricity-magnetism.scene.json`

Install/render:
`cd remotion && npm install && npm run start`

The renderer starter is intentionally minimal; the next renderer pass should replace the generic SceneRenderer with specialized reusable components for equations, circuits, graphs, particles, field lines, timelines and interactive assessment.
