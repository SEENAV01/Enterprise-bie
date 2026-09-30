'use strict';

const state = { file: null, validation: null, runId: null, run: null };
const $ = (id) => document.getElementById(id);
const sourceFile = $('sourceFile');
const createButton = $('createButton');
const validateButton = $('validateButton');
const refreshButton = $('refreshButton');
const validationBadge = $('validationBadge');
const sourceFacts = $('sourceFacts');
const sourceMessage = $('sourceMessage');
const runFacts = $('runFacts');
const runMessage = $('runMessage');
const timeline = $('timeline');
const failureView = $('failureView');
const artifactId = $('artifactId');
const graphMessage = $('graphMessage');
const graphCanvas = $('graphCanvas');
const graphTable = $('graphTable');

function text(node, value) { node.textContent = value == null ? '' : String(value); }
function clear(node) { node.replaceChildren(); }
function factList(node, rows) {
  clear(node);
  rows.forEach((row) => {
    const dt = document.createElement('dt');
    const dd = document.createElement('dd');
    text(dt, row[0]); text(dd, row[1]);
    node.append(dt, dd);
  });
}
async function jsonResponse(response) {
  let body = null;
  try { body = await response.json(); } catch (_) { body = null; }
  if (!response.ok) {
    const code = body && body.error && body.error.code ? body.error.code : 'http_error';
    throw new Error(code);
  }
  return body;
}
function setValidation(value) {
  state.validation = value;
  validationBadge.className = 'badge ' + (value && value.valid ? 'good' : value ? 'bad' : 'neutral');
  text(validationBadge, value ? (value.valid ? 'Valid' : 'Invalid') : 'Not checked');
  createButton.disabled = !(value && value.valid && state.file);
  if (!value) {
    clear(sourceFacts); return;
  }
  factList(sourceFacts, [
    ['SHA-256', value.source_sha256],
    ['Bytes', value.byte_length],
    ['Media type', value.media_type],
    ['Issues', value.issues.length ? value.issues.join(', ') : 'None'],
  ]);
}
function setControlAvailability(run) {
  document.querySelectorAll('[data-action]').forEach((button) => { button.disabled = true; });
  if (!run) return;
  const byAction = {};
  document.querySelectorAll('[data-action]').forEach((button) => { byAction[button.dataset.action] = button; });
  byAction.pause.disabled = !(run.canonical_status === 'READY' && run.control_state === 'ACTIVE' && run.queue_state === 'READY');
  byAction.resume.disabled = !(run.canonical_status === 'READY' && run.control_state === 'PAUSED');
  byAction.retry.disabled = !(run.canonical_status === 'FAILED' && run.queue_state === 'DEAD_LETTER' && run.control_state === 'ACTIVE');
  byAction.cancel.disabled = !(['READY', 'RUNNING'].includes(run.canonical_status) && ['ACTIVE', 'PAUSED', 'CANCEL_REQUESTED'].includes(run.control_state));
}
function renderRun(run) {
  state.run = run;
  factList(runFacts, [
    ['Run', run.job_id],
    ['Status', run.status],
    ['Canonical stage', run.canonical_status],
    ['Run state', run.run_state],
    ['Attempt', run.attempt],
    ['Queue', run.queue_state],
    ['Control', run.control_state],
    ['Source SHA-256', run.source_hash],
    ['Result available', run.result_available],
  ]);
  setControlAvailability(run);
  refreshButton.disabled = false;
  artifactId.disabled = false;
  document.querySelectorAll('[data-graph]').forEach((button) => { button.disabled = false; });
}
function renderTimeline(value) {
  clear(timeline);
  if (!value.events.length) {
    const li = document.createElement('li'); li.className = 'empty'; text(li, 'No transition events recorded.'); timeline.append(li); return;
  }
  value.events.forEach((event) => {
    const li = document.createElement('li');
    const strong = document.createElement('strong');
    const small = document.createElement('small');
    text(strong, event.from_state + ' → ' + event.to_state);
    text(small, event.event_kind + ' · attempt ' + event.attempt + ' · ' + event.reason + ' · ' + event.timestamp);
    li.append(strong, small); timeline.append(li);
  });
}
function renderFailure(value) {
  clear(failureView);
  if (!value.failure_available) {
    failureView.className = 'empty'; text(failureView, 'No failure evidence available.'); return;
  }
  failureView.className = '';
  const p = document.createElement('p');
  text(p, 'Diagnostics: ' + (value.diagnostic_codes.length ? value.diagnostic_codes.join(', ') : 'none'));
  const e = document.createElement('p');
  text(e, 'Evidence refs: ' + (value.evidence_refs.length ? value.evidence_refs.join(', ') : 'none'));
  const r = document.createElement('p');
  text(r, 'Retryable: ' + String(value.retryable));
  failureView.append(p, e, r);
}
async function validateSelected() {
  state.file = sourceFile.files && sourceFile.files[0] ? sourceFile.files[0] : null;
  setValidation(null);
  if (!state.file) { text(sourceMessage, 'Choose a PDF source first.'); return; }
  validateButton.disabled = true; text(sourceMessage, 'Validating against the backend…');
  try {
    const response = await fetch('/v1/app/sources/validate', {
      method: 'POST',
      headers: {'Content-Type': state.file.type || 'application/octet-stream'},
      body: state.file,
    });
    const value = await jsonResponse(response);
    setValidation(value);
    text(sourceMessage, value.valid ? 'Source passed bounded validation.' : 'Source is blocked: ' + value.issues.join(', '));
  } catch (error) {
    setValidation(null); text(sourceMessage, 'Validation request failed: ' + error.message);
  } finally { validateButton.disabled = false; }
}
async function createRun(event) {
  event.preventDefault();
  if (!state.file || !state.validation || !state.validation.valid) return;
  createButton.disabled = true; text(sourceMessage, 'Creating a durable run…');
  try {
    const response = await fetch('/v1/app/runs', {
      method: 'POST',
      headers: {
        'Content-Type': state.file.type || 'application/pdf',
        'Idempotency-Key': crypto.randomUUID(),
      },
      body: state.file,
    });
    const value = await jsonResponse(response);
    state.runId = value.run.job_id;
    renderRun(value.run);
    text(sourceMessage, 'Run created from the validated source.');
    await refreshRun();
  } catch (error) {
    text(sourceMessage, 'Run creation failed: ' + error.message);
    createButton.disabled = false;
  }
}
async function refreshRun() {
  if (!state.runId) return;
  refreshButton.disabled = true; text(runMessage, 'Refreshing authoritative state…');
  try {
    const paths = [
      '/v1/app/runs/' + encodeURIComponent(state.runId),
      '/v1/app/runs/' + encodeURIComponent(state.runId) + '/timeline',
      '/v1/app/runs/' + encodeURIComponent(state.runId) + '/failure',
    ];
    const responses = await Promise.all(paths.map((path) => fetch(path).then(jsonResponse)));
    renderRun(responses[0]); renderTimeline(responses[1]); renderFailure(responses[2]);
    text(runMessage, 'State refreshed from persisted backend data.');
  } catch (error) { text(runMessage, 'Refresh failed: ' + error.message); }
  finally { refreshButton.disabled = false; }
}
async function control(action) {
  if (!state.runId) return;
  setControlAvailability(null); text(runMessage, 'Applying ' + action + '…');
  try {
    const path = '/v1/app/runs/' + encodeURIComponent(state.runId) + '/' + action;
    const value = await fetch(path, {method: 'POST'}).then(jsonResponse);
    renderRun(value); await refreshRun();
  } catch (error) {
    text(runMessage, action + ' failed: ' + error.message);
    setControlAvailability(state.run);
  }
}
function svg(tag) { return document.createElementNS('http://www.w3.org/2000/svg', tag); }
function renderGraph(value) {
  while (graphCanvas.lastChild && !['title', 'desc'].includes(graphCanvas.lastChild.tagName && graphCanvas.lastChild.tagName.toLowerCase())) {
    graphCanvas.removeChild(graphCanvas.lastChild);
  }
  const nodes = value.nodes || [], edges = value.edges || [];
  if (!nodes.length) { text(graphMessage, 'Artifact is valid but contains no graph nodes.'); clear(graphTable); return; }
  const positions = new Map();
  const cx = 480, cy = 250, radius = Math.min(200, 80 + nodes.length * 8);
  nodes.forEach((node, index) => {
    const angle = (Math.PI * 2 * index / nodes.length) - Math.PI / 2;
    positions.set(node.id, [cx + radius * Math.cos(angle), cy + radius * Math.sin(angle)]);
  });
  edges.forEach((edge) => {
    const a = positions.get(edge.source), b = positions.get(edge.target);
    if (!a || !b) return;
    const line = svg('line');
    line.setAttribute('x1', a[0]); line.setAttribute('y1', a[1]);
    line.setAttribute('x2', b[0]); line.setAttribute('y2', b[1]);
    line.setAttribute('stroke', 'currentColor'); line.setAttribute('opacity', '.35');
    graphCanvas.append(line);
  });
  nodes.forEach((node) => {
    const p = positions.get(node.id);
    const group = svg('g');
    const circle = svg('circle');
    circle.setAttribute('cx', p[0]); circle.setAttribute('cy', p[1]);
    circle.setAttribute('r', '25'); circle.setAttribute('fill', 'Canvas');
    circle.setAttribute('stroke', 'currentColor');
    const label = svg('text');
    label.setAttribute('x', p[0]); label.setAttribute('y', p[1] + 42);
    label.setAttribute('text-anchor', 'middle'); label.setAttribute('font-size', '12');
    label.textContent = node.label.slice(0, 42);
    const title = svg('title'); title.textContent = node.label + ' (' + node.kind + ')';
    group.append(circle, label, title); graphCanvas.append(group);
  });
  text(graphMessage, value.kind + ' graph · ' + value.node_count + ' nodes · ' + value.edge_count + ' edges');
  clear(graphTable);
  const table = document.createElement('table');
  const head = document.createElement('tr');
  ['Node', 'Kind', 'Evidence/source refs'].forEach((name) => { const th = document.createElement('th'); text(th, name); head.append(th); });
  table.append(head);
  nodes.forEach((node) => {
    const row = document.createElement('tr');
    [node.label, node.kind, node.source_refs.join(', ')].forEach((valueText) => { const td = document.createElement('td'); text(td, valueText); row.append(td); });
    table.append(row);
  });
  graphTable.append(table);
}
async function loadGraph(kind) {
  if (!state.runId || !artifactId.value.trim()) { text(graphMessage, 'Enter an actual artifact ID first.'); return; }
  document.querySelectorAll('[data-graph]').forEach((button) => { button.disabled = true; });
  text(graphMessage, 'Loading ' + kind + ' graph from artifact storage…');
  try {
    const path = '/v1/app/runs/' + encodeURIComponent(state.runId) + '/graphs/' + kind + '?artifact_id=' + encodeURIComponent(artifactId.value.trim());
    const value = await fetch(path).then(jsonResponse);
    renderGraph(value);
  } catch (error) { text(graphMessage, 'Graph unavailable: ' + error.message); }
  finally { document.querySelectorAll('[data-graph]').forEach((button) => { button.disabled = !state.runId; }); }
}

sourceFile.addEventListener('change', () => { state.file = sourceFile.files && sourceFile.files[0] ? sourceFile.files[0] : null; setValidation(null); text(sourceMessage, state.file ? 'Source selected. Validate it before creating a run.' : ''); });
validateButton.addEventListener('click', validateSelected);
$('sourceForm').addEventListener('submit', createRun);
refreshButton.addEventListener('click', refreshRun);
document.querySelectorAll('[data-action]').forEach((button) => button.addEventListener('click', () => control(button.dataset.action)));
document.querySelectorAll('[data-graph]').forEach((button) => button.addEventListener('click', () => loadGraph(button.dataset.graph)));
setValidation(null);
