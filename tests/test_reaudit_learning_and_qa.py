from dataclasses import replace
from contextlib import closing
import json,re,sqlite3,unittest
from bie.game_engine.compiler_engine.fixtures import compiler_context
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.compiler_engine.contracts import hashlib_sha
from bie.game_engine.qa_engine.qa_002 import evaluate as rules_qa
from bie.game_engine.qa_engine.qa_006 import evaluate as feedback_qa
from bie.game_engine.operations_engine.mastery import PersistentMasteryStore
from bie.game_engine.operations_engine.telemetry import GovernedTelemetrySink
from bie.game_engine.operations_engine.contracts import TelemetryConsent

class ReauditLearningQA(unittest.TestCase):
    def bundle(self,path,field,mutate):
        ctx=compiler_context();game=ctx.document.experiences[0];level=game.levels[0]
        ctx=replace(ctx,document=replace(ctx.document,experiences=(replace(game,levels=(level,replace(level,level_id='level:2'))),)))
        b=compile_game(ctx);a=next(x for x in b.artifacts if x.path==path)
        match=re.search(r'(export const '+field+r' = )(\{.*\})( as const;)',a.content)
        data=json.loads(match[2]);mutate(data);content=a.content[:match.start(2)]+json.dumps(data)+a.content[match.end(2):]
        a2=replace(a,content=content,sha256=hashlib_sha(content))
        return ctx.document,replace(b,artifacts=tuple(a2 if x.path==path else x for x in b.artifacts))

    def test_qa_detects_missing_rule_in_one_of_two_levels(self):
        d,b=self.bundle('runtime/rules.ts','ruleMetadata',lambda x:x['rules'].pop())
        self.assertEqual(rules_qa(d,b).status.value,'fail')

    def test_qa_detects_changed_compiled_effect(self):
        d,b=self.bundle('runtime/rules.ts','ruleMetadata',lambda x:x['rules'][0]['effects'][0].update(value=99))
        self.assertEqual(rules_qa(d,b).status.value,'fail')

    def test_qa_detects_missing_feedback_in_one_of_two_levels(self):
        d,b=self.bundle('runtime/feedback.ts','feedbackProgram',lambda x:x['feedback'].pop())
        self.assertEqual(feedback_qa(d,b).status.value,'fail')

    def test_browser_succeeded_outcome_increases_mastery(self):
        with closing(sqlite3.connect(':memory:')) as db:
            record=PersistentMasteryStore(db).update('a'*64,'obj:test','succeeded',1,1,'event:1')
            self.assertGreater(record.estimate,0)

    def test_crash_replayed_learning_event_is_applied_once(self):
        with closing(sqlite3.connect(':memory:')) as db:
            s=PersistentMasteryStore(db);first=s.update('a'*64,'obj:test','success',1,1,'event:1')
            second=s.update('a'*64,'obj:test','success',1,1,'event:1')
            self.assertEqual(first,second);self.assertEqual(s.get('a'*64,'obj:test').version,1)

    def test_conflicting_learning_replay_rejected(self):
        with closing(sqlite3.connect(':memory:')) as db:
            s=PersistentMasteryStore(db);s.update('a'*64,'obj:test','success',1,1,'event:1')
            with self.assertRaises(Exception):s.update('a'*64,'obj:test','incorrect',1,1,'event:1')

    def test_nonterminal_outcome_cannot_be_scored_as_failure(self):
        with closing(sqlite3.connect(':memory:')) as db:
            s=PersistentMasteryStore(db)
            with self.assertRaises(Exception):s.update('a'*64,'obj:test','in_progress',1,1,'event:1')
            self.assertIsNone(s.get('a'*64,'obj:test'))

    def test_explicit_telemetry_replay_key_is_idempotent(self):
        with closing(sqlite3.connect(':memory:')) as db:
            s=GovernedTelemetrySink(db);consent=TelemetryConsent(True,'policy:test')
            event={'event':'mechanic_completed','challenge_id':'challenge:1','attempt_number':1}
            first=s.record('session:1',event,consent,('mechanic_completed',),event_key='outcome:1')
            second=s.record('session:1',event,consent,('mechanic_completed',),event_key='outcome:1')
            self.assertEqual(first,second);self.assertEqual(len(s.export('session:1')),1)
