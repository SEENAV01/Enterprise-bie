from pathlib import Path
from tempfile import TemporaryDirectory
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.build_runtime_engine.workspace import build_workspace

def built():
    td=TemporaryDirectory(prefix='bie-game-h3-');ctx,assets=build_inputs();ws=build_workspace(ctx,assets,Path(td.name));return td,ctx,assets,ws
