"""Differential checks of emitted code against the authoritative typed evaluator."""
import json,os,random,shutil,subprocess,tempfile,unittest
from pathlib import Path
from bie.game_engine.expressions import *
from bie.game_engine.compiler_engine.expression_codegen import compile_expr
from bie.game_engine.compiler_engine.errors import GameCompilerError
from bie.game_engine.state_engine.expression_runtime import evaluate_typed

class ExpressionRuntimeParity(unittest.TestCase):
    def emitted(self,cases):
        functions=[]
        for expr,state,types in cases:
            expression=compile_expr(expr,types)
            functions.append('(()=>{const state:Record<string,string|number|boolean|null>='+json.dumps(state)+';try{return {value:('+expression+')}}catch(e){return {error:String(e)}}})()')
        node=os.environ.get('BIE_NODE') or shutil.which('node');self.assertIsNotNone(node)
        with tempfile.TemporaryDirectory(prefix='bie-parity-') as td:
            p=Path(td)/'expressions.ts';p.write_text('console.log(JSON.stringify(['+',\n'.join(functions)+']));',encoding='utf-8')
            tsc_js=os.environ.get('BIE_TSC_JS')
            cmd=[node,'--preserve-symlinks','--preserve-symlinks-main',tsc_js] if tsc_js else [shutil.which('tsc')]
            self.assertIsNotNone(cmd[0])
            built=subprocess.run(cmd+['--strict','--target','ES2020','--module','commonjs','--noEmitOnError',str(p)],capture_output=True,text=True,timeout=60)
            self.assertEqual(built.returncode,0,built.stdout+built.stderr)
            p=p.with_suffix('.js')
            run=subprocess.run([node,'--preserve-symlinks','--preserve-symlinks-main',str(p)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr);return json.loads(run.stdout)

    def test_dynamic_zero_division_is_error_in_both_engines(self):
        expr=Binary(BinaryOp.DIV,Literal(5),Variable('d'));state={'d':0};types={'d':ValueType.NUMBER}
        with self.assertRaisesRegex(Exception,'GAME_EXPR_DIV_ZERO'):evaluate_typed(expr,state,types)
        self.assertIn('GAME_EXPR_DIV_ZERO',self.emitted([(expr,state,types)])[0].get('error',''))

    def test_boolean_operands_preserve_authoritative_eager_error(self):
        expr=Boolean(BoolOp.AND,(Literal(False),Compare(CompareOp.GT,Binary(BinaryOp.DIV,Literal(1),Variable('d')),Literal(0))))
        with self.assertRaisesRegex(Exception,'GAME_EXPR_DIV_ZERO'):evaluate_typed(expr,{'d':0},{'d':ValueType.NUMBER})
        self.assertIn('GAME_EXPR_DIV_ZERO',self.emitted([(expr,{'d':0},{'d':ValueType.NUMBER})])[0].get('error',''))

    def test_numeric_enum_preserves_primitive_identity(self):
        expr=Compare(CompareOp.EQ,Variable('choice'),Literal(2));case=(expr,{'choice':2},{'choice':ValueType.ENUM})
        self.assertEqual(self.emitted([case])[0]['value'],evaluate_typed(*case))

    def test_boolean_numeric_equality_matches_authoritative_semantics(self):
        cases=[(Compare(op,Literal(a),Literal(b)),{}, {}) for op in (CompareOp.EQ,CompareOp.NE) for a,b in ((True,1),(False,0),(True,2))]
        self.assertEqual([r['value'] for r in self.emitted(cases)],[evaluate_typed(*case) for case in cases])

    def test_mixed_arithmetic_rejects_before_emission(self):
        expr=Binary(BinaryOp.ADD,Literal(True),Literal(1))
        with self.assertRaisesRegex(Exception,'NUMERIC'):evaluate_typed(expr,{}, {})
        with self.assertRaises(GameCompilerError):compile_expr(expr)

    def test_generated_numeric_trees_match_typed_evaluation(self):
        rng=random.Random(150703);cases=[]
        for _ in range(512):
            a,b,c=[rng.randint(-50,50) for _ in range(3)]
            expr=Compare(rng.choice(tuple(CompareOp)),Binary(rng.choice((BinaryOp.ADD,BinaryOp.SUB,BinaryOp.MUL)),Variable('x'),Literal(b)),Literal(c))
            cases.append((expr,{'x':a},{'x':ValueType.INTEGER}))
        self.assertEqual([r['value'] for r in self.emitted(cases)],[evaluate_typed(*case) for case in cases])
