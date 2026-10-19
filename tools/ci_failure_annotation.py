"""Print a failed CI job's evidence summary as GitHub annotations (Task 037B).

Job logs and artifacts of this repository cannot be downloaded from the cloud
workspace where the work is done, but run annotations can be read through the
REST API. After a failed step this script reads the job's evidence directories
and prints one bounded ``::error`` line per failing receipt: lane results,
failing test identities and the last exception line of each failure.

It only reads. It never changes evidence, test results or the job outcome.
"""
from pathlib import Path
import json, re, sys

MESSAGE_LIMIT = 3000
EXCEPTION = re.compile(r'^[A-Za-z_][\w.]*(?:Error|Exception|Exit|Failure|Interrupt)\b.*')


def escape(text):
    return text.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')


def escape_property(text):
    return escape(text).replace(':', '%3A').replace(',', '%2C')


def failing_tests(transcript, limit=8):
    """FAIL/ERROR blocks of a unittest transcript: identity and last exception line."""
    rows = []
    for block in re.split(r'(?m)^(?=(?:FAIL|ERROR): test)', transcript)[1:]:
        lines = block.splitlines()
        cause = ''
        for line in lines[1:]:
            if line.startswith('=' * 10):
                break
            if EXCEPTION.match(line):
                cause = line
        rows.append(f'{lines[0].strip()} :: {cause[:400]}')
    return rows[:limit], len(rows)


def read_json(path):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def tail(path, lines=6, chars=700):
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''
    return '\n'.join(text.strip().splitlines()[-lines:])[-chars:]


def summaries(root):
    messages = []
    for path in sorted(root.rglob('VALIDATION.json')):
        data = read_json(path)
        if not data or data.get('passed') is True:
            continue
        lanes = data.get('lanes') or []
        text = ['lanes: ' + ', '.join(f"{l.get('name')}={'pass' if l.get('passed') else 'FAIL'}"
                                      f"(exit {l.get('exit_code')}, {l.get('duration_s')}s)" for l in lanes)]
        if data.get('failure_type'):
            text.append(f"failure: {data['failure_type']}: {str(data.get('failure', ''))[:600]}")
        for lane in lanes:
            if not lane.get('passed'):
                text.append(f"{lane.get('name')} stderr tail:\n" + tail(path.parent / f"{lane.get('name')}.stderr.log"))
        messages.append((path.relative_to(root).as_posix(), '\n'.join(text)))
    for path in sorted(root.rglob('TEST_RESULT.json')):
        data = read_json(path)
        if not data or data.get('passed') is not False:
            continue
        counts = {k: data.get(k) for k in ('tests_run', 'failures', 'errors', 'skipped', 'skips') if k in data}
        text = [json.dumps(counts, sort_keys=True)]
        transcript = path.with_name('TEST_RESULT.txt')
        if transcript.is_file():
            rows, total = failing_tests(transcript.read_text(encoding='utf-8', errors='replace'))
            text += rows + ([f'... {total - len(rows)} more'] if total > len(rows) else [])
        messages.append((path.relative_to(root).as_posix(), '\n'.join(text)))
    for path in sorted(root.rglob('integrated_tests.json')):
        data = read_json(path)
        summary = (data or {}).get('summary') or {}
        if not data or summary.get('passed') is not False:
            continue
        failed = [r for r in data.get('results', []) if not r.get('passed')]
        text = [json.dumps({k: summary.get(k) for k in ('tests_run', 'failures', 'errors', 'skipped', 'failed_files')},
                           sort_keys=True)]
        text += [f"{r.get('path')} (failures {r.get('failures')}, errors {r.get('errors')})" for r in failed[:10]]
        messages.append((path.relative_to(root).as_posix(), '\n'.join(text)))
    return messages


def main(argv):
    if len(argv) < 2:
        print('usage: ci_failure_annotation.py TITLE EVIDENCE_DIR...', file=sys.stderr)
        return 2
    title, found = argv[0], 0
    for directory in argv[1:]:
        root = Path(directory)
        if not root.is_dir():
            continue
        for name, text in summaries(root):
            found += 1
            print(f'::error title={escape_property(title + " (" + name + ")")}::{escape(text[:MESSAGE_LIMIT])}', flush=True)
    if not found:
        print(f'::error title={escape_property(title)}::No failing evidence receipt found; see the job log.', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
