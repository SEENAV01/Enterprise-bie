"""Versioned Section18 delegation to the canonical Task032 producer slice."""
from .knowledge_producer import KnowledgeProducerControlPlane
from bie.productization.pedagogy_plan import PROFILE, profile_config
from bie.productization.pedagogy_slice import PedagogyProducerService, run_identity


class PedagogyProducerControlPlane(KnowledgeProducerControlPlane):
    profile = PROFILE
    native_service = PedagogyProducerService
    config_for = staticmethod(profile_config)
    identity_for = staticmethod(run_identity)
