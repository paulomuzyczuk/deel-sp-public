#!/usr/bin/env bash
# End-to-end reproduction: raw CSV -> clean data -> audit -> notebooks/figures
# -> number verification -> deck figures -> deck.pptx -> deck.pdf.
#
# Requires: python3 (venv created on first run), Microsoft PowerPoint (macOS)
# for the final PDF export step only.
set -euo pipefail
cd "$(dirname "$0")"

CSV="briefing/Deel Marketing Analytics Challenge - Dataset - raw_data.csv"
mkdir -p briefing
if [ ! -f "$CSV" ]; then
    echo "ERROR: dataset not found at $CSV"
    echo "Place the case dataset CSV there, then re-run ./run.sh"
    exit 1
fi

PY=.venv/bin/python
if [ ! -x "$PY" ]; then
    python3 -m venv .venv
    .venv/bin/pip install -q -r requirements.txt
fi

echo "== 1/8 cleaning pipeline =="
"$PY" data-cleaning/clean.py

echo "== 2/8 raw-data audit =="
"$PY" data-cleaning/audit.py > data-cleaning/output/audit_report.txt
tail -3 data-cleaning/output/audit_report.txt || true

echo "== 3/8 analysis notebooks (figures + saved outputs) =="
"$PY" analysis/run_notebooks.py

echo "== 4/8 verify headline numbers against RAW csv =="
"$PY" analysis/verify_numbers.py | tail -2

echo "== 5/8 deck figure variants (latte, no internal titles) =="
"$PY" analysis/run_notebooks.py --deck

echo "== 6/8 slide illustrations =="
"$PY" presentation/make_illustrations.py

echo "== 7/8 build deck.pptx from deck_spec.json =="
"$PY" presentation/build_deck.py

echo "== 8/8 export deck.pdf via PowerPoint =="
"$PY" presentation/export_pdf.py presentation/deck.pptx

echo "done: presentation/deck.pptx + presentation/deck.pdf"
