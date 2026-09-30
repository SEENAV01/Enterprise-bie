import {equivalent} from './math.mjs';
const lesson = await (await fetch('./lesson.json')).json();
const feedback = document.getElementById('feedback');
const progress = document.getElementById('progress');
const note = document.getElementById('note');
function restore() {progress.textContent = 'Solved: ' + (localStorage.getItem('solved')==='yes'?'1':'0') + '/1';note.value=localStorage.getItem('note')||'';}
restore();
document.getElementById('wrong').addEventListener('click',async()=>{const texts=await import('./feedback.mjs');feedback.textContent=texts.wrong;});
document.getElementById('right').addEventListener('click',async()=>{const texts=await import('./feedback.mjs');if(equivalent(1,2,2,4)){feedback.textContent=texts.correct;localStorage.setItem('solved','yes');restore();}});
note.addEventListener('input',()=>localStorage.setItem('note',note.value));
document.getElementById('reset').addEventListener('click',()=>{localStorage.clear();restore();feedback.textContent='Choose an answer.';});
if (lesson.version === 1) document.getElementById('ready').textContent='Lesson ready';
