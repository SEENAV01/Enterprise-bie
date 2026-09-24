#!/usr/bin/env python3
"""Offline native-audio sync monitor. NOT a rendered Remotion lecture."""
from pathlib import Path
import argparse,base64,json

def build(folder,output):
    folder=Path(folder);r=json.loads((folder/'SYNC_REPORT.json').read_text());a=json.loads((folder/'ANIMATION_SYNC.json').read_text())
    timeline=r['timeline'];rate=timeline['sample_rate'];cues=[];words=[]
    for p,c,w in zip(timeline['segments'],r['caption_tracks'],r['word_timings']):
        for cue in c['cues']:cues.append({'start':p['start_sample']+cue['start_sample'],'end':p['start_sample']+cue['end_sample'],'text':'\n'.join(cue['lines'])})
        for word in w['words']:words.append({'start':p['start_sample']+word['start_sample'],'end':p['start_sample']+word['end_sample'],'text':word['spoken']})
    payload=json.dumps({'rate':rate,'total':timeline['total_samples'],'scenes':timeline['scenes'],'cues':cues,'words':words,'pauses':r['pause_sync']['windows'],'tracks':a['tracks']},ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    b64=base64.b64encode((folder/'speech.wav').read_bytes()).decode()
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BIE • Audio sync evidence</title>
<style>body{margin:0;background:#101822;color:#e5edf5;font:17px system-ui,sans-serif}main{max-width:960px;margin:auto;padding:40px 22px}h1{font-size:36px;letter-spacing:-1px;margin:10px 0}.eyebrow{color:#79d7cc;letter-spacing:2px;font-size:12px}.note{color:#b8c7d6;line-height:1.6}.card{padding:24px;background:#192636;border:1px solid #31445b;border-radius:14px;margin:22px 0}.caption{min-height:86px;font-size:27px;line-height:1.4;white-space:pre-line}.status{display:flex;gap:12px;flex-wrap:wrap}.pill{padding:8px 12px;background:#22384a;border-radius:8px}audio{width:100%}progress{width:100%;height:22px}button{background:#79d7cc;border:0;border-radius:8px;color:#102029;padding:12px 20px;font-weight:bold;cursor:pointer}.muted{color:#9cafc3;font-size:14px}.word{font-size:22px;color:#79d7cc}code{font-size:14px}</style>
<main><div class="eyebrow">MY BOOK INTELLIGENCE ENGINE / TECHNICAL EVIDENCE</div><h1>Audio-driven synchronization</h1><p class="note">Native WAV playback controls the captions, word indicator, scene selection and declared animation progress. Seek anywhere; no previous frames need to run.</p>
<div class="card"><audio id="audio" controls preload="metadata" src="data:audio/wav;base64,''' + b64 + '''"></audio><p><button id="play">Play / pause</button></p><div class="status"><span class="pill" id="scene"></span><span class="pill" id="clock"></span><span class="pill" id="pause"></span></div></div>
<div class="card"><div class="eyebrow">SOURCE-PRESERVING CAPTIONS</div><p id="caption" class="caption"></p><p class="word" id="word"></p></div>
<div class="card"><div class="eyebrow">DECLARED ANIMATION TIMING</div><p id="trackLabel"></p><progress id="progress" max="1" value="0"></progress><p class="muted">The bar is a timing monitor, not a generated teaching animation. Explicit “hold” intervals freeze its progress during pedagogical pauses.</p></div>
<p class="muted">Technical local formant voice; native engine timing marks. Not independent acoustic alignment, pronunciation approval, a real-book evaluation, cinematic voice acceptance or a rendered Remotion video.</p></main>
<script>const data='''+payload+''';const audio=document.querySelector('#audio');
function update(){const sample=Math.min(data.total,Math.floor(audio.currentTime*data.rate));
const cue=data.cues.find(c=>sample>=c.start&&sample<c.end),word=data.words.find(w=>sample>=w.start&&sample<w.end),scene=data.scenes.find(s=>sample>=s.start_sample&&sample<s.end_sample),pause=data.pauses.find(p=>sample>=p.start_sample&&sample<p.end_sample);
document.querySelector('#caption').textContent=cue?cue.text:'';document.querySelector('#word').textContent=word?'Speaking: '+word.text:'';document.querySelector('#scene').textContent=scene?scene.scene_id:'End';document.querySelector('#clock').textContent=audio.currentTime.toFixed(3)+' s';document.querySelector('#pause').textContent=pause?'Declared pause':'Speech / native spacing';
const t=data.tracks[0];let value=0;if(t){let total=t.end_sample-t.start_sample-t.holds.reduce((n,h)=>n+h[1]-h[0],0);let elapsed=Math.max(0,Math.min(sample,t.end_sample)-t.start_sample);for(const h of t.holds)elapsed-=Math.max(0,Math.min(sample,h[1])-h[0]);value=Math.max(0,Math.min(1,elapsed/total));document.querySelector('#trackLabel').textContent=t.binding.action+' • '+t.binding.target_id+' • '+(value*100).toFixed(1)+'%';}else document.querySelector('#trackLabel').textContent='No animation bindings supplied';document.querySelector('#progress').value=value;}
document.querySelector('#play').onclick=()=>audio.paused?audio.play():audio.pause();audio.addEventListener('timeupdate',update);audio.addEventListener('seeked',update);audio.addEventListener('loadedmetadata',update);function loop(){update();requestAnimationFrame(loop)}requestAnimationFrame(loop);window.bieSync={data,update};</script></html>'''
    Path(output).write_text(html,encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('output',type=Path);a=p.parse_args();build(a.folder,a.output)
