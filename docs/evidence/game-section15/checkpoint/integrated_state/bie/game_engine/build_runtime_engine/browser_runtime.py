from __future__ import annotations
from pathlib import Path
from urllib.parse import urlparse
from html import unescape
import hashlib,json
from .contracts import BrowserEvidence,BuildPolicy
from .errors import GameBuildError
from .sandbox import sandboxed_chromium,sandbox_evidence

def browser_smoke(dist,policy=BuildPolicy()):
    policy.validate();dist=Path(dist);html=(dist/'runtime/index.html').read_text();decoded_html=unescape(html);headers=json.loads((dist/'runtime/security-headers.json').read_text());bundle=(dist/'runtime/smoke-bundle.js').read_text();bundle_sha=hashlib.sha256(bundle.encode()).hexdigest()
    if 'Content-Security-Policy' not in html or "connect-src 'none'" not in decoded_html or "frame-ancestors 'none'" not in headers.get('Content-Security-Policy','') or 'data-slide-deck="false"' not in html:raise GameBuildError('GAME_BUILD_HTML_SECURITY_OR_QUALITY')
    external=[];console=[];page_errors=[]
    with sandboxed_chromium(policy) as (ctx,profile,worker_manifest):
        page=ctx.pages[0] if ctx.pages else ctx.new_page();page.on('request',lambda req: external.append(req.url) if urlparse(req.url).scheme in ('http','https') else None);page.on('console',lambda msg: console.append(msg.text) if msg.type=='error' else None);page.on('pageerror',lambda err:page_errors.append(str(err)))
        shell=html.replace('<script type="module" src="./entry.js"></script>','')
        page.set_content(shell,wait_until='load',timeout=policy.browser_timeout_ms);page.evaluate(bundle);page.wait_for_function('globalThis.__BIE_GAME_RUNTIME__?.booted === true',timeout=policy.browser_timeout_ms)
        apps=page.locator('main[role="application"]')
        if apps.count()!=1:raise GameBuildError('GAME_BUILD_APPLICATION_ROOT_COUNT',str(apps.count()))
        studio=apps.get_attribute('data-studio-grade')=='true';slide=apps.get_attribute('data-slide-deck')=='true';entities=page.locator('[data-entity-id]').count();keys=tuple(page.evaluate('globalThis.__BIE_GAME_RUNTIME__.bindingKeys'));geom=page.evaluate('() => Array.from(document.querySelectorAll("[data-entity-id]")).map((n) => { const r=n.getBoundingClientRect(); return {id:n.getAttribute("data-entity-id"),width:r.width,height:r.height,text:(n.textContent||"").trim()}; })');body_text=page.locator('body').inner_text().strip();actions=page.evaluate('globalThis.__BIE_GAME_RUNTIME__.actionIds()')
        if not body_text or any((g['width']<8 or g['height']<8 or not g['text']) for g in geom):raise GameBuildError('GAME_BUILD_BLANK_OR_ZERO_AREA_RUNTIME')
        if not actions or page.evaluate('typeof globalThis.__BIE_GAME_RUNTIME__.dispatch')!='function':raise GameBuildError('GAME_BUILD_LIVE_CONTROLLER_MISSING')
        sb=sandbox_evidence(profile,worker_manifest);version=ctx.browser.version if ctx.browser else 'unknown'
        ev=BrowserEvidence('about:blank','playwright_devtools_self_contained_bundle',version,studio,slide,entities,tuple(sorted(set(external))),tuple(console),tuple(page_errors),tuple(keys),bundle_sha,False,sb.uid,sb.no_new_privs,sb.renderer_seccomp,sb.canonical_worker_blob).validate()
    return ev
