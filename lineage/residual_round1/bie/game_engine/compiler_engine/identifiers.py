import re
from .errors import GameCompilerError
def ts_identifier(prefix,value):
    raw=prefix+'_'+re.sub(r'[^A-Za-z0-9_]+','_',value)
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',raw):raise GameCompilerError('GAME_COMP_IDENTIFIER',value)
    return raw
