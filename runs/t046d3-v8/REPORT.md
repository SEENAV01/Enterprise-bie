# Render

- 7.02 minutes of video in 8 chunks: 3.9 minutes wall-clock (parallel), 23.7 machine minutes, 0.112 s per frame, 3.37 render seconds per video second; ₹15.89 at the list price (billed ₹0).
- video.mp4 36.8 MB, review-720p.mp4 10.8 MB, 420.93 s.
- Compiled again with this commit's code: v8 8 parts compiled, 2 refused (a refused part needs the director again).
  - v8_s2 refused: text does not fit its cell even at 36px: 'Government of India issue करता है' (split it or give it a bigger cell)
  - v8_s5 refused: metal: the icon is 34px with its label at the readable size (36px, CV-17); give it a taller cell (2 rows) or no label
- Text check (421 frames, one every 30): 0 texts under 36 px for a second or more (5 in all), 2 pairs of texts on each other for a second or more (2 in all), 0 under the caption strip.
  - on each other: "English" and "₹100" at 259.0–266.0 s
  - on each other: "Hindi" and "₹100" at 259.0–266.0 s
