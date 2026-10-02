"""One actual bounded worker process; never automatic retry/reconciliation."""
from pathlib import Path
import os
import sys
from .contracts import ident, require, strict_json, OperatorError
from .process_limits import PdfProcessBudget
from .process_supervision import child_environment, supervise

CHILD = Path(__file__).with_name('pdf_worker_child.py')


def execute_worker(root, run_id, budget=None):
    ident(run_id)
    budget = PdfProcessBudget() if budget is None else budget
    require(type(budget) is PdfProcessBudget, 'pdf_process_budget_invalid', 400)
    env = child_environment()
    env['BIE_OPERATOR_TOKEN'] = os.environ.get('BIE_OPERATOR_TOKEN', '')
    outcome = supervise([sys.executable, '-I', '-B', str(CHILD), '--data-root', str(Path(root).absolute()),
                         '--run-id', run_id, '--memory', str(budget.memory_bytes),
                         '--cpu', str(budget.cpu_seconds)], env, budget)
    require(outcome.completed and outcome.exit_code == 0, 'worker_process_failed', 503)
    try:
        envelope = strict_json(outcome.output, 4096)
        require(type(envelope) is dict and set(envelope) == {'enforcement', 'result'} and
                envelope['enforcement'] in ('LINUX_RLIMIT', 'WINDOWS_JOB_OBJECT'), 'worker_contract_invalid')
        result = envelope['result']
        require(type(result) is dict and {'outcome', 'dispatched'} <= set(result) <=
                {'outcome', 'dispatched', 'job_id', 'task_id'} and type(result['dispatched']) is bool and
                result['outcome'] in ('ACKED', 'FAILED', 'EMPTY', 'PAUSED', 'CANCELLED', 'TERMINAL'),
                'worker_contract_invalid')
        for key in ('job_id', 'task_id'):
            if key in result:ident(result[key])
        return result
    except (ValueError, TypeError, KeyError):
        raise OperatorError('worker_contract_invalid', 503) from None
