# Render

- 7.74 minutes of video in 8 chunks: 3.9 minutes wall-clock (parallel), 27.7 machine minutes, 0.119 s per frame, 3.58 render seconds per video second; ₹18.63 at the list price (billed ₹0).
- video.mp4 48.9 MB, review-720p.mp4 14.2 MB, 464.37 s.
- Compiled again with this commit's code: v4 15 parts compiled, 3 refused (a refused part needs the director again).
  - v4_s2b refused: gram_example: the icon is 34px with its label at the readable size (36px, CV-17); give it a taller cell (2 rows) or no label
  - v4_s5 refused: tag usd_tag is wider than its cell: '$ USD\nUnited States Dollar'
  - v4_s8 refused: history: a timeline picture needs at least 3 rows of the grid, so its icons and their labels are readable (36px, CV-17)
- Text check (465 frames, one every 30): 0 texts under 36 px for a second or more (8 in all), 6 pairs of texts on each other for a second or more (8 in all), 0 under the caption strip.
  - on each other: "1" and "₹500" at 178.0–186.0 s
  - on each other: "लेना मर्ज़ी है" and "₹1,000" at 185.0–186.0 s
  - on each other: "1" and "आगे मर्ज़ी है" at 226.0–228.0 s
  - on each other: "4" and "≠" at 316.0–322.0 s
  - on each other: "9" and "denomination" at 321.0–322.0 s
  - on each other: "credit इस्तेमाल किया" and "₹1,000" at 409.0–410.0 s
