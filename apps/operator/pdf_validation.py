"""Supervise the genuine source parser with bounded input/output/time.

OS memory/CPU limits live in the child. This is local resource containment, not
network isolation or a general executable sandbox. Never persist request bytes.
"""
from pathlib import Path
import hashlib
import os
import subprocess
import sys
import threading
from .contracts import require, strict_json, MAX_PDF_BYTES
from .process_limits import PdfProcessBudget
from .process_supervision import child_environment

CHILD = Path(__file__).with_name('pdf_validation_child.py')


def inspect_source(data, budget=None):
    require(type(data) is bytes and 0 < len(data) <= MAX_PDF_BYTES, 'invalid_source_size', 400)
    budget = PdfProcessBudget() if budget is None else budget
    require(type(budget) is PdfProcessBudget, 'pdf_process_budget_invalid', 400)
    # Explicit narrow environment. Do not propagate API/provider credentials,
    # PYTHONPATH, user-site settings or arbitrary execution configuration.
    env = child_environment()
    process = subprocess.Popen([sys.executable, '-I', '-B', str(CHILD),
                                str(budget.memory_bytes), str(budget.cpu_seconds)],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, env=env,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    output = bytearray()
    overflow = threading.Event()

    def read_output():
        while True:
            chunk = process.stdout.read(1024)
            if not chunk:
                return
            if len(output) + len(chunk) > 4096:
                overflow.set()
                try:process.kill()
                except ProcessLookupError:pass
                return
            output.extend(chunk)

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()

    def send_input():
        try:
            process.stdin.write(data)
            process.stdin.close()
        except (BrokenPipeError, OSError):
            pass

    writer = threading.Thread(target=send_input, daemon=True)
    writer.start()
    blocked = dict(status='BLOCKED', diagnostic_codes=['pdf_resource_or_worker_failed'],
                   page_count=None, native_text_pages=None)
    try:
        try:
            process.wait(timeout=budget.wall_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
            return blocked
        writer.join(timeout=5)
        reader.join(timeout=5)
        if process.returncode != 0 or overflow.is_set() or reader.is_alive() or writer.is_alive():
            return blocked
        result = strict_json(bytes(output), max_bytes=4096)
        if result.get('enforcement') not in ('LINUX_RLIMIT', 'WINDOWS_JOB_OBJECT'):
            return blocked
        if result.get('status') == 'INVALID' and set(result) == {'status', 'diagnostic_code', 'enforcement'}:
            require(result['diagnostic_code'] == 'pdf_validation_failed', 'pdf_child_contract_invalid')
            return dict(status='INVALID', diagnostic_codes=['pdf_validation_failed'],
                        page_count=None, native_text_pages=None)
        require(set(result) == {'status', 'source_hash', 'page_count', 'native_text_pages', 'enforcement'} and
                result['status'] == 'VALID' and result['source_hash'] == hashlib.sha256(data).hexdigest() and
                type(result['page_count']) is int and result['page_count'] > 0 and
                type(result['native_text_pages']) is int and 0 <= result['native_text_pages'] <= result['page_count'],
                'pdf_child_contract_invalid')
        return dict(status='VALID', diagnostic_codes=[], page_count=result['page_count'],
                    native_text_pages=result['native_text_pages'])
    except (ValueError, TypeError, OSError):
        return blocked
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        writer.join(timeout=5)
        reader.join(timeout=5)
        process.stdin.close()
        process.stdout.close()
