"""Section16 animation QA: bounded checks, never automatic product acceptance."""
from .models import *
from .attestation import Review,ReviewKey,ReviewVerifier
from .evaluator import evaluate,evaluate_temporal,evaluate_motion,evaluate_alignment,verify_reports,AnimationResult
