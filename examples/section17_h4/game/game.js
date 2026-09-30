'use strict';
const feedback=document.getElementById('feedback');
const progress=document.getElementById('progress');
document.getElementById('wrong').addEventListener('click',()=>{
 feedback.textContent='Try again. Multiply both numerator and denominator by 2.';
 progress.textContent='Solved: 0/1';
});
document.getElementById('right').addEventListener('click',()=>{
 feedback.textContent='Correct. 1/2 = 2/4.';
 progress.textContent='Solved: 1/1';
});
