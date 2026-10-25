# BIE toolbox (auzaar-ghar)

BIE ka auzaar-ghar: har library, tool aur asset source jo BIE kisi bhi scene ko dikhane ke liye use karta hai. A Python library computes, a BIE block shows.

Registry `2026-10-25.3`, capabilities `2026-10-25.1`, npm packages as of `2026-10-17T12:00:00Z`. Tools: 80 (demo proven 78, blocked 2).

Status words: **installed** (the package is pinned and installs), **wrapped** (a BIE adapter or block uses it, with tests), **demo proven** (a BIE-made clip shows it working), **used on a real book** (it drew part of a real lesson), **blocked** (the reason says what it needs). Nothing here is ACCEPTED: that is Navin's verdict.

## Proof clips (batch 1, 2, 3)

50 of 51 clips passed the checks (not blank, something moves, 3–5 s). Rendered in the cloud workspace for all three batches. hist-archive-images could not run there: Wikimedia answers 429 (too many requests) to the workspace's shared address; the toolbox CI lane renders it.

Proof clips are internal proofs of the tools, not lessons. A clip whose content a lesson may not use (licence policy `2026-10-25.1`) is marked **internal proof, not for lessons**; it stays as evidence.

| Clip | What it shows | Tools it proves | Length | Checks | Lesson use |
| --- | --- | --- | --- | --- | --- |
| `bio-cell-sheet-flow` | Blender-made columnar epithelium in three.js with particles flowing through | blender, three, react-three-fiber, drei, remotion-three | 4.5 s | passed | lessons may use its content |
| `bio-ecg` | An ECG simulated by NeuroKit2 drawn on its paper | neurokit2, d3 | 4.2 s | passed | lessons may use its content |
| `bio-heart-bodyparts3d` | BodyParts3D heart joined by trimesh, zooming in | bodyparts3d, trimesh, three, react-three-fiber, drei, remotion-three | 4.0 s | passed | **internal proof, not for lessons**: bodyparts3d: needs Navin |
| `bio-heart-nih3d` | NIH 3D heart model turning | nih-3d, three, react-three-fiber, drei, remotion-three | 4.0 s | passed | lessons may use its content |
| `bio-heart-zanatomy` | Z-Anatomy heart chambers exported by Blender, left ventricle glowing | z-anatomy, blender, three, react-three-fiber, drei, remotion-three | 4.0 s | passed | **internal proof, not for lessons**: z-anatomy: refused |
| `bio-organ-zoom` | Lung to alveolus zoom on Servier pictures | servier-medical-art, bie-blocks | 5.0 s | passed | lessons may use its content |
| `bio-protein-3dmol` | Crambin from the PDB, read by Biopython, drawn by 3Dmol.js | rcsb-pdb, biopython, 3dmol | 4.0 s | passed | lessons may use its content |
| `bio-protein-molstar` | Green fluorescent protein in Mol* | molstar, rcsb-pdb | 4.0 s | passed | lessons may use its content |
| `chem-molecule-pubchem` | Caffeine's 3D record from PubChem | pubchem, 3dmol | 3.5 s | passed | lessons may use its content |
| `chem-molecule-rdkit` | Aspirin in 3D from RDKit, drawn by 3Dmol.js | rdkit, 3dmol | 4.0 s | passed | lessons may use its content |
| `chem-reaction` | Esterification by RDKit and H2 + O2 kinetics by Cantera | rdkit, cantera, d3, bie-blocks | 5.0 s | passed | lessons may use its content |
| `cs-graph-bfs` | Breadth-first search on a graph | networkx, d3 | 4.5 s | passed | lessons may use its content |
| `maths-equation` | A linear equation solved step by step, every step checked by SymPy, typeset by KaTeX | sympy, katex | 4.5 s | passed | lessons may use its content |
| `maths-function-graph` | A parabola drawn over time | sympy, numpy, d3 | 4.0 s | passed | lessons may use its content |
| `maths-manim` | A function drawn by Manim (offline path) | manim, sympy | 4.1 s | passed | lessons may use its content |
| `maths-regression` | A least-squares line fitted by statsmodels | statsmodels, d3 | 4.0 s | passed | lessons may use its content |
| `physics-collision-3d` | A ball passes its momentum on and knocks a tower over (3D) | cannon-es, three, react-three-fiber, drei, remotion-three | 4.0 s | passed | lessons may use its content |
| `physics-falling` | A falling body with and without air drag | scipy, numpy, d3 | 4.0 s | passed | lessons may use its content |
| `physics-matter` | Boxes and a ball under gravity | matter-js | 4.0 s | passed | lessons may use its content |
| `physics-wave` | Two travelling waves make a standing wave | numpy, d3 | 4.0 s | passed | lessons may use its content |
| `aero-aircraft` | A trainer aircraft and its lift curve from AeroSandbox | aerosandbox, trimesh, three, react-three-fiber, drei, remotion-three, d3, bie-science-blocks | 4.2 s | passed | lessons may use its content |
| `aero-climb` | A Cessna 172 climb simulated by JSBSim | jsbsim, d3, bie-science-blocks | 4.2 s | passed | lessons may use its content |
| `astro-earthrise` | Earthrise from NASA's image library, zoom and focus | nasa-images, bie-blocks | 4.2 s | passed | lessons may use its content |
| `astro-orbits` | The inner planets' orbits from JPL DE421 (Skyfield, Astropy) | skyfield, astropy, jpl-de421, d3, bie-science-blocks | 4.2 s | passed | lessons may use its content |
| `astro-sky` | The night sky over New Delhi from the Hipparcos catalogue (Skyfield) | skyfield, astropy, hipparcos, jpl-de421, bie-science-blocks | 4.0 s | passed | **internal proof, not for lessons**: hipparcos: needs Navin |
| `elec-rc-circuit` | An RC circuit drawn by schemdraw, simulated by ngspice, solved by lcapy | schemdraw, ngspice, lcapy, katex, d3, bie-science-blocks | 4.6 s | passed | lessons may use its content |
| `elec-step-response` | Step responses for three damping ratios (python-control, checked by scipy.signal) | python-control, scipy-signal, katex, d3, bie-science-blocks | 4.2 s | passed | lessons may use its content |
| `geo-plates` | Continents drifting over 200 million years by pyGPlates | pygplates, gplates-muller2019, d3, bie-science-blocks | 4.2 s | passed | lessons may use its content |
| `geo-quake-map` | 2025's strong earthquakes from the USGS on a Natural Earth map | usgs-earthquakes, natural-earth, topojson-client, d3, bie-science-blocks | 4.2 s | passed | lessons may use its content |
| `geo-relief` | Himalaya relief and profile by PyGMT | pygmt, gmt, gmt-earth-relief, bie-blocks, d3, bie-science-blocks | 4.2 s | passed | **internal proof, not for lessons**: gmt-earth-relief: needs Navin |
| `geo-seismic-rays` | Seismic rays through the Earth's layers by ObsPy TauP | obspy, bie-science-blocks | 4.2 s | passed | lessons may use its content |
| `mech-beam` | A loaded steel beam bends (PyNite, checked by sympy.physics) | pynite, sympy-physics, bie-science-blocks | 4.0 s | passed | lessons may use its content |
| `mech-flange` | A pipe flange built by CadQuery, turning in three.js | cadquery, trimesh, three, react-three-fiber, drei, remotion-three | 4.0 s | passed | lessons may use its content |
| `mech-heat-plate` | Heat flow in a plate by scikit-fem | scikit-fem, d3, bie-science-blocks | 4.0 s | passed | lessons may use its content |
| `mech-rankine` | A Rankine steam cycle on a T-s chart from CoolProp | coolprop, d3, bie-science-blocks | 4.2 s | passed | lessons may use its content |
| `econ-cobb-douglas-plotly` | A Cobb-Douglas production function in Plotly | numpy, plotly, bie-social-blocks | 4.2 s | passed | lessons may use its content |
| `econ-growth-chartjs` | India's GDP growth from the World Bank in Chart.js | world-bank, chartjs, bie-social-blocks | 4.2 s | passed | lessons may use its content |
| `econ-wealth-health-vega` | Wealth and health of eight countries in Vega-Lite | world-bank, vega-lite, vega, bie-social-blocks | 4.2 s | passed | lessons may use its content |
| `edu-learning-cycle` | Kolb's learning cycle as a process cycle | bie-social-blocks | 4.0 s | passed | lessons may use its content |
| `edu-teaching-logit` | A teaching method's effect by statsmodels (logit) | statsmodels, d3, bie-science-blocks | 4.2 s | passed | lessons may use its content |
| `geo-india-state` | Uttar Pradesh on India's map (Natural Earth, Shapely, d3-geo) | natural-earth-vector, shapely, d3, bie-social-blocks | 4.2 s | passed | **internal proof, not for lessons**: block india_map: needs Navin |
| `hist-archive-images` | The Salt March from Wikimedia Commons and Openverse | wikimedia-commons, openverse, bie-blocks | — s | failed: HTTPError: HTTP Error 429: Too many requests (f061ab2) | lessons may use its content |
| `hist-gt-road` | The Grand Trunk Road drawn town by town | natural-earth-vector, shapely, d3, bie-social-blocks | 4.2 s | passed | **internal proof, not for lessons**: block india_map: needs Navin |
| `hist-timeline` | Towards independence, 1857 to 1950, on a D3 time scale | d3, bie-social-blocks | 4.2 s | passed | lessons may use its content |
| `lang-kinetic-sanskrit` | A Sanskrit line word by word in Devanagari and Roman | indic-nlp, indic-transliteration, noto-devanagari, bie-social-blocks | 4.2 s | passed | lessons may use its content |
| `law-case-card` | Kesavananda Bharati v. State of Kerala as a case card | sc-judgments, pyarrow, bie-social-blocks | 4.4 s | passed | lessons may use its content |
| `law-courts-tree` | Classes of criminal courts (BNSS s. 6) as a tree | india-code, d3, bie-social-blocks | 4.0 s | passed | **internal proof, not for lessons**: india-code: needs Navin |
| `law-procedure-flow` | A criminal case from FIR to judgment, sections from India Code | india-code, dagre, bie-social-blocks | 4.2 s | passed | **internal proof, not for lessons**: india-code: needs Navin |
| `polity-bill-mermaid` | How a Bill becomes an Act, in Mermaid with the ELK layout | mermaid, mermaid-layout-elk, elkjs, bie-social-blocks | 4.2 s | passed | lessons may use its content |
| `psy-brain-lobes` | The brain lobe by lobe (Z-Anatomy, Blender, three.js) | z-anatomy, blender, three, react-three-fiber, drei, remotion-three | 4.2 s | passed | **internal proof, not for lessons**: z-anatomy: refused |
| `psy-stroop-flow` | The Stroop experiment designed by PsychoPy | psychopy, bie-social-blocks | 4.2 s | passed | lessons may use its content |

## By subject family

### All subjects

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| particle_flow | BIE block library (bie/brain/video/blocks) (demo proven), three.js (demo proven) | — | — | — | `bio-cell-sheet-flow` |
| organ_zoom | BIE block library (bie/brain/video/blocks) (demo proven) | — | Openverse (demo proven), Wikimedia Commons (demo proven), Servier Medical Art (demo proven); not for lessons: z-anatomy | — | `bio-organ-zoom`, `bio-heart-bodyparts3d` |
| focus_glow | BIE block library (bie/brain/video/blocks) (demo proven) | — | Openverse (demo proven), Wikimedia Commons (demo proven), NASA Image and Video Library (demo proven) | — | `bio-cell-sheet-flow`, `bio-organ-zoom`, `bio-heart-zanatomy`, `astro-earthrise`, `hist-archive-images` (not passed) |
| kinetic_caption | BIE block library (bie/brain/video/blocks) (demo proven) | Indic NLP Library (demo proven) | Noto Sans Devanagari (font) (demo proven) | — | none yet |
| concept_arrow | BIE block library (bie/brain/video/blocks) (demo proven) | — | — | — | none yet |
| board_build | BIE block library (bie/brain/video/blocks) (demo proven) | — | — | — | none yet |
| mnemonic_card | **missing** | — | — | — | none yet |
| split_compare | **missing** | — | — | — | none yet |
| timeline | BIE block library (bie/brain/video/blocks) (demo proven), BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven), D3 (demo proven) | — | — | — | `hist-timeline` |
| flowchart | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven), dagre (@dagrejs/dagre) (demo proven), elkjs (Eclipse Layout Kernel) (demo proven) | NetworkX (demo proven), PsychoPy (psychopy.data) (demo proven) | **none**; not for lessons: india-code | — | `polity-bill-mermaid`, `law-procedure-flow`, `psy-stroop-flow` |
| process_cycle | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven) | — | — | — | `edu-learning-cycle` |
| tree_hierarchy | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven), D3 (demo proven), Mermaid (demo proven) | NetworkX (demo proven) | **none**; not for lessons: india-code | — | `law-courts-tree` |
| chart_bar_line_pie | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven), D3 (demo proven), Chart.js (demo proven) | statsmodels (demo proven) | World Bank Indicators API (World Development Indicators) (demo proven) | — | `chem-reaction`, `maths-regression`, `econ-growth-chartjs`, `econ-wealth-health-vega`, `edu-teaching-logit` |
| table_build | BIE block library (bie/brain/video/blocks) (demo proven) | — | — | — | none yet |
| text_kinetic | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Indic NLP Library (demo proven), indic_transliteration (sanscript) (demo proven) | Noto Sans Devanagari (font) (demo proven) | — | `lang-kinetic-sanskrit` |

### Biology and medical

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| cell_sheet_3d | three.js (demo proven), @react-three/drei (demo proven), React Three Fiber (demo proven) | — | — | Blender (bpy, headless) (demo proven) | `bio-cell-sheet-flow` |
| organ_zoom | BIE block library (bie/brain/video/blocks) (demo proven) | — | Servier Medical Art (demo proven), Openverse (demo proven), Wikimedia Commons (demo proven); not for lessons: z-anatomy | — | `bio-organ-zoom`, `bio-heart-bodyparts3d` |
| anatomy_3d | three.js (demo proven), @react-three/drei (demo proven), React Three Fiber (demo proven) | trimesh (demo proven) | NIH 3D (demo proven), Servier Medical Art (demo proven); not for lessons: bodyparts3d, z-anatomy | Blender (bpy, headless) (demo proven) | `bio-heart-nih3d`, `bio-heart-zanatomy`, `bio-heart-bodyparts3d`, `psy-brain-lobes` |
| molecule_3d | 3Dmol.js (demo proven), Mol* (demo proven) | RDKit (demo proven) | PubChem (demo proven) | — | `chem-molecule-rdkit`, `chem-molecule-pubchem` |
| signal_plot | D3 (demo proven), BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | NeuroKit2 (demo proven), SciPy signal (scipy.signal) (demo proven), NumPy (demo proven) | — | — | `bio-ecg`, `elec-rc-circuit`, `elec-step-response` |
| process_cycle | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven) | — | — | — | `edu-learning-cycle` |
| ecg_trace | D3 (demo proven) | NeuroKit2 (demo proven) | — | — | `bio-ecg` |
| protein_3d | 3Dmol.js (demo proven), Mol* (demo proven) | Biopython (demo proven) | NIH 3D (demo proven), RCSB Protein Data Bank (demo proven) | — | `bio-protein-3dmol`, `bio-protein-molstar` |

### Chemistry

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| molecule_3d | 3Dmol.js (demo proven), Mol* (demo proven) | RDKit (demo proven) | PubChem (demo proven) | — | `chem-molecule-rdkit`, `chem-molecule-pubchem` |
| reaction_steps | BIE block library (bie/brain/video/blocks) (demo proven) | Cantera (demo proven), RDKit (demo proven) | — | — | `chem-reaction` |
| equation_transform | KaTeX (demo proven) | SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-equation` |
| protein_3d | 3Dmol.js (demo proven), Mol* (demo proven) | Biopython (demo proven) | NIH 3D (demo proven), RCSB Protein Data Bank (demo proven) | — | `bio-protein-3dmol`, `bio-protein-molstar` |

### Maths and statistics

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| function_graph | Plotly.js (plotly.js-dist-min) (demo proven), BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven), D3 (demo proven) | SciPy (demo proven), statsmodels (demo proven), SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-function-graph`, `maths-regression`, `maths-manim`, `physics-falling`, `mech-rankine`, `econ-cobb-douglas-plotly`, `edu-teaching-logit` |
| equation_transform | KaTeX (demo proven) | SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-equation` |
| vector_field | Plotly.js (plotly.js-dist-min) (demo proven), BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | NumPy (demo proven), scikit-fem (demo proven) | — | Manim (Community Edition) (demo proven) | `mech-heat-plate` |
| network_graph | D3 (demo proven), elkjs (Eclipse Layout Kernel) (demo proven) | NetworkX (demo proven) | — | — | `cs-graph-bfs` |
| chart_bar_line_pie | Plotly.js (plotly.js-dist-min) (demo proven), Vega (demo proven), Vega-Lite (demo proven) | statsmodels (demo proven) | World Bank Indicators API (World Development Indicators) (demo proven) | — | `chem-reaction`, `maths-regression`, `econ-growth-chartjs`, `econ-wealth-health-vega`, `edu-teaching-logit` |

### Physics

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| circuit_diagram | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Lcapy (demo proven), ngspice (demo proven) | — | — | `elec-rc-circuit` |
| signal_plot | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven), D3 (demo proven) | Lcapy (demo proven), ngspice (demo proven), NumPy (demo proven) | — | — | `bio-ecg`, `elec-rc-circuit`, `elec-step-response` |
| function_graph | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven), Plotly.js (plotly.js-dist-min) (demo proven), BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven) | CoolProp (demo proven), SciPy (demo proven), SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-function-graph`, `maths-regression`, `maths-manim`, `physics-falling`, `mech-rankine`, `econ-cobb-douglas-plotly`, `edu-teaching-logit` |
| equation_transform | KaTeX (demo proven) | SymPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-equation` |
| vector_field | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven), Plotly.js (plotly.js-dist-min) (demo proven) | NumPy (demo proven), scikit-fem (demo proven) | — | Manim (Community Edition) (demo proven) | `mech-heat-plate` |
| physics_sim_2d | Matter.js (demo proven), D3 (demo proven) | SciPy (demo proven) | — | — | `physics-falling`, `physics-matter` |
| physics_sim_3d | three.js (demo proven), @react-three/drei (demo proven), React Three Fiber (demo proven) | cannon-es (demo proven) | — | — | `physics-collision-3d` |
| wave_motion | D3 (demo proven) | NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | `physics-wave` |
| orbit_motion | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Astropy (demo proven), Skyfield (demo proven) | JPL ephemeris DE421 (demo proven) | — | `astro-orbits` |
| flight_motion | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | JSBSim (demo proven) | — | — | `aero-climb` |
| earthquake_waves | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | ObsPy (demo proven) | USGS earthquake catalogue (demo proven) | — | `geo-seismic-rays` |

### Computer science

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| flowchart | dagre (@dagrejs/dagre) (demo proven), Mermaid (demo proven), BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven) | NetworkX (demo proven), PsychoPy (psychopy.data) (demo proven) | **none**; not for lessons: india-code | — | `polity-bill-mermaid`, `law-procedure-flow`, `psy-stroop-flow` |
| network_graph | D3 (demo proven), elkjs (Eclipse Layout Kernel) (demo proven) | NetworkX (demo proven) | — | — | `cs-graph-bfs` |

### Electrical and electronics

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| circuit_diagram | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Lcapy (demo proven), ngspice (demo proven) | — | — | `elec-rc-circuit` |
| signal_plot | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven), D3 (demo proven) | Lcapy (demo proven), ngspice (demo proven), Python Control Systems Library (demo proven) | — | — | `bio-ecg`, `elec-rc-circuit`, `elec-step-response` |
| vector_field | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven), Plotly.js (plotly.js-dist-min) (demo proven) | scikit-fem (demo proven), NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | `mech-heat-plate` |
| wave_motion | D3 (demo proven) | NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | `physics-wave` |

### Mechanical and civil

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| physics_sim_2d | Matter.js (demo proven), D3 (demo proven) | SciPy (demo proven) | — | — | `physics-falling`, `physics-matter` |
| physics_sim_3d | three.js (demo proven), @react-three/drei (demo proven), React Three Fiber (demo proven) | cannon-es (demo proven) | — | — | `physics-collision-3d` |
| machine_part_3d | three.js (demo proven) | trimesh (demo proven) | — | Blender (bpy, headless) (demo proven), CadQuery (with OCP, OpenCascade) (demo proven) | `mech-flange` |
| structure_load | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | PyNite (PyNiteFEA) (demo proven), SymPy physics (sympy.physics) (demo proven) | — | — | `mech-beam` |

### Geology and earth science

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| wave_motion | D3 (demo proven) | NumPy (demo proven) | — | Manim (Community Edition) (demo proven) | `physics-wave` |
| map_region | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven), topojson-client (demo proven), BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Shapely (demo proven) | Natural Earth (world-atlas TopoJSON) (demo proven), Natural Earth 1:10m vector data (GeoJSON) (demo proven), USGS earthquake catalogue (demo proven) | GMT (Generic Mapping Tools) (demo proven), PyGMT (demo proven) | `geo-relief`, `geo-quake-map`, `geo-india-state` |
| map_route | topojson-client (demo proven), BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven), D3 (demo proven) | Shapely (demo proven) | Natural Earth (world-atlas TopoJSON) (demo proven), Natural Earth 1:10m vector data (GeoJSON) (demo proven) | — | `hist-gt-road` |
| terrain_or_layers | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | ObsPy (demo proven) | **none**; not for lessons: gmt-earth-relief | GMT (Generic Mapping Tools) (demo proven), PyGMT (demo proven) | `geo-relief`, `geo-seismic-rays` |
| earthquake_waves | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | ObsPy (demo proven) | USGS earthquake catalogue (demo proven) | — | `geo-seismic-rays` |
| plate_motion | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | pyGPlates (demo proven) | Müller et al. (2019) plate model (demo proven) | — | `geo-plates` |
| process_cycle | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven) | — | — | — | `edu-learning-cycle` |

### Astronomy and space

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| orbit_motion | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Astropy (demo proven), Skyfield (demo proven) | JPL ephemeris DE421 (demo proven) | — | `astro-orbits` |
| sky_map | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Astropy (demo proven), Skyfield (demo proven) | JPL ephemeris DE421 (demo proven); not for lessons: hipparcos | — | `astro-sky` |

### Aerospace

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| aircraft_shape | three.js (demo proven) | AeroSandbox (demo proven) | — | — | `aero-aircraft` |
| flight_motion | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | JSBSim (demo proven) | — | — | `aero-climb` |

### Geography, history and polity

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| sky_map | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Skyfield (demo proven), Astropy (demo proven) | JPL ephemeris DE421 (demo proven); not for lessons: hipparcos | — | `astro-sky` |
| map_region | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven), BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven), topojson-client (demo proven) | Shapely (demo proven) | Natural Earth (world-atlas TopoJSON) (demo proven), Natural Earth 1:10m vector data (GeoJSON) (demo proven), USGS earthquake catalogue (demo proven) | GMT (Generic Mapping Tools) (demo proven), PyGMT (demo proven) | `geo-relief`, `geo-quake-map`, `geo-india-state` |
| map_route | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven), topojson-client (demo proven), D3 (demo proven) | Shapely (demo proven) | Natural Earth (world-atlas TopoJSON) (demo proven), Natural Earth 1:10m vector data (GeoJSON) (demo proven) | — | `hist-gt-road` |
| terrain_or_layers | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | ObsPy (demo proven) | **none**; not for lessons: gmt-earth-relief | GMT (Generic Mapping Tools) (demo proven), PyGMT (demo proven) | `geo-relief`, `geo-seismic-rays` |
| plate_motion | BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | pyGPlates (demo proven) | Müller et al. (2019) plate model (demo proven) | — | `geo-plates` |
| timeline | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven), Mermaid (demo proven), BIE block library (bie/brain/video/blocks) (demo proven) | — | — | — | `hist-timeline` |

### Economics, commerce and management

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| function_graph | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven), Plotly.js (plotly.js-dist-min) (demo proven), D3 (demo proven) | statsmodels (demo proven), CoolProp (demo proven), SciPy (demo proven) | — | Manim (Community Edition) (demo proven) | `maths-function-graph`, `maths-regression`, `maths-manim`, `physics-falling`, `mech-rankine`, `econ-cobb-douglas-plotly`, `edu-teaching-logit` |
| map_region | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven), D3 (demo proven), BIE science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Shapely (demo proven) | Natural Earth (world-atlas TopoJSON) (demo proven), Natural Earth 1:10m vector data (GeoJSON) (demo proven), World Bank Indicators API (World Development Indicators) (demo proven) | GMT (Generic Mapping Tools) (demo proven), PyGMT (demo proven) | `geo-relief`, `geo-quake-map`, `geo-india-state` |
| network_graph | D3 (demo proven), elkjs (Eclipse Layout Kernel) (demo proven) | NetworkX (demo proven) | — | — | `cs-graph-bfs` |
| chart_bar_line_pie | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven), Chart.js (demo proven), Plotly.js (plotly.js-dist-min) (demo proven) | statsmodels (demo proven) | World Bank Indicators API (World Development Indicators) (demo proven) | — | `chem-reaction`, `maths-regression`, `econ-growth-chartjs`, `econ-wealth-health-vega`, `edu-teaching-logit` |
| case_card | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Apache Arrow (pyarrow) (demo proven) | Indian Supreme Court Judgments (open dataset) (demo proven); not for lessons: india-code | — | `law-case-card` |

### Law

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| flowchart | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven), dagre (@dagrejs/dagre) (demo proven), Mermaid (demo proven) | NetworkX (demo proven), PsychoPy (psychopy.data) (demo proven) | **none**; not for lessons: india-code | — | `polity-bill-mermaid`, `law-procedure-flow`, `psy-stroop-flow` |
| case_card | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Apache Arrow (pyarrow) (demo proven) | Indian Supreme Court Judgments (open dataset) (demo proven); not for lessons: india-code | — | `law-case-card` |

### Psychology, education and sociology

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| anatomy_3d | three.js (demo proven), @react-three/drei (demo proven), React Three Fiber (demo proven) | trimesh (demo proven) | NIH 3D (demo proven), Servier Medical Art (demo proven); not for lessons: z-anatomy, bodyparts3d | Blender (bpy, headless) (demo proven) | `bio-heart-nih3d`, `bio-heart-zanatomy`, `bio-heart-bodyparts3d`, `psy-brain-lobes` |
| case_card | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Apache Arrow (pyarrow) (demo proven) | Indian Supreme Court Judgments (open dataset) (demo proven); not for lessons: india-code | — | `law-case-card` |

### Languages and literature

| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |
| --- | --- | --- | --- | --- | --- |
| text_kinetic | BIE social-science blocks (bie/brain/video/blocks/toolbox) (demo proven) | Indic NLP Library (demo proven), indic_transliteration (sanscript) (demo proven) | Noto Sans Devanagari (font) (demo proven) | — | `lang-kinetic-sanskrit` |

## Every tool

Lesson use comes from the licence policy: content is allowed, refused, needs Navin or checked per item (per file); a program's licence governs the program, not what BIE draws with it.

| Tool | Kind | Role / path | Version | Licence | Flags | Lesson use | Status | Batch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Blender (bpy, headless)](https://pypi.org/project/bpy/) | app | offline_render / offline | 5.2.2 | GPL-3.0-or-later (the program); models BIE makes with it are BIE's own | GPL | software: allowed; cloud/CI/VM only, never in apps/ | demo proven | 1 |
| [BodyParts3D](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html) | asset_source | asset / offline | 4.0 (PART-OF tree, 99% reduced OBJ) | CC BY 4.0 (licence page read 25 October 2026; releases up to 3.0 were CC BY-SA 2.1 Japan; the page also asks users to contact DBCLS) | own licence | **needs Navin** | demo proven | 1 |
| [NIH 3D](https://3d.nih.gov) | asset_source | asset / web | 3d.nih.gov API (entries, download) | per model (Public Domain / CC0, CC BY and others) | licence per item | per item | demo proven | 1 |
| [Servier Medical Art](https://smart.servier.com) | asset_source | asset / web | SMART 2026-10 (site) | CC BY 4.0 | — | allowed (credit) | demo proven | 1 |
| [Z-Anatomy](https://github.com/LluisV/Z-Anatomy) | asset_source | asset / offline | PC-Version branch (FBX systems) | CC BY-SA 4.0 | share-alike | **refused** | demo proven | 1 |
| [PubChem](https://pubchem.ncbi.nlm.nih.gov) | dataset | asset / web | PUG REST (live) | Public domain (NCBI); a few depositor records carry their own terms | licence per item | per item | demo proven | 1 |
| [RCSB Protein Data Bank](https://www.rcsb.org) | dataset | asset / web | files.rcsb.org (live archive) | CC0 1.0 (PDB data) | — | allowed | demo proven | 1 |
| [3Dmol.js](https://github.com/3dmol/3Dmol.js) | js_lib | draw / web | 2.5.5 | BSD-3-Clause | — | software: allowed | demo proven | 1 |
| [BIE block library (bie/brain/video/blocks)](https://github.com/SEENAV01/Enterprise-bie) | js_lib | draw / web | bie-2026-10-25 | BIE's own code | — | software: allowed | demo proven | 1 |
| [cannon-es](https://github.com/pmndrs/cannon-es) | js_lib | compute / web | 0.20.0 | MIT | — | software: allowed | demo proven | 1 |
| [D3](https://github.com/d3/d3) | js_lib | draw / web | 7.9.0 | ISC | — | software: allowed | demo proven | 1 |
| [@react-three/drei](https://github.com/pmndrs/drei) | js_lib | draw / web | 10.7.9 | MIT | — | software: allowed | demo proven | 1 |
| [KaTeX](https://github.com/KaTeX/KaTeX) | js_lib | draw / web | 0.19.0 | MIT | — | software: allowed | demo proven | 1 |
| [Matter.js](https://github.com/liabru/matter-js) | js_lib | draw / web | 0.20.0 | MIT | — | software: allowed | demo proven | 1 |
| [Mol*](https://github.com/molstar/molstar) | js_lib | draw / web | 5.13.1 | MIT | — | software: allowed | demo proven | 1 |
| [React Three Fiber](https://github.com/pmndrs/react-three-fiber) | js_lib | draw / web | 9.8.2 | MIT | — | software: allowed | demo proven | 1 |
| [Remotion](https://www.remotion.dev/license) | js_lib | draw / web | 4.0.536 | Remotion License: free for individuals and companies of up to 3 people; a paid company licence above that | own licence | software: allowed; Remotion licence: Navin | demo proven | 1 |
| [@remotion/three](https://www.npmjs.com/package/@remotion/three) | js_lib | draw / web | 4.0.536 | MIT | — | software: allowed | demo proven | 1 |
| [three.js](https://github.com/mrdoob/three.js) | js_lib | draw / web | 0.186.1 | MIT | — | software: allowed | demo proven | 1 |
| [Biopython](https://biopython.org) | python_lib | compute / python | 1.88 | Biopython License Agreement (BSD-style) | — | software: allowed | demo proven | 1 |
| [Cantera](https://cantera.org) | python_lib | compute / python | 3.2.0 | BSD-3-Clause | — | software: allowed | demo proven | 1 |
| [Manim (Community Edition)](https://www.manim.community) | python_lib | offline_render / offline | 0.22.0 | MIT | — | software: allowed | demo proven | 1 |
| [NetworkX](https://networkx.org) | python_lib | compute / python | 3.7 | BSD-3-Clause | — | software: allowed | demo proven | 1 |
| [NeuroKit2](https://github.com/neuropsychology/NeuroKit) | python_lib | compute / python | 0.2.13 | MIT | — | software: allowed | demo proven | 1 |
| [NumPy](https://numpy.org) | python_lib | compute / python | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | — | software: allowed | demo proven | 1 |
| [RDKit](https://www.rdkit.org) | python_lib | compute / python | 2026.9.1 | BSD-3-Clause | — | software: allowed | demo proven | 1 |
| [SciPy](https://scipy.org) | python_lib | compute / python | 1.18.1 | BSD-3-Clause | — | software: allowed | demo proven | 1 |
| [statsmodels](https://www.statsmodels.org) | python_lib | compute / python | 0.15.0 | BSD-3-Clause | — | software: allowed | demo proven | 1 |
| [SymPy](https://www.sympy.org) | python_lib | compute / python | 1.14.0 | BSD-3-Clause | — | software: allowed | demo proven | 1 |
| [trimesh](https://github.com/mikedh/trimesh) | python_lib | compute / python | 5.1.1 | MIT | — | software: allowed | demo proven | 1 |
| [GMT (Generic Mapping Tools)](https://www.generic-mapping-tools.org) | app | offline_render / offline | 6.5.0 | LGPL-3.0-or-later | — | software: allowed; cloud/CI/VM only, never in apps/ | demo proven | 2 |
| [ngspice](https://ngspice.sourceforge.io) | app | compute / offline | 42 | BSD-3-Clause (modified BSD; some parts under other free licences) | — | software: allowed | demo proven | 2 |
| [OpenVSP](https://openvsp.org) | app | offline_render / offline | 3.x (not installed) | NOSA 1.3 (NASA Open Source Agreement) | own licence | software: allowed | blocked | 2 |
| [NASA Image and Video Library](https://images.nasa.gov) | asset_source | asset / web | images-api.nasa.gov (live) | per item (NASA media are generally not copyrighted; some carry third-party rights) | licence per item | per item | demo proven | 2 |
| [GMT Earth relief (SRTM15+ V2.7)](https://www.generic-mapping-tools.org/remote-datasets/earth-relief.html) | dataset | asset / offline | SRTM15+ V2.7 (GMT remote data, 2 arc-min tiles) | Free to use with citation (Tozer et al., 2019, Scripps); GMT remote data | own licence | **needs Navin** | demo proven | 2 |
| [Müller et al. (2019) plate model](https://doi.org/10.5281/zenodo.11601026) | dataset | asset / offline | v2.0 (doi:10.5281/zenodo.11601026) | CC BY 4.0 | — | allowed (credit) | demo proven | 2 |
| [Hipparcos star catalogue](https://cdsarc.cds.unistra.fr/viz-bin/cat/I/239) | dataset | asset / offline | ESA 1997 (CDS I/239) | Free for scientific use with citation (CDS); commercial use under ESA's rules for the Hipparcos data | own licence | **needs Navin** | demo proven | 2 |
| [JPL ephemeris DE421](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de421.bsp) | dataset | asset / offline | DE421 (1900–2050) | Public domain (NASA JPL) | — | allowed | demo proven | 2 |
| [Natural Earth (world-atlas TopoJSON)](https://github.com/topojson/world-atlas) | dataset | asset / web | 2.0.2 | Public domain (Natural Earth data); ISC (the world-atlas package) | — | allowed; India boundary: needs Navin | demo proven | 2 |
| [USGS earthquake catalogue](https://earthquake.usgs.gov/fdsnws/event/1/) | dataset | asset / web | FDSN event API (live) | Public domain (USGS) | — | allowed | demo proven | 2 |
| [BIE science blocks (bie/brain/video/blocks/toolbox)](https://github.com/SEENAV01/Enterprise-bie) | js_lib | draw / web | bie-2026-10-25 | BIE's own code | — | software: allowed | demo proven | 2 |
| [topojson-client](https://github.com/topojson/topojson-client) | js_lib | draw / web | 3.1.0 | ISC | — | software: allowed | demo proven | 2 |
| [AeroSandbox](https://github.com/peterdsharpe/AeroSandbox) | python_lib | compute / python | 4.2.10 | MIT | — | software: allowed | demo proven | 2 |
| [Astropy](https://www.astropy.org) | python_lib | compute / python | 8.0.2 | BSD-3-Clause | — | software: allowed | demo proven | 2 |
| [CadQuery (with OCP, OpenCascade)](https://github.com/CadQuery/cadquery) | python_lib | offline_render / offline | 2.8.0 | Apache-2.0 (CadQuery and the OCP bindings; OpenCascade itself LGPL-2.1 with an exception) | — | software: allowed; cloud/CI/VM only, never in apps/ | demo proven | 2 |
| [CoolProp](https://github.com/CoolProp/CoolProp) | python_lib | compute / python | 8.0.0 | MIT | — | software: allowed | demo proven | 2 |
| [FEniCSx (DOLFINx)](https://fenicsproject.org) | python_lib | compute / python | 0.10 (not installed) | LGPL-3.0-or-later | — | software: allowed; cloud/CI/VM only, never in apps/ | blocked | 2 |
| [JSBSim](https://github.com/JSBSim-Team/jsbsim) | python_lib | compute / python | 1.3.3 | LGPL-2.1-or-later | — | software: allowed; cloud/CI/VM only, never in apps/ | demo proven | 2 |
| [Lcapy](https://github.com/mph-/lcapy) | python_lib | compute / python | 1.26 | LGPL-2.1-or-later | — | software: allowed; cloud/CI/VM only, never in apps/ | demo proven | 2 |
| [ObsPy](https://www.obspy.org) | python_lib | compute / python | 1.5.1 | LGPL-3.0 | — | software: allowed; cloud/CI/VM only, never in apps/ | demo proven | 2 |
| [PyGMT](https://www.pygmt.org) | python_lib | offline_render / offline | 0.19.0 | BSD-3-Clause | — | software: allowed | demo proven | 2 |
| [pyGPlates](https://www.gplates.org) | python_lib | compute / python | 1.0.0 | GPL-2.0 (pyGPlates; GPlates is GPL-2.0-or-later) | GPL | software: allowed; cloud/CI/VM only, never in apps/ | demo proven | 2 |
| [PyNite (PyNiteFEA)](https://github.com/JWock82/Pynite) | python_lib | compute / python | 3.2.0 | MIT | — | software: allowed | demo proven | 2 |
| [Python Control Systems Library](https://python-control.org) | python_lib | compute / python | 0.10.2 | BSD-3-Clause | — | software: allowed | demo proven | 2 |
| [Schemdraw](https://schemdraw.readthedocs.io) | python_lib | draw / python | 0.23 | MIT | — | software: allowed | demo proven | 2 |
| [scikit-fem](https://github.com/kinnala/scikit-fem) | python_lib | compute / python | 12.0.2 | BSD-3-Clause | — | software: allowed | demo proven | 2 |
| [SciPy signal (scipy.signal)](https://docs.scipy.org/doc/scipy/reference/signal.html) | python_lib | compute / python | 1.18.1 | BSD-3-Clause | — | software: allowed | demo proven | 2 |
| [Skyfield](https://rhodesmill.org/skyfield/) | python_lib | compute / python | 1.55 | MIT | — | software: allowed | demo proven | 2 |
| [SymPy physics (sympy.physics)](https://docs.sympy.org/latest/modules/physics/) | python_lib | compute / python | 1.14.0 | BSD-3-Clause | — | software: allowed | demo proven | 2 |
| [Noto Sans Devanagari (font)](https://github.com/notofonts/devanagari) | asset_source | asset / web | google/fonts e7db6ca6 (variable font) | SIL Open Font License 1.1 | — | allowed | demo proven | 3 |
| [Openverse](https://openverse.org) | asset_source | asset / web | Openverse API v1 (live) | per item (CC BY, CC BY-SA, CC0, public domain mark; non-commercial and no-derivatives refused) | licence per item | per item | demo proven | 3 |
| [Wikimedia Commons](https://commons.wikimedia.org) | asset_source | asset / web | MediaWiki API (live) | per item (public domain, CC BY, CC BY-SA ...; non-commercial and no-derivatives refused) | licence per item | per item | demo proven | 3 |
| [India Code (official repository of Indian law)](https://indiacode.gov.in) | dataset | asset / web | DSpace 9 REST API (live) | Government of India content; Acts may be reproduced (Copyright Act 1957, s. 52(1)(q)) with the source acknowledged | own licence | **needs Navin** | demo proven | 3 |
| [Natural Earth 1:10m vector data (GeoJSON)](https://github.com/nvkelso/natural-earth-vector) | dataset | asset / python | 5.1.2 | Public domain (Natural Earth) | — | allowed; India boundary: needs Navin | demo proven | 3 |
| [Indian Supreme Court Judgments (open dataset)](https://registry.opendata.aws/indian-supreme-court-judgments/) | dataset | asset / web | metadata parquet by year (AWS Open Data, updated every two months) | CC BY 4.0 (dataset by Dattam Labs); judgments from the Supreme Court of India | — | allowed (credit) | demo proven | 3 |
| [World Bank Indicators API (World Development Indicators)](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392) | dataset | asset / web | API v2 (live) | CC BY 4.0 | — | allowed (credit) | demo proven | 3 |
| [BIE social-science blocks (bie/brain/video/blocks/toolbox)](https://github.com/SEENAV01/Enterprise-bie) | js_lib | draw / web | bie-2026-10-25 | BIE's own code | — | software: allowed | demo proven | 3 |
| [Chart.js](https://github.com/chartjs/Chart.js) | js_lib | draw / web | 4.5.1 | MIT | — | software: allowed | demo proven | 3 |
| [dagre (@dagrejs/dagre)](https://github.com/dagrejs/dagre) | js_lib | draw / web | 3.1.1 | MIT | — | software: allowed | demo proven | 3 |
| [elkjs (Eclipse Layout Kernel)](https://github.com/kieler/elkjs) | js_lib | draw / web | 0.9.3 | EPL-2.0 (one of elkjs's two licences; BIE takes EPL-2.0 and does not modify it) | — | software: allowed | demo proven | 3 |
| [Mermaid](https://github.com/mermaid-js/mermaid) | js_lib | draw / web | 12.1.0 | MIT | — | software: allowed | demo proven | 3 |
| [@mermaid-js/layout-elk](https://github.com/mermaid-js/mermaid/tree/develop/packages/mermaid-layout-elk) | js_lib | draw / web | 1.0.1 | MIT | — | software: allowed | demo proven | 3 |
| [Plotly.js (plotly.js-dist-min)](https://github.com/plotly/plotly.js) | js_lib | draw / web | 4.1.1 | MIT | — | software: allowed | demo proven | 3 |
| [Vega](https://github.com/vega/vega) | js_lib | draw / web | 6.4.0 | BSD-3-Clause | — | software: allowed | demo proven | 3 |
| [Vega-Lite](https://github.com/vega/vega-lite) | js_lib | draw / web | 6.4.3 | BSD-3-Clause | — | software: allowed | demo proven | 3 |
| [Indic NLP Library](https://github.com/anoopkunchukuttan/indic_nlp_library) | python_lib | compute / python | 0.92 | MIT (library and indic_nlp_resources) | — | software: allowed | demo proven | 3 |
| [indic_transliteration (sanscript)](https://github.com/indic-transliteration/indic_transliteration_py) | python_lib | compute / python | 2.3.82 | MIT | — | software: allowed | demo proven | 3 |
| [PsychoPy (psychopy.data)](https://www.psychopy.org) | python_lib | compute / python | 2026.2.4 | GPL-3.0-or-later | GPL | software: allowed; cloud/CI/VM only, never in apps/ | demo proven | 3 |
| [Apache Arrow (pyarrow)](https://arrow.apache.org) | python_lib | compute / python | 26.0.0 | Apache-2.0 | — | software: allowed | demo proven | 3 |
| [Shapely](https://github.com/shapely/shapely) | python_lib | compute / python | 2.2.0 | BSD-3-Clause | — | software: allowed | demo proven | 3 |

## Blocked, and what each needs

- **FEniCSx (DOLFINx)**: DOLFINx has no PyPI wheel: it installs from conda-forge, Docker or Ubuntu's apt (python3-dolfinx, built for the system Python 3.12), while BIE's toolbox runs on Python 3.13 with pip. Needs a separate conda or Docker lane; scikit-fem covers the textbook finite-element cases meanwhile.
- **OpenVSP**: OpenVSP is not on PyPI: its Python API ships only inside OpenVSP's own release builds, compiled for one Python version, and there is no Ubuntu apt package. Needs a pinned OpenVSP build in its own lane; AeroSandbox builds aircraft shapes meanwhile.

## Missing capabilities

Capabilities in the vocabulary that no tool in the registry can draw yet (later batches, or the Task 046 merge path: an AI writes the block once, BIE tests it, Navin approves it):

- mnemonic_card: a memory trick on a card
- split_compare: two or more things side by side (added from the Task 046 benchmark)

## UGC NET and GATE map

86 UGC NET subjects (plus Paper I) and 30 GATE papers, from the official lists (bie/toolbox/exam_map.json names the pages and the date). Fit is Claude's reading of the syllabus headings, for Navin to check: strong = the subject's own tools exist, partial = some, general = only the general blocks.

- UGC NET: strong 45, partial 37, general 4
- GATE: strong 22, partial 8, general 0
- Subjects with no usable tool at all: none

### UGC NET

| Code | Subject | Families | Fit | Tools | Missing |
| --- | --- | --- | --- | --- | --- |
| 00 | General Paper on Teaching & Research Aptitude (Paper -I) | Psychology, education and sociology, Maths and statistics, Computer science | partial | 17 | data-interpretation charts are there; no gap block, only general ones |
| 01 | Economics / Rural Economics /Co-operation / Demography / Development Planning/ Development Studies / Econometrics/ Applied Economics/Development Eco./Business Economics | Economics, commerce and management, Maths and statistics | strong | 17 | — |
| 02 | Political Science | Geography, history and polity, Law | strong | 19 | — |
| 03 | Philosophy | Languages and literature, Psychology, education and sociology | general | 9 | argument maps (premise to conclusion), which Mermaid can draw but no block teaches yet |
| 04 | Psychology | Psychology, education and sociology, Biology and medical | strong | 18 | — |
| 05 | Sociology | Psychology, education and sociology, Economics, commerce and management | partial | 14 | survey and network diagrams of social data |
| 06 | History | Geography, history and polity | strong | 16 | — |
| 07 | Anthropology | Biology and medical, Psychology, education and sociology, Geography, history and polity | partial | 32 | 3D skulls and artefacts (an open 3D museum source such as Smithsonian Open Access 3D) |
| 08 | Commerce | Economics, commerce and management | strong | 11 | — |
| 09 | Education | Psychology, education and sociology | strong | 6 | — |
| 10 | Social Work | Psychology, education and sociology, Law | partial | 11 | case-work flow and community maps |
| 11 | Defence and Strategic Studies | Geography, history and polity | partial | 16 | military maps with movements and terrain, beyond the route block |
| 12 | Home Science | Biology and medical, Chemistry, Psychology, education and sociology | partial | 22 | nutrition tables and food models |
| 14 | Public Administration | Geography, history and polity, Law, Economics, commerce and management | strong | 24 | — |
| 15 | Population Studies | Economics, commerce and management, Geography, history and polity, Maths and statistics | strong | 28 | — |
| 16 | Music | Languages and literature | general | 4 | music notation and sound (for example music21 or VexFlow; BIE has no audio stage yet) |
| 17 | Management (including Business Admn. Mgt./Marketing/ Marketing Mgt./Industrial Relations and Personnel Mgt./ Personnel Mgt./Financial Mgt./Co-operative Management) | Economics, commerce and management | strong | 11 | — |
| 18 | Maithili | Languages and literature | strong | 4 | — |
| 19 | Bengali | Languages and literature | partial | 4 | a Noto font for the Bengali script (the kinetic text block takes any font from the asset library) |
| 20 | Hindi | Languages and literature | strong | 4 | — |
| 21 | Kannada | Languages and literature | partial | 4 | a Noto font for the Kannada script (the kinetic text block takes any font from the asset library) |
| 22 | Malayalam | Languages and literature | partial | 4 | a Noto font for the Malayalam script (the kinetic text block takes any font from the asset library) |
| 23 | Oriya | Languages and literature | partial | 4 | a Noto font for the Odia script (the kinetic text block takes any font from the asset library) |
| 24 | Punjabi | Languages and literature | partial | 4 | a Noto font for the Gurmukhi script (the kinetic text block takes any font from the asset library) |
| 25 | Sanskrit | Languages and literature | strong | 4 | — |
| 26 | Tamil | Languages and literature | partial | 4 | a Noto font for the Tamil script (the kinetic text block takes any font from the asset library) |
| 27 | Telugu | Languages and literature | partial | 4 | a Noto font for the Telugu script (the kinetic text block takes any font from the asset library) |
| 28 | Urdu | Languages and literature | partial | 4 | right-to-left layout and a Noto Naskh or Nastaliq font for the kinetic text block |
| 29 | Arabic | Languages and literature, Geography, history and polity | partial | 19 | right-to-left layout and a Noto Naskh or Nastaliq font for the kinetic text block |
| 30 | English | Languages and literature | strong | 4 | — |
| 31 | Linguistics | Languages and literature | strong | 4 | — |
| 32 | Chinese | Languages and literature | partial | 4 | a CJK font and pinyin |
| 33 | Dogri | Languages and literature | strong | 4 | — |
| 34 | Nepali | Languages and literature | strong | 4 | — |
| 35 | Manipuri | Languages and literature | partial | 4 | a Noto font for the Meitei Mayek and Bengali script (the kinetic text block takes any font from the asset library) |
| 36 | Assamese | Languages and literature | partial | 4 | a Noto font for the Bengali-Assamese script (the kinetic text block takes any font from the asset library) |
| 37 | Gujarati | Languages and literature | partial | 4 | a Noto font for the Gujarati script (the kinetic text block takes any font from the asset library) |
| 38 | Marathi | Languages and literature | strong | 4 | — |
| 39 | French (French Version) | Languages and literature | strong | 4 | — |
| 40 | Spanish | Languages and literature | strong | 4 | — |
| 41 | Russian | Languages and literature | partial | 4 | a Noto font for the Cyrillic script (the kinetic text block takes any font from the asset library) |
| 42 | Persian | Languages and literature, Geography, history and polity | partial | 19 | right-to-left layout and a Noto Naskh or Nastaliq font for the kinetic text block |
| 43 | Rajasthani | Languages and literature | strong | 4 | — |
| 44 | German | Languages and literature | strong | 4 | — |
| 45 | Japanese | Languages and literature | partial | 4 | a CJK font and romaji |
| 46 | Adult Education/ Continuing Education/ Andragogy/ Non Formal Education. | Psychology, education and sociology | strong | 6 | — |
| 47 | Physical Education | Biology and medical, Physics, Psychology, education and sociology | partial | 37 | human movement (skeleton animation, for example from OpenSim) |
| 49 | Arab Culture and Islamic Studies | Geography, history and polity, Languages and literature | partial | 19 | right-to-left layout and a Noto Naskh or Nastaliq font for the kinetic text block |
| 50 | Indian Culture | Geography, history and polity, Languages and literature | strong | 19 | — |
| 55 | Labour Welfare/Personnel Management/Industrial Relations/ Labour and Social Welfare/Human Resource Management | Economics, commerce and management, Law | strong | 15 | — |
| 58 | Law | Law | strong | 6 | — |
| 59 | Library and Information Science | Computer science, Psychology, education and sociology | partial | 9 | catalogue and classification schemes as interactive trees |
| 60 | Buddhist, Jaina, Gandhian and Peace Studies | Geography, history and polity, Languages and literature | strong | 19 | — |
| 62 | Comparative Study of Religions | Geography, history and polity, Languages and literature | partial | 19 | comparison tables across traditions (Task 046's split_compare block) |
| 63 | Mass Communication and Journalism | Languages and literature, Psychology, education and sociology | partial | 9 | news-page and media layouts |
| 65 | Performing Art - Dance/Drama/Theatre | Languages and literature | general | 4 | dance and stage movement (motion capture) and sound |
| 66 | Museology & Conservation | Geography, history and polity, Chemistry | partial | 26 | 3D artefacts (Smithsonian Open Access 3D or similar) |
| 67 | Archaeology | Geography, history and polity, Geology and earth science | partial | 18 | 3D artefacts and excavation layers |
| 68 | Criminology | Law, Psychology, education and sociology | strong | 11 | — |
| 70 | Tribal and Regional Language/Literature | Languages and literature | partial | 4 | fonts for tribal scripts (Ol Chiki, Warang Citi ...) and audio |
| 71 | Folk Literature | Languages and literature | partial | 4 | audio for oral literature |
| 72 | Comparative Literature | Languages and literature | partial | 4 | comparison tables across texts (split_compare) |
| 73 | Sanskrit traditional subjects (including) Jyotisha/Sidhanta Jyotish/ Navya Vyakarna/ Vyakarna/ Mimansa/ Navya Nyaya/ Sankhya Yoga/ Tulanatmaka Darsan/ Shukla Yajurveda/ Madhav Vedant/ Dharmasasta/ Sahitya/ Puranotihasa /Agama). | Languages and literature, Astronomy and space, Maths and statistics | strong | 20 | — |
| 74 | Women Studies | Psychology, education and sociology, Economics, commerce and management | partial | 14 | survey charts with sex-disaggregated data from more sources |
| 79 | Visual Art (including Drawing & Painting/Sculpture Graphics/Applied Art/History of Art) | Languages and literature, Geography, history and polity | general | 19 | art images are there (Commons, Openverse); a drawing-process block is missing |
| 80 | Geography | Geography, history and polity, Geology and earth science | strong | 18 | — |
| 81 | Social Medicine & Community Health | Biology and medical, Maths and statistics | strong | 24 | — |
| 82 | Forensic Science | Biology and medical, Chemistry, Law | strong | 24 | — |
| 83 | Pali | Languages and literature | strong | 4 | — |
| 84 | Kashmiri | Languages and literature | partial | 4 | right-to-left layout and a Noto Naskh or Nastaliq font for the kinetic text block |
| 85 | Konkani | Languages and literature | strong | 4 | — |
| 87 | Computer Science and Applications | Computer science, Maths and statistics | strong | 12 | — |
| 88 | Electronic Science | Electrical and electronics, Physics | strong | 21 | — |
| 89 | Environmental Sciences | Geology and earth science, Biology and medical, Chemistry | strong | 31 | — |
| 90 | Politics including International Relations/International Studies including Defence/Strategic Studies, West Asian Studies, South East Asian Studies, African Studies, South Asian Studies, Soviet Studies, American Studies. | Geography, history and polity, Law | strong | 19 | — |
| 91 | Prakrit | Languages and literature | strong | 4 | — |
| 92 | Human Rights and Duties | Law, Geography, history and polity | strong | 19 | — |
| 93 | Tourism Administration and Management. | Geography, history and polity, Economics, commerce and management | strong | 22 | — |
| 95 | Santali | Languages and literature | partial | 4 | a Noto font for the Ol Chiki script (the kinetic text block takes any font from the asset library) |
| 100 | Yoga | Biology and medical, Languages and literature | partial | 18 | posture figures (a human pose model) |
| 101 | Sindhi | Languages and literature | partial | 4 | right-to-left layout and a Noto Naskh or Nastaliq font for the kinetic text block; Devanagari Sindhi works now |
| 102 | Hindu Studies | Languages and literature, Geography, history and polity | strong | 19 | — |
| 103 | Indian Knowledge System | Geography, history and polity, Languages and literature, Maths and statistics, Astronomy and space | strong | 33 | — |
| 104 | Disaster Management | Geology and earth science, Geography, history and polity | strong | 18 | — |
| 105 | Ayurveda Biology | Biology and medical, Chemistry | strong | 18 | — |
| 106 | Forestry | Biology and medical, Geology and earth science | partial | 27 | plant and tree 3D models |
| 107 | Statistics | Maths and statistics | strong | 10 | — |

### GATE

| Code | Subject | Families | Fit | Tools | Missing |
| --- | --- | --- | --- | --- | --- |
| AE | Aerospace Engineering | Aerospace, Physics | strong | 22 | — |
| AG | Agricultural Engineering | Mechanical and civil, Geology and earth science, Biology and medical | partial | 36 | farm machinery and soil-water models |
| AR | Architecture and Planning | Mechanical and civil, Geography, history and polity | partial | 27 | building models (Blender from IFC files, for example IfcOpenShell) |
| BM | Biomedical Engineering | Biology and medical, Electrical and electronics | strong | 21 | — |
| BT | Biotechnology | Biology and medical, Chemistry | strong | 18 | — |
| CE | Civil Engineering | Mechanical and civil, Geology and earth science | strong | 24 | — |
| CH | Chemical Engineering | Chemistry, Mechanical and civil | strong | 20 | — |
| CS | Computer Science & Information Technology | Computer science, Maths and statistics | strong | 12 | — |
| CY | Chemistry | Chemistry | strong | 10 | — |
| DA | Data Science & Artificial Intelligence | Computer science, Maths and statistics | strong | 12 | — |
| EC | Electronics & Communication Engineering | Electrical and electronics | strong | 8 | — |
| EE | Electrical Engineering | Electrical and electronics | strong | 8 | — |
| ES | Environmental Science & Engineering | Geology and earth science, Chemistry, Biology and medical | strong | 31 | — |
| EY | Ecology and Evolution | Biology and medical, Maths and statistics | partial | 24 | phylogenetic trees from data (the tree block draws them; a tree-of-life source is missing) |
| GE | Geomatics Engineering | Geography, history and polity, Geology and earth science | strong | 18 | — |
| GG | Geology & Geophysics | Geology and earth science | strong | 13 | — |
| IN | Instrumentation Engineering | Electrical and electronics | strong | 8 | — |
| MA | Mathematics | Maths and statistics | strong | 10 | — |
| ME | Mechanical Engineering | Mechanical and civil | strong | 12 | — |
| MN | Mining Engineering | Geology and earth science, Mechanical and civil | partial | 24 | mine layouts and ventilation networks |
| MT | Metallurgical Engineering | Chemistry, Mechanical and civil | partial | 20 | phase diagrams (for example pycalphad) and crystal lattices |
| NM | Naval Architecture & Marine Engineering | Mechanical and civil, Physics | partial | 26 | hull shapes and hydrostatics (for example Capytaine) |
| PE | Petroleum Engineering | Geology and earth science, Chemistry | partial | 23 | reservoir and well models |
| PH | Physics | Physics | strong | 20 | — |
| PI | Production & Industrial Engineering | Mechanical and civil, Economics, commerce and management | strong | 23 | — |
| ST | Statistics | Maths and statistics | strong | 10 | — |
| TF | Textile Engineering & Fibre Science | Mechanical and civil, Chemistry | partial | 20 | fibre and weave structures |
| XE | Engineering Sciences | Mechanical and civil, Physics, Maths and statistics, Chemistry | strong | 36 | — |
| XH | Humanities & Social Sciences | Economics, commerce and management, Languages and literature, Psychology, education and sociology | strong | 17 | — |
| XL | Life Sciences | Biology and medical, Chemistry | strong | 18 | — |


## Lesson licence gate

Navin, 2026-10-25: "Final videos mein sirf CC0 aur CC BY assets lein; CC BY-SA nahi; NC bilkul nahi."

Policy `2026-10-25.1` (`bie/toolbox/licence_policy.json`, the only source of truth). Lessons (anything seen or heard in a lesson video, game or notes) take only CC0, public domain and CC BY (with author, licence, licence URL and source page). The gate (`lesson_licence_check`) runs before any lesson output is rendered or packaged and stops it with the reason; nothing is swapped silently.

Refused for lessons:

- Z-Anatomy: share-alike licence: a lesson that adapts it may have to carry the same licence (Navin: CC BY-SA nahi)

Needs Navin (blocked until he approves the source by name in the policy file):

- BodyParts3D: the licence page says CC BY 4.0, but the BodyParts3D page asks users to contact DBCLS; Navin decides after DBCLS answers
- GMT Earth relief (SRTM15+ V2.7): SRTM15+ relief (Tozer et al., 2019, Scripps) is free to use with citation: own terms, not a CC licence
- Hipparcos star catalogue: free for scientific use with citation (CDS); commercial use under ESA's rules for the Hipparcos catalogue
- India Code (official repository of Indian law): Government of India content; Acts may be reproduced under the Copyright Act 1957, s. 52(1)(q), with the source acknowledged: own terms, not a CC licence
- India's political boundary: any asset or map that draws India's political boundary (including Natural Earth's India-view file) waits until Navin approves a boundary matched to the Survey of India map (sources: natural-earth, natural-earth-vector; blocks: india_map)

Checked per item (each file on its own licence):

- NIH 3D: each model's own licence from its NIH 3D record
- PubChem: public domain (NCBI) except depositor records with their own terms
- NASA Image and Video Library: each file on its own: NASA media are US government works, public domain unless the record names a third-party copyright holder; such a file is refused
- Wikimedia Commons: each file's own licence as Commons states it
- Openverse: each file's own licence as Openverse records it

Software: a program's licence (MIT, BSD, Apache, ISC, LGPL, GPL, EPL, NOSA, Remotion's own ...) governs the program, not the pictures BIE makes with it. GPL and LGPL programs (gpl-flagged registry tools such as Blender, PsychoPy, pyGPlates) run only in the cloud, CI or VM render path and never ship inside apps/ (android, web, operator, api): Blender (bpy, headless), Lcapy, CadQuery (with OCP, OpenCascade), FEniCSx (DOLFINx), GMT (Generic Mapping Tools), ObsPy, pyGPlates, JSBSim, PsychoPy (psychopy.data).

- Open decision (Navin): Remotion licence: free for individuals and companies of up to 3 people; a paid company licence above that
