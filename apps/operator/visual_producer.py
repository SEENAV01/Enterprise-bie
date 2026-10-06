"""Versioned Task034 delegation through the existing Section18 control plane."""
from .knowledge_producer import KnowledgeProducerControlPlane
from contextlib import contextmanager
from bie.productization.visual_contract import PROFILE, profile_config, run_identity, code_identity_scope
from bie.productization.visual_slice import VisualProducerService


class VisualProducerControlPlane(KnowledgeProducerControlPlane):
    profile = PROFILE
    native_service = VisualProducerService
    config_for = staticmethod(profile_config)
    identity_for = staticmethod(run_identity)

    @contextmanager
    def native(self, principal, run_id, permission, **options):
        with code_identity_scope():
            with super().native(principal, run_id, permission, **options) as service:
                yield service
