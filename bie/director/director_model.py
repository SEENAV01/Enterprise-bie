"""BIE-DIR-HARD-DIRECTOR-001: bounded structured model execution for directing."""
from dataclasses import asdict, dataclass
from bie.model_gateway.model_interface import ModelRequest, ModelResponse, validate_request
from bie.model_gateway.schema_validation import validate as validate_schema
from .director_artifacts import canonical, fingerprint, parse_json
from .contract_validation import nonblank
from .semantic_execution import EvaluatorIdentity


@dataclass(frozen=True)
class DirectingPolicy:
    version: str = "bie-dir-grounded-directing/1.0.0"
    plan_prompt_version: str = "bie-dir-plan/1.0.0"
    narration_prompt_version: str = "bie-dir-narrate/1.0.0"
    maximum_attempts: int = 2
    maximum_request_characters: int = 96000
    maximum_response_characters: int = 64000
    maximum_scenes: int = 128
    maximum_total_beats: int = 1024
    maximum_spoken_characters: int = 240000
    maximum_stage_attempts: int = 3

    def validate(self):
        for name in ("version", "plan_prompt_version", "narration_prompt_version"):
            nonblank(getattr(self, name), name)
        for name in ("maximum_attempts", "maximum_request_characters", "maximum_response_characters",
                     "maximum_scenes", "maximum_total_beats", "maximum_spoken_characters", "maximum_stage_attempts"):
            value = getattr(self, name)
            if type(value) is not int or value < 1: raise ValueError(name + " must be a positive integer")
        if self.maximum_attempts > 3 or self.maximum_stage_attempts > 3:
            raise ValueError("retry policy must be bounded to at most three attempts")


@dataclass(frozen=True)
class DirectingAttempt:
    phase: str
    subject_id: str
    attempt: int
    request_fingerprint: str
    response_fingerprint: str | None
    outcome: str


class ResourceLimit(ValueError):
    """Do not retry a resource limit by silently cutting educational content."""


class DirectingFailure(Exception):
    def __init__(self, code, attempts=(), owner="DIR"):
        super().__init__(code)
        self.code, self.attempts, self.owner = code, tuple(attempts), owner


def model_identity(identity):
    if not isinstance(identity, EvaluatorIdentity): raise ValueError("expected canonical evaluator identity")
    for value in (identity.provider, identity.model, identity.adapter_version): nonblank(value, "provider identity")


def request_material(identity, policy, phase, subject_id, instruction, payload, schema, number=1, last_error=None):
    """One authoritative request recipe for invocation, budgeting and replay audit."""
    system = instruction
    if last_error:
        system += "\nThe previous record failed contract validation: " + last_error + ". Return a complete corrected record."
    content = canonical(payload)
    if len(system) + len(content) + len(canonical(schema)) > policy.maximum_request_characters:
        raise ResourceLimit('director request exceeds its configured context budget')
    return {"phase": phase, "subject_id": subject_id, "identity": asdict(identity), "policy": asdict(policy),
            "messages": ({"role": "system", "content": system}, {"role": "user", "content": content}),
            "schema": schema, "temperature": 0.0, "attempt": number}


def invoke_structured(provider, identity, policy, phase, subject_id, instruction, payload, schema, validator):
    policy.validate(); model_identity(identity)
    if not callable(getattr(provider, "invoke", None)): raise ValueError("canonical ModelProvider required")
    attempts = []
    last_error = None
    for number in range(1, policy.maximum_attempts + 1):
        try:
            material = request_material(identity, policy, phase, subject_id, instruction, payload, schema, number, last_error)
        except ResourceLimit:
            raise DirectingFailure("DIRECTOR_CONTEXT_BUDGET_EXCEEDED", attempts, "DIR_SCOPE")
        request_hash = fingerprint(material)
        # No shared mutable schema/message objects are passed to a transport.
        request = ModelRequest("dir-generate:" + request_hash[7:], tuple(parse_json(canonical(material["messages"]))),
                               frozenset(("text", "structured_output")), parse_json(canonical(schema)), 0.0)
        validate_request(request)
        response_hash = None
        terminal = False
        try:
            raw = provider.invoke(request)
        except Exception:
            outcome = "PROVIDER_EXECUTION_FAILED"
        else:
            if isinstance(raw, ModelResponse):
                envelope = {key: getattr(raw, key) for key in ("provider", "model", "content", "finish_reason")}
            elif type(raw) is dict and {"provider", "model", "content", "finish_reason"} <= raw.keys():
                envelope = {key: raw[key] for key in ("provider", "model", "content", "finish_reason")}
            else:
                envelope = None
            try: response_hash = fingerprint(envelope)
            except (ValueError, TypeError, OverflowError, RecursionError): pass
            if envelope is None:
                outcome = "RESPONSE_ENVELOPE_INVALID"
            elif (envelope["provider"], envelope["model"]) != (identity.provider, identity.model):
                outcome, terminal = "PROVIDER_IDENTITY_MISMATCH", True
            elif envelope["finish_reason"] not in ("stop", "completed", "end_turn"):
                outcome = "INCOMPLETE_OR_REFUSED_RESPONSE"
                terminal = envelope["finish_reason"] not in ("length", "max_tokens")
            else:
                try:
                    value = envelope["content"]
                    if type(value) is dict: value = canonical(value)
                    if type(value) is not str: raise ValueError("response must be JSON")
                    if len(value) > policy.maximum_response_characters: raise ResourceLimit("response limit")
                    parsed = parse_json(value)
                    validate_schema(parsed, schema)
                    result = validator(parsed)
                except ResourceLimit:
                    outcome, terminal = "DIRECTOR_OUTPUT_BUDGET_EXCEEDED", True
                except (ValueError, TypeError, OverflowError, RecursionError, KeyError):
                    outcome = "RESPONSE_CONTRACT_REJECTED"
                else:
                    attempts.append(DirectingAttempt(phase, subject_id, number, request_hash, response_hash, "VALIDATED_OUTPUT"))
                    return result, tuple(attempts)
        attempts.append(DirectingAttempt(phase, subject_id, number, request_hash, response_hash, outcome))
        if terminal or number == policy.maximum_attempts:
            raise DirectingFailure(outcome, attempts, "DIR_MODEL" if outcome != "DIRECTOR_OUTPUT_BUDGET_EXCEEDED" else "DIR_SCOPE")
        last_error = outcome
    raise AssertionError("bounded attempt loop exhausted without result")
