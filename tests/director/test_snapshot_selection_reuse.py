"""Operation-local reuse only; no cached validation or product-time probes."""
from dataclasses import replace
import unittest
from unittest.mock import patch

from qa_fixtures import case
from bie.director import qa_contract as qa
from bie.director.narration_annotations import selection


class SnapshotSelectionReuseTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = case(('A triangle has three sides.', 'A circle is round.')).snapshot
        self.u = self.snapshot.utterances[0]
        self.raw = dict(utterance_id=self.u.utterance_id, start_char=0,
                        end_char=len(self.u.text), quote=self.u.text)

    def reject(self, **change):
        with self.assertRaises((ValueError, TypeError)):
            selection(self.snapshot, dict(self.raw, **change))

    def test_default_selection_reconstructs_complete_snapshot_once(self):
        with patch.object(qa, 'snapshot_script', wraps=qa.snapshot_script) as rebuild:
            span = selection(self.snapshot, self.raw)
        self.assertEqual(rebuild.call_count, 1)
        self.assertEqual(span, qa.bind_span(self.snapshot, self.u.utterance_id))

    def test_public_bind_span_still_reconstructs_once_on_every_call(self):
        with patch.object(qa, 'snapshot_script', wraps=qa.snapshot_script) as rebuild:
            for _ in range(3): qa.bind_span(self.snapshot, self.u.utterance_id)
        self.assertEqual(rebuild.call_count, 3)

    def test_caller_index_does_not_elide_fresh_validation(self):
        index = qa.validate_snapshot(self.snapshot)
        with patch.object(qa, 'snapshot_script', wraps=qa.snapshot_script) as rebuild:
            actual = selection(self.snapshot, self.raw, index)
        self.assertEqual(rebuild.call_count, 1)
        self.assertEqual(actual.utterance_fingerprint, self.u.fingerprint())

    def test_no_cross_call_cache_after_in_place_snapshot_tamper(self):
        selection(self.snapshot, self.raw)
        object.__setattr__(self.snapshot, 'language', 'hi')
        for fn in (lambda: selection(self.snapshot, self.raw),
                   lambda: qa.bind_span(self.snapshot, self.u.utterance_id)):
            with self.assertRaises(ValueError): fn()

    def test_caller_index_cannot_authorize_stale_snapshot(self):
        index = qa.validate_snapshot(self.snapshot)
        with self.assertRaises(ValueError):
            selection(replace(self.snapshot, language='hi'), self.raw, index)

    def test_modified_unselected_utterance_is_rejected(self):
        modified = replace(self.snapshot.utterances[1], text='Invented fact.')
        snapshot = replace(self.snapshot, utterances=(self.u, modified))
        with self.assertRaises(ValueError): selection(snapshot, self.raw)

    def test_modified_draft_is_rejected(self):
        drafts = (replace(self.snapshot.drafts[0], text='Invented fact.'),) + self.snapshot.drafts[1:]
        with self.assertRaises(ValueError): selection(replace(self.snapshot, drafts=drafts), self.raw)

    def test_forged_selected_entry_is_rejected(self):
        index = qa.validate_snapshot(self.snapshot)
        index[self.u.utterance_id] = replace(self.u, text='Forged speech.')
        with self.assertRaises(ValueError): selection(self.snapshot, self.raw, index)

    def test_forged_unselected_entry_is_rejected(self):
        index = qa.validate_snapshot(self.snapshot)
        other = self.snapshot.utterances[1]
        index[other.utterance_id] = replace(other, text='Forged speech.')
        with self.assertRaises(ValueError): selection(self.snapshot, self.raw, index)

    def test_missing_or_extra_index_entries_are_rejected(self):
        for index in ({self.u.utterance_id:self.u},
                      dict(qa.validate_snapshot(self.snapshot), foreign=self.u), {}):
            with self.subTest(keys=tuple(index)), self.assertRaises(ValueError):
                selection(self.snapshot, self.raw, index)

    def test_index_equality_spoof_cannot_supply_authority(self):
        class Forged:
            def __eq__(self, other): return True
        with self.assertRaises(ValueError):
            selection(self.snapshot, self.raw, {u.utterance_id:Forged() for u in self.snapshot.utterances})
        class Mapping(dict):
            def __eq__(self, other): return True
        with self.assertRaises(ValueError): selection(self.snapshot, self.raw, Mapping())

    def test_invalid_index_types_are_rejected(self):
        for index in (True, [], (), 'index', 1):
            with self.subTest(kind=type(index).__name__), self.assertRaises(ValueError):
                selection(self.snapshot, self.raw, index)

    def test_unknown_and_invalid_utterance_ids_rejected(self):
        for uid in ('unknown', None, True, [], {}): self.reject(utterance_id=uid)

    def test_noninteger_and_boolean_boundaries_rejected(self):
        for key in ('start_char', 'end_char'):
            for value in (True, False, 1.0, None, '1', float('nan')): self.reject(**{key:value})

    def test_invalid_bounds_rejected(self):
        for start, end in ((-1, 4), (0, 0), (4, 4), (5, 3), (0, len(self.u.text)+1)):
            self.reject(start_char=start, end_char=end)

    def test_partial_words_rejected(self):
        self.reject(start_char=3, quote=self.u.text[3:])
        self.reject(end_char=4, quote=self.u.text[:4])

    def test_incorrect_quote_or_missing_keys_rejected(self):
        for quote in ('Different speech.', '', None, True): self.reject(quote=quote)
        for key in self.raw:
            raw = dict(self.raw); del raw[key]
            with self.assertRaises(ValueError): selection(self.snapshot, raw)
        self.reject(unknown='field')

    def test_span_revision_checks_remain_active(self):
        span = selection(self.snapshot, self.raw)
        with self.assertRaises(ValueError):
            qa.span_text(qa.validate_snapshot(self.snapshot), replace(span, utterance_fingerprint='sha256:'+'0'*64))

    def test_unicode_and_exact_quote_conserved(self):
        snapshot = case(('Café naïve — triangles have three sides.',)).snapshot
        u = snapshot.utterances[0]
        raw = dict(utterance_id=u.utterance_id, start_char=0, end_char=len(u.text), quote=u.text)
        span = selection(snapshot, raw)
        self.assertEqual(qa.span_text(qa.validate_snapshot(snapshot), span), u.text)

    def test_valid_partial_sentence_and_caller_index_conserve_identity(self):
        raw = dict(self.raw, start_char=2, end_char=10, quote='triangle')
        index = qa.validate_snapshot(self.snapshot)
        self.assertEqual(selection(self.snapshot, raw), selection(self.snapshot, raw, index))
        self.assertEqual(selection(self.snapshot, raw), qa.bind_span(self.snapshot, self.u.utterance_id, 2, 10))


if __name__ == '__main__': unittest.main()
