// Test-only observation UI; never included in the production game entry.
const errors=[];window.addEventListener('error',e=>errors.push(e.message));
window.addEventListener('unhandledrejection',e=>errors.push(String(e.reason)));
await import('./entry.js');
const snapshots=[];
document.querySelector('#capture-routing').addEventListener('click',()=>{
 const api=window.__BIE_GAME_RUNTIME__;
 snapshots.push({index:snapshots.length,state:api.getState(),score:api.getScore(),events:api.getTelemetry(),selected_challenge:document.querySelector('[data-challenge-control="select"]')?.value,errors:[...errors]});
 document.querySelector('#routing-evidence').textContent=JSON.stringify({schema_version:'bie.game.native-input-proof/1',scope:'Native browser gestures with test-only readout of current controller state',platform:navigator.platform,linux_sandbox_verified:false,product_accepted:false,snapshots},null,2);
});
