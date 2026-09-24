#!/usr/bin/env python3
"""Internal fixed Linux-workload bootstrap. Not a general command endpoint."""
import sys
# The canonical adapter stages only the approved engine at this fixed mount.
sys.path.insert(0, '/engine')
from bie.audio.kernel_entry import main
if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
        print(getattr(exc, 'code', 'KERNEL_CHILD_FAILED'), file=sys.stderr)
        raise SystemExit(2)
