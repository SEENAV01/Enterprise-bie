# Toolbox test fixtures (Task 046a)

- `hip_main_3stars.dat`: three lines (Rigel, HIP 24436; Betelgeuse, HIP 27989; Sirius, HIP 32349) of the Hipparcos
  Catalogue, ESA 1997 (ESA SP-1200), as distributed by CDS (catalogue I/239, `hip_main.dat`). Used so the astronomy
  wrapper test reads the real catalogue format without the 53 MB download.
- `indic_nlp_resources/script/all_script_phonetic_data.csv` and `tamil_script_phonetic_data.csv`: the two script tables
  of the Indic NLP resources (anoopkunchukuttan/indic_nlp_resources at commit 5b4ff17c, MIT licence), byte for byte; the
  language wrapper test reads them instead of fetching them (`bie/toolbox/sources.py` pins the same files by hash).
- `bsc5_3stars.dat`: the same three stars (Rigel HR 1713, Betelgeuse HR 2061, Sirius HR 2491) as three lines of the Yale Bright
  Star Catalogue, 5th revised edition (Hoffleit & Warren 1991; `bsc5.dat` as distributed by the Harvard-Smithsonian CfA, public
  domain), the default star source since 29 October 2026.
