"""Task033 explicitly enabled Section18 delegation, not a second control plane."""
from .knowledge_producer import KnowledgeProducerControlPlane
from bie.productization.director_contract import PROFILE, profile_config, run_identity
from bie.productization.director_slice import DirectorProducerService


class DirectorProducerControlPlane(KnowledgeProducerControlPlane):
    profile = PROFILE
    native_service = DirectorProducerService
    config_for = staticmethod(profile_config)
    identity_for = staticmethod(run_identity)
