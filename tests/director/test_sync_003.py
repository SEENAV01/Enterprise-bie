import unittest
from dataclasses import replace
from bie.director.equation_narration_sync import *
from sync_fixtures import equation_case,binding


class EquationSyncTests(unittest.TestCase):
    def test_original_derivation_steps_and_token_highlight(self):
        c,v,states,rows=equation_case()
        h=EquationIntent(binding(c,'highlight','u1',0,2),'v','q1',states[1].fingerprint(),'HIGHLIGHT_TOKEN',('x',))
        p=sync_equation_narration(c,v,states,rows+(h,))
        self.assertFalse(p.issues)
        cue=next(c for c in p.cues if c.kind=='HIGHLIGHT_TOKEN')
        self.assertEqual(dict(cue.parameters)['token_spans'],(('x',0,1,'x'),))
        self.assertEqual(dict(cue.parameters)['source_step_fingerprint'],fingerprint(states[1].step))

    def test_token_requires_current_visible_equation_state(self):
        c,v,states,rows=equation_case()
        h=EquationIntent(binding(c,'highlight','u1'),'v','q1',states[1].fingerprint(),'HIGHLIGHT_TOKEN',('x',))
        p=sync_equation_narration(c,v,states,(rows[0],h))
        self.assertIn('TOKEN_HIGHLIGHT_WITHOUT_ACTIVE_STATE',{i.code for i in p.issues})
        self.assertIn('MISSING_EQUATION_DISPLAY',{i.code for i in p.issues})

    def test_token_revision_and_expression_edits_invalidate_old_request(self):
        c,v,states,rows=equation_case()
        changed=replace(states[0],step=replace(states[0].step,expression='y = one'))
        with self.assertRaises(ValueError): sync_equation_narration(c,v,(changed,states[1]),rows)

    def test_wrong_narration_step_binding_rejected(self):
        c,v,states,rows=equation_case()
        wrong=replace(rows[0],binding=binding(c,'wrong','u1'))
        with self.assertRaises(ValueError): sync_equation_narration(c,v,states,(wrong,rows[1]))

    def test_unknown_tokens_and_bad_expression_spans_rejected(self):
        c,v,states,rows=equation_case()
        h=EquationIntent(binding(c,'h'),'v','q0',states[0].fingerprint(),'HIGHLIGHT_TOKEN',('unknown',))
        with self.assertRaises(ValueError): sync_equation_narration(c,v,states,rows+(h,))
        for token in (EquationToken('x',0,99),EquationToken('x',True,1),EquationToken('x',1,2)):
            with self.subTest(token=token),self.assertRaises(ValueError):
                sync_equation_narration(c,v,(replace(states[0],tokens=(token,)),states[1]),rows)

    def test_step_reordering_requires_explicit_revisit(self):
        c,v,states,rows=equation_case()
        swapped=(replace(states[0],step=replace(states[0].step,index=2)),replace(states[1],step=replace(states[1].step,index=1)))
        r=tuple(replace(row,state_fingerprint=s.fingerprint()) for row,s in zip(rows,swapped))
        p=sync_equation_narration(c,v,swapped,r)
        self.assertIn('EQUATION_STEP_ORDER',{i.code for i in p.issues})
        reviewed=sync_equation_narration(c,v,swapped,(r[0],replace(r[1],allow_revisit=True)))
        self.assertFalse(reviewed.issues)

    def test_source_evidence_and_duplicate_step_ids_rejected(self):
        c,v,states,rows=equation_case()
        bad=replace(states[0],step=replace(states[0].step,evidence_ids=('other',)))
        with self.assertRaises(ValueError): sync_equation_narration(c,v,(bad,states[1]),rows)
        with self.assertRaises(ValueError): sync_equation_narration(c,v,(states[0],states[0]),rows)

    def test_definition_and_intent_order_do_not_change_fingerprint(self):
        c,v,states,rows=equation_case()
        a=sync_equation_narration(c,v,states,rows)
        b=sync_equation_narration(c,v,reversed(states),(r for r in reversed(rows)))
        self.assertEqual(a.fingerprint(),b.fingerprint())

    def test_math_acceptance_not_inferred_from_aligned_steps(self):
        c,v,states,rows=equation_case(); p=sync_equation_narration(c,v,states,rows)
        self.assertFalse(p.accepted)
        self.assertIn('EQUATION_SEMANTICS_NOT_PROVEN_BY_SYNCHRONIZATION',p.review_reasons)
