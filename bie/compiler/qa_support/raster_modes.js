options => {
  // Trusted, reversible observation helper. It never edits source/geometry/text.
  if (globalThis.__bieH8Restore) globalThis.__bieH8Restore();
  const changed = [];
  const hide = node => {
    changed.push([node, node.style.getPropertyValue('visibility'), node.style.getPropertyPriority('visibility')]);
    node.style.setProperty('visibility', 'hidden', 'important');
    // Descendants may explicitly override inherited visibility. Hide the entire
    // selected subtree, preserving the original value of every declaration.
    for (const child of node.querySelectorAll('*')) {
      changed.push([child, child.style.getPropertyValue('visibility'), child.style.getPropertyPriority('visibility')]);
      child.style.setProperty('visibility', 'hidden', 'important');
    }
  };
  globalThis.__bieH8Restore = () => {
    for (const [node, value, priority] of changed.reverse()) {
      if (value) node.style.setProperty('visibility', value, priority);
      else node.style.removeProperty('visibility');
    }
    globalThis.__bieH8Restore = null;
  };
  const owners = [...document.querySelectorAll('[data-bie-layer-id]')];
  const targets = options.targets;
  if (!Array.isArray(targets) || targets.length > 128) throw Error('RASTER_TARGET_BUDGET');
  const nodes = new Map();
  const inventory = targets.map(t => {
    const matching = owners.filter(e => e.getAttribute('data-bie-layer-id') === t.element_id);
    if (matching.length !== 1) throw Error('RASTER_OWNER_IDENTITY:' + t.target_id);
    const owner = matching[0];
    const candidates = t.layer_id === null ? [owner] : [...owner.querySelectorAll('[data-layer-id]')].filter(e => e.getAttribute('data-layer-id') === t.layer_id);
    if (candidates.length !== 1) throw Error('RASTER_FEATURE_IDENTITY:' + t.target_id);
    const node = candidates[0]; nodes.set(t.target_id, {node, owner});
    let visible = true, unresolvedEffect = false;
    for (let n=node; n; n=n.parentElement) {
      const s=getComputedStyle(n);
      if (s.display === 'none' || s.visibility !== 'visible' || +s.opacity === 0) visible=false;
      if (s.filter !== 'none' || s.mixBlendMode !== 'normal' || (s.backdropFilter && s.backdropFilter !== 'none')) unresolvedEffect=true;
    }
    for (const n of node.querySelectorAll('*')) {
      if (n.closest('defs,title,desc')) continue;
      const s=getComputedStyle(n);
      if (s.filter !== 'none' || s.mixBlendMode !== 'normal' || (s.backdropFilter && s.backdropFilter !== 'none')) unresolvedEffect=true;
    }
    const box=node.getBoundingClientRect();
    return {target_id:t.target_id, visible, unresolved_effect:unresolvedEffect,
      box:[box.x,box.y,box.width,box.height]};
  });
  const expectedOwners=new Set(targets.filter(t=>t.layer_id===null).map(t=>t.element_id));
  if (owners.length !== expectedOwners.size || owners.some(e=>!expectedOwners.has(e.dataset.bieLayerId))) throw Error('RASTER_UNDECLARED_OWNER');
  const mode=options.mode || {kind:'full'};
  if (mode.kind !== 'full') {
    const selected=nodes.get(mode.target_id);
    if (!selected) throw Error('RASTER_MODE_TARGET_INVALID');
    const {node,owner}=selected;
    if (mode.kind === 'muted') hide(node);
    else if (mode.kind === 'isolated' || mode.kind === 'baseline') {
      for (const other of owners) if(other!==owner && !other.contains(owner)) hide(other);
      // Hide sibling branches along the path, NOT the ancestors. This preserves
      // their layout/background; an isolated-baseline pair cancels that paint.
      if (node!==owner) {
        for (let n=node; n && n!==owner; n=n.parentElement) {
          for (const sibling of n.parentElement.children) if(sibling!==n) hide(sibling);
        }
      }
      if (mode.kind==='baseline') hide(node);
    } else throw Error('RASTER_MODE_INVALID');
  }
  const imageErrors=[...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.getAttribute('src'));
  return {mode,inventory,fonts_ready:document.fonts.status==='loaded',image_errors:imageErrors};
}
