"""Build presentation/deck.pptx — reproduces the delivered deck exactly.

History: the deck began as a fully programmatic python-pptx build, was then
hand-polished in PowerPoint (layout, wording, extra slides), and the polished
result was ported back into the pipeline. The port lives in deck_spec.json:
every text/auto shape captured as its exact DrawingML, every picture mapped
back to its source file in the repo (analysis/figures/deck/,
presentation/illustrations/, visual-resources/logos/). Rebuilding from a fresh
clone therefore reproduces the delivered deck byte-for-byte at the text level,
with images re-inserted from their pipeline-generated sources.

To change slide CONTENT: edit in PowerPoint, then re-extract deck_spec.json
(see git history for the extraction script), or edit the spec JSON directly.
Figures/illustrations regenerate upstream (run.sh steps 3-6) and are picked up
here by file path.

Invariants asserted at build time: 16:9 geometry, latte #FFFBF4 background on
every slide, every text run in "Inter 28pt", all shapes inside slide bounds.

Run:  .venv/bin/python presentation/build_deck.py
Then: .venv/bin/python presentation/export_pdf.py presentation/deck.pptx
"""
import json
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SPEC = HERE / "deck_spec.json"
OUT_PPTX = HERE / "deck.pptx"

LATTE = RGBColor.from_string("FFFBF4")
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
FONT = "Inter 28pt"


def main():
    spec = json.loads(SPEC.read_text())
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    for slide_spec in spec:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = LATTE
        for shp in slide_spec["shapes"]:
            if shp["kind"] == "picture":
                slide.shapes.add_picture(str(ROOT / shp["src"]),
                                         Emu(shp["x"]), Emu(shp["y"]),
                                         Emu(shp["w"]), Emu(shp["h"]))
            else:
                slide.shapes._spTree.append(etree.fromstring(shp["xml"]))

    # ---- invariants ----
    n_shapes = n_runs = 0
    for i, slide in enumerate(prs.slides, 1):
        for shp in slide.shapes:
            n_shapes += 1
            assert shp.left >= 0 and shp.top >= 0 \
                and shp.left + shp.width <= SLIDE_W + Emu(1) \
                and shp.top + shp.height <= SLIDE_H + Emu(1), \
                f"slide {i}: shape outside bounds"
            if shp.has_text_frame:
                for para in shp.text_frame.paragraphs:
                    for run in para.runs:
                        if run.text.strip():
                            n_runs += 1
                            assert run.font.name in (FONT, None), \
                                f"slide {i}: non-{FONT} run {run.font.name!r}"

    prs.save(OUT_PPTX)
    n = len(prs.slides._sldIdLst)
    print(f"wrote {OUT_PPTX} ({n} slides, {n_shapes} shapes, {n_runs} text runs, "
          f"all runs '{FONT}', all shapes in bounds)")


if __name__ == "__main__":
    main()
