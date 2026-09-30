"""Section 18 product/operator read-model and control-plane adapters.

These adapters never replace canonical BIE engines. They bind product UI state to
persisted canonical jobs, queues, artifacts, evidence and graphs.
"""

from .context import OperatorContext
from .models import OperatorError, OperatorConflict, RunSnapshot

__all__ = ["OperatorContext", "OperatorError", "OperatorConflict", "RunSnapshot"]
