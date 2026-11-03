# Render

- 7.37 minutes of video in 8 chunks: 4.1 minutes wall-clock (parallel), 26.2 machine minutes, 0.119 s per frame, 3.56 render seconds per video second; ₹17.61 at the list price (billed ₹0).
- video.mp4 48.7 MB, review-720p.mp4 14.4 MB, 442.2 s.
- Compiled again with this commit's code: v2 15 parts compiled, 3 refused (a refused part needs the director again).
  - v2_s3 refused: history: a timeline picture needs at least 3 rows of the grid, so its icons and their labels are readable (36px, CV-17)
  - v2_s6 refused: note_question: the icon is 34px with its label at the readable size (36px, CV-17); give it a taller cell (2 rows) or no label
  - v2_s8a refused: tag pastoral_phrase is wider than its cell: 'पशु रखने से रोज़ी'
- Text check (443 frames, one every 30): 0 texts under 36 px for a second or more (0 in all), 0 pairs of texts on each other for a second or more (2 in all), 0 under the caption strip.
