#!/usr/bin/env python3
"""Deterministic synthetic examples; no book-ingestion or source-truth claim."""
from dataclasses import asdict
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'dependency_snapshot'))
from build_audio_example import example
from audio_prepare import read_request
from bie.audio.multilingual_terms import LanguageTerm
from bie.audio.compat204.contracts import from_director
from bie.audio.compat204.pronunciation_lexicon import Lexicon
from bie.audio.compat204.narration_segmentation import SegmentationPolicy

def main():
    out=ROOT/'examples/audio_batch002';out.mkdir(exist_ok=True)
    def write(name,data): (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    english=example('en');english['pauses']=[{'utterance_id':'narration:1','offset':len(english['drafts'][0]['text']),
        'milliseconds':400,'source_refs':['synthetic:requested-pause']}]
    write('english.json',english);write('hindi.json',example('hi'))
    mixed=example('hi');mixed['drafts'][0]['text']='यह photosynthesis का उदाहरण है। यह केवल आवाज़ की तकनीकी जाँच है।'
    write('mixed.json',mixed)
    utterances,_=read_request(json.loads(json.dumps(mixed)));u=utterances[0];a=u.text.index('photosynthesis')
    term=LanguageTerm(u.utterance_id,u.fingerprint(),a,a+14,'photosynthesis','photosynthesis','en',('synthetic:language-decision',),'term:photosynthesis')
    write('mixed_terms.json',[asdict(term)])
    older=example('en');older['drafts'][0]['text']=r'Read the sum carefully: \(\sum_{i=1}^{n}{i}\). The lower and upper limits remain explicit.'
    utterances,_=read_request(json.loads(json.dumps(older)))
    doc=from_director(utterances,document_id='compat:lesson',lesson_id='lesson:audio-fixture',expected_script_fingerprint=utterances[0].script_fingerprint,
        domains={u.utterance_id:'math' for u in utterances})
    write('compat204.json',{'document':asdict(doc),'lexicon':asdict(Lexicon('compat:empty','1',())), 'policy':asdict(SegmentationPolicy())})
    write('review_required.json',example('en',True))

if __name__=='__main__':main()
