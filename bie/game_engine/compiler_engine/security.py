from __future__ import annotations
import re
from .errors import GameCompilerError
BANNED_SOURCE=(r'\beval\s*\(',r'\bnew\s+Function\b',r'\bFunction\s*\(',r'javascript:',r'http://',r'https://')
def validate_generated_source(source:str,*,allow_imports=False):
    for pat in BANNED_SOURCE:
        if re.search(pat,source,re.I):raise GameCompilerError('GAME_COMP_UNSAFE_GENERATED_SOURCE',pat)
    if not allow_imports and re.search(r'\bimport\s*\(',source):raise GameCompilerError('GAME_COMP_DYNAMIC_IMPORT_FORBIDDEN')
    return source
def csp_value():return "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
