from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json,time
from .contracts import RuntimeExperienceProfile
from ..build_runtime_engine.contracts import BuildPolicy
from ..errors import GameContractError

@dataclass(frozen=True)
class RuntimeQualityEvidence:
    locale:str; direction:str; mobile_pass:bool; tablet_pass:bool; keyboard_pass:bool; focus_pass:bool; touch_targets_pass:bool; live_region_pass:bool; reduced_motion_pass:bool; audio_event_pass:bool; attribution_pass:bool; first_render_ms:float; interaction_latency_ms:float; initial_js_bytes:int; package_bytes:int; product_accepted:bool=False
    def validate(self,profile:RuntimeExperienceProfile):
        p=profile.validate().performance
        if self.product_accepted or not all((self.mobile_pass,self.tablet_pass,self.keyboard_pass,self.focus_pass,self.touch_targets_pass,self.live_region_pass,self.reduced_motion_pass,self.audio_event_pass,self.attribution_pass)): raise GameContractError('GAME_RUNTIME_QUALITY_FAILED')
        if self.first_render_ms>p.max_first_render_ms or self.interaction_latency_ms>p.max_interaction_latency_ms or self.initial_js_bytes>p.max_initial_js_bytes or self.package_bytes>p.max_package_bytes: raise GameContractError('GAME_RUNTIME_PERFORMANCE_FAILED')
        return self

def verify_runtime_quality(dist:Path,profile:RuntimeExperienceProfile,policy=BuildPolicy()):
    from ..build_runtime_engine.sandbox import sandboxed_chromium
    profile.validate();dist=Path(dist);runtime=dist/'runtime'; bundle=(runtime/'smoke-bundle.js').read_text(); html=(runtime/'index.html').read_text().replace('<script type="module" src="./entry.js"></script>','')
    js_bytes=sum(p.stat().st_size for p in runtime.glob('*.js')); package_bytes=sum(p.stat().st_size for p in dist.rglob('*') if p.is_file())
    catalog=profile.catalog(); msgs=dict(catalog.messages)
    with sandboxed_chromium(policy) as (ctx,_,__):
        page=ctx.pages[0] if ctx.pages else ctx.new_page(); page.set_viewport_size({'width':profile.performance.mobile_viewport_width,'height':740}); t=time.perf_counter();page.set_content(html,wait_until='load');page.evaluate(bundle);page.wait_for_function('globalThis.__BIE_GAME_RUNTIME__?.booted === true',timeout=policy.browser_timeout_ms); first=(time.perf_counter()-t)*1000
        root=page.locator('main[role="application"]'); mobile=root.count()==1 and root.bounding_box()['width']<=profile.performance.mobile_viewport_width+1 and page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        lang=root.get_attribute('lang'); direction=root.get_attribute('dir'); live=page.locator('#bie-game-feedback').get_attribute('aria-live')=='polite'
        target=page.locator('[data-entity-id]').first; target.focus(); focus=page.evaluate('document.activeElement?.hasAttribute("data-entity-id")===true'); boxes=page.locator('button[data-entity-id]').evaluate_all('(els)=>els.map(e=>{const r=e.getBoundingClientRect();return [r.width,r.height]})');touch=bool(boxes) and all(min(b)>=profile.accessibility.min_touch_target_px for b in boxes);
        t=time.perf_counter(); target.press('Enter'); latency=(time.perf_counter()-t)*1000; keyboard=page.evaluate('globalThis.__BIE_GAME_RUNTIME__.getScore()')>0
        reduced=page.evaluate('globalThis.__BIE_GAME_RUNTIME__.reducedMotionSupported===true')
        audio=page.evaluate('globalThis.__BIE_GAME_RUNTIME__.audioRuntimeAvailable===true')
        attribution=page.locator('[data-rights-attribution="true"]').count()==1
        page.set_viewport_size({'width':profile.performance.tablet_viewport_width,'height':1024}); tablet=root.bounding_box()['width']<=profile.performance.tablet_viewport_width+1 and page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
    return RuntimeQualityEvidence(lang or '',direction or '',mobile,tablet,keyboard,focus,touch,live,reduced,audio,attribution,first,latency,js_bytes,package_bytes,False).validate(profile)
