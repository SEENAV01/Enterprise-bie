from .contracts import *

def run_game_qa(*args,**kwargs):
    from .pipeline import run_game_qa as run
    return run(*args,**kwargs)
