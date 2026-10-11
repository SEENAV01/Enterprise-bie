"""Task036 profile delegates through the existing Section18 operator authority."""
from contextlib import contextmanager
from .knowledge_producer import KnowledgeProducerControlPlane
from bie.productization.scene_ir_contract import PROFILE, profile_config, run_identity, code_identity_scope
from bie.productization.scene_ir_slice import SceneIRProducerService


class SceneIRProducerControlPlane(KnowledgeProducerControlPlane):
    profile = PROFILE
    native_service = SceneIRProducerService
    config_for = staticmethod(profile_config)
    identity_for = staticmethod(run_identity)

    @contextmanager
    def native(self, principal, run_id, permission, **options):
        with code_identity_scope():
            with super().native(principal, run_id, permission, **options) as service:
                yield service
