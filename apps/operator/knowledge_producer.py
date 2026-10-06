"""Distinct trusted Section18 producer port; legacy HTTP/profile remains intact.

No new server, auth implementation, queue, run-store schema or CAS. Caller must
explicitly enable this profile and pass an existing authenticated principal.
Controls are intentionally fail-closed: this slice exposes no pretend in-flight
pause/cancel. The existing inspection controls and worker remain unchanged.
"""
from contextlib import contextmanager
import uuid
from bie.productization.contracts import PROFILE, profile_config, ProducerError
from bie.productization.durable_slice import KnowledgeProducerService, run_identity
from .contracts import private_path, ident, require


class KnowledgeProducerControlPlane:
    profile = PROFILE
    native_service = KnowledgeProducerService
    config_for = staticmethod(profile_config)
    identity_for = staticmethod(run_identity)

    def __init__(self, operator, *, enabled_profiles=()):
        self.operator = operator
        self.enabled = frozenset(enabled_profiles)
        require(self.enabled <= {self.profile}, "producer_profile_invalid")

    def authorize(self, principal, permission):
        self.operator.authorize(principal,permission)
        require(self.profile in self.enabled, "producer_profile_not_enabled",409)

    @contextmanager
    def native(self, principal, run_id, permission, **options):
        self.authorize(principal,permission);ident(run_id)
        root=private_path(self.operator.root,"runs",run_id)
        self.operator._verify_native_tree(root)
        native=self.native_service(root,self.operator.cas,
            authorize=lambda:self.authorize(principal,permission),**options)
        try:
            yield native
            self.authorize(principal,permission)
        finally:native.close()

    def admit(self, principal, source_id, key, *, provider=None, model=None, producer_config=None):
        self.authorize(principal,"create")
        self.authorize(principal,"worker")  # Explicit permission to this producer lane.
        require(producer_config is None or (provider is None and model is None),
                "producer_configuration_conflict")
        source=self.operator.source(principal,source_id)
        require(source["stored"] and source["validation"]["status"]=="VALID","source_not_valid")
        self.operator._raw_source(source)  # Authoritative digest/length/path validation.
        admitted=dict(source_id=source["source_id"],sha256=source["sha256"],
            size_bytes=source["byte_length"],media_type=source["media_type"],
            tenant=principal.tenant,privacy=source["source_privacy"],rights="LOCAL_PROCESSING_ONLY")
        config=producer_config if producer_config is not None else (
            self.config_for() if provider is None and model is None else self.config_for(provider,model))
        run_id=self.identity_for(principal.tenant,key)
        with self.operator.catalog.tx() as db:
            operation="prodop-"+uuid.uuid4().hex
            self.operator.catalog.reserve_worker(db,operation)
            with self.native(principal,run_id,"create") as native:
                native.admit(admitted,principal.tenant,key,config)
                result=native.status(run_id,principal.tenant)
            self.operator.catalog.event(db,principal.actor,"PRODUCER_ADMITTED",run_id,
                dict(profile=self.profile,source_sha256=source["sha256"]),tenant=principal.tenant,
                reservation=operation,final_reservation=True)
        return result

    def work_once(self, principal, run_id, **options):
        with self.operator.catalog.tx() as db:
            operation="prodop-"+uuid.uuid4().hex
            self.operator.catalog.reserve_worker(db,operation)
            with self.native(principal,run_id,"worker",**options) as native:
                result=native.work_once(run_id,principal.tenant)
            self.operator.catalog.event(db,principal.actor,"PRODUCER_STAGE_OUTCOME",run_id,
                dict(stages=result["stages"],slice_complete=result["slice_complete"]),tenant=principal.tenant,
                reservation=operation,final_reservation=True)
        return result

    def status(self, principal, run_id):
        with self.native(principal,run_id,"read") as native:
            return native.status(run_id,principal.tenant)

    def recover(self, principal, run_id):
        self.authorize(principal,"admin_recover")
        with self.operator.catalog.tx() as db:
            operation="prodop-"+uuid.uuid4().hex
            self.operator.catalog.reserve_worker(db,operation)
            with self.native(principal,run_id,"worker") as native:
                result=native.recover(run_id,principal.tenant)
            self.operator.catalog.event(db,principal.actor,"PRODUCER_RECOVERED",run_id,
                dict(stages=result["stages"]),tenant=principal.tenant,
                reservation=operation,final_reservation=True)
        return result

    def control(self, principal, run_id, action):
        self.authorize(principal,"control")
        self.status(principal,run_id)
        raise ProducerError("producer_control_not_supported")
