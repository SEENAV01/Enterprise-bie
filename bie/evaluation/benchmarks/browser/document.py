"""Compile a bounded in-memory DOM shell from verified local assets.
No navigation or network permission is required. Classic scripts execute from
original snapshot bytes via the browser debugging API. ES module boot is not
simulated. The explicit canonical mode mirrors the canonical smoke-bundle path.
"""
from html.parser import HTMLParser
from html import escape
import posixpath,hashlib
from ..models import BenchmarkError,digest

def local_asset(entry,relative,assets):
    if type(relative) is not str or not relative or ':' in relative or relative.startswith(('/','\\')) or '?' in relative or '#' in relative:
        raise BenchmarkError('BROWSER_EXTERNAL_ASSET_UNSUPPORTED')
    name=posixpath.normpath(posixpath.join(posixpath.dirname(entry),relative))
    if name.startswith('../') or name not in assets:raise BenchmarkError('BROWSER_ASSET_MISSING')
    return name,assets[name].decode('utf-8')

class Shell(HTMLParser):
    def __init__(self,entry,assets,mode):
        super().__init__(convert_charrefs=False);self.entry=entry;self.assets=assets;self.mode=mode
        self.out=[];self.scripts=[];self.script_depth=0;self.inline=[];self.script_src=None;self.script_type=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='script':
            if self.script_depth:raise BenchmarkError('BROWSER_NESTED_SCRIPT')
            self.script_depth=1;self.inline=[];self.script_src=a.get('src');self.script_type=a.get('type')
            return
        if tag=='base' or tag in ('iframe','object','embed'):raise BenchmarkError('BROWSER_UNSUPPORTED_DOCUMENT_ELEMENT')
        if tag=='link' and a.get('rel')=='stylesheet':
            name,css=local_asset(self.entry,a.get('href'),self.assets)
            if '</style' in css.lower() or '@import' in css.lower() or 'url(' in css.lower():
                raise BenchmarkError('BROWSER_COMPLEX_STYLESHEET_UNSUPPORTED')
            self.out.append('<style>'+css+'</style>');return
        if tag=='link':raise BenchmarkError('BROWSER_LINK_PROFILE_UNSUPPORTED')
        if tag=='meta' and a.get('http-equiv','').lower()=='content-security-policy':
            # No weakening of network policy: context blocks ALL requests. The
            # source CSP is preserved in asset hashes but cannot grant permissions.
            return
        self.out.append(self.get_starttag_text())
    def handle_endtag(self,tag):
        if tag=='script' and self.script_depth:
            self.script_depth=0
            if self.script_type=='module':
                if self.mode!='CANONICAL_SMOKE_BUNDLE':raise BenchmarkError('BROWSER_ES_MODULE_BOOT_UNSUPPORTED')
                return
            if self.script_type not in (None,'','text/javascript','application/javascript'):raise BenchmarkError('BROWSER_SCRIPT_TYPE_UNSUPPORTED')
            if self.script_src:
                name,code=local_asset(self.entry,self.script_src,self.assets)
            else:name=self.entry+'#inline';code=''.join(self.inline)
            if code.strip():self.scripts.append({'path':name,'code':code,'sha256':hashlib.sha256(code.encode()).hexdigest()})
            return
        self.out.append('</'+tag+'>')
    def handle_startendtag(self,tag,attrs):
        if tag in ('script','iframe','object','embed'):raise BenchmarkError('BROWSER_UNSUPPORTED_DOCUMENT_ELEMENT')
        self.handle_starttag(tag,attrs)
    def handle_data(self,data):
        (self.inline if self.script_depth else self.out).append(data)
    def handle_entityref(self,name):self.handle_data('&'+name+';')
    def handle_charref(self,name):self.handle_data('&#'+name+';')
    def handle_decl(self,decl):self.out.append('<!'+decl+'>')
    def handle_comment(self,data):self.out.append('<!--'+data+'-->')

def prepare(candidate,assets):
    parser=Shell(candidate['entrypoint'],assets,candidate['load_mode'])
    parser.feed(assets[candidate['entrypoint']].decode('utf-8'));parser.close()
    if parser.script_depth:raise BenchmarkError('BROWSER_UNCLOSED_SCRIPT')
    if candidate['load_mode']=='CANONICAL_SMOKE_BUNDLE':
        if parser.scripts:raise BenchmarkError('BROWSER_CANONICAL_MIXED_BOOT_UNSUPPORTED')
        name='runtime/smoke-bundle.js'
        if name not in assets:raise BenchmarkError('BROWSER_NATIVE_SMOKE_BUNDLE_MISSING')
        code=assets[name].decode('utf-8');parser.scripts=[{'path':name,'code':code,'sha256':hashlib.sha256(code.encode()).hexdigest()}]
    if not parser.scripts:raise BenchmarkError('BROWSER_NO_EXECUTABLE_SCRIPT')
    shell=''.join(parser.out)
    return shell,parser.scripts,{'mode':candidate['load_mode'],'shell_sha256':hashlib.sha256(shell.encode()).hexdigest(),
        'scripts':[{'path':x['path'],'sha256':x['sha256']} for x in parser.scripts],
        'transport':'IN_MEMORY_ABOUT_BLANK_NO_NETWORK_NAVIGATION','url_reload_verified':False,
        'module_boot_verified':False,'csp_enforcement_verified':False}
