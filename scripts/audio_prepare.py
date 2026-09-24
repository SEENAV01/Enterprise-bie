#!/usr/bin/env python3
"""Prepare realized DIR narration. No synthesis; JSON output is not an audio receipt."""
from __future__ import annotations
import argparse
from dataclasses import asdict
from pathlib import Path
import json,os,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
# Namespace packages allow canonical dependencies to live at a user-supplied repo root.
sys.path.insert(0,str(ROOT))
if '--standalone-fixture' in sys.argv:
    sys.path.append(str(ROOT/'dependency_snapshot'))
from bie.audio.common import AudioError, strict_json, exact_fields
from bie.audio.lexicon import Lexeme,build_lexicon
from bie.audio.symbol_pronunciation import SymbolRule,make_table
from bie.audio.acronym_pronunciation import AcronymRule,make_acronyms
from bie.audio.segmentation import SegmentPolicy,Pause
from bie.audio.preparation import ReadingRequest,prepare_narration
from bie.director.script_plan import ScriptSegment,build_script_plan,validate_script_plan
from bie.director.voiceover_generation import VoiceoverDraft
from bie.director.speech_timing import utterances_from_script


def read_request(data):
    keys=('schema_version','lesson_id','voice_profile','language','segments','drafts','segment_order','lexicon','symbols','acronyms','readings','pauses','policy','domain')
    exact_fields(data,keys)
    if data['schema_version']!='bie.audio.input/1':raise AudioError('INPUT_SCHEMA_VERSION')
    def tuple_fields(row,cls,names):
        exact_fields(row,tuple(cls.__dataclass_fields__))
        value=dict(row)
        for n in names:
            if type(value[n])is not list:raise AudioError('JSON_ARRAY_REQUIRED',n)
            value[n]=tuple(value[n])
        return cls(**value)
    def arr(name):
        v=data[name]
        if type(v)is not list:raise AudioError('JSON_ARRAY_REQUIRED',name)
        return v
    segments=tuple(tuple_fields(r,ScriptSegment,('evidence_ids','objective_ids')) for r in arr('segments'))
    drafts=tuple(tuple_fields(r,VoiceoverDraft,('evidence_ids','unsupported_claims')) for r in arr('drafts'))
    script=build_script_plan(data['lesson_id'],segments,data['voice_profile']);validate_script_plan(script)
    utterances=tuple(utterances_from_script(script,drafts,tuple(arr('segment_order')),data['language']))
    lex=data['lexicon'];exact_fields(lex,('version','entries'))
    if type(lex['entries'])is not list:raise AudioError('JSON_ARRAY_REQUIRED','entries')
    lexicon=build_lexicon(lex['version'],tuple(tuple_fields(x,Lexeme,('evidence_refs',)) for x in lex['entries']))
    symbols=make_table('input-symbols/1',tuple(tuple_fields(x,SymbolRule,('evidence_refs',)) for x in arr('symbols')))
    acronyms=make_acronyms('input-acronyms/1',tuple(tuple_fields(x,AcronymRule,('evidence_refs',)) for x in arr('acronyms')))
    requests=tuple(tuple_fields(x,ReadingRequest,()) for x in arr('readings'))
    pauses=tuple(tuple_fields(x,Pause,('source_refs',)) for x in arr('pauses'))
    policy=tuple_fields(data['policy'],SegmentPolicy,('abbreviations',))
    return utterances,dict(lexicon=lexicon,symbols=symbols,acronyms=acronyms,requests=requests,pauses=pauses,policy=policy,domain=data['domain'])


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--standalone-fixture',action='store_true',help='Explicitly use pinned DIR dependency snapshot for this standalone technical example');args=ap.parse_args()
    try:
        if args.output.exists():raise AudioError('OUTPUT_EXISTS')
        inputs,kw=read_request(strict_json(args.input.read_text(encoding='utf-8')))
        result=prepare_narration(inputs,**kw)
        value=asdict(result);value['preparation_fingerprint']=result.fingerprint()
        encoded=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        # Publish a complete file atomically, with exclusive destination creation.
        fd, temporary = tempfile.mkstemp(prefix='.audio-preparation-', dir=args.output.parent)
        try:
            with os.fdopen(fd,'wb') as f:
                f.write(encoded);f.flush();os.fsync(f.fileno())
            os.link(temporary,args.output,follow_symlinks=False)
        finally:
            Path(temporary).unlink(missing_ok=True)
        print(json.dumps({'output':str(args.output),'preparation_passed':result.preparation_passed,'audio_generated':False,'reviews':result.review_reasons,'scope':'STANDALONE_DEPENDENCY_FIXTURE' if args.standalone_fixture else 'CANONICAL_WORKSPACE'},ensure_ascii=False))
        return 0 if result.preparation_passed else 2
    except (AudioError,ValueError,OSError,TypeError) as exc:
        print(json.dumps({'error':str(exc),'audio_generated':False}),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
