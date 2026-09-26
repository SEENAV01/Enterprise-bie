from dataclasses import replace
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest
from bie.game_engine.operations_engine.pipeline import _target, run_enterprise_session
from bie.game_engine.operations_engine.errors import GameOperationsError
from tests.hardening_h5.support import context_assets, request

class OutcomeScopeRegression(unittest.TestCase):
    def test_shared_objective_uses_selected_challenge_target(self):
        ctx,_=context_assets();game=ctx.document.experiences[0];level=game.levels[0];ch=level.challenges[0]
        other=replace(ch,challenge_id='challenge:other',learning=replace(ch.learning,mastery_target=.95,misconception_ids=()))
        doc=replace(ctx.document,experiences=(replace(game,levels=(replace(level,challenges=(ch,other)),)),))
        outcome=replace(request().outcomes[0],challenge_id=other.challenge_id)
        self.assertEqual(_target(doc,outcome),(.95,False))

    def test_scoped_and_unscoped_alias_of_one_attempt_rejected_before_write(self):
        ctx,assets=context_assets();game=ctx.document.experiences[0];level=game.levels[0];req=request();original=req.outcomes[0]
        req=replace(req,outcomes=(original,replace(original,game_id=game.game_id,level_id=level.level_id)))
        with TemporaryDirectory() as td:
            root=Path(td)/'session'
            with self.assertRaisesRegex(GameOperationsError,'DUPLICATE_OUTCOME'):
                run_enterprise_session(ctx,assets,root,req)
            self.assertFalse(root.exists())
