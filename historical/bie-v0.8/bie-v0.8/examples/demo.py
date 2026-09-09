import json
from pathlib import Path
from bie_m8.game import build_game,compile_game
x=json.loads(Path(__file__).with_name("game-input.json").read_text())
print(json.dumps(compile_game(build_game(x["targets"])),indent=2))
