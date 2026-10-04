"""Private bounded source-inspection child. Never writes source PDF bytes.

Import canonical parser only AFTER OS limits apply. No provider credentials or
source titles are needed. Fixed safe output; parser warnings go to /dev/null.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from apps.operator.process_limits import PdfProcessBudget, enforce_current_process


def main():
    memory, cpu = map(int, sys.argv[1:3])
    enforcement = enforce_current_process(PdfProcessBudget(memory_bytes=memory, cpu_seconds=cpu))
    from bie.document_intelligence.real_pdf_runtime import inspect_real_pdf, RealPdfRuntimeError
    raw = sys.stdin.buffer.read(25 * 1024 * 1024 + 1)
    if not 0 < len(raw) <= 25 * 1024 * 1024:
        raise ValueError('source_size_invalid')
    try:
        inspection = inspect_real_pdf(raw)
        result = dict(status='VALID', source_hash=inspection.source_hash,
                      page_count=inspection.page_count, native_text_pages=inspection.text_pages)
    except RealPdfRuntimeError:
        result = dict(status='INVALID', diagnostic_code='pdf_validation_failed')
    result['enforcement'] = enforcement
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        # No traceback, exception text, PDF metadata, title, key or filesystem path.
        raise SystemExit(2)
