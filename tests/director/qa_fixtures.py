"""Small controlled source fixtures, never real-book or benchmark evidence."""
import hashlib
from types import SimpleNamespace
from bie.director.script_plan import ScriptSegment, build_script_plan
from bie.director.voiceover_generation import VoiceoverDraft
from bie.director.qa_contract import (snapshot_script, bind_span, ScriptClaim,
                                     SourcePage, SourcePassage, SourceCatalog)


def case(texts=("A triangle has three straight sides.",), source_texts=None,
         scene_ids=None, language="en", shared=False):
    source_texts = tuple(source_texts if source_texts is not None else texts)
    pages, passages, source_data = [], [], []
    for i, text in enumerate(source_texts, 1):
        data = text.encode("utf-8")
        p = SourcePage(f"page{i}", f"source{i}", "sha256:" + hashlib.sha256(data).hexdigest(),
                       1, text, "controlled-utf8/1")
        pages.append(p)
        passages.append(SourcePassage(f"e{i}", p.page_id, p.fingerprint(), "paragraph1", 0, len(text), text))
        source_data.append((p.source_id, data))
    segs, drafts = [], []
    for i, text in enumerate(texts, 1):
        sid = scene_ids[i-1] if scene_ids else "scene1"
        evidence = ("e1",) if shared else (f"e{i}",)
        segs.append(ScriptSegment(f"u{i}", sid, "EXPLAIN", "Explain grounded concept", evidence, ("o1",)))
        drafts.append(VoiceoverDraft(f"u{i}", text, evidence, (), False))
    script = build_script_plan("lesson1", segs, "clear")
    snapshot = snapshot_script(script, tuple(drafts), tuple(s.segment_id for s in segs), language)
    claims = tuple(ScriptClaim(f"c{i}", bind_span(snapshot, u.utterance_id), "FACT", u.evidence_ids)
                   for i, u in enumerate(snapshot.utterances, 1))
    return SimpleNamespace(snapshot=snapshot, claims=claims,
        catalog=SourceCatalog(tuple(pages), tuple(passages)), source_data=tuple(source_data))


def codes(result):
    return {f.code for f in result.findings}
