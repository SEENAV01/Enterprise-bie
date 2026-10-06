"""Versioned Section18 delegation to Task031 native composition, not an engine."""
from .knowledge_producer import KnowledgeProducerControlPlane
from bie.productization.math_evidence import PROFILE, profile_config
from bie.productization.math_slice import MathProducerService


class MathProducerControlPlane(KnowledgeProducerControlPlane):
    profile=PROFILE
    native_service=MathProducerService
    config_for=staticmethod(profile_config)
