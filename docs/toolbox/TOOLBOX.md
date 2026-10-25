# BIE toolbox (auzaar-ghar)

BIE ka auzaar-ghar: har library, tool aur asset source jo BIE kisi bhi scene ko dikhane ke liye use karta hai. A Python library computes, a BIE block shows.

Registry `2026-10-25.1`, capabilities `2026-10-25.1`, npm packages as of `2026-10-17T12:00:00Z`. Tools: 30 (demo proven 30).

Status words: **installed** (the package is pinned and installs), **wrapped** (a BIE adapter or block uses it, with tests), **demo proven** (a BIE-made clip shows it working), **used on a real book** (it drew part of a real lesson), **blocked** (the reason says what it needs). Nothing here is ACCEPTED: that is Navin's verdict.

## Proof clips (batch 1)

20 of 20 clips passed the checks (not blank, something moves, 3–5 s). Rendered on the cloud workspace on 25 October 2026 (about 31 minutes for all 20); CI renders them again in the demos job of every toolbox PR (artifact bie-toolbox-demos-batch-1). Bridge: bio-cell-sheet-flow rendered again by real Remotion 4.0.536, mean frame difference 0.0 on all six frames.

| Clip | What it shows | Tools it proves | Length | Checks |
| --- | --- | --- | --- | --- |
| `bio-cell-sheet-flow` | Blender-made columnar epithelium in three.js with particles flowing through | blender, three, react-three-fiber, drei, remotion-three | 4.5 s | passed |
| `bio-ecg` | An ECG simulated by NeuroKit2 drawn on its paper | neurokit2, d3 | 4.2 s | passed |
| `bio-heart-bodyparts3d` | BodyParts3D heart joined by trimesh, zooming in | bodyparts3d, trimesh, three, react-three-fiber, drei, remotion-three | 4.0 s | passed |
| `bio-heart-nih3d` | NIH 3D heart model turning | nih-3d, three, react-three-fiber, drei, remotion-three | 4.0 s | passed |
| `bio-heart-zanatomy` | Z-Anatomy heart chambers exported by Blender, left ventricle glowing | z-anatomy, blender, three, react-three-fiber, drei, remotion-three | 4.0 s | passed |
| `bio-organ-zoom` | Lung to alveolus zoom on Servier pictures | servier-medical-art, bie-blocks | 5.0 s | passed |
| `bio-protein-3dmol` | Crambin from the PDB, read by Biopython, drawn by 3Dmol.js | rcsb-pdb, biopython, 3dmol | 4.0 s | passed |
| `bio-protein-molstar` | Green fluorescent protein in Mol* | molstar, rcsb-pdb | 4.0 s | passed |
| `chem-molecule-pubchem` | Caffeine's 3D record from PubChem | pubchem, 3dmol | 3.5 s | passed |
| `chem-molecule-rdkit` | Aspirin in 3D from RDKit, drawn by 3Dmol.js | rdkit, 3dmol | 4.0 s | passed |
| `chem-reaction` | Esterification by RDKit and H2 + O2 kinetics by Cantera | rdkit, cantera, d3, bie-blocks | 5.0 s | passed |
| `cs-graph-bfs` | Breadth-first search on a graph | networkx, d3 | 4.5 s | passed |
| `maths-equation` | A linear equation solved step by step, every step checked by SymPy, typeset by KaTeX | sympy, katex | 4.5 s | passed |
| `maths-function-graph` | A parabola drawn over time | sympy, numpy, d3 | 4.0 s | passed |
| `maths-manim` | A function drawn by Manim (offline path) | manim, sympy | 4.1 s | passed |
| `maths-regression` | A least-squares line fitted by statsmodels | statsmodels, d3 | 4.0 s | passed |
| `physics-collision-3d` | A ball passes its momentum on and knocks a tower over (3D) | cannon-es, three, react-three-fiber, drei, remotion-three | 4.0 s | passed |
| `physics-falling` | A falling body with and without air drag | scipy, numpy, d3 | 4.0 s | passed |
| `physics-matter` | Boxes and a ball under gravity | matter-js | 4.0 s | passed |
| `physics-wave` | Two travelling waves make a standing wave | numpy, d3 | 4.0 s | passed |

## By subject family

### All subjects

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| particle_flow | BIE block library (bie/brain/video/blocks) (demo proven), three.js (demo proven) | — | — | — | `bio-cell-sheet-flow` |
| organ_zoom | BIE block library (bie/brain/video/blocks) (demo proven) | — | Servier Medical Art (demo proven), Z-Anatomy (demo proven) | — | `bio-organ-zoom`, `bio-heart-bodyparts3d` |
| focus_glow | BIE block library (bie/brain/video/blocks) (demo proven) | — | — | — | `bio-cell-sheet-flow`, `bio-organ-zoom`, `bio-heart-zanatomy` |
| kinetic_caption | BIE block library (bie/brain/video/blocks) (demo proven) | — | — | — | none yet |
| concept_arrow | BIE block library (bie/brain/video/blocks) (demo proven) | — | — | — | none yet |
| board_build | BIE block library (bie/brain/video/blocks) (demo proven) | — | — | — | none yet |
| mnemonic_card | **missing** | — | — | — | none yet |
| split_compare | **missing** | — | — | — | none yet |
| timeline | BIE block library (bie/brain/video/blocks) (demo proven) | — | — | — | none yet |
| flowchart | **missing** | NetworkX (demo proven) | — | — | none yet |
| process_cycle | **missing** | — | — | — | none yet |
| tree_hierarchy | **missing** | NetworkX (demo proven) | — | — | none yet |
| chart_bar_line_pie | D3 (demo proven) | statsmodels (demo proven) | — | — | `chem-reaction`, `maths-regression` |
| table_build | BIE block library (bie/brain/video/blocks) (demo proven) | — | — | — | none yet |
| text_kinetic | **missing** | — | — | — | none yet |

### Biology and medical

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| cell_sheet_3d | three.js (demo proven), @react-three/drei (demo proven), React Three Fiber (demo proven) | — | — | Blender (bpy, headless) (demo proven) | `bio-cell-sheet-flow` |
| organ_zoom | BIE block library (bie/brain/video/blocks) (demo proven) | — | Servier Medical Art (demo proven), Z-Anatomy (demo proven) | — | `bio-organ-zoom`, `bio-heart-bodyparts3d` |
| anatomy_3d | three.js (demo proven), @react-three/drei (demo proven), React Three Fiber (demo proven) | trimesh (demo proven) | BodyParts3D (demo proven), NIH 3D (demo proven), Servier Medical Art (demo proven) | Blender (bpy, headless) (demo proven) | `bio-heart-nih3d`, `bio-heart-zanatomy`, `bio-heart-bodyparts3d` |
| molecule_3d | 3Dmol.js (demo proven), Mol* (demo proven) | RDKit (demo proven) | PubChem (demo proven) | — | `chem-molecule-rdkit`, `chem-molecule-pubchem` |
| signal_plot | D3 (demo proven) | NeuroKit2 (demo proven), NumPy (demo proven), SciPy (demo proven) | — | — | `bio-ecg` |
| process_cycle | **missing** | — | — | — | none yet |
| ecg_trace | D3 (demo proven) | NeuroKit2 (demo proven) | — | — | `bio-ecg` |
| protein_3d | 3Dmol.js (demo proven), Mol* (demo proven) | Biopython (demo proven) | NIH 3D (demo proven), RCSB Protein Data Bank (demo proven) | — | `bio-protein-3dmol`, `bio-protein-molstar` |

### Chemistry

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| molecule_3d | 3Dmol.js (demo proven), Mol* (demo proven) | RDKit (demo proven) | PubChem (demo proven) | — | `chem-molecule-rdkit`, `chem-molecule-pubchem` |
| reaction_steps | BIE block library (bie/brain/video/blocks) (demo proven) | Cantera (demo proven), RDKit (demo proven) | — | — | `chem-reaction` |
| equation_transform | KaTeX (demo proven) | SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-equation` |
| protein_3d | 3Dmol.js (demo proven), Mol* (demo proven) | Biopython (demo proven) | NIH 3D (demo proven), RCSB Protein Data Bank (demo proven) | — | `bio-protein-3dmol`, `bio-protein-molstar` |

### Maths and statistics

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| function_graph | D3 (demo proven) | SciPy (demo proven), statsmodels (demo proven), SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-function-graph`, `maths-regression`, `maths-manim`, `physics-falling` |
| equation_transform | KaTeX (demo proven) | SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-equation` |
| vector_field | Manim (Community Edition) (demo proven) | NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | none yet |
| network_graph | D3 (demo proven) | NetworkX (demo proven) | — | — | `cs-graph-bfs` |
| chart_bar_line_pie | D3 (demo proven) | statsmodels (demo proven) | — | — | `chem-reaction`, `maths-regression` |

### Physics

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| circuit_diagram | **missing** | — | — | — | none yet |
| signal_plot | D3 (demo proven) | NumPy (demo proven), SciPy (demo proven), NeuroKit2 (demo proven) | — | — | `bio-ecg` |
| function_graph | D3 (demo proven) | SciPy (demo proven), SymPy (demo proven), statsmodels (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-function-graph`, `maths-regression`, `maths-manim`, `physics-falling` |
| equation_transform | KaTeX (demo proven) | SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-equation` |
| vector_field | Manim (Community Edition) (demo proven) | NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | none yet |
| physics_sim_2d | Matter.js (demo proven), D3 (demo proven) | SciPy (demo proven) | — | — | `physics-falling`, `physics-matter` |
| physics_sim_3d | three.js (demo proven), @react-three/drei (demo proven), React Three Fiber (demo proven) | cannon-es (demo proven) | — | — | `physics-collision-3d` |
| wave_motion | D3 (demo proven) | NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | `physics-wave` |
| orbit_motion | **missing** | — | — | — | none yet |
| flight_motion | **missing** | — | — | — | none yet |
| earthquake_waves | **missing** | — | — | — | none yet |

### Computer science

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| flowchart | **missing** | NetworkX (demo proven) | — | — | none yet |
| network_graph | D3 (demo proven) | NetworkX (demo proven) | — | — | `cs-graph-bfs` |

### Electrical and electronics

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| circuit_diagram | **missing** | — | — | — | none yet |
| signal_plot | D3 (demo proven) | SciPy (demo proven), NumPy (demo proven), NeuroKit2 (demo proven) | — | — | `bio-ecg` |
| vector_field | Manim (Community Edition) (demo proven) | NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | none yet |
| wave_motion | D3 (demo proven) | NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | `physics-wave` |

### Mechanical and civil

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| physics_sim_2d | Matter.js (demo proven), D3 (demo proven) | SciPy (demo proven) | — | — | `physics-falling`, `physics-matter` |
| physics_sim_3d | three.js (demo proven), @react-three/drei (demo proven), React Three Fiber (demo proven) | cannon-es (demo proven) | — | — | `physics-collision-3d` |
| machine_part_3d | three.js (demo proven) | trimesh (demo proven) | — | Blender (bpy, headless) (demo proven) | none yet |
| structure_load | **missing** | — | — | — | none yet |

### Geology and earth science

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| wave_motion | D3 (demo proven) | NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | `physics-wave` |
| map_region | **missing** | — | — | — | none yet |
| map_route | **missing** | — | — | — | none yet |
| terrain_or_layers | **missing** | — | — | — | none yet |
| earthquake_waves | **missing** | — | — | — | none yet |
| plate_motion | **missing** | — | — | — | none yet |
| process_cycle | **missing** | — | — | — | none yet |

### Astronomy and space

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| orbit_motion | **missing** | — | — | — | none yet |
| sky_map | **missing** | — | — | — | none yet |

### Aerospace

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| aircraft_shape | **missing** | — | — | — | none yet |
| flight_motion | **missing** | — | — | — | none yet |

### Geography, history and polity

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| sky_map | **missing** | — | — | — | none yet |
| map_region | **missing** | — | — | — | none yet |
| map_route | **missing** | — | — | — | none yet |
| terrain_or_layers | **missing** | — | — | — | none yet |
| plate_motion | **missing** | — | — | — | none yet |
| timeline | BIE block library (bie/brain/video/blocks) (demo proven) | — | — | — | none yet |

### Economics, commerce and management

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| function_graph | D3 (demo proven) | statsmodels (demo proven), SciPy (demo proven), SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-function-graph`, `maths-regression`, `maths-manim`, `physics-falling` |
| map_region | **missing** | — | — | — | none yet |
| network_graph | D3 (demo proven) | NetworkX (demo proven) | — | — | `cs-graph-bfs` |
| chart_bar_line_pie | D3 (demo proven) | statsmodels (demo proven) | — | — | `chem-reaction`, `maths-regression` |
| case_card | **missing** | — | — | — | none yet |

### Law

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| flowchart | **missing** | NetworkX (demo proven) | — | — | none yet |
| case_card | **missing** | — | — | — | none yet |

### Psychology, education and sociology

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| anatomy_3d | three.js (demo proven), @react-three/drei (demo proven), React Three Fiber (demo proven) | trimesh (demo proven) | Z-Anatomy (demo proven), BodyParts3D (demo proven), NIH 3D (demo proven) | Blender (bpy, headless) (demo proven) | `bio-heart-nih3d`, `bio-heart-zanatomy`, `bio-heart-bodyparts3d` |
| case_card | **missing** | — | — | — | none yet |

### Languages and literature

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| text_kinetic | **missing** | — | — | — | none yet |

## Every tool

| Tool | Kind | Role / path | Version | Licence | Flags | Status | Batch |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Blender (bpy, headless)](https://pypi.org/project/bpy/) | app | offline_render / offline | 5.2.2 | GPL-3.0-or-later (the program); models BIE makes with it are BIE's own | GPL | demo proven | 1 |
| [BodyParts3D](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html) | asset_source | asset / offline | 4.0 (PART-OF tree, 99% reduced OBJ) | CC BY 4.0 (licence page read 25 October 2026; releases up to 3.0 were CC BY-SA 2.1 Japan; the page also asks users to contact DBCLS) | own licence | demo proven | 1 |
| [NIH 3D](https://3d.nih.gov) | asset_source | asset / web | 3d.nih.gov API (entries, download) | per model (Public Domain / CC0, CC BY and others) | licence per item | demo proven | 1 |
| [Servier Medical Art](https://smart.servier.com) | asset_source | asset / web | SMART 2026-10 (site) | CC BY 4.0 | — | demo proven | 1 |
| [Z-Anatomy](https://github.com/LluisV/Z-Anatomy) | asset_source | asset / offline | PC-Version branch (FBX systems) | CC BY-SA 4.0 | share-alike | demo proven | 1 |
| [PubChem](https://pubchem.ncbi.nlm.nih.gov) | dataset | asset / web | PUG REST (live) | Public domain (NCBI); a few depositor records carry their own terms | licence per item | demo proven | 1 |
| [RCSB Protein Data Bank](https://www.rcsb.org) | dataset | asset / web | files.rcsb.org (live archive) | CC0 1.0 (PDB data) | — | demo proven | 1 |
| [3Dmol.js](https://github.com/3dmol/3Dmol.js) | js_lib | draw / web | 2.5.5 | BSD-3-Clause | — | demo proven | 1 |
| [BIE block library (bie/brain/video/blocks)](https://github.com/SEENAV01/Enterprise-bie) | js_lib | draw / web | bie-2026-10-25 | BIE's own code | — | demo proven | 1 |
| [cannon-es](https://github.com/pmndrs/cannon-es) | js_lib | compute / web | 0.20.0 | MIT | — | demo proven | 1 |
| [D3](https://github.com/d3/d3) | js_lib | draw / web | 7.9.0 | ISC | — | demo proven | 1 |
| [@react-three/drei](https://github.com/pmndrs/drei) | js_lib | draw / web | 10.7.9 | MIT | — | demo proven | 1 |
| [KaTeX](https://github.com/KaTeX/KaTeX) | js_lib | draw / web | 0.19.0 | MIT | — | demo proven | 1 |
| [Matter.js](https://github.com/liabru/matter-js) | js_lib | draw / web | 0.20.0 | MIT | — | demo proven | 1 |
| [Mol*](https://github.com/molstar/molstar) | js_lib | draw / web | 5.13.1 | MIT | — | demo proven | 1 |
| [React Three Fiber](https://github.com/pmndrs/react-three-fiber) | js_lib | draw / web | 9.8.2 | MIT | — | demo proven | 1 |
| [Remotion](https://www.remotion.dev/license) | js_lib | draw / web | 4.0.536 | Remotion License: free for individuals and companies of up to 3 people; a paid company licence above that | own licence | demo proven | 1 |
| [@remotion/three](https://www.npmjs.com/package/@remotion/three) | js_lib | draw / web | 4.0.536 | MIT | — | demo proven | 1 |
| [three.js](https://github.com/mrdoob/three.js) | js_lib | draw / web | 0.186.1 | MIT | — | demo proven | 1 |
| [Biopython](https://biopython.org) | python_lib | compute / python | 1.88 | Biopython License Agreement (BSD-style) | — | demo proven | 1 |
| [Cantera](https://cantera.org) | python_lib | compute / python | 3.2.0 | BSD-3-Clause | — | demo proven | 1 |
| [Manim (Community Edition)](https://www.manim.community) | python_lib | offline_render / offline | 0.22.0 | MIT | — | demo proven | 1 |
| [NetworkX](https://networkx.org) | python_lib | compute / python | 3.7 | BSD-3-Clause | — | demo proven | 1 |
| [NeuroKit2](https://github.com/neuropsychology/NeuroKit) | python_lib | compute / python | 0.2.13 | MIT | — | demo proven | 1 |
| [NumPy](https://numpy.org) | python_lib | compute / python | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | — | demo proven | 1 |
| [RDKit](https://www.rdkit.org) | python_lib | compute / python | 2026.9.1 | BSD-3-Clause | — | demo proven | 1 |
| [SciPy](https://scipy.org) | python_lib | compute / python | 1.18.1 | BSD-3-Clause | — | demo proven | 1 |
| [statsmodels](https://www.statsmodels.org) | python_lib | compute / python | 0.15.0 | BSD-3-Clause | — | demo proven | 1 |
| [SymPy](https://www.sympy.org) | python_lib | compute / python | 1.14.0 | BSD-3-Clause | — | demo proven | 1 |
| [trimesh](https://github.com/mikedh/trimesh) | python_lib | compute / python | 5.1.1 | MIT | — | demo proven | 1 |

## Blocked, and what each needs

- Nothing is blocked.

## Missing capabilities

Capabilities in the vocabulary that no tool in the registry can draw yet (later batches, or the Task 046 merge path: an AI writes the block once, BIE tests it, Navin approves it):

- mnemonic_card: a memory trick on a card
- split_compare: two or more things side by side (added from the Task 046 benchmark)
- circuit_diagram: an electric circuit drawn part by part
- orbit_motion: bodies in orbit
- sky_map: the sky as seen from a place and time
- aircraft_shape: an aircraft or wing shape in 3D
- flight_motion: a flight path or flight dynamics
- map_region: a map with a region highlighted
- map_route: a route drawn on a map
- terrain_or_layers: terrain, relief or layers of the earth
- earthquake_waves: seismic waves spreading and recorded
- plate_motion: tectonic plates moving over time
- flowchart: a flowchart that builds step by step
- process_cycle: a cycle of stages
- tree_hierarchy: a family tree or hierarchy that grows
- case_card: a card for a case, judgment or example
- structure_load: a structure under load (beam, truss) with its deflection
- text_kinetic: a sentence animated word by word (Devanagari and Roman)

## Licences to decide (Navin)

Recorded, not blocked. Share-alike content may make an adapted video carry the same licence; a GPL program's outputs (the models BIE makes) are not GPL; Remotion needs a company licence above 3 people.

- Remotion: Remotion License: free for individuals and companies of up to 3 people; a paid company licence above that
- Blender (bpy, headless): GPL-3.0-or-later (the program); models BIE makes with it are BIE's own
- Z-Anatomy: CC BY-SA 4.0
- BodyParts3D: CC BY 4.0 (licence page read 25 October 2026; releases up to 3.0 were CC BY-SA 2.1 Japan; the page also asks users to contact DBCLS)
