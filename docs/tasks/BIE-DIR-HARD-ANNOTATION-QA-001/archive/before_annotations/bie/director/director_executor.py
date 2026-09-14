"""BIE-DIR-HARD-DIRECTOR-001: register actual DIR execution in existing INFRA.

SUCCEEDED means a reviewable component result exists. It does not authorize
rendering, release, or product acceptance. Catalog-index recovery remains INFRA.
"""
from dataclasses import asdict
from uuid import uuid4

from bie.infrastructure.artifact_store import BlobRef
from bie.infrastructure.execution_graph import default_enterprise_graph
from bie.infrastructure.idempotency_store import SQLiteIdempotencyStore, IdempotencyError
from bie.infrastructure.orchestrator import ExecutionContext, StageDefinition, StageExecutionResult, StageExecutionFailure
from .contract_validation import nonblank
from .director_artifacts import DirectorArtifactIO, canonical, parse_json, fields, fingerprint
from .director_inputs import load_director_inputs
from .director_model import DirectingPolicy, DirectingFailure, model_identity
from .grounded_directing import execute_grounded_director, code_fingerprint
from .semantic_execution import SemanticExecutionPolicy


def register_director_stage(definitions, executors, executor):
    contract = default_enterprise_graph().stages["DIRECTOR"]
    definition = StageDefinition(contract.stage_id, list(contract.required_predecessors),
        list(contract.consumes), contract.emits, "DIR")
    if "DIRECTOR" in executors: raise ValueError("DIRECTOR executor already registered")
    if "DIRECTOR" in definitions:
        prior = definitions["DIRECTOR"]
        if (prior.stage_id != definition.stage_id or set(prior.predecessors) != set(definition.predecessors)
                or set(prior.input_types) != set(definition.input_types) or prior.output_type != definition.output_type):
            raise ValueError("existing DIRECTOR contract differs from canonical graph")
        definition = prior
    if not callable(executor): raise ValueError("callable DIRECTOR executor required")
    return {**definitions, "DIRECTOR": definition}, {**executors, "DIRECTOR": executor}


class DirectorStageExecutor:
    def __init__(self, io, idempotency, generator, generator_identity, critic, critic_identity,
                 policy=DirectingPolicy(), semantic_policy=SemanticExecutionPolicy()):
        if not isinstance(io, DirectorArtifactIO) or not isinstance(idempotency, SQLiteIdempotencyStore):
            raise ValueError("canonical artifact IO and idempotency store required")
        policy.validate(); semantic_policy.validate()
        model_identity(generator_identity); model_identity(critic_identity)
        if not callable(getattr(generator, "invoke", None)) or not callable(getattr(critic, "invoke", None)):
            raise ValueError("configured ModelProvider instances required")
        self.io, self.idempotency = io, idempotency
        self.generator, self.generator_identity = generator, generator_identity
        self.critic, self.critic_identity = critic, critic_identity
        self.policy, self.semantic_policy = policy, semantic_policy

    def _blob(self, record):
        blob = self.io.catalog.cas.put_bytes(canonical(record).encode())
        return "cas:sha256:" + blob.digest + ":" + str(blob.size)

    def _read_blob(self, ref):
        prefix, algorithm, digest, size = ref.split(":")
        if prefix != "cas" or algorithm != "sha256": raise ValueError("operational receipt reference")
        return parse_json(self.io.catalog.cas.get_bytes(BlobRef(algorithm, digest, int(size))))

    def _failure(self, context, code, owner, attempts=(), evidence=()):
        # Input failures cannot truthfully claim a valid source lineage. Their
        # diagnostic is a real CAS operational record, not a fake source root.
        ref = self._blob({"schema_version": "bie.dir.operational_failure/1.0.0", "run_id": context.run_id,
            "stage_id": context.stage_id, "attempt": context.attempt, "code": code,
            "owner": owner, "generation_attempts": [asdict(a) for a in attempts], "accepted": False})
        return StageExecutionFailure([code], list(evidence) + [ref], owner)

    def _replay(self, ref, execution_fingerprint):
        record = self._read_blob(ref)
        fields(record, ("schema_version", "execution_fingerprint", "outcome", "value"), "stage replay")
        if record["schema_version"] != "bie.dir.stage_replay/1.0.0" or record["execution_fingerprint"] != execution_fingerprint:
            raise ValueError("stage replay binding mismatch")
        value = record["value"]
        if record["outcome"] == "FAILED":
            fields(value, ("diagnostics", "evidence_refs", "remediation_owner"), "failure replay")
            for evidence in value["evidence_refs"]:
                if evidence.startswith("cas:"): self._read_blob(evidence)
                else: self.io.load_graph((self.io.load(evidence).to_ref(),))
            raise StageExecutionFailure(**value)
        if record["outcome"] != "SUCCEEDED": raise ValueError("unknown replay outcome")
        fields(value, StageExecutionResult.__dataclass_fields__, "success replay")
        result = StageExecutionResult(**value); result.validate()
        self.io.load_graph(tuple(self.io.load(r).to_ref() for r in result.output_artifact_refs + result.evidence_refs))
        return result

    def _complete(self, context, owner, execution_fingerprint, outcome, value):
        ref = self._blob({"schema_version": "bie.dir.stage_replay/1.0.0", "execution_fingerprint": execution_fingerprint,
            "outcome": outcome, "value": value})
        self.idempotency.complete(context.idempotency_key, owner, ref)

    def __call__(self, context):
        if not isinstance(context, ExecutionContext): raise ValueError("canonical ExecutionContext required")
        owner = str(uuid4()); claimed = False; execution_fingerprint = None; phase = "INPUT"
        try:
            for value in (context.run_id, context.idempotency_key): nonblank(value, "execution identity")
            if context.stage_id != "DIRECTOR": raise ValueError("wrong stage")
            if type(context.attempt) is not int or context.attempt < 1: raise ValueError("invalid attempt")
            if context.attempt > self.policy.maximum_stage_attempts:
                raise DirectingFailure("DIRECTOR_STAGE_ATTEMPT_BUDGET_EXCEEDED", owner="DIR_REPAIR")
            config = fields(context.configuration["director"], ("lesson_id", "title", "language"), "director configuration")
            if type(context.input_artifact_refs) is not list or len(context.input_artifact_refs) != 2:
                raise ValueError("exactly one actual RE and PED artifact required")
            artifacts = [self.io.load(r) for r in context.input_artifact_refs]
            typed = {a.artifact_type: a.to_ref() for a in artifacts}
            if set(typed) != {"reasoning.decision_set", "pedagogy.plan"}: raise ValueError("unexpected input types")
            inputs = load_director_inputs(self.io, typed["reasoning.decision_set"], typed["pedagogy.plan"],
                run_id=context.run_id, **config)
            execution_fingerprint = fingerprint({"inputs": inputs.fingerprint(), "policy": asdict(self.policy),
                "semantic_policy": asdict(self.semantic_policy), "generator": asdict(self.generator_identity),
                "critic": asdict(self.critic_identity), "code": code_fingerprint(), "run_id": context.run_id,
                "stage_id": context.stage_id, "attempt": context.attempt, "configuration": context.configuration})
            phase = "IDEMPOTENCY"
            claim = self.idempotency.claim(context.idempotency_key, execution_fingerprint, owner)
            if claim.state == "COMPLETED": return self._replay(claim.result_ref, execution_fingerprint)
            if claim.owner != owner:
                raise DirectingFailure("DIRECTOR_IN_FLIGHT_REQUIRES_RECOVERY", owner="INFRA")
            claimed = True; phase = "EXECUTION"
            result = execute_grounded_director(self.io, inputs, self.generator, self.generator_identity,
                self.critic, self.critic_identity, self.policy, self.semantic_policy)
            phase = "PERSISTENCE"
            metadata = {"requires_review": True, "accepted": False, "release_ready": False,
                        "status": result.status, "execution_fingerprint": execution_fingerprint}
            evidence = self.io.derive("evidence.director_execution", context.run_id, inputs.parent_refs,
                {"schema_version": "bie.dir.execution/1.0.0", "result": asdict(result), "result_fingerprint": result.fingerprint(),
                 "policy": asdict(self.policy), "semantic_policy": asdict(self.semantic_policy),
                 "generator": asdict(self.generator_identity), "critic": asdict(self.critic_identity)},
                stage_id="DIRECTOR", metadata=metadata, evidence=True)
            if result.status == "BLOCKED":
                raise self._failure(context, "DIRECTOR_QA_BLOCKED", "DIR_QA", result.generation_attempts, (evidence.artifact_id,))
            output = self.io.derive("director.plan", context.run_id, inputs.parent_refs + (evidence,),
                {"schema_version": "bie.dir.grounded_plan/1.0.0", "lesson_id": inputs.lesson_id,
                 "plan": asdict(result.plan), "execution": asdict(result.execution),
                 "assessment_bindings": result.generated_assessment_bindings,
                 "execution_evidence_ref": asdict(evidence), "result_fingerprint": result.fingerprint()},
                stage_id="DIRECTOR", metadata=metadata)
            stage_result = StageExecutionResult([output.artifact_id], [evidence.artifact_id],
                ["DIRECTOR_COMPONENT_EXECUTED_REVIEW_REQUIRED"], metadata)
            self._complete(context, owner, execution_fingerprint, "SUCCEEDED", asdict(stage_result))
            return stage_result
        except StageExecutionFailure as failure:
            if claimed:
                self._complete(context, owner, execution_fingerprint, "FAILED", {
                    "diagnostics": failure.diagnostics, "evidence_refs": failure.evidence_refs,
                    "remediation_owner": failure.remediation_owner})
            raise
        except Exception as error:
            if isinstance(error, DirectingFailure):
                code, remediation, attempts = error.code, error.owner, error.attempts
            elif isinstance(error, IdempotencyError):
                code, remediation, attempts = "DIRECTOR_IDEMPOTENCY_CONFLICT", "INFRA", ()
            else:
                code, remediation, attempts = "DIRECTOR_" + phase + "_INVALID", "DIR_INPUTS" if phase == "INPUT" else "INFRA", ()
            failure = self._failure(context, code, remediation, attempts)
            if claimed:
                self._complete(context, owner, execution_fingerprint, "FAILED", {
                    "diagnostics": failure.diagnostics, "evidence_refs": failure.evidence_refs,
                    "remediation_owner": failure.remediation_owner})
            raise failure from None
