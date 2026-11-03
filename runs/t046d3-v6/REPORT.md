# Render

- 9.16 minutes of video in 8 chunks: 4.8 minutes wall-clock (parallel), 34.0 machine minutes, 0.124 s per frame, 3.71 render seconds per video second; ₹22.85 at the list price (billed ₹0).
- video.mp4 57.8 MB, review-720p.mp4 17.4 MB, 549.67 s.
- Compiled again with this commit's code: v6 10 parts compiled, 5 refused (a refused part needs the director again).
  - v6_s2b refused: rbi_timeline: a timeline picture needs at least 3 rows of the grid, so its icons and their labels are readable (36px, CV-17)
  - v6_s5a refused: table separate_tracks has too many rows for its cell: its text would be 24px, under the readable 36px (CV-17); give it more rows of the grid or split it in two
  - v6_s6 refused: table old_units has too many rows for its cell: its text would be 34px, under the readable 36px (CV-17); give it more rows of the grid or split it in two
  - v6_s8b refused: text does not fit its cell even at 36px: '2022 का Digital Rupee' (split it or give it a bigger cell)
  - v6_s9 refused: chronology: a timeline picture needs at least 3 rows of the grid, so its icons and their labels are readable (36px, CV-17)
- Text check (550 frames, one every 30): 0 texts under 36 px for a second or more (6 in all), 9 pairs of texts on each other for a second or more (11 in all), 0 under the caption strip.
  - on each other: "Rupee" and "copper पर Dam" at 224.0–228.0 s
  - on each other: "Dam" and "copper पर Dam" at 225.0–228.0 s
  - on each other: "silver" and "silver" at 257.0–258.0 s
  - on each other: "same gold-linked foreign payme" and "सस्ता" at 266.0–267.0 s
  - on each other: "same gold-linked foreign payme" and "कमजोर" at 266.0–267.0 s
  - on each other: "1" and "actual या expected supply" at 285.0–287.0 s
  - on each other: "2" and "actual या expected supply" at 286.0–289.0 s
  - on each other: "3" and "actual या expected supply" at 287.0–289.0 s
  - on each other: "smoothing" and "तय rate की commitment" at 491.0–494.0 s
