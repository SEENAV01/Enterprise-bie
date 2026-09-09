# Scene architecture

BIE decides:
1. pedagogical purpose
2. source/content references
3. visual representation type
4. timing beats

Remotion decides:
1. pixels
2. animation interpolation
3. typography/layout
4. audio/captions
5. final MP4 rendering

This separation is critical for scaling to many books.

A future scene can be rendered by:
`SceneDSL -> component registry -> Remotion composition -> MP4`

Component registry examples:
- definition_card
- equation_derivation
- circuit_schematic
- circuit_animation
- graph
- parameter_simulation
- field_lines
- particle_flow
- comparison
- worked_problem
- adaptive_question
