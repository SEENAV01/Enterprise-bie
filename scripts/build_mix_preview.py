#!/usr/bin/env python3
"""Offline technical audio/clock monitor. Not an animated lecture or Remotion render."""
from pathlib import Path
import argparse,base64,json

def build(evidence,out):
    cases=[]
    for name in ('english-dry','english-mix','hindi-mix','compat204-mix'):
        p=Path(evidence)/(name+'-run-0');r=json.loads((p/'MIX_RECEIPT.json').read_text())
        cases.append({'name':name,'clock':json.loads((p/'MIX_CLOCK.json').read_text()),
                      'wav':'data:audio/wav;base64,'+base64.b64encode((p/'master.wav').read_bytes()).decode(),
                      'original':'data:audio/wav;base64,'+base64.b64encode((p/'source.wav').read_bytes()).decode(),
                      'lufs':r['peak_control']['after']['integrated_lufs'],'tp':r['peak_control']['after']['true_peak_dbtp'],
                      'trim':r['trim']['removed_trailing_samples'],'review':r['review_reasons']})
    data=json.dumps(cases,ensure_ascii=False).replace('<','\\u003c')
    html=r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; media-src data:; img-src data:">
<title>BIE · AUDIO 004 Mixing Monitor</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#e5edf6;font:16px system-ui,sans-serif;padding:32px}main{max-width:980px;margin:auto}h1{font-size:36px;margin:10px 0}.eyebrow{color:#6ed8cb;letter-spacing:2px;font-size:12px;font-weight:700}.muted{color:#a7b4c6;line-height:1.6}.panel{background:#142034;border:1px solid #263750;border-radius:14px;padding:22px;margin:20px 0}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.num{font-size:27px;font-weight:600}label{display:block;margin-bottom:10px}select{background:#1f2e43;color:#fff;padding:10px;border-radius:8px;border:1px solid #52657c;font:inherit;width:100%}audio{width:100%;margin:12px 0}#caption{min-height:80px;font-size:25px;line-height:1.6;white-space:pre-line}#word{color:#6ed8cb;font-weight:650;font-size:20px}.bar{height:12px;background:#2d405d;border-radius:10px;overflow:hidden}.bar span{height:100%;background:#6ed8cb;display:block;width:0%}#pause{font-weight:600;color:#ffce75}input[type=range]{width:100%}.small{font-size:13px;line-height:1.7}footer{border-top:1px solid #263750;padding-top:18px}details{margin-top:18px}@media(max-width:650px){body{padding:18px}h1{font-size:27px}.grid{grid-template-columns:1fr}}
</style></head><body><main><div class="eyebrow">MY BOOK INTELLIGENCE ENGINE / AUDIO 004</div><h1>Speech → Mix → Preserved timing</h1><p class="muted">Actual local speech, generated technical tone bed and cue. A mixing/synchronization monitor—not a cinematic lecture, neural-voice demo or acceptance result.</p>
<div class="panel"><label for="case">Verified technical case</label><select id="case"></select><audio id="master" controls preload="metadata"></audio><div class="grid"><div><span class="muted small">OUTPUT LOUDNESS</span><div id="lufs" class="num"></div></div><div><span class="muted small">TRUE PEAK</span><div id="peak" class="num"></div></div><div><span class="muted small">TRIMMED EDGE SAMPLES</span><div id="trim" class="num"></div></div></div></div>
<div class="panel"><div id="scene" class="eyebrow"></div><div id="caption"></div><div id="word"></div><p id="pause"></p><p class="muted small">Declared animation progress (technical monitor only)</p><div class="bar"><span id="progress"></span></div><label for="seek" class="small">Sample position <span id="position"></span></label><input id="seek" type="range" min="0" value="0" step="1"><div id="review" class="small muted"></div></div>
<details class="panel"><summary>Original narration before mixing</summary><p class="small muted">This is the unchanged source WAV. Its leading/trailing clock can differ from the derived master clock.</p><audio id="original" controls preload="metadata"></audio></details>
<footer class="muted small">Word markers are engine events, not independently approved phonetic endings. Human listening, real-book instruction, neural voice and actual Remotion AV acceptance remain open. Offline page: no external requests or assets.</footer></main>
<script>const CASES=__DATA__;let selected=0;const el=(id)=>document.getElementById(id);
function prog(t,s){if(s<=t.start_sample)return 0;if(s>=t.end_sample)return 1;let held=0,total=t.end_sample-t.start_sample;for(const [a,b]of t.holds){total-=b-a;if(s>a)held+=Math.max(0,Math.min(s,b)-a)}return(s-t.start_sample-held)/total}
function mixState(sample){const c=CASES[selected].clock;return{scene:c.scenes.find(s=>s.start_sample<=sample&&sample<s.end_sample)?.scene_id??null,captions:c.captions.filter(s=>s.start_sample<=sample&&sample<s.end_sample).map(x=>x.text),words:c.words.filter(s=>s.start_sample<=sample&&sample<s.end_sample).map(x=>x.spoken),pause:c.pauses.some(s=>s.start_sample<=sample&&sample<s.end_sample),animations:c.animations.map(t=>({binding_id:t.binding.binding_id,target_id:t.binding.target_id,active:t.start_sample<=sample&&sample<t.end_sample,progress:prog(t,sample)}))}}
function renderAtSample(sample){const s=mixState(sample);el('scene').textContent=s.scene??'End of media';el('caption').textContent=s.captions.join('\n');el('word').textContent=s.words.join(' ');el('pause').textContent=s.pause?'Declared pedagogical pause':' ';el('progress').style.width=((s.animations[0]?.progress??0)*100)+'%';el('position').textContent=sample+' / '+CASES[selected].clock.total_samples;el('seek').value=sample;return s}
function selectCase(i){selected=i;const c=CASES[i];el('master').pause();el('original').pause();el('master').src=c.wav;el('original').src=c.original;el('seek').max=c.clock.total_samples;el('lufs').textContent=c.lufs.toFixed(2)+' LUFS';el('peak').textContent=c.tp.toFixed(2)+' dBTP';el('trim').textContent=c.trim;el('review').textContent=c.review.length?'Review: '+c.review.join(', '):'Configured technical loudness and peak checks met. Not product acceptance.';el('case').value=String(i);renderAtSample(0)}
CASES.forEach((c,i)=>{const o=document.createElement('option');o.value=i;o.textContent=c.name;el('case').append(o)});el('case').addEventListener('change',()=>selectCase(Number(el('case').value)));
el('seek').addEventListener('input',()=>{const s=Number(el('seek').value);el('master').currentTime=s/CASES[selected].clock.sample_rate;renderAtSample(s)});
el('master').addEventListener('timeupdate',()=>renderAtSample(Math.min(CASES[selected].clock.total_samples,Math.floor(el('master').currentTime*CASES[selected].clock.sample_rate))));
function tick(){if(!el('master').paused)renderAtSample(Math.min(CASES[selected].clock.total_samples,Math.floor(el('master').currentTime*CASES[selected].clock.sample_rate)));requestAnimationFrame(tick)}selectCase(0);tick();
window.mixState=mixState;window.renderAtSample=renderAtSample;window.selectCase=selectCase;window.mixCases=CASES;
</script></body></html>'''.replace('__DATA__',data)
    Path(out).write_text(html,encoding='utf-8')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('evidence',type=Path);a.add_argument('output',type=Path);p=a.parse_args();build(p.evidence,p.output)
