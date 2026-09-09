# BIE MASTER SPECIFICATION
Status: AUTHORITATIVE — Final fully fledged enterprise product.

## North Star
Give BIE any good-quality textbook chapter/book. BIE independently determines what to teach, in what order and why; identifies prerequisites, dependencies, misconceptions and objectives; designs the lesson; determines what the teacher says, what the learner sees and how it animates; generates executable video code; compiles, renders, validates and repairs it; and from the same grounded understanding designs, generates, validates and repairs an interactive revision game with executable game code.

BIE is an autonomous textbook-to-learning production compiler, not a summarizer, template filler, prompt wrapper, or raw-book-to-code shortcut.

## Mandatory outputs
Video: grounded curriculum -> lesson -> director script -> visual plan -> animation plan -> Scene IR -> Remotion project -> build -> render -> validated media.
Game: learning model -> revision strategy -> game director -> mechanics/interactions -> Game IR -> executable game -> build/runtime validation -> validated revision experience.

## Architecture Constitution
1. Grounding/provenance survives every transformation.
2. Important reasoning decisions are structured, auditable artifacts.
3. Pedagogy is adaptive; fixed lesson templates are components, never intelligence.
4. Visual grammar is concept-selected; no universal fixed layout is final architecture.
5. Animation planning is semantic and attention-aware.
6. Scene IR and Game IR isolate intelligence from implementation frameworks.
7. Game generation is first-class, not quiz generation.
8. LLM/model providers are replaceable; BIE owns orchestration, state, graphs, contracts, compilers, QA and evaluation.
9. Deterministic problems use deterministic tools where appropriate.
10. Generated code alone is never production SUCCESS.
11. Video requires actual build/render verification; game requires build/runtime/interaction verification.
12. QA covers grounding, semantics, prerequisites, pedagogy, mathematics, visuals, animation, timing/audio, code, runtime and regression.
13. Failure routes to the upstream layer that owns the faulty decision; repair cannot weaken gates.
14. Every artifact is versioned and traceable to source, decisions, configuration, models/tools, code and evidence.
15. Architecture changes require decision records.
16. Atomic tasks are not ACCEPTED without required tests/evidence.
17. First achieve measured final capability/quality; optimize cost later without weakening quality.

## Capability planes
BI Source/Book Intelligence
KI Knowledge/Concept Intelligence
PR Prerequisite Plus
RE Reasoning Intelligence
PED Learner/Pedagogy
DIR Teaching/Script Director
VIS Visual Director
ANI Animation Director
DSL Universal Scene IR
COMP Video/Remotion Compiler
GAME Revision Game Intelligence + Game IR/Compiler
QA Production QA/Auto-Repair
INFRA Enterprise orchestration/state/artifacts/model gateway/cache/observability/security/reproducibility/evaluation.

## Authoritative flow
SOURCE -> Document Intelligence -> Grounded Knowledge/Concept Graph -> Prerequisite Graph -> Reasoning -> Pedagogy -> Lesson Architecture.
Video -> Script Director -> Visual Director -> Animation Director -> Scene IR -> Compiler -> Remotion -> Build -> Render -> QA -> Repair/Reverify -> Release.
Game -> Revision Reasoning -> Game Director -> Mechanics -> Game IR -> Game Compiler -> Executable Game -> Runtime/Learning QA -> Repair/Reverify -> Release.

## Enterprise Done
Not one demo. A versioned multi-domain golden benchmark must demonstrate grounded understanding, defensible teaching order, adaptive pedagogy/directing, concept-appropriate visuals/animation, executable video+game code, actual execution/rendering, multilayer QA, bounded repair, reproducibility and traceability.

## Development doctrine
System -> subsystem -> capability -> component -> atomic task.
Lifecycle: PLANNED -> READY -> IN_PROGRESS -> IMPLEMENTED -> UNIT_TESTED -> INTEGRATION_TESTED -> GOLDEN_TESTED -> QA_VERIFIED -> ACCEPTED.
Stable task IDs are never reused.
