#!/usr/bin/env python3
"""Illustrations for the measurement-plan slides (geo-holdout, MMM, tracking debts).

Two kinds, clearly separated:
- schematic illustrations (geo-holdout design, MMM saturation concept): labeled
  "illustrative" in the image itself; they depict a design, NOT this dataset.
- real-data minis (tracking debts): three small panels drawn from
  data-cleaning/output/clean_daily.csv.

Output: presentation/illustrations/*.png, latte background, Deel accent colors.

Run:  .venv/bin/python presentation/make_illustrations.py
"""
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "illustrations"
OUT.mkdir(exist_ok=True)

LATTE = "#FFFBF4"
ACAI = "#5938B7"
BLUE = "#2187CF"
CORN = "#C98A00"
INK = "#141414"
INK2 = "#404040"
MUT = "#A6A6A6"
GRID = "#E6E6E6"

plt.rcParams.update({
    "figure.facecolor": LATTE, "axes.facecolor": LATTE, "savefig.facecolor": LATTE,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"],
    "axes.edgecolor": MUT, "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.labelcolor": INK2, "savefig.dpi": 200, "savefig.bbox": "tight",
    "legend.frameon": False,
})

rng = np.random.default_rng(7)  # fixed seed: deterministic output


def geo_holdout():
    """Schematic: matched geo markets, ~20% of spend paused (holdout)."""
    fig, ax = plt.subplots(figsize=(4.2, 4.0))
    ax.set_xlim(0, 5)
    ax.set_ylim(-1.6, 5.6)
    ax.axis("off")
    cells = [(c, r) for r in range(5) for c in range(5)]
    holdout = {(1, 3), (3, 1), (0, 0), (4, 2), (2, 4)}  # 5 of 25 = 20%
    for (c, r) in cells:
        color = ACAI if (c, r) in holdout else GRID
        ax.add_patch(plt.Rectangle((c + 0.06, r + 0.06), 0.88, 0.88,
                                   facecolor=color, edgecolor=LATTE, lw=1.5))
    ax.text(0, 5.35, "geo markets", fontsize=10, color=INK2)
    ax.add_patch(plt.Rectangle((0.0, -0.65), 0.3, 0.3, facecolor=ACAI, edgecolor=LATTE))
    ax.text(0.42, -0.5, "holdout: brand search paused (~20% of spend)",
            fontsize=9, color=INK, va="center")
    ax.add_patch(plt.Rectangle((0.0, -1.1), 0.3, 0.3, facecolor=GRID, edgecolor=LATTE))
    ax.text(0.42, -0.95, "business as usual; matched on 12-month pre-period",
            fontsize=9, color=INK, va="center")
    ax.text(0.0, -1.55, "readout: TOTAL SQOs per geo, holdout vs synthetic control",
            fontsize=9, color=INK2, va="center")
    fig.text(0.99, 0.01, "illustrative design, not data", fontsize=8,
             color=MUT, ha="right")
    fig.savefig(OUT / "illus_geo_holdout.png")
    plt.close(fig)


def mmm_curves():
    """Schematic: saturation curves, the concept MMM estimates per channel."""
    fig, ax = plt.subplots(figsize=(4.2, 3.6))
    x = np.linspace(0, 10, 200)
    for k, color, label in [(0.55, ACAI, "channel A"), (0.32, BLUE, "channel B"),
                            (0.18, CORN, "channel C")]:
        y = 1 - np.exp(-k * x)
        ax.plot(x, y, color=color, lw=2.4)
        ax.annotate(label, xy=(x[-1], y[-1]), xytext=(4, 0),
                    textcoords="offset points", color=color, fontsize=9.5,
                    fontweight="bold", va="center")
    ax.plot([4.2], [1 - np.exp(-0.55 * 4.2)], marker="o", ms=7, color=INK)
    ax.annotate("marginal return of the\nnext dollar differs by channel",
                xy=(4.2, 1 - np.exp(-0.55 * 4.2)), xytext=(4.6, 0.52),
                fontsize=8.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 1.12)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("spend")
    ax.set_ylabel("incremental outcome")
    fig.text(0.99, 0.01, "illustrative response curves, not fitted to this data",
             fontsize=8, color=MUT, ha="right")
    fig.savefig(OUT / "illus_mmm.png")
    plt.close(fig)


def tracking_debts():
    """Real-data minis: the three tracking debts, drawn from clean_daily.csv."""
    d = pd.read_csv(ROOT / "data-cleaning" / "output" / "clean_daily.csv",
                    parse_dates=["date"])
    d = d[~d.flag_excluded].copy()
    d["ym"] = d["date"].dt.to_period("M")

    fig, axes = plt.subplots(3, 1, figsize=(4.2, 4.9))

    # 1. MQP capture starts Feb-24
    mqp = d.groupby("ym")["mqp"].sum()
    axes[0].plot(mqp.index.to_timestamp(), mqp.values / 1000, color=ACAI, lw=2)
    axes[0].axvline(pd.Timestamp("2024-02-26"), color=CORN, lw=1.2, ls="--")
    axes[0].set_title("monthly MQP (000s): effectively zero before Feb-24", fontsize=9,
                      loc="left", color=INK)

    # 2. website demo definition shift Nov-23
    wd = d[d.program == "website"].groupby("ym")["demo"].sum()
    axes[1].plot(wd.index.to_timestamp(), wd.values, color=ACAI, lw=2)
    axes[1].axvline(pd.Timestamp("2023-11-01"), color=CORN, lw=1.2, ls="--")
    axes[1].set_title("website monthly demo: level shift at Nov-23", fontsize=9,
                      loc="left", color=INK)

    # 3. vendor click batch-dumps (paid_sponsorship daily clicks, FY25 H2)
    sp = d[(d.program == "paid_sponsorship") & (d.date >= "2025-01-01")]
    axes[2].plot(sp["date"], sp["clicks"] / 1000, color=ACAI, lw=1.2)
    axes[2].set_title("paid_sponsorship daily clicks (000s), 2025:\nmonth-start batch spikes",
                      fontsize=9, loc="left", color=INK)

    for ax in axes:
        ax.tick_params(labelsize=7)
        ax.grid(color=GRID, lw=0.5)
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 7)))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
        ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    fig.text(0.99, -0.005, "real series from clean_daily.csv", fontsize=8,
             color=MUT, ha="right")
    fig.tight_layout(h_pad=1.4)
    fig.savefig(OUT / "illus_tracking_debts.png")
    plt.close(fig)


if __name__ == "__main__":
    geo_holdout()
    mmm_curves()
    tracking_debts()
    for p in sorted(OUT.glob("illus_*.png")):
        print(f"wrote {p.relative_to(ROOT)}")
