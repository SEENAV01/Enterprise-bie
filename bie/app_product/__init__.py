"""Section 18 product/operator application layer.

This package projects existing canonical BIE runtime state for product/operator
surfaces. It does not replace canonical engines, persistence, queues or QA.
"""

from .contracts import (
    AppProductError, InvalidSource, ControlConflict, ProjectionError, GraphViewError,
    SourceValidation, RunView, RunTimeline, FailureView, ControlReceipt,
    GraphNode, GraphEdge, GraphView,
)
from .source_validation import validate_source, render_source_validation_html
from .service import OperatorService
from .graph_view import concept_graph_view, prerequisite_graph_view, render_graph_html

__all__ = [
    "AppProductError", "InvalidSource", "ControlConflict", "ProjectionError", "GraphViewError",
    "SourceValidation", "RunView", "RunTimeline", "FailureView", "ControlReceipt",
    "GraphNode", "GraphEdge", "GraphView",
    "validate_source", "render_source_validation_html", "OperatorService",
    "concept_graph_view", "prerequisite_graph_view", "render_graph_html",
]
