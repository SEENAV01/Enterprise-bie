import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from ontology_extractor import classify_statement
def test_axes():
 assert classify_statement("Why does current flow because of potential difference?")=="why"
