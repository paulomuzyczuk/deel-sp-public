"""Deel brand palette, extracted from deel.com's live design tokens.

Source: CSS custom properties in https://website-media.deel.com/_next/static/css/*.css
(fetched 2026-08-07). Token names below are Deel's own names, not invented.

Usage in the analysis notebook:

    import sys; sys.path.append("../visual-resources/palette")
    from deel_palette import CORE, CATEGORICAL, SEQUENTIAL_PURPLE, SURFACE
    import matplotlib.pyplot as plt
    plt.style.use("../visual-resources/palette/deel.mplstyle")
"""

# --- Core brand colours (Deel's three "work cycle" hues) -------------------
CORE = {
    "acai": "#5938B7",       # purple  — "afterglow"      (--color-core-acai)
    "blueberry": "#00499D",  # blue    — "mid-day sky"    (--color-core-blue-berry)
    "cornbread": "#FFCF25",  # yellow  — "bright morning" (--color-core-cornbread)
}

# --- Surfaces --------------------------------------------------------------
SURFACE = {
    "white": "#FFFFFF",
    "latte_25": "#FFFBF4",       # default warm page background
    "latte_125": "#FAF4EE",      # highlight / card surface
    "latte_100": "#FEF0D8",      # warm tint
    "dark": "#1B1B1B",
    "dark_purple": "#201547",    # brand dark surface
}

# --- Ink / text ------------------------------------------------------------
INK = {
    "primary": "#141414",
    "secondary": "#1B1B1BD9",    # 85% alpha
    "tertiary": "#1B1B1BB3",     # 70% alpha
    "on_dark": "#FAF4EE",
    "border": "#1B1B1B29",       # 16% alpha
}

# --- Full ramps (Deel token steps) ----------------------------------------
PURPLE = {  # "acai"
    25: "#FAF6FF", 100: "#F6F0FE", 175: "#EDE5FF", 250: "#E1D7FB",
    325: "#D6C9FD", 400: "#C4B1F9", 525: "#A98DF6", 600: "#926EDE",
    675: "#724EC9", 750: "#5938B7", 825: "#452995", 950: "#201547",
}
BLUE = {  # "blueberry" / "seltzer"
    50: "#E9F2FB", 100: "#EDF3FA", 150: "#D8EBFF", 175: "#DBEEFF",
    325: "#B1D8FC", 400: "#92C4F3", 600: "#2187CF", 750: "#0067DF",
    825: "#192253",
}
YELLOW = {  # "cornbread"
    150: "#F5ECC9", 300: "#FFE27C", 400: "#FFCF25",
}
GREEN = {
    100: "#E6F7E0", 250: "#C2EEB5", 375: "#8CCA82",
    400: "#83D072", 600: "#3F9532", 675: "#15740F",
}
RED = {400: "#FFA69B", 600: "#F95250"}
NEUTRAL = {
    50: "#FAFAFA", 100: "#F2F2F2", 200: "#E6E6E6", 275: "#CFCFCF",
    300: "#CCCCCC", 400: "#A6A6A6", 700: "#404040", 900: "#141414",
}

# --- Chart palettes --------------------------------------------------------
# Validated on surface #FFFBF4 (light): lightness band PASS, chroma floor PASS,
# CVD separation PASS (worst adjacent dE 14.1 deutan), normal-vision floor PASS
# (worst adjacent dE 19.4).
# CAVEAT: #C98A00 (2.86:1) and #A98DF6 (2.60:1) fall below 3:1 contrast against
# the latte surface -> any chart using slots 3 or 4 must carry visible direct
# labels or an accompanying data table. Do not rely on the fill alone.
#
# Assign these in FIXED ORDER by entity, never cycled and never by rank.
CATEGORICAL = [
    "#5938B7",  # 1 acai purple      (Deel core)
    "#2187CF",  # 2 blue 600         (blueberry family, lightened for contrast)
    "#C98A00",  # 3 dark cornbread   (derived: cornbread darkened to clear the
                #                      lightness band; #FFCF25 itself is L 0.87)
    "#A98DF6",  # 4 purple 525
    "#15740F",  # 5 green 675        (only when no status meaning is implied)
]

# Magnitude / intensity — one hue, light to dark (Deel's own acai ramp).
SEQUENTIAL_PURPLE = [
    "#EDE5FF", "#D6C9FD", "#C4B1F9", "#A98DF6",
    "#926EDE", "#724EC9", "#5938B7", "#452995",
]

# Polarity (e.g. over/under plan) — two hues + NEUTRAL grey midpoint.
DIVERGING = ["#C98A00", "#E4C77F", "#E6E6E6", "#A98DF6", "#5938B7"]

# Reserved status colours — never reuse as a categorical series.
STATUS = {
    "good": "#15740F",
    "warning": "#FFCF25",
    "critical": "#F95250",
}

# --- Typography ------------------------------------------------------------
# Deel's brand typeface is Bagoss (Displaay Type Foundry) - COMMERCIAL LICENCE,
# not redistributed in this repo. Deel's own stylesheet declares Inter alongside
# the three Bagoss families, so Inter is the defensible free stand-in.
#
# IMPORTANT — the literal family name is "Inter 28pt", not "Inter".
# Google Fonts ships Inter as optical-size subfamilies; the installed static
# files (Inter_28pt-{Regular,Medium,SemiBold,Bold}.ttf) register as:
#   nameID1: "Inter 28pt" (Regular+Bold), "Inter 28pt Medium", "Inter 28pt SemiBold"
#   nameID16 (typographic family): "Inter 28pt" for all four
# Passing "Inter" fails to resolve. Use PPTX_FONT / PPTX_FONT_MEDIUM below when
# writing <a:latin typeface="..."/> via python-pptx.
FONT_FAMILY = "Inter 28pt"
PPTX_FONT = "Inter 28pt"              # Regular + Bold (bold=True toggles weight)
PPTX_FONT_MEDIUM = "Inter 28pt Medium"
PPTX_FONT_SEMIBOLD = "Inter 28pt SemiBold"

FONT_STACK = ["Inter 28pt", "Helvetica Neue", "Arial", "DejaVu Sans", "sans-serif"]
