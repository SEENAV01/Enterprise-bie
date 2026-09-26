# Batch 05 Mechanics Architecture

The Mechanics layer converts governed learning intent into semantic learner interactions. It does not bypass the State Engine. Mechanic-local outcomes can be projected through `state_bridge.py` into typed proposed StateDelta patches; authoritative state transitions remain the responsibility of the State Engine.

## Layers
1. `contracts.py` — typed mechanic/action/motion/quality/receipt contracts.
2. 17 independent mechanic modules — capability-specific semantics and failure modes.
3. `studio_policy.py` — anti-slide, state-causal motion, accessibility and no-speed-pressure gate.
4. `state_bridge.py` — typed integration with Batch 04 State Engine schema.
5. `reset.py` / `replay.py` — deterministic reset/replay evidence.
6. `pipeline.py` — governed enum dispatch, never keyword routing.

## Studio quality principle
Animation is a consequence/explanation of learner-driven state change. Decorative motion is insufficient. Drag/place/order actions require keyboard parity. Retrieval hides answers until submission. Prediction commits before observation. Maps require sourced coordinates. Simulations explicitly declare model scope.
