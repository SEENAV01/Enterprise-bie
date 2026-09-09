# Reasoning continuation: spatial and temporal intelligence

These tasks continue after RE-CAUSAL-003/004/005 and RE-SPATIAL-001/002. Their actual existing implementations were integrated and regression-tested, not recreated.

| Task | Implemented behavior | Tests |
| --- | --- | ---: |
| RE-SPATIAL-003 | Explicit planar scale/orientation, distance/bearing, grounded directed shortest routes and unreachable results | 16 |
| RE-SPATIAL-004 | Exact coordinate predicates, polygon area/perimeter/centroid, containment, segment relations and triangle classification | 18 |
| RE-TEMP-001 | BCE/CE and Gregorian day axes, uncertain/open event dates, proven order and unresolved comparisons | 15 |
| RE-TEMP-002 | Explicit/date-derived precedence, deterministic partial orders, cycle witnesses and interval-chain contradiction checks | 13 |
| RE-TEMP-003 | Source-defined half-open periods, nested schemes, boundary uncertainty, overlaps and unassigned events | 16 |

Operations are deterministic and provider-neutral. They require evidence and reject unknown references, invalid coordinates, incompatible time axes and unsafe bounds; contradictions and uncertainty are explicit. Payloads are versioned and hashed. Confidence is the weakest supplied evidence strength, not a calibrated probability. Ambiguity/conflict/low strength requires review.

`GroundedResult` uses the existing `EvidenceRef`, rich `ReasoningDecision` and `ArtifactEnvelope` contracts. Artifact creation resolves evidence IDs to validated parents and retains source locators. Synthetic integration tests trace source → inference → decision and a revision-game challenge; they do not claim a complete render or executable game.

## Domain limits

- Maps use explicit local planar frames. No geographic CRS guessing, map OCR, geodesics or inferred roads.
- Geometry handles supplied coordinates and simple polygons without holes. No raster understanding, symbolic theorem discovery or general 3D solids.
- Temporal ranges express date uncertainty, not duration. Equal ticks are simultaneous only at declared resolution; ordering inside a year needs finer evidence. Year/day axes are not silently mixed.
- Precedence does not prove causation. A lexical display or topological extension is not an inferred historical total order.
- Period boundaries, parents and competing schemes come from source evidence; no historiography or missing period is invented.

## Evidence and acceptance

78 task tests + 13 integration/contract tests + 12 assembly guards + 1,551 restored regressions = **1,654 passing tests**, zero failures/errors/skips. Numerical/history fixtures are synthetic and labelled accordingly; unavailable textbook data was not fabricated.

Status: **IMPLEMENTED, NOT ACCEPTED**. Diverse real-book integrated reasoning and downstream compiler/render/game QA remain required. The task names came from the user; concrete bounded interfaces are specifications established in this continuation, not purported recovered specifications.
