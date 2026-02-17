"""
science_plot.py
Publication-quality plot configuration following Nature/Science standards.

Rules applied:
- Font: Helvetica / sans-serif, 7–8 pt (panel labels 8 pt bold)
- Line width: 0.75–1.5 pt
- Marker size: 4–6 pt
- Color palettes: colorblind-safe, max 6 colors
- White background, black axes, inward ticks
- No top/right spines
- Figure size: single column 3.5 in, double column 7.0 in
- DPI: 300 for print, 150 for screen
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import AutoMinorLocator

# ── Nature-style matplotlib rcParams ─────────────────────────────────────────
NATURE_RC = {
    # fonts
    "font.family":          "sans-serif",
    "font.sans-serif":      ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size":            8,
    "axes.titlesize":       8,
    "axes.labelsize":       8,
    "xtick.labelsize":      7,
    "ytick.labelsize":      7,
    "legend.fontsize":      7,
    "legend.title_fontsize":7,
    # axes
    "axes.linewidth":       0.8,
    "axes.spines.top":      False,
    "axes.spines.right":    False,
    "axes.unicode_minus":   False,
    "axes.formatter.use_mathtext": True,
    # ticks
    "xtick.direction":      "in",
    "ytick.direction":      "in",
    "xtick.major.width":    0.8,
    "ytick.major.width":    0.8,
    "xtick.minor.width":    0.5,
    "ytick.minor.width":    0.5,
    "xtick.major.size":     3.5,
    "ytick.major.size":     3.5,
    "xtick.minor.size":     2.0,
    "ytick.minor.size":     2.0,
    "xtick.top":            False,
    "ytick.right":          False,
    # lines & markers
    "lines.linewidth":      1.2,
    "lines.markersize":     4.5,
    "patch.linewidth":      0.8,
    # legend
    "legend.frameon":       True,
    "legend.framealpha":    0.9,
    "legend.edgecolor":     "0.8",
    "legend.handlelength":  1.5,
    # figure
    "figure.dpi":           150,
    "savefig.dpi":          300,
    "savefig.bbox":         "tight",
    "savefig.pad_inches":   0.05,
    "figure.facecolor":     "white",
    "axes.facecolor":       "white",
}

def apply_nature_style():
    """Apply Nature-journal rcParams globally."""
    mpl.rcParams.update(NATURE_RC)

# ── Colorblind-safe palettes ──────────────────────────────────────────────────
# Based on Wong (2011) Nature Methods — 7 colors
WONG7 = ["#000000","#E69F00","#56B4E9","#009E73",
          "#F0E442","#0072B2","#D55E00","#CC79A7"]

# Cool-to-warm for temperature gradient (matches physics intuition)
def temp_cmap(n):
    """Return n colors from cool (low T) to warm (high T)."""
    cmap = mpl.colormaps.get_cmap("RdYlBu_r")
    return [mcolors.to_hex(cmap(i/(max(n-1,1)))) for i in range(n)]

def seq_cmap(n, name="viridis"):
    cmap = mpl.colormaps.get_cmap(name)
    return [mcolors.to_hex(cmap(i/(max(n-1,1)))) for i in range(n)]

# ── Figure size helpers ───────────────────────────────────────────────────────
SINGLE_COL = (3.5, 2.8)   # inches
DOUBLE_COL = (7.0, 2.8)
TALL_SINGLE = (3.5, 4.5)
TALL_DOUBLE = (7.0, 4.5)

# ── Axis formatting helpers ───────────────────────────────────────────────────
def format_ax(ax, minor=True):
    """Standard axis cleanup."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    if minor:
        ax.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax.yaxis.set_minor_locator(AutoMinorLocator(2))

def panel_label(ax, letter, x=-0.18, y=1.05):
    """Add bold panel letter (a, b, c …)."""
    ax.text(x, y, letter, transform=ax.transAxes,
            fontsize=9, fontweight="bold", va="top", ha="left")

# ── Plotly layout template ────────────────────────────────────────────────────
PLOTLY_TEMPLATE = {
    "layout": {
        "font":       {"family": "Helvetica, Arial, sans-serif", "size": 12, "color": "#1a1a1a"},
        "title":      {"font": {"size": 13, "color": "#1a1a1a"}, "x": 0.5, "xanchor": "center"},
        "xaxis":      {"showgrid": False, "zeroline": False, "linecolor": "#1a1a1a",
                       "linewidth": 1.0, "ticks": "inside", "ticklen": 5,
                       "mirror": False, "showspikes": False,
                       "title": {"font": {"size": 12}}},
        "yaxis":      {"showgrid": False, "zeroline": False, "linecolor": "#1a1a1a",
                       "linewidth": 1.0, "ticks": "inside", "ticklen": 5,
                       "mirror": False, "showspikes": False,
                       "title": {"font": {"size": 12}}},
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "legend":     {"bgcolor": "rgba(255,255,255,0.9)",
                       "bordercolor": "#cccccc", "borderwidth": 0.8,
                       "font": {"size": 11}},
        "margin":     {"l": 60, "r": 20, "t": 50, "b": 50},
        "hoverlabel": {"bgcolor": "white", "bordercolor": "#aaa",
                       "font": {"size": 11}},
    }
}

def apply_plotly_style(fig, height=420, title=""):
    """Apply Nature-style layout to a Plotly figure."""
    import plotly.graph_objects as go
    fig.update_layout(
        height=height,
        font=PLOTLY_TEMPLATE["layout"]["font"],
        title=dict(text=title, **{k:v for k,v in PLOTLY_TEMPLATE["layout"]["title"].items() if k!="font"},
                   font=PLOTLY_TEMPLATE["layout"]["title"]["font"]),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=PLOTLY_TEMPLATE["layout"]["legend"],
        margin=PLOTLY_TEMPLATE["layout"]["margin"],
        hoverlabel=PLOTLY_TEMPLATE["layout"]["hoverlabel"],
    )
    fig.update_xaxes(**PLOTLY_TEMPLATE["layout"]["xaxis"])
    fig.update_yaxes(**PLOTLY_TEMPLATE["layout"]["yaxis"])
    return fig
