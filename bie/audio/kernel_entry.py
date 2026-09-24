"""Fixed H4-R1 child entry. No command input, signing key, store or network API."""
from pathlib import Path
import os
import stat
import sys


def _read(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or not 0 < st.st_size <= limit:
            raise ValueError('KERNEL_CHILD_INPUT_BUDGET')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            value = stream.read(limit + 1)
        if len(value) != st.st_size:
            raise ValueError('KERNEL_CHILD_INPUT_CHANGED')
        return value
    finally:
        os.close(fd)


def main():
    if len(sys.argv) != 1:
        raise ValueError('KERNEL_CHILD_ARGUMENTS_FORBIDDEN')
    from bie.audio.common import strict_json
    from bie.audio.acoustic_contract import canonical, fields, sha, validate_job
    from bie.audio.acoustic_worker import measure
    request = strict_json(_read('/work/request.json', 4_000_000).decode())
    fields(request, ('operation', 'nonce', 'job', 'runtime'))
    if request['operation'] != 'AUDIO_ACOUSTIC_DIAGNOSTIC_V1':
        raise ValueError('KERNEL_CHILD_OPERATION')
    sha(request['nonce'])
    wav = _read('/work/source.wav', request['job']['policy']['max_source_bytes'])
    validate_job(request['job'], wav)
    result = measure(request['job'], wav, request['runtime'], Path('/work/output'))
    output = canonical({'operation': request['operation'], 'nonce': request['nonce'],
                        'measurement': result})
    if len(output) > 4_000_000:
        raise ValueError('KERNEL_CHILD_OUTPUT_BUDGET')
    with open('/work/output/result.json', 'xb') as stream:
        stream.write(output)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
        # No transcript, arbitrary filesystem error, native log or secret reflection.
        print(getattr(exc, 'code', 'KERNEL_CHILD_FAILED'), file=sys.stderr)
        raise SystemExit(2)
