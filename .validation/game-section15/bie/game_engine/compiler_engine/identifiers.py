import re
from .errors import GameCompilerError
def ts_identifier(prefix,value):
    # UTF-8 hex is reversible: punctuation-distinct IDs cannot collapse.
    raw=prefix+'_'+value.encode('utf-8').hex()
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',raw):raise GameCompilerError('GAME_COMP_IDENTIFIER',value)
    return raw
