"""GAME-AUD-026: replayable generated properties and minimized counterexamples."""
import json, math, random, unittest
from bie.game_engine.codec import loads, dumps
from bie.game_engine.expressions import Literal, Variable, Binary, Compare, BinaryOp, CompareOp, ValueType, evaluate
from bie.game_engine.state_engine.expression_runtime import evaluate_typed
from bie.game_engine.state_engine.snapshots import validate_values
from bie.game_engine.fixtures import sample_document
from bie.game_engine.build_runtime_engine.contracts import safe_relative
from bie.game_engine.errors import GameContractError

class H7CodecProperties(unittest.TestCase):
    def test_duplicate_key_is_never_last_value_wins(self):
        for key in ('x','$type','$enum','product_accepted'):
            wire='{'+json.dumps(key)+':0,'+json.dumps(key)+':1}'
            with self.subTest(key=key), self.assertRaises(GameContractError):loads(wire)

    def test_nonfinite_numbers_rejected_at_wire_boundary(self):
        for value in ('NaN','Infinity','-Infinity','1e999'):
            with self.subTest(value=value), self.assertRaises(GameContractError):loads('{"value":'+value+'}')

    def test_deep_input_is_bounded_with_contract_error(self):
        with self.assertRaises(GameContractError):loads('['*160+'0'+']'*160)

    def test_malformed_tags_never_escape_as_python_type_error(self):
        for tag in ('$enum','$type'):
            for value in ([],{},1,True,None):
                with self.subTest(tag=tag,value=value), self.assertRaises(GameContractError):loads(json.dumps({tag:value,'value':'bad'}))

    def test_generated_roundtrip_and_order_independence(self):
        rng=random.Random(1507001)
        for case in range(128):
            rows=[(str(i),[rng.randrange(-999,999),rng.choice(['Δx','حرکت','गति','🧪']),None]) for i in range(rng.randrange(1,10))]
            value=dict(rows);wire=dumps(value);rng.shuffle(rows)
            with self.subTest(case=case):
                self.assertEqual(loads(wire),value)
                self.assertEqual(dumps(dict(rows)),wire)

class H7ExpressionProperties(unittest.TestCase):
    def test_equality_does_not_evaluate_unselected_ordering_operators(self):
        for a,b in ((None,None),('x',2),(True,False),(None,0)):
            expr=Compare(CompareOp.EQ,Literal(a),Literal(b))
            with self.subTest(a=a,b=b):
                self.assertEqual(evaluate(expr,{}),a==b)
                self.assertEqual(evaluate_typed(expr,{},{}),a==b)

    def test_mixed_ordering_is_rejected_as_contract_error(self):
        for a,b in (('x',2),(1,None),(True,'text')):
            expr=Compare(CompareOp.LT,Literal(a),Literal(b))
            with self.subTest(a=a,b=b), self.assertRaises(GameContractError):evaluate_typed(expr,{},{})

    def test_generated_arithmetic_matches_independent_integer_identities(self):
        rng=random.Random(1507002)
        for case in range(256):
            x=rng.randint(-10000,10000);k=rng.randint(-100,100)
            # (x+k)^2 - (x-k)^2 = 4*x*k, independent expanded oracle.
            plus=Binary(BinaryOp.ADD,Variable('x'),Literal(k));minus=Binary(BinaryOp.SUB,Variable('x'),Literal(k))
            expr=Binary(BinaryOp.SUB,Binary(BinaryOp.MUL,plus,plus),Binary(BinaryOp.MUL,minus,minus))
            with self.subTest(case=case):
                self.assertEqual(evaluate(expr,{'x':x}),4*x*k)
                self.assertEqual(evaluate_typed(expr,{'x':x},{'x':ValueType.INTEGER}),4*x*k)

    def test_nonfinite_state_rejected_before_evaluation(self):
        model=sample_document().experiences[0].levels[0].state
        for value in (float('nan'),float('inf'),-float('inf')):
            with self.subTest(value=value), self.assertRaises(GameContractError):validate_values(model,{'x':value,'attempts':0})

class H7PathProperties(unittest.TestCase):
    def test_cross_platform_path_escapes_and_aliases_reject(self):
        for path in ('C:escape','C:/escape','a//b','a/./b','a/../b','../x','/x','a\\b','a\x00b','a/','a:stream'):
            with self.subTest(path=path), self.assertRaises(ValueError):safe_relative(path)

    def test_generated_safe_paths_preserve_exact_identity(self):
        rng=random.Random(1507003)
        for case in range(256):
            path='/'.join('asset-'+str(rng.randrange(100000)) for _ in range(rng.randrange(1,6)))+'.json'
            with self.subTest(case=case):self.assertEqual(safe_relative(path),path)
