# Deel marketing analytics case

Materials prepared for the hiring team, for the Senior Data Analyst
(Marketing Analytics) role at Deel.

**Note:** the original task description, the dataset, and the cleaned
row-level data are deliberately not included in this repo, to protect the
privacy of the data and the brief that were shared with me. To reproduce the
pipeline, place the case dataset CSV in `briefing/` (the expected filename is
at the top of `data-cleaning/clean.py`); `run.sh` regenerates everything else.
The `briefing/` directory is created automatically by `run.sh`, which stops
with a clear message until the CSV is in place.

## Contents

- `presentation/deck.pdf` - the presentation (source: `deck.pptx`, built by
  `presentation/build_deck.py`)
- `data-cleaning/` - cleaning pipeline and an independent audit of the raw data
- `analysis/` - the two analysis notebooks, figures, and
  `verify_numbers.py`, which re-derives every number cited in the deck from
  the raw file
- `ASSUMPTIONS.md` - running log of every assumption and cleaning decision
- `run.sh` - end-to-end build: clean, audit, notebooks, figures, deck, PDF
