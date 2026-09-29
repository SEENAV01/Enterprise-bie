"""Section16 H6: accessibility, governed repair, local recovery and test corpus."""
from .common import Binding, RepairScope, Change
from .accessibility import AccessibilityPolicy, evaluate_accessibility
from .repairs import source_proposal, contextual_proposal, code_proposal, prepare_for_controller
from .durable import LeasePolicy, LeaseJournal
from .corpus import CorpusPolicy, Suite, register, execute_registered
