"""Task032 seven-stage durable composition; Director validation only."""
import uuid
from bie.infrastructure.artifact_store import BlobRef
from bie.infrastructure.orchestrator import StageExecutionResult, StageExecutionFailure
from bie.director.director_artifacts import envelope_from_dict
from .math_slice import MathProducerService, STAGES as MATH_STAGES
from .math_evidence import verify_reasoning
from .contracts import require, ProducerError, digest, identifier, canonical
from .pedagogy_plan import PROFILE, SCHEMA, POLICY, profile_config, pedagogy_components, verify_components
from . import pedagogy_codec

STAGES = MATH_STAGES + ("PEDAGOGY",)


def run_identity(tenant, key):
    """Native ArtifactEnvelope requires UUID; old profile identities stay pinned."""
    identifier(tenant); identifier(key)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, canonical(
        dict(tenant=tenant, key=key, profile=PROFILE)).decode()))


def run_identity_valid(value):
    try:
        parsed = uuid.UUID(value)
        return str(parsed) == value and parsed.version == 5
    except (ValueError, TypeError, AttributeError):
        return False


class PedagogyProducerService(MathProducerService):
    stages = STAGES
    profile = PROFILE
    capability = "producer:" + PROFILE
    completion_stage = "PEDAGOGY"
    identity_for = staticmethod(run_identity)
    run_identity_valid = staticmethod(run_identity_valid)
    config_for = staticmethod(profile_config)
    downstream = tuple(s for s in MathProducerService.graph_for().stages if s not in STAGES)

    def record(self, run_id, artifact_id):
        # Canonical ArtifactEnvelope identities use ':'; legacy producer IDs do
        # not. Only this explicitly marked codec family is admitted here.
        if ":" not in artifact_id:
            return super().record(run_id, artifact_id)
        record = self.persistence.load_artifact(artifact_id)
        require(record.run_id == run_id and record.metadata.get("producer_codec") == "director-input-v1",
                "foreign_director_artifact")
        raw = self.cas.get_bytes(BlobRef(record.blob_algorithm, record.blob_digest, record.blob_size))
        from .contracts import strict_json
        envelope = envelope_from_dict(strict_json(raw))
        require(envelope.artifact_id == artifact_id and envelope.run_id == run_id and
                envelope.artifact_type == record.artifact_type and
                [r.artifact_id for r in envelope.parent_refs] == record.parent_artifact_ids,
                "director_codec_index_mismatch")
        return record

    def pedagogy_inputs(self, run_id, config):
        document, k, p, did, kid, khash, pid = self.upstream(run_id, config)
        mid, m = self.verified_math(run_id, config)
        rid, rr = self.stage_ref(run_id, "REASONING")
        require({kid, pid, mid} <= set(rr.parent_artifact_ids), "upstream_identity")
        attempt = self.persistence.load_run_state(run_id)["stages"]["REASONING"]["attempts"][-1]["attempt"]
        r = verify_reasoning(self.read(run_id, rid), k, p, m,
            self.pr_context(run_id, config, kid, khash, attempt), pid, mid)
        ids = dict(document=did, knowledge=kid, prerequisite=pid, math=mid, reasoning=rid)
        values = dict(document=document, knowledge=k, prerequisite=p, math=m, reasoning=r)
        hashes = {name: digest(value) for name, value in values.items()}
        require(all(self.record(run_id, ids[name]).blob_digest == hashes[name] for name in ids),
                "upstream_hash_mismatch")
        return document, k, p, m, r, ids, hashes

    def components(self, run_id, config, attempt):
        doc, k, p, m, r, ids, hashes = self.pedagogy_inputs(run_id, config)
        kwargs = dict(run_id=run_id, source_id=run_id + "-source", artifact_ids=ids,
                      artifact_hashes=hashes, attempt=attempt)
        value = pedagogy_components(doc, k, p, m, r, **kwargs)
        verify_components(value, doc, k, p, m, r, **kwargs)
        return value, (doc, k, p, m, r, ids, hashes)

    def executor(self, config, stage, lease):
        if stage != "PEDAGOGY":
            return super().executor(config, stage, lease)

        def execute(context):
            try:
                run = context.run_id
                value, upstream = self.components(run, config, context.attempt)
                doc, k, p, m, r, ids, hashes = upstream
                require(context.input_artifact_refs == [ids["reasoning"]], "upstream_identity")
                candidate = self.put(run, stage, "pedagogy.plan.candidates", value,
                                     list(ids.values()))
                envelope = pedagogy_codec.publish(self, run, doc, p, m, r, ids, value)
                pedagogy_codec.validate(self, run, envelope, doc, p, m, r, ids, value)
                output = self.put(run, stage, "pedagogy.plan", envelope,
                    list(ids.values()) + [candidate, envelope["artifact_id"]])
                receipt = dict(schema="bie.producer.stage-evidence/1", run_id=run, stage=stage,
                    profile=PROFILE, attempt=context.attempt, source_sha256=config["source_sha256"],
                    input_artifact_ids=context.input_artifact_refs,
                    input_sha256=[hashes["reasoning"]], upstream_artifact_ids=ids,
                    upstream_sha256=hashes, candidate_artifact_id=candidate,
                    output_artifact_id=output, output_sha256=self.record(run, output).blob_digest,
                    envelope_id=envelope["artifact_id"], envelope_hash=envelope["content_hash"],
                    policy=POLICY, schema_version=SCHEMA, validation="PASS",
                    grounding="EXACT_SOURCE_REASONING_BOUND", director_input_compatibility="PASS",
                    director_executed=False, fencing_epoch=lease.epoch,
                    evidence_kind="TECHNICAL_SOURCE_DERIVED", live_provider_executed=False,
                    academic_acceptance=False, learner_mastery_claimed=False, product_accepted=False)
                evidence = self.put(run, stage, "producer.evidence", receipt,
                    context.input_artifact_refs + [output], True)
                self.leases.assert_active(lease)
                return StageExecutionResult([output], [evidence])
            except StageExecutionFailure:
                raise
            except Exception as exc:
                code = exc.code if isinstance(exc, ProducerError) else "pedagogy_execution_failed"
                evidence = self.put(context.run_id, stage, "producer.failure",
                    dict(schema="bie.producer.failure/1", code=code, stage=stage,
                         attempt=context.attempt, product_accepted=False), evidence=True)
                raise StageExecutionFailure([code], [evidence], "PROD032") from None
        return execute

    def verified_pedagogy(self, run_id, tenant):
        config = self.configuration(run_id, tenant)
        aid, record = self.stage_ref(run_id, "PEDAGOGY")
        current = self.persistence.load_run_state(run_id)["stages"]["PEDAGOGY"]["attempts"][-1]
        expected, upstream = self.components(run_id, config, current["attempt"])
        doc, k, p, m, r, ids, hashes = upstream
        require(set(ids.values()) <= set(record.parent_artifact_ids), "upstream_identity")
        require(current["input_artifact_refs"] == [ids["reasoning"]], "upstream_identity")
        value = self.read(run_id, aid)
        require(value["artifact_id"] in record.parent_artifact_ids, "pedagogy_catalog_mismatch")
        inputs = pedagogy_codec.validate(self, run_id, value, doc, p, m, r, ids, expected)
        return aid, record, value, expected, inputs

    def director_inputs(self, run_id, tenant):
        """Actual canonical loader/validator only; no Director executor exists here."""
        return self.verified_pedagogy(run_id, tenant)[-1]

    def status(self, run_id, tenant):
        result = super().status(run_id, tenant)
        result["pedagogy"] = None
        if result["stages"]["PEDAGOGY"] == "SUCCEEDED":
            aid, record, value, components, inputs = self.verified_pedagogy(run_id, tenant)
            result["pedagogy"] = dict(artifact_id=aid, sha256=record.blob_digest,
                schema=SCHEMA, objective_count=len(components["objectives"]),
                unit_count=len(components["units"]), assessment_count=sum(
                    len(b["assessments"]) for b in components["bindings"]),
                misconception_plan_count=0, requires_review=True,
                director_compatible=True, learner_mastery_claimed=False,
                validation="PASS", evidence_kind="TECHNICAL_SOURCE_DERIVED")
        return result
