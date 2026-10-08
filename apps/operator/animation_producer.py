"""Task035 delegation through the existing Section18 operator control plane."""
from contextlib import contextmanager
from .knowledge_producer import KnowledgeProducerControlPlane
from bie.productization.animation_contract import PROFILE, profile_config, run_identity, code_identity_scope
from bie.productization.animation_slice import AnimationProducerService


class AnimationProducerControlPlane(KnowledgeProducerControlPlane):
    profile = PROFILE
    native_service = AnimationProducerService
    config_for = staticmethod(profile_config)
    identity_for = staticmethod(run_identity)

    @contextmanager
    def native(self, principal, run_id, permission, **options):
        with code_identity_scope():
            with super().native(principal, run_id, permission, **options) as service:
                yield service
