#!/usr/bin/env python3
"""Inspect/resolve the safe paid-call journal without reading provider secrets.

This tool never retries a provider request. ``authorize-reissue`` records explicit
operator evidence so a later normal synthesis invocation may create one new attempt.
"""
from pathlib import Path
import argparse, json, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,required=True)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('list')
    inspect=sub.add_parser('inspect');inspect.add_argument('call_key')
    resolve=sub.add_parser('authorize-reissue');resolve.add_argument('call_key');resolve.add_argument('--resolution-ref',required=True);resolve.add_argument('--authority-revision',required=True)
    a=p.parse_args(argv)
    try:
        from bie.audio.neural_call_journal import PaidCallJournal
        journal=PaidCallJournal(a.cache/'paid-call-journal')
        if a.command=='list':result=journal.safe_states()
        elif a.command=='inspect':result=journal.safe_state(a.call_key)
        else:
            journal.authorize_reissue(a.call_key,resolution_ref=a.resolution_ref,authority_revision=a.authority_revision)
            result=journal.safe_state(a.call_key)
        print(json.dumps({'status':'OK','result':result,'remote_call_performed':False,'product_accepted':False},sort_keys=True))
        return 0
    except (ValueError,TypeError,OSError,KeyError):
        e=sys.exc_info()[1];code=getattr(e,'code','NEURAL_RECOVERY_INPUT_OR_IO_ERROR')
        print(json.dumps({'status':'BLOCKED','error_code':code,'remote_call_performed':False,'product_accepted':False},sort_keys=True),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
