"""Versioned control-plane delegation; no second auth/queue/operator engine."""
import uuid
from bie.productization.pr_reasoning import PROFILE, profile_config
from bie.productization.reasoning_slice import ReasoningProducerService
from .knowledge_producer import KnowledgeProducerControlPlane


class ReasoningProducerControlPlane(KnowledgeProducerControlPlane):
    profile=PROFILE
    native_service=ReasoningProducerService
    config_for=staticmethod(profile_config)

    def continue_completed(self,principal,run_id):
        self.authorize(principal,"create");self.authorize(principal,"worker")
        with self.operator.catalog.tx() as db:
            operation="prodop-"+uuid.uuid4().hex
            self.operator.catalog.reserve_worker(db,operation)
            with self.native(principal,run_id,"create") as native:
                native.continue_completed(run_id,principal.tenant)
                result=native.status(run_id,principal.tenant)
            self.operator.catalog.event(db,principal.actor,"PRODUCER_CONTINUED",run_id,
                dict(profile=PROFILE,source_sha256=result["source_sha256"]),tenant=principal.tenant,
                reservation=operation,final_reservation=True)
        return result
