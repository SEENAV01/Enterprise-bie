"""Section 16 narrative/script/timing/fidelity QA. Local checks are not acceptance."""
from .models import (Scene, Beat, Route, Transition, Promise, TermIntroduction,
                     SpokenForm, ConditionWitness, FidelityMapping, DirectorRequest,
                     SceneRequirement, RouteRequirement, TermRequirement, FacetRequirement,
                     TimingConstraint, PacingLimits, DirectorPolicy)
from .attestation import Review, ReviewKey, ReviewVerifier
from .evaluator import (DirectorResult, evaluate, verify_reports, evaluate_narrative,
                        evaluate_script, evaluate_pacing, evaluate_source_fidelity)
