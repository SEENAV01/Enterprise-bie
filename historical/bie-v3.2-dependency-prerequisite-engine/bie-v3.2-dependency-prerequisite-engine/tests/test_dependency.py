import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from cycle_checker import check_graph
def test_cycle():
 assert check_graph([{"source":"a","target":"b"},{"source":"b","target":"c"}])["has_cycle"] is False
 assert check_graph([{"source":"a","target":"b"},{"source":"b","target":"a"}])["has_cycle"] is True
