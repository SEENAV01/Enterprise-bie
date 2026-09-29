"""Section16 H3: native evidence adapters and conservative assessment interfaces."""
from .common import Binding, Finding, Report
from .documents import DocumentPolicy, OCRRunner, inspect_pdf, verify_document, to_source_records
from .knowledge import KnowledgePolicy, ConceptFacet, native_claims, source_request, inspect_inventory
from .assessors import AssessorRegistry, AssessmentTask, Provider, TransportResult, TransientAssessorError
from .calibration import CalibrationPolicy, CriterionFloor, RaterIdentity, evaluate_calibration, evaluate_quality
from .readiness import ReadinessPolicy, evaluate_readiness
