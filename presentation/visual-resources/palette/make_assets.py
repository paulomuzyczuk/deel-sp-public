"""Regenerates derived visual assets: palette swatch sheet + inverted logo.

Run:  .venv/bin/python visual-resources/palette/make_assets.py
Inputs are the downloaded originals in visual-resources/logos/.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image

import deel_palette as dp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def _text_on(hex_color: str) -> str:
    """Black or white label, whichever is legible on the swatch."""
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#141414" if lum > 0.5 else "#FAF4EE"


def swatch_sheet(out: Path) -> None:
    rows = [
        ("Core brand", [(k.title(), v) for k, v in dp.CORE.items()]),
        ("Surfaces", [(k, v) for k, v in dp.SURFACE.items()]),
        ("Acai / purple ramp", [(str(k), v) for k, v in dp.PURPLE.items()]),
        ("Blueberry / blue ramp", [(str(k), v) for k, v in dp.BLUE.items()]),
        ("Cornbread / yellow", [(str(k), v) for k, v in dp.YELLOW.items()]),
        ("Green", [(str(k), v) for k, v in dp.GREEN.items()]),
        ("Neutral", [(str(k), v) for k, v in dp.NEUTRAL.items()]),
        ("Chart categorical (fixed order)",
         [(str(i + 1), c) for i, c in enumerate(dp.CATEGORICAL)]),
        ("Chart sequential (magnitude)",
         [("", c) for c in dp.SEQUENTIAL_PURPLE]),
        ("Chart diverging (polarity)", [("", c) for c in dp.DIVERGING]),
        ("Status (reserved)", [(k, v) for k, v in dp.STATUS.items()]),
    ]

    ncols = max(len(items) for _, items in rows)
    fig, ax = plt.subplots(figsize=(1.35 * ncols + 3.4, 0.95 * len(rows) + 0.9))
    fig.patch.set_facecolor(dp.SURFACE["latte_25"])
    ax.set_facecolor(dp.SURFACE["latte_25"])

    for r, (label, items) in enumerate(rows):
        y = len(rows) - r - 1
        ax.text(-0.15, y + 0.45, label, ha="right", va="center",
                fontsize=10.5, color="#141414", fontweight="bold")
        for c, (name, hexv) in enumerate(items):
            ax.add_patch(Rectangle((c, y), 0.94, 0.9, facecolor=hexv,
                                   edgecolor="#1B1B1B29", linewidth=0.7))
            fg = _text_on(hexv)
            if name:
                ax.text(c + 0.47, y + 0.6, name, ha="center", va="center",
                        fontsize=8.5, color=fg, fontweight="bold")
            ax.text(c + 0.47, y + 0.27, hexv.upper(), ha="center", va="center",
                    fontsize=7, color=fg)

    ax.set_xlim(-3.2, ncols)
    ax.set_ylim(0, len(rows))
    ax.axis("off")
    ax.set_title("Deel brand palette — extracted from deel.com design tokens",
                 loc="left", fontsize=13, fontweight="bold", color="#141414",
                 pad=14)
    fig.savefig(out, dpi=200, bbox_inches="tight",
                facecolor=dp.SURFACE["latte_25"])
    plt.close(fig)


def invert_logo(src: Path, out: Path) -> None:
    """Make a knock-out-white wordmark for dark slides, preserving alpha."""
    img = Image.open(src).convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            # The source is dark ink on transparency; recolour ink to latte.
            if a > 0:
                px[x, y] = (250, 244, 238, a)
    img.save(out)


if __name__ == "__main__":
    swatch_sheet(ROOT / "palette" / "deel-palette-swatches.png")
    src = ROOT / "logos" / "deel-logo-black-transparent.png"
    invert_logo(src, ROOT / "logos" / "deel-logo-latte-on-dark.png")
    print("wrote palette/deel-palette-swatches.png and "
          "logos/deel-logo-latte-on-dark.png")
