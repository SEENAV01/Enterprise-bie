import { bootstrap, runtimeBindings } from "./bootstrap.js";
const React = {
  createElement(tag, props = {}, ...children) {
    const el = document.createElement(tag);
    for (const [key, value] of Object.entries(props || {})) {
      if (key === "key" || value === undefined || value === null) continue;
      if (key === "className") el.setAttribute("class", String(value));
      else el.setAttribute(key, String(value));
    }
    for (const child of children.flat(Infinity)) {
      if (child instanceof Node) el.appendChild(child);
      else if (child !== undefined && child !== null) el.appendChild(document.createTextNode(String(child)));
    }
    return el;
  }
};
function mount(node) {
  const root = document.getElementById("bie-game-root");
  if (!root) throw new Error("GAME_BUILD_ROOT_MISSING");
  if (!(node instanceof HTMLElement)) throw new Error("GAME_BUILD_ROOT_INVALID");
  node.id = "bie-game-root";
  root.replaceWith(node);
}
bootstrap(React, mount);
globalThis.__BIE_GAME_RUNTIME__ = Object.freeze({booted:true,bindingKeys:Object.keys(runtimeBindings).sort()});
