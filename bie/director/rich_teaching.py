"""Grounded codecs for examples, demonstrations, inquiry and misconceptions.

The records in this module are upstream teaching data.  They never create source
facts, infer learner state, or award a directing/quality verdict.  Compilation
uses the existing deterministic DIR teaching helpers and emits exact obligations
that the ordinary plan/narration validators must later realize.
"""
from dataclasses import asdict, dataclass

from .contract_validation import ids, nonblank
from .demonstration_narration import narrate_demonstration
from .misconception_dialogue import build_misconception_dialogue
from .socratic_dialogue import socratic_sequence


@dataclass(frozen=True)
class GroundedWorkedExample:
    example_id: str
    concept_id: str
    setup: object
    steps: tuple[object, ...]
    outcome: object


@dataclass(frozen=True)
class GroundedDemonstration:
    demonstration_id: str
    concept_id: str
    setup: object
    action: object
    observation: object
    interpretation: object


@dataclass(frozen=True)
class GroundedInquiry:
    inquiry_id: str
    concept_id: str
    claim: object
    evidence: object
    misconception: object | None = None


@dataclass(frozen=True)
class GroundedMisconception:
    misconception_id: str
    concept_id: str
    belief: object
    counterevidence: object
    replacement: object


@dataclass(frozen=True)
class GroundedNotation:
    notation_id: str
    concept_id: str
    symbol: object
    spoken_form: str
    meaning: object


RICH_TYPES = (
    GroundedWorkedExample,
    GroundedDemonstration,
    GroundedInquiry,
    GroundedMisconception,
    GroundedNotation,
)


def _source(excerpt, resolve):
    text = resolve(excerpt)
    return text, excerpt.evidence_id


def _obligation(identifier, kind, concept_id, required, evidence, reason, predecessors=()):
    return {
        "obligation_id": nonblank(identifier, "rich obligation id"),
        "kind": nonblank(kind, "rich obligation kind"),
        "concept_id": nonblank(concept_id, "rich concept id"),
        "required_texts": list(ids(tuple(required), "rich required text")),
        "evidence_ids": list(ids(tuple(sorted(set(evidence))), "rich evidence")),
        "source_reason": nonblank(reason, "rich source reason"),
        "predecessor_obligation_ids": list(ids(tuple(predecessors), "rich predecessors", required=False)),
    }


def compile_rich_teaching(specs, concept_ids, resolve):
    """Validate typed source spans and compile deterministic teaching obligations."""
    specs = tuple(specs)
    if len(specs) > 4096:
        raise ValueError("rich teaching resource budget")
    known = set(concept_ids)
    identifiers = []
    obligations = []
    strategy_rows = []
    for spec in specs:
        if type(spec) not in RICH_TYPES:
            raise ValueError("known frozen rich teaching record required")
        concept_id = nonblank(spec.concept_id, "rich concept id")
        if concept_id not in known:
            raise ValueError("rich teaching concept outside knowledge context")
        record = asdict(spec)
        if isinstance(spec, GroundedWorkedExample):
            identifier = nonblank(spec.example_id, "example id")
            if not spec.steps:
                raise ValueError("worked example needs source-grounded steps")
            setup, setup_eid = _source(spec.setup, resolve)
            outcome, outcome_eid = _source(spec.outcome, resolve)
            sequence = [("SETUP", setup, setup_eid)]
            sequence.extend(("STEP",) + _source(step, resolve) for step in spec.steps)
            sequence.append(("OUTCOME", outcome, outcome_eid))
            previous = ()
            for index, (phase, text, evidence_id) in enumerate(sequence, 1):
                oid = f"rich:example:{identifier}:{index}"
                obligations.append(_obligation(oid, "WORKED_EXAMPLE_STEP", concept_id, (text,),
                    (evidence_id,), f"{phase} of source-grounded worked example {identifier}.", previous))
                previous = (oid,)
        elif isinstance(spec, GroundedDemonstration):
            identifier = nonblank(spec.demonstration_id, "demonstration id")
            rows = [_source(value, resolve) for value in
                    (spec.setup, spec.action, spec.observation, spec.interpretation)]
            deterministic = narrate_demonstration(*(text for text, _ in rows), tuple(eid for _, eid in rows))
            previous = ()
            for index, (step, (_, evidence_id)) in enumerate(zip(deterministic, rows), 1):
                oid = f"rich:demonstration:{identifier}:{index}"
                obligations.append(_obligation(oid, "DEMONSTRATION_STEP", concept_id,
                    (step.narration,), (evidence_id,), f"{step.phase} phase of demonstration {identifier}.", previous))
                previous = (oid,)
        elif isinstance(spec, GroundedInquiry):
            identifier = nonblank(spec.inquiry_id, "inquiry id")
            claim, claim_eid = _source(spec.claim, resolve)
            evidence, evidence_eid = _source(spec.evidence, resolve)
            misconception = None
            misconception_eid = None
            if spec.misconception is not None:
                misconception, misconception_eid = _source(spec.misconception, resolve)
            sequence = socratic_sequence(concept_id, claim, (claim_eid, evidence_eid), misconception)
            previous = ()
            for index, step in enumerate(sequence, 1):
                required = (evidence,) if step.kind == "PROBE" else ((misconception,) if step.kind == "CHALLENGE" else (claim,))
                evidence_ids = (evidence_eid,) if step.kind == "PROBE" else ((misconception_eid,) if step.kind == "CHALLENGE" else (claim_eid,))
                oid = f"rich:inquiry:{identifier}:{index}"
                obligations.append(_obligation(oid, "SOCRATIC_" + step.kind, concept_id, required,
                    evidence_ids, step.prompt, previous))
                previous = (oid,)
        elif isinstance(spec, GroundedMisconception):
            identifier = nonblank(spec.misconception_id, "misconception id")
            belief, belief_eid = _source(spec.belief, resolve)
            counter, counter_eid = _source(spec.counterevidence, resolve)
            replacement, replacement_eid = _source(spec.replacement, resolve)
            dialogue = build_misconception_dialogue(belief, counter, replacement,
                (belief_eid, counter_eid, replacement_eid))
            sequence = (
                ("ELICIT", belief, belief_eid, dialogue.elicitation),
                ("CONFLICT", counter, counter_eid, dialogue.conflict_prompt),
                ("REPLACE", replacement, replacement_eid, dialogue.replacement_prompt),
                ("TRANSFER", replacement, replacement_eid, dialogue.transfer_check),
            )
            previous = ()
            for index, (phase, text, evidence_id, prompt) in enumerate(sequence, 1):
                oid = f"rich:misconception:{identifier}:{index}"
                obligations.append(_obligation(oid, "MISCONCEPTION_" + phase, concept_id,
                    (text,), (evidence_id,), prompt, previous))
                previous = (oid,)
        else:
            identifier = nonblank(spec.notation_id, "notation id")
            symbol, symbol_eid = _source(spec.symbol, resolve)
            meaning, meaning_eid = _source(spec.meaning, resolve)
            spoken = nonblank(spec.spoken_form, "notation spoken form")
            if len(spoken) > 160 or not symbol.strip():
                raise ValueError("bounded notation pronunciation required")
            obligations.append(_obligation(f"rich:notation:{identifier}", "NOTATION_EXPLANATION",
                concept_id, (symbol, spoken, meaning), (symbol_eid, meaning_eid),
                "Speak the exact notation, pronunciation and source-grounded meaning."))
        identifiers.append(identifier)
        strategy_rows.append({"type": type(spec).__name__, "id": identifier,
                              "concept_id": concept_id, "source_record": record})
    ids(tuple(identifiers), "rich teaching strategy ids", required=False)
    ids(tuple(row["obligation_id"] for row in obligations), "rich teaching obligations", required=False)
    known_obligations = {row["obligation_id"] for row in obligations}
    if any(not set(row["predecessor_obligation_ids"]) <= known_obligations for row in obligations):
        raise ValueError("rich teaching predecessor outside bundle")
    return {
        "schema_version": "bie.dir.rich_teaching/1.0.0",
        "strategies": strategy_rows,
        "obligations": obligations,
        "coverage": {concept: sorted(row["obligation_id"] for row in obligations if row["concept_id"] == concept)
                     for concept in sorted(known)},
        "accepted": False,
    }
