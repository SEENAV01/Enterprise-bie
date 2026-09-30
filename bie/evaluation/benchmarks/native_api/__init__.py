"""Local canonical BenchmarkAPI binding; never an acceptance authority."""
from .admission import Admission, context
from .service import Service
__all__ = ['Admission', 'Service', 'context']
