import ast, pathlib, unittest
from bie.game_engine.strategy_engine.contracts import StrategyKind
from bie.game_engine.strategy_engine.selector import ASSESSORS
class Batch02ArchitectureTests(unittest.TestCase):
    def test_nine_strategy_modules_registered(self):self.assertEqual(set(ASSESSORS),set(StrategyKind))
    def test_no_eval_exec_compile_import_calls(self):
        root=pathlib.Path(__file__).resolve().parents[1]/'bie/game_engine/strategy_engine';bad=[]
        for p in root.glob('*.py'):
            tree=ast.parse(p.read_text())
            for n in ast.walk(tree):
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'eval','exec','compile','__import__'}:bad.append((p.name,n.func.id,n.lineno))
        self.assertEqual(bad,[])
    def test_strategy_files_are_independent_modules(self):
        root=pathlib.Path(__file__).resolve().parents[1]/'bie/game_engine/strategy_engine'
        expected={'retrieval.py','manipulation.py','simulation.py','prediction.py','diagnostic.py','timeline.py','map_strategy.py','equation.py','causal_system.py'}
        self.assertTrue(expected <= {p.name for p in root.glob('*.py')})
    def test_product_acceptance_not_true_literal(self):
        root=pathlib.Path(__file__).resolve().parents[1]/'bie/game_engine/strategy_engine';self.assertFalse(any('product_accepted=True' in p.read_text().replace(' ','') for p in root.glob('*.py')))
if __name__=='__main__':unittest.main()
