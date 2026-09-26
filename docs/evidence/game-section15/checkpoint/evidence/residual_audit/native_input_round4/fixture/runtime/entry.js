import { bootstrap, runtimeBindings } from "./bootstrap.js";
import { React, createRoot, flushSync, reactDomVersion } from "./react-vendor.js";
globalThis.__BIE_GAME_ASSETS__ = Object.freeze({"audio:probe":"./probe.wav"});

export function startGameRuntime() {
  if (globalThis.__BIE_GAME_RUNTIME__?.booted) throw new Error("GAME_REACT_ALREADY_MOUNTED");
  if (React.version !== "19.3.0" || reactDomVersion !== "19.3.0") throw new Error("GAME_REACT_VERSION_MISMATCH");
  let reactRoot = null;
  let controller = null;
  let live = true;
  let renderError = null;
  function mount(element) {
    const placeholder = document.getElementById("bie-game-root");
    if (!placeholder) throw new Error("GAME_BUILD_ROOT_MISSING");
    if (!React.isValidElement(element)) throw new Error("GAME_BUILD_ROOT_INVALID");
    const container = document.createElement("div");
    container.id = "bie-game-root";
    placeholder.replaceWith(container);
    reactRoot = createRoot(container, {
      onUncaughtError(error) { renderError = error; },
      onRecoverableError(error) { renderError = error; }
    });
    // The existing controller requires committed DOM nodes when mount returns.
    flushSync(() => reactRoot.render(element));
    if (renderError) throw new Error("GAME_REACT_RENDER_FAILED");
    const application = container.querySelector('main[role="application"]');
    if (!application || container.querySelectorAll('main[role="application"]').length !== 1) {
      throw new Error("GAME_REACT_COMMIT_MISSING");
    }
    return application;
  }
  try {
    controller = bootstrap(React, mount);
  } catch (error) {
    live = false;
    controller?.dispose();
    reactRoot?.unmount();
    throw error;
  }
  const call = name => (...args) => {
    if (!live) throw new Error("GAME_RUNTIME_DISPOSED");
    return controller[name](...args);
  };
  const api = Object.freeze({
    get booted() { return live; },
    framework: Object.freeze({name:"react", reactVersion:React.version, reactDomVersion,
      mountAPI:"react-dom/client.createRoot", synchronousInitialCommit:true}),
    bindingKeys:Object.keys(runtimeBindings).sort(),
    dispatch:call("dispatch"), getState:call("getState"), getScore:call("getScore"),
    getFeedback:call("getFeedback"), getTelemetry:call("getTelemetry"),
    actionIds:call("actionIds"), playNarration:call("playNarration"),
    audioRuntimeAvailable:controller.audioRuntimeAvailable,
    reducedMotionSupported:controller.reducedMotionSupported,
    dispose() {
      if (!live) return;
      live = false;
      controller.dispose();
      reactRoot.unmount();
    }
  });
  globalThis.__BIE_GAME_RUNTIME__ = api;
  return api;
}
startGameRuntime();
