"""Shared loading, classification, disclosure control and chart style."""
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import os

PAPER = Path(__file__).resolve().parents[1]         # the package folder (paper/ or the public repo)
ROOT = Path(os.environ.get("BDI_DATA_DIR", PAPER.parent))   # folder holding the confidential BDI_*.dta files
EXT = PAPER / "ext"
# PUBLIC mode (BDI_PUBLIC=1): sanitized outputs for external release, written to paper/public/.
PUBLIC = os.environ.get("BDI_PUBLIC") == "1"
OUT = PAPER / "public" if PUBLIC else PAPER
FIG = OUT / "figures"
TAB = OUT / "tables"
NUM_FILE = OUT / "numbers.json"
DLOG_FILE = OUT / "disclosure_log.txt"
TEX_FILE = OUT / ("burundi_trade_stylized_facts_public.tex" if PUBLIC else "burundi_trade_stylized_facts.tex")
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

DYN_START = 2015   # firm identifiers are consistent (tax-ID format) from 2015 onward
MIN_FIRMS = 3          # disclosure rule: no published cell with fewer than 3 firms
MAX_DOM = 85.0         # PUBLIC mode: no published cell where one firm exceeds 85% of the value
MERGE_DOM = 75.0       # PUBLIC mode: a combined (confidential) cell must have top-firm share <= 75%
NUM = {}               # numbers quoted in the text
CHART_DATA = []        # data behind every chart panel (exported to the Excel workbook)
TABLE_DATA = {}        # generated tables (exported to the Excel workbook)
SUPPRESSED = []        # log of disclosure-control actions


# --------------------------------------------------------------------------- data
def load():
    E = pd.read_stata(ROOT / "BDI_EXP.dta")
    EM = pd.read_stata(ROOT / "BDI_EXP_monthly.dta")
    IM = pd.read_stata(ROOT / "BDI_IMP_monthly.dta")
    for df in (E, EM, IM):
        df["y"] = df["y"].astype(int)
        df["h2"] = df.hs.str[:2]
        df["h4"] = df.hs.str[:4]
    E["grp"] = E.hs.map(export_group)
    EM["grp"] = EM.hs.map(export_group)
    IM["cat"] = IM.hs.map(import_category)
    E["region"] = E.d.map(export_region)
    EM["region"] = EM.d.map(export_region)
    IM["region"] = IM.o.map(partner_region)
    IM["date"] = pd.to_datetime(dict(year=IM.y, month=IM.m, day=1))
    EM["date"] = pd.to_datetime(dict(year=EM.y, month=EM.m, day=1))
    fix_fuel_values(IM)
    return E, EM, IM


FUEL_UV_MAX = 20  # US$/kg; refined petroleum trades at roughly US$1/kg
FUEL_V_MIN = 1e6  # only records large enough to move the totals


def fix_fuel_values(IM):
    """Revalue large HS 27 records whose unit value is implausible (treated as value-entry errors) at the median
    unit value of the other HS 27 records in the same month. Tonnage is kept."""
    fu = (IM.cat == "Fuel") & (IM.q > 0)
    uv = IM.v / IM.q
    bad = fu & (uv > FUEL_UV_MAX) & (IM.v > FUEL_V_MIN)
    med = uv[fu & ~bad].groupby([IM.y, IM.m]).median()
    new = IM.loc[bad, "q"] * [med[(y, m)] for y, m in zip(IM.loc[bad, "y"], IM.loc[bad, "m"])]
    NUM.update(fuel_fix_n=int(bad.sum()), fuel_fix_uv_min=uv[bad].min(), fuel_fix_v_old=IM.loc[bad, "v"].sum() / 1e6, fuel_fix_v_new=new.sum() / 1e6)
    IM.loc[bad, "v"] = new


def wdi(code):
    d = json.load(open(EXT / f"wdi_{code}.json"))
    return pd.Series({int(r["date"]): r["value"] for r in d[1] if r["value"] is not None}).sort_index()


# ---------------------------------------------------------------- classifications
EXPORT_GROUPS = ["Coffee", "Tea and other agriculture", "Gold and mineral ores",
                 "Agro-industry", "Manufactures", "Machinery, vehicles and fuel"]


def export_group(hs):
    h2, h4 = hs[:2], hs[:4]
    if not h2.isdigit():
        return "Manufactures"
    c = int(h2)
    if h4 == "0901" or (PUBLIC and h4 == "0902"):        # PUBLIC: tea merged with coffee
        return "Coffee"
    if h2 in ("26", "71"):
        return "Gold and mineral ores"
    if c == 11 or 15 <= c <= 24:
        return "Agro-industry"
    if c <= 14:
        return "Tea and other agriculture"
    if c == 27 or 84 <= c <= 89:
        return "Machinery, vehicles and fuel"
    return "Manufactures"


IMPORT_CATS = ["Fuel", "Food and agriculture", "Fertilisers", "Pharmaceuticals",
               "Other chemicals and plastics", "Construction materials and metals",
               "Machinery and equipment", "Vehicles and transport equipment",
               "Consumer manufactures"]


def import_category(hs):
    h2 = hs[:2]
    if not h2.isdigit():
        return "Consumer manufactures"
    c = int(h2)
    if c == 27:
        return "Fuel"
    if c <= 24:
        return "Food and agriculture"
    if c == 31:
        return "Other chemicals and plastics" if PUBLIC else "Fertilisers"   # PUBLIC: merged
    if c == 30:
        return "Pharmaceuticals"
    if 28 <= c <= 40:
        return "Other chemicals and plastics"
    if c in (25, 26, 68, 69, 70) or 72 <= c <= 83:
        return "Construction materials and metals"
    if c in (84, 85, 90):
        return "Machinery and equipment"
    if 86 <= c <= 89:
        return "Vehicles and transport equipment"
    return "Consumer manufactures"


EAC5 = ["KEN", "UGA", "TZA", "RWA", "SSD"]
REGIONAL_SET = set(["COD"] + EAC5)   # DR Congo + EAC partners
EU_EUR = ["AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN",
          "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP",
          "SWE", "GBR", "CHE", "NOR", "ISL"]
GULF = ["ARE", "SAU", "OMN", "QAT", "KWT", "BHR"]
AFRICA = ["DZA", "AGO", "BEN", "BWA", "BFA", "BDI", "CPV", "CMR", "CAF", "TCD", "COM", "COG", "COD",
          "CIV", "DJI", "EGY", "GNQ", "ERI", "SWZ", "ETH", "GAB", "GMB", "GHA", "GIN", "GNB", "KEN",
          "LSO", "LBR", "LBY", "MDG", "MWI", "MLI", "MRT", "MUS", "MAR", "MOZ", "NAM", "NER", "NGA",
          "RWA", "STP", "SEN", "SYC", "SLE", "SOM", "ZAF", "SSD", "SDN", "TZA", "TGO", "TUN", "UGA",
          "ZMB", "ZWE", "ESH"]
COMESA = ["COM", "COD", "DJI", "EGY", "ERI", "ETH", "KEN", "LBY", "MDG", "MWI", "MUS", "RWA", "SYC",
          "SOM", "SDN", "SWZ", "TUN", "UGA", "ZMB", "ZWE"]
SADC = ["AGO", "BWA", "COM", "COD", "SWZ", "LSO", "MDG", "MWI", "MUS", "MOZ", "NAM", "SYC", "ZAF",
        "TZA", "ZMB", "ZWE"]

REGIONS = ["DR Congo", "EAC partners", "Rest of Africa", "Gulf states", "Europe",
           "China", "India", "Other Asia and rest of world"]


def partner_region(iso):
    if iso == "COD":
        return "DR Congo"
    if iso in EAC5:
        return "EAC partners"
    if iso in AFRICA:
        return "Rest of Africa"
    if iso in GULF:
        return "Gulf states"
    if iso in EU_EUR:
        return "Europe"
    if iso == "CHN":
        return "China"
    if iso == "IND":
        return "India"
    return "Other Asia and rest of world"


def export_region(iso):
    """Export destinations; PUBLIC merges the Gulf, China and India into one region (dominance rule)."""
    r = partner_region(iso)
    if PUBLIC and r in ("Gulf states", "China", "India"):
        return "Other Asia and rest of world"
    return r


# display labels for merged categories in PUBLIC mode
LABELS = {"Coffee": "Coffee and tea", "Tea and other agriculture": "Other agriculture",
          "Other chemicals and plastics": "Chemicals, fertilisers and plastics",
          "Other AfCFTA": "Rest of Africa (AfCFTA)"} if PUBLIC else {}
COMBINED = "Combined for confidentiality"


def lab(x):
    return LABELS.get(x, x)


def bloc(iso):
    """Mutually exclusive trade-agreement tiers from Burundi's viewpoint."""
    if iso == "COD":
        return "DR Congo"
    if iso in EAC5:
        return "EAC partners"
    if (iso in COMESA or iso in SADC) and not PUBLIC:     # PUBLIC: merged into one Africa tier
        return "Other COMESA/SADC"
    if iso in AFRICA:
        return "Other AfCFTA"
    return "Rest of world"


# ---------------------------------------------------------------- disclosure control
def chart_data(fig_no, panel, title, df, unit="", note=""):
    """Register the data plotted in one chart panel (paper figure number, panel letter)."""
    df = df.to_frame() if isinstance(df, pd.Series) else df.copy()
    df.columns = [str(x) for x in df.columns]
    CHART_DATA.append(dict(fig=fig_no, panel=panel, title=title, df=df, unit=unit, note=note))


def table_data(no, title, df, note=""):
    """Register a generated table (paper table number)."""
    df = df.copy()
    df.columns = [str(x) for x in df.columns]
    TABLE_DATA[no] = dict(title=title, df=df, note=note)


def check_cells(df, by, label, firm="f"):
    """Record/return cells with fewer than MIN_FIRMS distinct firms."""
    n = df.groupby(by)[firm].nunique()
    bad = n[n < MIN_FIRMS]
    if len(bad):
        SUPPRESSED.append((label, len(bad), [tuple(np.atleast_1d(i)) for i in bad.index[:8]]))
    return n


def top_share(df, by, value="v"):
    """Share (%) of the largest firm in each cell defined by `by`."""
    by = [by] if isinstance(by, str) else list(by)
    g = df.groupby(by + ["f"])[value].sum()
    lv = list(range(len(by)))
    return g.groupby(level=lv).max() / g.groupby(level=lv).sum() * 100


def dominated(df, by, value="v"):
    """Boolean Series: cells where one firm exceeds MAX_DOM (always False outside PUBLIC mode)."""
    s = top_share(df, by, value)
    return (s > MAX_DOM) if PUBLIC else (s > 1e9)


def safe_pivot(df, index, columns, label, values="v", scale=1e6):
    """Pivot of summed values; cells < MIN_FIRMS (and, in PUBLIC mode, dominated cells) set to NaN."""
    val = df.pivot_table(index=index, columns=columns, values=values, aggfunc="sum")
    n = df.pivot_table(index=index, columns=columns, values="f", aggfunc="nunique")
    mask = n < MIN_FIRMS
    if mask.values.sum():
        SUPPRESSED.append((label, int(mask.values.sum()), "cells suppressed (<3 firms)"))
    if PUBLIC:
        dm = top_share(df, [index, columns], values).unstack().reindex_like(val) > MAX_DOM
        dm = dm.fillna(False).astype(bool)
        if dm.values.sum():
            SUPPRESSED.append((label, int(dm.values.sum()), "cells suppressed (dominance)",
                               [(r, c) for r in dm.index for c in dm.columns if dm.loc[r, c]]))
        mask = mask | dm
    return (val / scale).where(~mask), n


def sdc_pivot(df, index, columns, label, values="v", scale=1e6):
    """safe_pivot + (PUBLIC mode) secondary suppression: each suppressed cell is combined with the
    smallest other cell(s) of the same row until the combined cell passes both rules; the combined
    value is reported in a separate column so shares still add up without revealing any cell."""
    val, n = safe_pivot(df, index, columns, label, values, scale)
    if not PUBLIC:
        return val, n
    raw = df.pivot_table(index=index, columns=columns, values=values, aggfunc="sum") / scale
    comb = pd.Series(np.nan, index=val.index)
    for r in val.index:
        hidden = [c for c in val.columns if pd.isna(val.loc[r, c]) and raw.loc[r, c] > 0]
        if not hidden:
            continue
        sub = df[df[index] == r]

        def ok(cs):
            g = sub[sub[columns].isin(cs)].groupby("f")[values].sum()
            return len(g) >= MIN_FIRMS and g.max() / g.sum() * 100 <= MERGE_DOM

        # smallest workable set: fewest partner cells first, then smallest combined value
        from itertools import combinations
        others = list(val.loc[r].dropna().index)
        cells = None
        for k in range(0, len(others) + 1):
            cands = sorted(combinations(others, k), key=lambda cs: raw.loc[r, list(cs)].sum() if cs else 0)
            for cs in cands:
                if ok(hidden + list(cs)):
                    cells = hidden + list(cs)
                    break
            if cells:
                break
        if cells:
            comb[r] = raw.loc[r, cells].sum()
            for c in cells:
                val.loc[r, c] = np.nan
            SUPPRESSED.append((label, r, "combined for confidentiality", cells))
            NUM.setdefault("sdc_combined", {}).setdefault(label, {})[str(r)] = [lab(c) for c in cells]
    if comb.notna().any():
        val[COMBINED] = comb
    return val, n


def monthly_exports(EM):
    """Monthly export totals (US$ m). PUBLIC: dominated months suppressed, plus secondary suppression
    of the smallest months of the same year until the suppressed set passes MERGE_DOM (the annual
    total is published, so a single hidden month could otherwise be recovered by subtraction)."""
    m = EM.groupby("date").v.sum() / 1e6
    if not PUBLIC:
        return m
    ts_ = top_share(EM, ["date"])
    primary = list(ts_[ts_ > MAX_DOM].index)
    hide = set()
    for d in primary:
        cells = [d]
        for d2 in m[(m.index.year == d.year) & (m.index != d)].sort_values().index:
            g = EM[EM.date.isin(cells)].groupby("f").v.sum()
            if g.max() / g.sum() * 100 <= MERGE_DOM:
                break
            cells.append(d2)
        hide |= set(cells)
    first = "monthly_suppressed" not in NUM
    NUM["monthly_suppressed"] = [d.strftime("%Y-%m") for d in sorted(hide)]
    if hide and first:
        SUPPRESSED.append(("monthly exports", len(hide), "months suppressed", NUM["monthly_suppressed"]))
    return m.where(~m.index.isin(sorted(hide)))


def stack_bars(a, df, cols, colors, width=0.78, lw=0.5):
    """Stacked bars in fixed order; skips empty series; draws a hatched 'combined' segment last."""
    bottom = np.zeros(len(df))
    for c in cols + ([COMBINED] if COMBINED in df.columns else []):
        if c not in df.columns or df[c].fillna(0).sum() == 0:
            continue
        v = df[c].fillna(0).values
        if c == COMBINED:
            a.bar(df.index, v, bottom=bottom, width=width, label=c, **COMBINED_STYLE)
        else:
            a.bar(df.index, v, bottom=bottom, color=colors[c], width=width, label=lab(c),
                  edgecolor="white", linewidth=lw)
        bottom += v


# ------------------------------------------------------------------------- style
C = dict(blue="#2a78d6", orange="#eb6834", aqua="#1baf7a", yellow="#eda100", magenta="#e87ba4",
         green="#008300", violet="#4a3aa7", red="#e34948", gray="#b5b3ab", dark="#52514e",
         ink="#0b0b0b", ink2="#52514e", muted="#898781", grid="#e1e0d9", axis="#c3c2b7",
         shade="#f0efec", navy="#184f95", lightblue="#9ec5f4")
CAT8 = [C["blue"], C["orange"], C["aqua"], C["yellow"], C["magenta"], C["green"], C["violet"], C["red"]]

EXPORT_COLORS = dict(zip(EXPORT_GROUPS, [C["navy"], C["aqua"], C["yellow"], C["orange"],
                                         C["violet"], C["gray"]]))
IMPORT_COLORS = dict(zip(IMPORT_CATS, [C["dark"], C["aqua"], C["green"], C["magenta"], C["violet"],
                                       C["yellow"], C["blue"], C["navy"], C["orange"]]))
REGION_COLORS = dict(zip(REGIONS, [C["orange"], C["aqua"], C["green"], C["yellow"], C["blue"],
                                   C["red"], C["magenta"], C["gray"]]))
BLOC_COLORS = {"DR Congo": C["orange"], "EAC partners": C["aqua"], "Other COMESA/SADC": C["green"],
               "Other AfCFTA": C["yellow"], "Rest of world": C["gray"]}
COMBINED_STYLE = dict(color="#dcdad3", hatch="////", edgecolor="#8f8d86", linewidth=0.3)

W_FULL, W_HALF = 6.3, 3.05


def set_style():
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 8, "axes.titlesize": 8.5, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.titlepad": 6,
        "axes.labelsize": 7.5, "axes.labelcolor": C["ink2"],
        "xtick.labelsize": 7, "ytick.labelsize": 7,
        "xtick.color": C["ink2"], "ytick.color": C["ink2"],
        "axes.edgecolor": C["axis"], "axes.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": C["grid"], "grid.linewidth": 0.5,
        "axes.axisbelow": True, "xtick.major.size": 2.5, "ytick.major.size": 0,
        "xtick.major.width": 0.6, "legend.fontsize": 7, "legend.frameon": False,
        "lines.linewidth": 1.6, "lines.solid_capstyle": "round",
        "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
        "pdf.fonttype": 42, "ps.fonttype": 42, "text.color": C["ink"],
        "patch.linewidth": 0,
    })


EVENTS = {  # (start, end, label) in fractional years for annual/monthly axes
    "crisis": (2015.3, 2015.9, "2015 political crisis"),
    "covid": (2020.2, 2020.6, "COVID-19"),
    "deval": (2023.35, 2023.45, "May 2023 devaluation"),
}


def shade_events(ax, keys=("crisis", "covid", "deval"), dates=False, label=True, ypos=0.98):
    for k in keys:
        a, b, lab = EVENTS[k]
        if dates:
            a = pd.Timestamp(int(a), int((a % 1) * 12) + 1, 1)
            b = pd.Timestamp(int(b), int((b % 1) * 12) + 1, 1)
        ax.axvspan(a, b, color=C["shade"], zorder=0, lw=0)
        if label:
            ax.text(a, ypos, " " + lab, transform=ax.get_xaxis_transform(), fontsize=6,
                    color=C["muted"], va="top", ha="left")


def _r(v):
    """Round to 6 significant digits for platform-independent comparison."""
    v = float(v)
    return 0.0 if v == 0 or not np.isfinite(v) else float(f"{v:.6g}")


def fig_data(fig):
    """Plotted data of a figure (lines, bars, points, labels), independent of fonts and renderer."""
    out = []
    for ax in fig.axes:
        d = {"title": ax.get_title(loc="left") or ax.get_title(), "xlabel": ax.get_xlabel(),
             "ylabel": ax.get_ylabel(), "lines": [], "bars": [], "points": [],
             "texts": sorted(t.get_text() for t in ax.texts if t.get_text()),
             "ticklabels": [t.get_text() for t in ax.get_yticklabels() + ax.get_xticklabels() if t.get_text()]}
        for ln in ax.get_lines():
            x = np.asarray(ln.get_xdata(), dtype=object)
            x = [str(v)[:10] if not isinstance(v, (int, float, np.floating, np.integer)) else _r(v) for v in x]
            d["lines"].append([ln.get_label() if not ln.get_label().startswith("_") else "",
                               x, [_r(v) for v in np.asarray(ln.get_ydata(), dtype=float)]])
        for p in ax.patches:
            if isinstance(p, mpl.patches.Rectangle):
                d["bars"].append([_r(p.get_x()), _r(p.get_y()), _r(p.get_width()), _r(p.get_height())])
        for col in ax.collections:
            off = col.get_offsets()
            if len(off) and len(off) < 5000:
                d["points"].append([[_r(a), _r(b)] for a, b in np.asarray(off, dtype=float)])
        leg = ax.get_legend()
        d["legend"] = [t.get_text() for t in leg.get_texts()] if leg else []
        out.append(d)
    if fig.legends:
        out.append({"figure_legend": [t.get_text() for lg in fig.legends for t in lg.get_texts()]})
    return out


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", metadata={"CreationDate": None, "ModDate": None})
    (FIG / "data").mkdir(exist_ok=True)
    (FIG / "data" / f"{name}.json").write_text(json.dumps(fig_data(fig), indent=0, default=str))
    plt.close(fig)


def fmt_m(x, _=None):
    return f"{x:,.0f}"


def year_axis(ax, years, step=2):
    ax.set_xticks([y for y in years if (y - years[0]) % step == 0])
    ax.set_xlim(min(years) - 0.6, max(years) + 0.6)
    ax.grid(axis="x", visible=False)


def direct_label_lines(ax, series_dict, colors, x_last, dx=0.25, min_gap=None, fontsize=6.5):
    """Place labels at the right end of lines, nudging to avoid overlaps."""
    items = sorted(((s.dropna().iloc[-1], k) for k, s in series_dict.items() if s.notna().any()))
    lo, hi = ax.get_ylim()
    gap = min_gap or (hi - lo) * 0.055
    ys = []
    for v, k in items:
        y = v if not ys or v - ys[-1] >= gap else ys[-1] + gap
        ys.append(y)
        ax.text(x_last + dx, y, k, color=C["ink2"], fontsize=fontsize, va="center", ha="left")
        ax.plot([x_last + 0.02, x_last + dx * 0.8], [series_dict[k].dropna().iloc[-1], y],
                color=colors[k], lw=0.6)


def save_numbers():
    json.dump(NUM, open(NUM_FILE, "w"), indent=1, default=float)
    with open(DLOG_FILE, "w") as fh:
        for row in SUPPRESSED:
            fh.write(repr(row) + "\n")


def _esc(x):
    return str(x).replace("&", r"\&").replace("%", r"\%").replace("$", r"\$")


def latex_table(df, name, fmt=None, index=True, col_format=None, header_rows=None):
    """Write a booktabs tabular body (no float wrapper). header_rows are raw LaTeX."""
    fmt = fmt or {}
    cols = list(df.columns)
    col_format = col_format or ("l" + "r" * len(cols) if index else "l" + "r" * (len(cols) - 1))
    lines = [f"\\begin{{tabular}}{{{col_format}}}", "\\toprule"]
    if header_rows:
        lines += header_rows
    else:
        head = ([df.index.name or ""] if index else []) + [_esc(c) for c in cols]
        lines.append(" & ".join(head) + r" \\")
    lines.append("\\midrule")
    for idx, row in df.iterrows():
        cells = [_esc(idx)] if index else []
        for c in cols:
            v = row[c]
            if isinstance(v, str):
                cells.append(_esc(v))
            elif pd.isna(v):
                cells.append("--")
            else:
                cells.append(fmt.get(c, "{:,.1f}").format(v))
        lines.append(" & ".join(cells) + r" \\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (TAB / f"{name}.tex").write_text("\n".join(lines) + "\n")
