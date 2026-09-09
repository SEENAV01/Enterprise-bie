import json
from pathlib import Path
def test_schema_file(): assert json.loads((Path(__file__).parents[1]/"schemas/book-unit.json").read_text())["type"]=="object"
