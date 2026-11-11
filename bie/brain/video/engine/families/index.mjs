// The families of saanche: each family is one file here (its drawings) and one manifest in ../saanche.d/<family>.json,
// so families built at the same time never edit the same lines. A family exports DRAWS = {name: {fn, anchor}} and may
// import the drawing helpers from "../draw.mjs" (tx, fit, shade, INK, FONT, esc, clamp01, parts, idxSet, isNum,
// smoothPath, easeIO, DIAG, rnd, label) - used inside its functions only, never at load time (draw.mjs loads the
// families first). Add one import and one spread below.
import { DRAWS as ECON_CHARTS } from "./econ_charts.mjs";
import { DRAWS as ECON_TOOLS } from "./econ_tools.mjs";
import { DRAWS as econ_finance } from "./econ_finance.mjs";

export const FAMILY_DRAWS = {
  ...ECON_CHARTS,
  ...ECON_TOOLS,
  ...econ_finance,
};
