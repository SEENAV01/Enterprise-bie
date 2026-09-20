"""Verify installed system-fallback glyph coverage, with hashes, never font copies.

This is a bounded Fontconfig+FreeType Linux preflight. Browser font readiness is
separately observed. Coverage is not multilingual shaping/translation expertise.
"""
import os,subprocess,unicodedata
from pathlib import Path
from .qa_common import CompilerQAError,digest
from .installed_toolchain import file_hash

def system_font_coverage(texts, *, family='sans-serif',max_codepoints=1024):
    if family not in {'sans-serif','serif','monospace'}:raise CompilerQAError('FONT_FAMILY_PROFILE_UNSUPPORTED')
    if not isinstance(texts,(tuple,list)) or len(texts)>4096 or any(not isinstance(t,str) or len(t)>100000 for t in texts):raise CompilerQAError('FONT_TEXT_BUDGET')
    chars=sorted({ord(c) for t in texts for c in t if not c.isspace() and unicodedata.category(c) not in {'Cf','Cc'}})
    if any(0xD800<=c<=0xDFFF for c in chars):raise CompilerQAError('FONT_INVALID_UNICODE')
    if len(chars)>max_codepoints:raise CompilerQAError('FONT_COVERAGE_BUDGET_NO_SAMPLING')
    from matplotlib.ft2font import FT2Font
    files={};rows=[];faces={}
    for cp in chars:
        r=subprocess.run(['/usr/bin/fc-match','-f','%{file}|%{index}\n',family+':charset='+format(cp,'x')],
                         env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent','LANG':'C.UTF-8'},capture_output=True,text=True,timeout=5)
        if r.returncode or len(r.stdout)>65536 or len(r.stdout.splitlines())!=1:raise CompilerQAError('FONTCONFIG_LOOKUP_BLOCKED')
        value,index=r.stdout.strip().rsplit('|',1);p=Path(value).resolve()
        if not p.is_absolute() or not p.is_file() or index!='0':raise CompilerQAError('FONT_FACE_PROFILE_UNSUPPORTED')
        key=str(p)
        if key not in faces:
            h,n=file_hash(p)
            if n>64*1024**2:raise CompilerQAError('FONT_FILE_BUDGET')
            faces[key]=FT2Font(key);files[key]={'sha256':h,'bytes':n,'basename':p.name,'face_index':0}
        glyph=faces[key].get_char_index(cp)
        rows.append({'codepoint':f'U+{cp:04X}','font_sha256':files[key]['sha256'],'glyph_present':glyph!=0 and unicodedata.category(chr(cp))!='Cn'})
    for name,r in files.items():
        if file_hash(name)[0]!=r['sha256']:raise CompilerQAError('FONT_CHANGED_DURING_COVERAGE')
    return {'schema_version':'bie.font-coverage.v1','family_profile':family,'passed':all(r['glyph_present'] for r in rows),
            'codepoints':rows,'font_identities':sorted(files.values(),key=lambda r:r['sha256']),
            'input_sha256':digest(texts),'fontconfig_sha256':file_hash('/usr/bin/fc-match')[0],
            'scope':'INSTALLED_SYSTEM_FALLBACK_GLYPH_COVERAGE_NOT_BROWSER_SHAPING_PROOF','accepted':False}

def source_texts(raw):
    """Required literal strings in source elements, dynamic states and narration.
    LaTeX math is independently typeset and its own selected fonts are hashed.
    """
    out=[]
    def walk(v):
        if isinstance(v,str):out.append(v)
        elif isinstance(v,dict):
            for k,x in v.items():
                if k not in {'source_refs','reasoning_refs','expression','public_path','sha256','schema_version'}:walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
    for e in raw['elements']:walk(e.get('props',{}));walk(e.get('alt_text',''))
    cfg=raw.get('metadata',{}).get('compiler_h6',{})
    walk(cfg.get('initial_state',{}));walk(cfg.get('narration_texts',{}))
    for ev in raw.get('events',[]):walk(ev.get('payload',{}).get('value'))
    return out
