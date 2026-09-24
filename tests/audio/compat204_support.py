from dataclasses import replace
from bie.audio.compat204.contracts import Annotation, NarrationBlock, NarrationDocument, fingerprint

REFS=('synthetic:source/p1',)
OBJS=('objective:technical-fixture',)


def block(raw='The source is unchanged.', **kw):
    values=dict(block_id='u1',scene_id='scene1',segment_id='script1',voice_id='voice1',language='en',
        domain='physics',raw_text=raw,evidence_ids=REFS,objective_ids=OBJS,upstream_fingerprint=fingerprint('source'))
    values.update(kw)
    return NarrationBlock(**values)


def document(raw='The source is unchanged.', **kw):
    return NarrationDocument('doc1','lesson1',fingerprint('script'),(block(raw,**kw),))


def rule(surface='DNA', kind='acronym', mode='letters', spoken='', **kw):
    from bie.audio.compat204.pronunciation_lexicon import PronunciationRule
    values=dict(rule_id='rule:'+surface,revision='1',kind=kind,surface=surface,spoken=spoken,language='en',
        source_refs=('synthetic:lexicon/p1',),mode=mode)
    values.update(kw)
    return PronunciationRule(**values)


def annotation(raw, surface, kind, **kw):
    a=raw.index(surface)
    return Annotation(a,a+len(surface),surface,kind,source_refs=REFS,**kw)
