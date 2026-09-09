from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from compiler import compile_pedagogy
assert compile_pedagogy([{'objective_id':'a'},{'objective_id':'b'}],[['a','b']])['quality_gate']['valid']
