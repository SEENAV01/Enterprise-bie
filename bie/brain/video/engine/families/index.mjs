// The families of saanche: each family is one file here (its drawings) and one manifest in ../saanche.d/<family>.json,
// so families built at the same time never edit the same lines. A family exports DRAWS = {name: {fn, anchor}} and may
// import the drawing helpers from "../draw.mjs" (tx, fit, shade, INK, FONT, esc, clamp01, parts, idxSet, isNum,
// smoothPath, easeIO, DIAG, rnd, label) - used inside its functions only, never at load time (draw.mjs loads the
// families first). Add one import and one spread below.
import { DRAWS as ECON_THINGS } from "./econ_things.mjs";

export const FAMILY_DRAWS = {
  ...ECON_THINGS,
};
