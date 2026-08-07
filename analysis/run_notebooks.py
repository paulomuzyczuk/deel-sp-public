#!/usr/bin/env python3
"""Execute the analysis notebooks headlessly.

Default: runs both notebooks in place (figures -> analysis/figures/, executed
outputs saved back into the .ipynb files).

--deck: runs them with DECK_FIGURES=1 — figure code then renders deck variants
(latte #FFFBF4 background, no takeaway titles/footnotes: the slide carries the
title) into analysis/figures/deck/. Notebook files are NOT overwritten in this
mode; the deck PNGs are the only output.

Run:  .venv/bin/python analysis/run_notebooks.py [--deck]
"""
import os
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent
NOTEBOOKS = [HERE / "task1_funnel_seasonality.ipynb", HERE / "task2_cost_brand.ipynb"]


def run(nb_path: Path, deck: bool):
    nb = nbformat.read(nb_path, as_version=4)
    if deck:
        os.environ["DECK_FIGURES"] = "1"
    else:
        os.environ.pop("DECK_FIGURES", None)
    client = NotebookClient(nb, timeout=600, kernel_name="python3",
                            resources={"metadata": {"path": str(HERE)}})
    client.execute()
    for cell in nb.cells:
        for out in cell.get("outputs", []):
            if out.get("output_type") == "error":
                raise SystemExit("\n".join(out["traceback"]))
    if not deck:
        nbformat.write(nb, nb_path)
    print(f"executed {nb_path.name}{' [deck figures]' if deck else ''}")


if __name__ == "__main__":
    deck = "--deck" in sys.argv
    for nb_path in NOTEBOOKS:
        run(nb_path, deck)
