#!/usr/bin/env python3
"""Generate explicitly synthetic narration inputs using the real pinned DIR producers."""
from pathlib import Path
import sys,json
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'dependency_snapshot'))
from bie.director.script_plan import ScriptSegment,build_script_plan
from bie.director.voiceover_generation import generate_voiceover
from bie.audio.lexicon import Lexeme
from bie.audio.acronym_pronunciation import AcronymRule
from bie.audio.symbol_pronunciation import standard_symbols
from bie.audio.segmentation import SegmentPolicy


def example(language='en',unresolved=False):
    content=(r'Dr. Rao reads \(\frac{x+2}{y}\). Keep the denominator nonzero. DNA is read as separate letters here.' if language=='en'
             else r'AI को अक्षर-अक्षर पढ़ें। समीकरण \(x^2+2=3\) को ध्यान से पढ़ें।')
    if unresolved:content='An unknown acronym XYZ needs a pronunciation decision.'
    seg=ScriptSegment('narration:1','scene:1','EXPLAIN','Synthetic pronunciation fixture, not a completed book lesson',('synthetic:audio-fixture:1',),('objective:exact-reading',))
    script=build_script_plan('lesson:audio-fixture',(seg,),'voice:unselected')
    draft=generate_voiceover(seg.segment_id,(content,),{content:seg.evidence_ids})
    entries=[Lexeme('lex:doctor','Dr.',language,'doctor',('synthetic:lexicon:1',))] if language=='en' else []
    rules=[AcronymRule('DNA' if language=='en' else 'AI',language,'LETTERS',('synthetic:lexicon:1',))]
    return {'schema_version':'bie.audio.input/1','lesson_id':script.lesson_id,'voice_profile':script.voice_profile,'language':language,
        'segments':[asdict(seg)],'drafts':[asdict(draft)],'segment_order':[seg.segment_id],
        'lexicon':{'version':'synthetic-lexicon/1','entries':[asdict(x) for x in entries]},
        'symbols':[asdict(x) for x in standard_symbols(language).rules],'acronyms':[asdict(x) for x in rules],
        'readings':[],'pauses':[],'policy':asdict(SegmentPolicy()),'domain':'technical-fixture'}

if __name__=='__main__':
    root=ROOT/'examples/audio';root.mkdir(parents=True,exist_ok=True)
    for name,language,review in (('english','en',False),('hindi','hi',False),('needs_review','en',True)):
        (root/(name+'.json')).write_text(json.dumps(example(language,review),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
