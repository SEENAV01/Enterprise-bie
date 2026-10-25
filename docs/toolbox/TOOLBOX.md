# BIE toolbox (auzaar-ghar)

BIE ka auzaar-ghar: har library, tool aur asset source jo BIE kisi bhi scene ko dikhane ke liye use karta hai. A Python library computes, a BIE block shows.

Registry `2026-10-25.1`, capabilities `2026-10-25.1`, npm packages as of `2026-10-17T12:00:00Z`. Tools: 59 (demo proven 57, blocked 2).

Status words: **installed** (the package is pinned and installs), **wrapped** (a BIE adapter or block uses it, with tests), **demo proven** (a BIE-made clip shows it working), **used on a real book** (it drew part of a real lesson), **blocked** (the reason says what it needs). Nothing here is ACCEPTED: that is Navin's verdict.

## Proof clips (batch 1, 2)

35 of 35 clips passed the checks (not blank, something moves, 3–5 s). Rendered on the cloud workspace on 25 October 2026 (batch 1 about 31 minutes, batch 2 about 20); CI renders each batch again in the demos job of every toolbox PR (artifacts bie-toolbox-demos-batch-1 and -2). Bridge: bio-cell-sheet-flow rendered again by real Remotion 4.0.536, mean frame difference 0.0 on all six frames.

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
| `aero-aircraft` | A trainer aircraft and its lift curve from AeroSandbox | aerosandbox, trimesh, three, react-three-fiber, drei, remotion-three, d3, bie-science-blocks | 4.2 s | passed |
| `aero-climb` | A Cessna 172 climb simulated by JSBSim | jsbsim, d3, bie-science-blocks | 4.2 s | passed |
| `astro-earthrise` | Earthrise from NASA's image library, zoom and focus | nasa-images, bie-blocks | 4.2 s | passed |
| `astro-orbits` | The inner planets' orbits from JPL DE421 (Skyfield, Astropy) | skyfield, astropy, jpl-de421, d3, bie-science-blocks | 4.2 s | passed |
| `astro-sky` | The night sky over New Delhi from the Hipparcos catalogue (Skyfield) | skyfield, astropy, hipparcos, jpl-de421, bie-science-blocks | 4.0 s | passed |
| `elec-rc-circuit` | An RC circuit drawn by schemdraw, simulated by ngspice, solved by lcapy | schemdraw, ngspice, lcapy, katex, d3, bie-science-blocks | 4.6 s | passed |
| `elec-step-response` | Step responses for three damping ratios (python-control, checked by scipy.signal) | python-control, scipy-signal, katex, d3, bie-science-blocks | 4.2 s | passed |
| `geo-plates` | Continents drifting over 200 million years by pyGPlates | pygplates, gplates-muller2019, d3, bie-science-blocks | 4.2 s | passed |
| `geo-quake-map` | 2025's strong earthquakes from the USGS on a Natural Earth map | usgs-earthquakes, natural-earth, topojson-client, d3, bie-science-blocks | 4.2 s | passed |
| `geo-relief` | Himalaya relief and profile by PyGMT | pygmt, gmt, gmt-earth-relief, bie-blocks, d3, bie-science-blocks | 4.2 s | passed |
| `geo-seismic-rays` | Seismic rays through the Earth's layers by ObsPy TauP | obspy, bie-science-blocks | 4.2 s | passed |
| `mech-beam` | A loaded steel beam bends (PyNite, checked by sympy.physics) | pynite, sympy-physics, bie-science-blocks | 4.0 s | passed |
| `mech-flange` | A pipe flange built by CadQuery, turning in three.js | cadquery, trimesh, three, react-three-fiber, drei, remotion-three | 4.0 s | passed |
| `mech-heat-plate` | Heat flow in a plate by scikit-fem | scikit-fem, d3, bie-science-blocks | 4.0 s | passed |
| `mech-rankine` | A Rankine steam cycle on a T-s chart from CoolProp | coolprop, d3, bie-science-blocks | 4.2 s | passed |

## By subject family

### All subjects

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| particle_flow | BIE block library (bie/brain/video/blocks) (demo proven), three.js (demo proven) | — | — | — | `bio-cell-sheet-flow` |
| organ_zoom | BIE block library (bie/brain/video/blocks) (demo proven) | — | Servier Medical Art (demo proven), Z-Anatomy (demo proven) | — | `bio-organ-zoom`, `bio-heart-bodyparts3d` |
| focus_glow | BIE block library (bie/brain/video/blocks) (demo proven) | — | NASA Image and Video Library (demo proven) | — | `bio-cell-sheet-flow`, `bio-organ-zoom`, `bio-heart-zanatomy`, `astro-earthrise` |
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
| signal_plot | D3 (demo proven), BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | NeuroKit2 (demo proven), SciPy signal (scipy.signal) (demo proven), NumPy (demo proven) | — | — | `bio-ecg`, `elec-rc-circuit`, `elec-step-response` |
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
| function_graph | D3 (demo proven), BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | SciPy (demo proven), statsmodels (demo proven), SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-function-graph`, `maths-regression`, `maths-manim`, `physics-falling`, `mech-rankine` |
| equation_transform | KaTeX (demo proven) | SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-equation` |
| vector_field | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | NumPy (demo proven), scikit-fem (demo proven) | — | Manim (Community Edition) (demo proven) | `mech-heat-plate` |
| network_graph | D3 (demo proven) | NetworkX (demo proven) | — | — | `cs-graph-bfs` |
| chart_bar_line_pie | D3 (demo proven) | statsmodels (demo proven) | — | — | `chem-reaction`, `maths-regression` |

### Physics

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| circuit_diagram | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Lcapy (demo proven), ngspice (demo proven) | — | — | `elec-rc-circuit` |
| signal_plot | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven), D3 (demo proven) | Lcapy (demo proven), ngspice (demo proven), NumPy (demo proven) | — | — | `bio-ecg`, `elec-rc-circuit`, `elec-step-response` |
| function_graph | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven), D3 (demo proven) | CoolProp (demo proven), SciPy (demo proven), SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-function-graph`, `maths-regression`, `maths-manim`, `physics-falling`, `mech-rankine` |
| equation_transform | KaTeX (demo proven) | SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-equation` |
| vector_field | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | NumPy (demo proven), scikit-fem (demo proven) | — | Manim (Community Edition) (demo proven) | `mech-heat-plate` |
| physics_sim_2d | Matter.js (demo proven), D3 (demo proven) | SciPy (demo proven) | — | — | `physics-falling`, `physics-matter` |
| physics_sim_3d | three.js (demo proven), @react-three/drei (demo proven), React Three Fiber (demo proven) | cannon-es (demo proven) | — | — | `physics-collision-3d` |
| wave_motion | D3 (demo proven) | NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | `physics-wave` |
| orbit_motion | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Astropy (demo proven), Skyfield (demo proven) | JPL ephemeris DE421 (demo proven) | — | `astro-orbits` |
| flight_motion | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | JSBSim (demo proven) | — | — | `aero-climb` |
| earthquake_waves | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | ObsPy (demo proven) | USGS earthquake catalogue (demo proven) | — | `geo-seismic-rays` |

### Computer science

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| flowchart | **missing** | NetworkX (demo proven) | — | — | none yet |
| network_graph | D3 (demo proven) | NetworkX (demo proven) | — | — | `cs-graph-bfs` |

### Electrical and electronics

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| circuit_diagram | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Lcapy (demo proven), ngspice (demo proven) | — | — | `elec-rc-circuit` |
| signal_plot | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven), D3 (demo proven) | Lcapy (demo proven), ngspice (demo proven), Python Control Systems Library (demo proven) | — | — | `bio-ecg`, `elec-rc-circuit`, `elec-step-response` |
| vector_field | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | scikit-fem (demo proven), NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | `mech-heat-plate` |
| wave_motion | D3 (demo proven) | NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | `physics-wave` |

### Mechanical and civil

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| physics_sim_2d | Matter.js (demo proven), D3 (demo proven) | SciPy (demo proven) | — | — | `physics-falling`, `physics-matter` |
| physics_sim_3d | three.js (demo proven), @react-three/drei (demo proven), React Three Fiber (demo proven) | cannon-es (demo proven) | — | — | `physics-collision-3d` |
| machine_part_3d | three.js (demo proven) | trimesh (demo proven) | — | Blender (bpy, headless) (demo proven), CadQuery (with OCP, OpenCascade) (demo proven) | `mech-flange` |
| structure_load | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | PyNite (PyNiteFEA) (demo proven), SymPy physics (sympy.physics) (demo proven) | — | — | `mech-beam` |

### Geology and earth science

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| wave_motion | D3 (demo proven) | NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | `physics-wave` |
| map_region | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven), topojson-client (demo proven) | — | Natural Earth (world-atlas TopoJSON) (demo proven), USGS earthquake catalogue (demo proven) | GMT (Generic Mapping Tools) (demo proven), PyGMT (demo proven) | `geo-relief`, `geo-quake-map` |
| map_route | topojson-client (demo proven) | — | Natural Earth (world-atlas TopoJSON) (demo proven) | — | none yet |
| terrain_or_layers | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | ObsPy (demo proven) | GMT Earth relief (SRTM15+ V2.7) (demo proven) | GMT (Generic Mapping Tools) (demo proven), PyGMT (demo proven) | `geo-relief`, `geo-seismic-rays` |
| earthquake_waves | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | ObsPy (demo proven) | USGS earthquake catalogue (demo proven) | — | `geo-seismic-rays` |
| plate_motion | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | pyGPlates (demo proven) | Müller et al. (2019) plate model (demo proven) | — | `geo-plates` |
| process_cycle | **missing** | — | — | — | none yet |

### Astronomy and space

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| orbit_motion | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Astropy (demo proven), Skyfield (demo proven) | JPL ephemeris DE421 (demo proven) | — | `astro-orbits` |
| sky_map | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Astropy (demo proven), Skyfield (demo proven) | Hipparcos star catalogue (demo proven), JPL ephemeris DE421 (demo proven) | — | `astro-sky` |

### Aerospace

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| aircraft_shape | three.js (demo proven) | AeroSandbox (demo proven) | — | — | `aero-aircraft` |
| flight_motion | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | JSBSim (demo proven) | — | — | `aero-climb` |

### Geography, history and polity

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| sky_map | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Skyfield (demo proven), Astropy (demo proven) | Hipparcos star catalogue (demo proven), JPL ephemeris DE421 (demo proven) | — | `astro-sky` |
| map_region | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven), topojson-client (demo proven) | — | Natural Earth (world-atlas TopoJSON) (demo proven), USGS earthquake catalogue (demo proven) | GMT (Generic Mapping Tools) (demo proven), PyGMT (demo proven) | `geo-relief`, `geo-quake-map` |
| map_route | topojson-client (demo proven) | — | Natural Earth (world-atlas TopoJSON) (demo proven) | — | none yet |
| terrain_or_layers | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | ObsPy (demo proven) | GMT Earth relief (SRTM15+ V2.7) (demo proven) | GMT (Generic Mapping Tools) (demo proven), PyGMT (demo proven) | `geo-relief`, `geo-seismic-rays` |
| plate_motion | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | pyGPlates (demo proven) | Müller et al. (2019) plate model (demo proven) | — | `geo-plates` |
| timeline | BIE block library (bie/brain/video/blocks) (demo proven) | — | — | — | none yet |

### Economics, commerce and management

| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| function_graph | D3 (demo proven), BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | statsmodels (demo proven), CoolProp (demo proven), SciPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-function-graph`, `maths-regression`, `maths-manim`, `physics-falling`, `mech-rankine` |
| map_region | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven), topojson-client (demo proven) | — | Natural Earth (world-atlas TopoJSON) (demo proven), USGS earthquake catalogue (demo proven) | GMT (Generic Mapping Tools) (demo proven), PyGMT (demo proven) | `geo-relief`, `geo-quake-map` |
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
| [GMT (Generic Mapping Tools)](https://www.generic-mapping-tools.org) | app | offline_render / offline | 6.5.0 | LGPL-3.0-or-later | — | demo proven | 2 |
| [ngspice](https://ngspice.sourceforge.io) | app | compute / offline | 42 | BSD-3-Clause (modified BSD; some parts under other free licences) | — | demo proven | 2 |
| [OpenVSP](https://openvsp.org) | app | offline_render / offline | 3.x (not installed) | NOSA 1.3 (NASA Open Source Agreement) | own licence | blocked | 2 |
| [NASA Image and Video Library](https://images.nasa.gov) | asset_source | asset / web | images-api.nasa.gov (live) | per item (NASA media are generally not copyrighted; some carry third-party rights) | licence per item | demo proven | 2 |
| [GMT Earth relief (SRTM15+ V2.7)](https://www.generic-mapping-tools.org/remote-datasets/earth-relief.html) | dataset | asset / offline | SRTM15+ V2.7 (GMT remote data, 2 arc-min tiles) | Free to use with citation (Tozer et al., 2019, Scripps); GMT remote data | own licence | demo proven | 2 |
| [Müller et al. (2019) plate model](https://doi.org/10.5281/zenodo.11601026) | dataset | asset / offline | v2.0 (doi:10.5281/zenodo.11601026) | CC BY 4.0 | — | demo proven | 2 |
| [Hipparcos star catalogue](https://cdsarc.cds.unistra.fr/viz-bin/cat/I/239) | dataset | asset / offline | ESA 1997 (CDS I/239) | Free for scientific use with citation (CDS); commercial use under ESA's rules for the Hipparcos data | own licence | demo proven | 2 |
| [JPL ephemeris DE421](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de421.bsp) | dataset | asset / offline | DE421 (1900–2050) | Public domain (NASA JPL) | — | demo proven | 2 |
| [Natural Earth (world-atlas TopoJSON)](https://github.com/topojson/world-atlas) | dataset | asset / web | 2.0.2 | Public domain (Natural Earth data); ISC (the world-atlas package) | — | demo proven | 2 |
| [USGS earthquake catalogue](https://earthquake.usgs.gov/fdsnws/event/1/) | dataset | asset / web | FDSN event API (live) | Public domain (USGS) | — | demo proven | 2 |
| [BIE science blocks (bie/brain/video/blocks/toolbox)](https://github.com/SEENAV01/Enterprise-bie) | js_lib | draw / web | bie-2026-10-25 | BIE's own code | — | demo proven | 2 |
| [topojson-client](https://github.com/topojson/topojson-client) | js_lib | draw / web | 3.1.0 | ISC | — | demo proven | 2 |
| [AeroSandbox](https://github.com/peterdsharpe/AeroSandbox) | python_lib | compute / python | 4.2.10 | MIT | — | demo proven | 2 |
| [Astropy](https://www.astropy.org) | python_lib | compute / python | 8.0.2 | BSD-3-Clause | — | demo proven | 2 |
| [CadQuery (with OCP, OpenCascade)](https://github.com/CadQuery/cadquery) | python_lib | offline_render / offline | 2.8.0 | Apache-2.0 (CadQuery and the OCP bindings; OpenCascade itself LGPL-2.1 with an exception) | — | demo proven | 2 |
| [CoolProp](https://github.com/CoolProp/CoolProp) | python_lib | compute / python | 8.0.0 | MIT | — | demo proven | 2 |
| [FEniCSx (DOLFINx)](https://fenicsproject.org) | python_lib | compute / python | 0.10 (not installed) | LGPL-3.0-or-later | — | blocked | 2 |
| [JSBSim](https://github.com/JSBSim-Team/jsbsim) | python_lib | compute / python | 1.3.3 | LGPL-2.1-or-later | — | demo proven | 2 |
| [Lcapy](https://github.com/mph-/lcapy) | python_lib | compute / python | 1.26 | LGPL-2.1-or-later | — | demo proven | 2 |
| [ObsPy](https://www.obspy.org) | python_lib | compute / python | 1.5.1 | LGPL-3.0 | — | demo proven | 2 |
| [PyGMT](https://www.pygmt.org) | python_lib | offline_render / offline | 0.19.0 | BSD-3-Clause | — | demo proven | 2 |
| [pyGPlates](https://www.gplates.org) | python_lib | compute / python | 1.0.0 | GPL-2.0 (pyGPlates; GPlates is GPL-2.0-or-later) | GPL | demo proven | 2 |
| [PyNite (PyNiteFEA)](https://github.com/JWock82/Pynite) | python_lib | compute / python | 3.2.0 | MIT | — | demo proven | 2 |
| [Python Control Systems Library](https://python-control.org) | python_lib | compute / python | 0.10.2 | BSD-3-Clause | — | demo proven | 2 |
| [Schemdraw](https://schemdraw.readthedocs.io) | python_lib | draw / python | 0.23 | MIT | — | demo proven | 2 |
| [scikit-fem](https://github.com/kinnala/scikit-fem) | python_lib | compute / python | 12.0.2 | BSD-3-Clause | — | demo proven | 2 |
| [SciPy signal (scipy.signal)](https://docs.scipy.org/doc/scipy/reference/signal.html) | python_lib | compute / python | 1.18.1 | BSD-3-Clause | — | demo proven | 2 |
| [Skyfield](https://rhodesmill.org/skyfield/) | python_lib | compute / python | 1.55 | MIT | — | demo proven | 2 |
| [SymPy physics (sympy.physics)](https://docs.sympy.org/latest/modules/physics/) | python_lib | compute / python | 1.14.0 | BSD-3-Clause | — | demo proven | 2 |

## Blocked, and what each needs

- **FEniCSx (DOLFINx)**: DOLFINx has no PyPI wheel: it installs from conda-forge, Docker or Ubuntu's apt (python3-dolfinx, built for the system Python 3.12), while BIE's toolbox runs on Python 3.13 with pip. Needs a separate conda or Docker lane; scikit-fem covers the textbook finite-element cases meanwhile.
- **OpenVSP**: OpenVSP is not on PyPI: its Python API ships only inside OpenVSP's own release builds, compiled for one Python version, and there is no Ubuntu apt package. Needs a pinned OpenVSP build in its own lane; AeroSandbox builds aircraft shapes meanwhile.

## Missing capabilities

Capabilities in the vocabulary that no tool in the registry can draw yet (later batches, or the Task 046 merge path: an AI writes the block once, BIE tests it, Navin approves it):

- mnemonic_card: a memory trick on a card
- split_compare: two or more things side by side (added from the Task 046 benchmark)
- flowchart: a flowchart that builds step by step
- process_cycle: a cycle of stages
- tree_hierarchy: a family tree or hierarchy that grows
- case_card: a card for a case, judgment or example
- text_kinetic: a sentence animated word by word (Devanagari and Roman)

## Licences to decide (Navin)

Recorded, not blocked. Share-alike content may make an adapted video carry the same licence; a GPL program's outputs (the models BIE makes) are not GPL; Remotion needs a company licence above 3 people.

- Remotion: Remotion License: free for individuals and companies of up to 3 people; a paid company licence above that
- Blender (bpy, headless): GPL-3.0-or-later (the program); models BIE makes with it are BIE's own
- Z-Anatomy: CC BY-SA 4.0
- BodyParts3D: CC BY 4.0 (licence page read 25 October 2026; releases up to 3.0 were CC BY-SA 2.1 Japan; the page also asks users to contact DBCLS)
- GMT Earth relief (SRTM15+ V2.7): Free to use with citation (Tozer et al., 2019, Scripps); GMT remote data
- pyGPlates: GPL-2.0 (pyGPlates; GPlates is GPL-2.0-or-later)
- Hipparcos star catalogue: Free for scientific use with citation (CDS); commercial use under ESA's rules for the Hipparcos data
- OpenVSP: NOSA 1.3 (NASA Open Source Agreement)
