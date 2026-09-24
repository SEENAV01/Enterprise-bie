"""Local CLI: python -m bie.audio request.json --output NEW_DIRECTORY.

Exit 0 = pronunciation text prepared, 2 = review required or invalid input.
Neither outcome claims generated/verified speech audio.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import argparse
import json
import os
import shutil
import sys
import tempfile
from .contracts import AudioError, canonical, document_from_dict, text_hash
from .narration_segmentation import SegmentationPolicy
from .pronunciation_lexicon import lexicon_from_dict
from .voiceover_preparation import prepare_voiceover, verify_preparation


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    tmp = None
    try:
        if args.request.is_symlink() or not args.request.is_file() or args.request.stat().st_size > 2_000_000:
            raise AudioError('REQUEST_FILE_INVALID')
        # Local publication must not replace an existing directory or follow a
        # declared symlink. This is not a hostile-filesystem security sandbox.
        if args.output.exists() or args.output.is_symlink() or any(p.is_symlink() for p in args.output.parents):
            raise AudioError('OUTPUT_EXISTS_OR_SYMLINK')
        def object_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise AudioError('DUPLICATE_JSON_KEY', key)
                result[key] = value
            return result
        request = json.loads(args.request.read_text('utf-8'), object_pairs_hook=object_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(AudioError('NONFINITE_JSON', value)))
        if type(request) is not dict or set(request) != {'document', 'lexicon', 'policy'}:
            raise AudioError('REQUEST_KEYS')
        doc, lex = document_from_dict(request['document']), lexicon_from_dict(request['lexicon'])
        if type(request['policy']) is not dict or set(request['policy']) != set(SegmentationPolicy.__dataclass_fields__):
            raise AudioError('POLICY_KEYS')
        policy = SegmentationPolicy(**request['policy'])
        plan = prepare_voiceover(doc, lex, policy)
        verify_preparation(plan, doc, lex)
        parent = args.output.parent
        if not parent.is_dir():
            raise AudioError('OUTPUT_PARENT_MISSING')
        tmp = Path(tempfile.mkdtemp(prefix='.bie-audio-', dir=parent))
        (tmp / 'REQUEST.json').write_text(canonical(request) + '\n', encoding='utf-8')
        (tmp / 'VOICEOVER_PREPARATION.json').write_text(canonical(plan.to_dict()) + '\n', encoding='utf-8')
        lines = ['AUDIO VO-001..005 — text preparation only; no audio generated.', '']
        for segment in plan.segments:
            lines.extend([f'[{segment.segment_id}] {segment.scene_id} / {segment.voice_id}',
                          'ORIGINAL: ' + segment.original_text, 'SPOKEN: ' + segment.spoken_text, ''])
        (tmp / 'SPOKEN_PREVIEW.txt').write_text('\n'.join(lines), encoding='utf-8')
        (tmp / 'OUTPUT_SHA256.json').write_text(canonical({p.name: text_hash(p.read_text('utf-8')) for p in sorted(tmp.iterdir())}) + '\n', encoding='utf-8')
        os.rename(tmp, args.output)
        tmp = None
        print(canonical({'status': plan.status, 'identity': plan.identity, 'segments': len(plan.segments),
                         'issues': len(plan.issues), 'audio_generated': False, 'product_accepted': False}))
        return 2 if plan.requires_review else 0
    except (AudioError, OSError, UnicodeError, ValueError, TypeError, RecursionError) as exc:
        print(canonical({'status': 'BLOCKED', 'error': str(exc), 'audio_generated': False}), file=sys.stderr)
        return 2
    finally:
        if tmp is not None:
            shutil.rmtree(tmp)


if __name__ == '__main__':
    raise SystemExit(main())
