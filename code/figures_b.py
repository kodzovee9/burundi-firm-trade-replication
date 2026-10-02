"""Imports under forex scarcity, firm-level forex balance sheet, corridors, DRC,
unit values and mirror statistics, AfCFTA readiness."""
import json

import matplotlib.pyplot as plt
import matplotlib.ticker as mt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from common import *  # noqa: F401,F403

M49 = {784: "ARE", 757: "CHE", 56: "BEL", 276: "DEU", 404: "KEN", 834: "TZA", 800: "UGA", 646: "RWA",
       180: "COD", 156: "CHN", 699: "IND", 586: "PAK", 826: "GBR", 842: "USA", 702: "SGP", 512: "OMN",
       729: "SDN", 894: "ZMB", 710: "ZAF", 682: "SAU", 251: "FRA", 392: "JPN", 818: "EGY", 528: "NLD",
       380: "ITA", 724: "ESP", 792: "TUR", 764: "THA", 360: "IDN", 458: "MYS", 36: "AUS", 124: "CAN",
       410: "KOR", 344: "HKG", 490: "TWN", 504: "MAR", 231: "ETH", 454: "MWI", 508: "MOZ", 716: "ZWE"}


# ----------------------------------------------------- imports under forex scarcity (P1)
def fig_monthly_imports(IM, E):
    nf = IM[IM.cat != "Fuel"]
    mv = nf.groupby("date").v.sum() / 1e6
    mv12 = mv.rolling(12).mean()
    nfirm = IM.groupby("date").f.nunique()
    nfirm12 = nfirm.rolling(12).mean()
    # exporter vs non-exporter imports (firm is an exporter in that calendar year)
    exp_fy = set(map(tuple, E[["f", "y"]].drop_duplicates().values))
    nf = nf.assign(exporter=[(f, y) in exp_fy for f, y in zip(nf.f, nf.y)])
    by = nf[nf.y >= DYN_START].groupby(["date", "exporter"]).v.sum().unstack() / 1e6
    by12 = by.rolling(12).mean()
    base = by12.loc["2015-12-01"]
    idx = by12 / base * 100
    fig, axs = plt.subplots(1, 3, figsize=(W_FULL, 2.35))
    a = axs[0]
    a.plot(mv.index, mv.values, color=C["lightblue"], lw=0.7, label="Monthly")
    a.plot(mv12.index, mv12.values, color=C["navy"], lw=1.6, label="12-month average")
    shade_events(a, dates=True, label=False)
    a.set_title("(a) Non-fuel imports, US$ m / month")
    a.legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    a.set_ylim(0, 85)
    a = axs[1]
    a.plot(nfirm.index, nfirm.values, color=C["lightblue"], lw=0.7)
    a.plot(nfirm12.index, nfirm12.values, color=C["navy"], lw=1.6)
    shade_events(a, dates=True, label=False)
    a.set_title("(b) Active importers per month")
    a.set_ylim(0, None)
    a = axs[2]
    a.plot(idx.index, idx[True], color=C["blue"], label="Exporting firms")
    a.plot(idx.index, idx[False], color=C["orange"], label="Non-exporting firms")
    shade_events(a, dates=True, label=False)
    a.axhline(100, color=C["axis"], lw=0.6)
    a.set_title("(c) Imports by trader type, Dec 2015 = 100")
    a.legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    for a in axs:
        a.grid(axis="x", visible=False)
        a.xaxis.set_major_locator(plt.matplotlib.dates.YearLocator(3))
        a.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%Y"))
    fig.tight_layout(w_pad=1.3)
    _a = pd.DataFrame({"Non-fuel imports, monthly": mv, "12-month average": mv12})
    _b = pd.DataFrame({"Active importers, monthly": nfirm, "12-month average": nfirm12})
    _c = idx.rename(columns={True: "Exporting firms", False: "Non-exporting firms"})
    for _df in (_a, _b, _c):
        _df.index = _df.index.strftime("%Y-%m")
    chart_data(11, "a", "Non-fuel imports per month", _a.rename_axis("Month"), "US$ million")
    chart_data(11, "b", "Active importers per month", _b.rename_axis("Month"), "Number of firms")
    chart_data(11, "c", "Non-fuel imports by trader type (12-month moving average)", _c.rename_axis("Month"), "Index, Dec 2015 = 100", "Exporting firm = a firm with exports in the same calendar year.")
    save(fig, "f10_monthly_imports")
    ann = nf.groupby("y").v.sum() / 1e6
    NUM.update(nf_2015=ann[2015], nf_2016=ann[2016], nf_2018=ann[2018], nf_2023=ann[2023], nf_2014=ann[2014],
               nf_drop_14_18=(ann[2018] / ann[2014] - 1) * 100,
               nfirm_month_2014=nfirm.loc["2014"].mean(), nfirm_month_2018=nfirm.loc["2018"].mean(),
               nfirm_month_2023=nfirm.loc["2023"].mean(),
               idx_exp_2018=idx.loc["2018-12-01", True], idx_non_2018=idx.loc["2018-12-01", False],
               idx_exp_2023=idx.loc["2023-12-01", True], idx_non_2023=idx.loc["2023-12-01", False])
    # pre/post devaluation window: Jun-Dec 2023 vs Jun-Dec 2022
    w1 = nf[(nf.date >= "2023-06-01") & (nf.date <= "2023-12-01")].v.sum()
    w0 = nf[(nf.date >= "2022-06-01") & (nf.date <= "2022-12-01")].v.sum()
    NUM["postdeval_yoy"] = (w1 / w0 - 1) * 100


def fig_import_categories(IM):
    val, n = safe_pivot(IM, "y", "cat", "import categories small multiples")
    cats = ["Food and agriculture", "Fertilisers", "Pharmaceuticals", "Construction materials and metals",
            "Machinery and equipment", "Vehicles and transport equipment", "Consumer manufactures",
            "Other chemicals and plastics", "Fuel"]
    cats = [c for c in cats if c in val.columns]
    fig, axs = plt.subplots(3, 3, figsize=(W_FULL, 4.6), sharex=True)
    for a in list(axs.flat)[len(cats):]:
        a.set_visible(False)
    for a, c in zip(axs.flat, cats):
        a.bar(val.index, val[c], color=IMPORT_COLORS[c], width=0.72)
        a2 = n[c]
        a.set_title(lab(c) if c != "Construction materials and metals" else "Construction materials, metals",
                    fontsize=7.2)
        a.set_ylim(0, val[c].max() * 1.32)
        a.text(0.99, 0.96, f"importers: {int(a2.iloc[0])} (2010), {int(a2.iloc[-1])} (2023)", transform=a.transAxes,
               ha="right", va="top", fontsize=5.8, color=C["ink2"])
        year_axis(a, list(val.index), 4)
    fig.supylabel("US$ million", fontsize=7, color=C["ink2"])
    fig.tight_layout(h_pad=0.9, w_pad=0.9)
    chart_data(12, "a", "Imports by product category (panel values)", val[cats].rename(columns=lab).rename_axis("Year"), "US$ million", "Blank = suppressed (fewer than 3 importers).")
    chart_data(12, "b", "Number of importers by product category (panel labels)", n[cats].rename(columns=lab).rename_axis("Year"), "Number of firms", "The chart labels each panel with the 2010 and 2023 counts.")
    save(fig, "f11_import_categories")
    NUM.update(pharma_2010_17=val.loc[2010:2017, "Pharmaceuticals"].mean(), pharma_2021_23=val.loc[2021:2023, "Pharmaceuticals"].mean(),
               fert_2010_18=val.loc[2010:2018, "Fertilisers"].mean() if "Fertilisers" in val else np.nan,
               fert_2020_23=val.loc[2020:2023, "Fertilisers"].mean() if "Fertilisers" in val else np.nan,
               fert_n_2010=IM[IM.h2 == "31"].groupby("y").f.nunique().get(2010), fert_n_2023=IM[IM.h2 == "31"].groupby("y").f.nunique().get(2023),
               cons_2014=val.loc[2014, "Consumer manufactures"], cons_2023=val.loc[2023, "Consumer manufactures"],
               mach_2015=val.loc[2015, "Machinery and equipment"], mach_2018=val.loc[2018, "Machinery and equipment"],
               mach_2023=val.loc[2023, "Machinery and equipment"],
               food_2010=val.loc[2010, "Food and agriculture"], food_2023=val.loc[2023, "Food and agriculture"])


def fig_importer_margins(IM):
    fy = IM.groupby(["f", "y"]).v.sum().reset_index()
    yrs = sorted(fy.y.unique())
    S = {y: set(fy.loc[fy.y == y, "f"]) for y in yrs}
    ent = pd.Series({y: len(S[y] - S[yrs[i - 1]]) / len(S[y]) * 100 for i, y in enumerate(yrs) if y > DYN_START})
    ext = pd.Series({y: len(S[yrs[i - 1]] - S[y]) / len(S[yrs[i - 1]]) * 100 for i, y in enumerate(yrs) if y > DYN_START})
    bins = [0, 1e4, 1e5, 1e6, np.inf]
    labs = ["< $10k", "$10k–100k", "$100k–1m", "≥ $1m"]
    fy["cls"] = pd.cut(fy.v, bins, labels=labs, right=False)
    cnt = fy.groupby(["y", "cls"], observed=False).f.nunique().unstack()
    fig, axs = plt.subplots(1, 2, figsize=(W_FULL, 2.35))
    a = axs[0]
    bottom = np.zeros(len(cnt))
    cols = [C["lightblue"], C["blue"], C["navy"], C["ink"]]
    for lab, col in zip(labs, cols):
        a.bar(cnt.index, cnt[lab], bottom=bottom, color=col, width=0.75, label=lab, edgecolor="white", linewidth=0.4)
        bottom += cnt[lab].values
    a.set_title("(a) Importers by annual import value")
    h, l = a.get_legend_handles_labels()
    a.legend(h[::-1], l[::-1], fontsize=6, loc="upper left", ncol=2)
    a.set_ylim(0, 8200)
    a.yaxis.set_major_formatter(mt.FuncFormatter(fmt_m))
    year_axis(a, yrs, 2)
    a = axs[1]
    a.plot(ent.index, ent.values, color=C["aqua"], marker="o", ms=2.5, label="Entry rate")
    a.plot(ext.index, ext.values, color=C["red"], marker="o", ms=2.5, label="Exit rate")
    a.set_xlim(2009.4, 2023.6)
    a.set_ylim(0, 85)
    a.set_title("(b) Importer turnover, % of importers")
    a.legend(fontsize=6, loc="lower left")
    year_axis(a, yrs, 2)
    fig.tight_layout(w_pad=2)
    chart_data(13, "a", "Importers by annual import value", cnt.rename(columns=str).rename_axis("Year"), "Number of firms")
    chart_data(13, "b", "Importer turnover", pd.DataFrame({"Entry rate": ent, "Exit rate": ext}).rename_axis("Year"), "% of importers", "Computed from 2016, when firm identifiers are consistent.")
    save(fig, "f12_importer_margins")
    f15 = fy[fy.y >= DYN_START]
    ny = f15.groupby("f").y.nunique()
    NUM.update(m_one_year_share=(ny == 1).mean() * 100, m_all_years_n=(ny == 9).sum(),
               m_all_years_vshare=f15[f15.f.isin(ny[ny == 9].index)].v.sum() / f15.v.sum() * 100,
               m_one_month_share=(IM[IM.y >= DYN_START].groupby(["f", "y"]).m.nunique() == 1).mean() * 100)
    NUM.update(m_entry_mean=ent.mean(), m_exit_mean=ext.mean(),
               m_small_2010=cnt.loc[2010, "< $10k"], m_small_2022=cnt.loc[2022, "< $10k"],
               m_big_2014=cnt.loc[2014, "≥ $1m"], m_big_2018=cnt.loc[2018, "≥ $1m"], m_big_2023=cnt.loc[2023, "≥ $1m"])


# --------------------------------------------------- firm-level forex balance sheet (P2)
def fx_panel(E, IM):
    x = E.groupby(["f", "y"]).v.sum().rename("x")
    m = IM.groupby(["f", "y"]).v.sum().rename("m")
    xm = pd.concat([x, m], axis=1).fillna(0).reset_index()
    xm = xm[xm.y >= 2013]
    main = E.groupby(["f", "y", "grp"]).v.sum().reset_index().sort_values("v").drop_duplicates(["f", "y"], keep="last")
    xm = xm.merge(main[["f", "y", "grp"]], on=["f", "y"], how="left")
    xm["type"] = np.where(xm.x == 0, "Pure importer", np.where(xm.x >= xm.m, "Net-earning exporter", "Net-using exporter"))
    return xm


def fig_fx_balance(E, IM):
    xm = fx_panel(E, IM)
    g = xm.groupby(["y", "type"]).agg(x=("x", "sum"), m=("m", "sum"), n=("f", "nunique")).unstack()
    fig, axs = plt.subplots(1, 2, figsize=(W_FULL, 2.7), gridspec_kw=dict(width_ratios=[1.35, 1]))
    a = axs[0]
    yrs = list(g.index)
    xn = g["x"]["Net-earning exporter"] / 1e6
    xu = g["x"]["Net-using exporter"] / 1e6
    mn = g["m"]["Net-earning exporter"] / 1e6
    mu = g["m"]["Net-using exporter"] / 1e6
    mp = g["m"]["Pure importer"] / 1e6
    w = 0.72
    a.bar(yrs, xn, color=C["blue"], width=w, label="Exports: net-earning exporters")
    a.bar(yrs, xu, bottom=xn, color=C["lightblue"], width=w, label="Exports: net-using exporters")
    a.bar(yrs, -mn, color=C["yellow"], width=w, label="Imports: net-earning exporters")
    a.bar(yrs, -mu, bottom=-mn, color=C["orange"], width=w, label="Imports: net-using exporters")
    a.bar(yrs, -mp, bottom=-mn - mu, color=C["gray"], width=w, label="Imports: pure importers")
    a.axhline(0, color=C["ink2"], lw=0.6)
    a.set_title("(a) Forex earned (+) and spent (–) via goods trade, US$ m")
    a.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    a.legend(fontsize=5.8, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    a.set_ylim(-800, 300)
    year_axis(a, yrs, 2)
    # Lorenz curve of net forex supply among net-earning exporters, 2019-2023 pooled firm totals
    a = axs[1]
    lorenz = {}
    for (y0, y1), col in [((2013, 2016), C["gray"]), ((2020, 2023), C["blue"])]:
        s = xm[(xm.y >= y0) & (xm.y <= y1) & (xm.type == "Net-earning exporter")]
        net = (s.x - s.m).groupby(s.f).sum().sort_values(ascending=False)
        cum_f = np.r_[0, net.cumsum() / net.sum() * 100]
        pct_f = np.r_[0, np.arange(1, len(net) + 1) / len(net) * 100]
        # disclosure: plot only at percentile steps that each contain at least MIN_FIRMS firms
        step = max(1.0, np.ceil(MIN_FIRMS / len(net) * 100))
        pct = np.r_[np.arange(0, 100, step), 100.0]
        cum = np.interp(pct, pct_f, cum_f)
        NUM[f"lorenz_n_{y0}_{y1}"] = len(net)
        NUM[f"lorenz_step_{y0}_{y1}"] = step
        a.plot(pct, cum, color=col, label=f"{y0}–{y1}")
        lorenz[f"{y0}-{y1}"] = pd.Series(cum, index=pct)
        if y0 == 2020:
            NUM["netfx_top1pct_2020_23"] = np.interp(1, pct, cum)
            NUM["netfx_top5pct_2020_23"] = np.interp(5, pct, cum)
            NUM["netfx_top10pct_2020_23"] = np.interp(10, pct, cum)
    a.plot([0, 100], [0, 100], color=C["axis"], lw=0.6)
    a.set_xlim(0, 100)
    a.set_ylim(0, 102)
    a.set_title("(b) Concentration of net forex supply")
    a.set_xlabel("% of net-earning exporters (largest first)")
    a.set_ylabel("Cumulative % of net supply")
    a.legend(fontsize=6, loc="lower right")
    a.grid(axis="x", visible=True)
    fig.tight_layout(w_pad=1.6)
    chart_data(14, "a", "Forex earned (+) and spent (-) through goods trade, by firm type", pd.DataFrame({"Exports: net-earning exporters": xn, "Exports: net-using exporters": xu, "Imports: net-earning exporters": -mn, "Imports: net-using exporters": -mu, "Imports: pure importers": -mp}).rename_axis("Year"), "US$ million", "Imports are shown as negative values (forex spent). Fuel is included.")
    chart_data(14, "b", "Concentration of net forex supply (Lorenz curve)", pd.DataFrame(lorenz).rename_axis("% of net-earning exporters (largest first)"), "Cumulative % of net forex supply", "Plotted at 1-percentile steps, each containing at least 3 firms.")
    save(fig, "f13_fx_balance")
    tot_m = g["m"].sum(1)
    NUM.update(exp_m_share_mean=((mn + mu) / tot_m * 1e6).mean() * 100,
               exp_m_share_2019=((mn + mu) / tot_m * 1e6)[2019] * 100, exp_m_share_2023=((mn + mu) / tot_m * 1e6)[2023] * 100,
               netuser_x_share_mean=(xu / (xn + xu)).mean() * 100,
               net_exporters_net_2023=(xn + xu - mn - mu)[2023],
               net_exporters_net_2014=(xn + xu - mn - mu)[2014],
               cover_customs_mean=((xn + xu) / (tot_m / 1e6)).mean() * 100,
               cover_customs_2023=((xn + xu) / (tot_m / 1e6))[2023] * 100,
               n_netearn_share=(g["n"]["Net-earning exporter"] / (g["n"]["Net-earning exporter"] + g["n"]["Net-using exporter"])).mean() * 100)
    # sector table
    s = xm[(xm.x > 0) & (xm.y >= 2019)]
    t = s.groupby("grp").agg(n=("f", "nunique"), x=("x", "sum"), m=("m", "sum"))
    t = t[t.n >= MIN_FIRMS].reindex([gg for gg in EXPORT_GROUPS if gg in t.index])
    t["net"] = (t.x - t.m) / 5e6
    t["ratio"] = t.m / t.x * 100
    t["x"] = t.x / 5e6
    t["m"] = t.m / 5e6
    if PUBLIC:
        for col in ["x", "m"]:
            dm = (top_share(s.rename(columns={col: "val"}), ["grp"], "val") > MAX_DOM).reindex(t.index).fillna(False)
            t.loc[dm, col] = np.nan
            t.loc[dm, ["net", "ratio"]] = np.nan
            NUM[f"t5_dominated_{col}"] = [lab(g) for g in t.index[dm]]
        NUM["t5_coffee_ratio"] = t.loc["Coffee", "ratio"]
        t.index = [lab(g) for g in t.index]
    t.index.name = "Main export group"
    table_data(5, "Net forex position of exporters by main export group, 2019-2023", t[["n", "x", "m", "net", "ratio"]].rename(columns={"n": "Firms (2019-23)", "x": "Exports (US$ m per year)", "m": "Own imports (US$ m per year)", "net": "Net (US$ m per year)", "ratio": "Imports/exports (%)"}), "Firms are assigned to the product group with the largest share of their exports in each year. Values are annual averages over 2019-2023.")
    latex_table(t[["n", "x", "m", "net", "ratio"]], "t05_fx_sector",
                fmt={"n": "{:,.0f}", "x": "{:,.1f}", "m": "{:,.1f}", "net": "{:,.1f}", "ratio": "{:,.0f}"},
                header_rows=[r"Main export group & Firms & Exports & Own imports & Net & Imports/exports (\%) \\",
                             r" & (2019--23) & \multicolumn{3}{c}{US\$ m per year, 2019--23} & \\"],
                col_format="lrrrrr")
    return xm


# -------------------------------------------------------------- corridors (P5)
CITIES = {"Bujumbura": (29.36, -3.38), "Gitega": (29.92, -3.43), "Dar es Salaam": (39.28, -6.79),
          "Kigoma": (29.63, -4.88), "Tabora": (32.80, -5.02), "Isaka": (32.43, -3.90),
          "Dodoma": (35.74, -6.17), "Mombasa": (39.67, -4.04), "Nairobi": (36.82, -1.29),
          "Kampala": (32.58, 0.35), "Kigali": (30.06, -1.95), "Uvira": (29.14, -3.40),
          "Bukavu": (28.86, -2.51), "Mpulungu": (31.11, -8.76), "Uvinza": (30.39, -5.10),
          "Musongati": (30.10, -3.70), "Kobero": (30.47, -2.93), "Goma": (29.23, -1.68),
          "Lubumbashi": (27.48, -11.66), "Kalemie": (29.19, -5.93), "Rusumo": (30.78, -2.38)}


def fig_corridor_map(IM):
    import geopandas as gpd
    world = gpd.read_file(EXT / "ne_countries.geojson")
    lakes = gpd.read_file(EXT / "ne_lakes.geojson")
    fig = plt.figure(figsize=(W_FULL, 4.1))
    a = fig.add_axes([0.0, 0.14, 0.64, 0.86])
    b = fig.add_axes([0.73, 0.30, 0.26, 0.62])
    xmin, xmax, ymin, ymax = 26.6, 40.4, -9.6, 1.4
    world.plot(ax=a, color="#f4f3ef", edgecolor="#c9c7bf", linewidth=0.5)
    world[world.ADM0_A3 == "BDI"].plot(ax=a, color="#dbe8f8", edgecolor=C["navy"], linewidth=0.9)
    lakes.plot(ax=a, color="#e3eef7", edgecolor="#b9cfe3", linewidth=0.3)
    for txt, (x, y) in {"DR CONGO": (27.6, -6.6), "TANZANIA": (35.3, -8.6), "KENYA": (38.4, 0.6),
                        "UGANDA": (32.9, 0.9), "RWANDA": (30.2, -1.25), "ZAMBIA": (29.9, -9.4)}.items():
        a.text(x, y, txt, fontsize=5.8, color=C["muted"], ha="center")
    a.text(30.0, -4.15, "BURUNDI", fontsize=6, color=C["navy"], ha="center", fontweight="bold", zorder=9)

    def route(pts, col, lw, ls="-", z=5):
        xs, ys = zip(*[CITIES[p] for p in pts])
        a.plot(xs, ys, color=col, lw=lw, ls=ls, zorder=z, solid_capstyle="round", dash_capstyle="round")

    route(["Dar es Salaam", "Dodoma", "Tabora", "Kigoma"], C["orange"], 2.6)
    route(["Tabora", "Isaka", "Rusumo", "Kobero", "Gitega", "Bujumbura"], C["orange"], 1.2, (0, (3, 1.5)))
    route(["Kigoma", "Bujumbura"], C["orange"], 1.4, (0, (1, 1.2)))
    route(["Mombasa", "Nairobi", "Kampala", "Kigali", "Bujumbura"], C["blue"], 2.6)
    route(["Uvinza", "Musongati"], C["green"], 1.9, (0, (4, 1.4)))
    route(["Musongati", "Gitega"], C["green"], 1.2, (0, (1, 1.2)))
    route(["Bujumbura", "Uvira", "Bukavu", "Goma"], C["violet"], 1.2)
    route(["Bujumbura", "Kalemie", "Mpulungu"], C["violet"], 1.1, (0, (1, 1.2)))
    offs = {"Bujumbura": (-0.25, -0.55, "right"), "Uvira": (-0.22, 0.0, "right"), "Bukavu": (-0.22, 0, "right"),
            "Goma": (-0.22, 0, "right"), "Kigoma": (-0.22, -0.12, "right"), "Kigali": (0.22, 0.12, "left"),
            "Gitega": (0.2, 0.2, "left"), "Kalemie": (-0.22, 0, "right"), "Mpulungu": (0.22, 0, "left"),
            "Uvinza": (0.2, -0.28, "left"), "Musongati": (0.25, 0.0, "left"), "Isaka": (0.22, 0.1, "left"), "Tabora": (0.1, -0.38, "left"),
            "Dodoma": (0.1, -0.38, "left"), "Nairobi": (0.1, -0.38, "left"), "Kampala": (-0.1, 0.35, "right"),
            "Dar es Salaam": (-0.1, -0.5, "right"), "Mombasa": (-0.15, -0.45, "right")}
    for c in offs:
        x, y = CITIES[c]
        big = c in ("Dar es Salaam", "Mombasa", "Bujumbura")
        a.plot(x, y, "o", ms=4.8 if big else 2.8, color=C["ink"] if big else C["ink2"], zorder=7,
               markeredgecolor="white", markeredgewidth=0.6)
        dx, dy, ha = offs[c]
        a.text(x + dx, y + dy, c, fontsize=6.2 if big else 5.5, ha=ha, va="center", color=C["ink"], zorder=8,
               fontweight="bold" if big else "normal")
    a.set_xlim(xmin, xmax)
    a.set_ylim(ymin, ymax)
    a.set_aspect("equal")
    a.axis("off")
    handles = [Line2D([], [], color=C["orange"], lw=2.6, label="Central Corridor: Dar es Salaam–Tabora–Kigoma"),
               Line2D([], [], color=C["orange"], lw=1.2, ls=(0, (3, 1.5)), label="Central Corridor road via Rusumo/Kobero"),
               Line2D([], [], color=C["orange"], lw=1.4, ls=(0, (1, 1.2)), label="Lake Tanganyika: Kigoma–Bujumbura"),
               Line2D([], [], color=C["blue"], lw=2.6, label="Northern Corridor: Mombasa–Kampala–Kigali"),
               Line2D([], [], color=C["green"], lw=1.9, ls=(0, (4, 1.4)), label="SGR Uvinza–Musongati (works launched 2025)"),
               Line2D([], [], color=C["green"], lw=1.2, ls=(0, (1, 1.2)), label="SGR extension to Gitega (study stage)"),
               Line2D([], [], color=C["violet"], lw=1.2, label="Links to eastern DRC and lake ports")]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.01, 0.0), ncol=2, fontsize=5.8)
    orig = IM[IM.o.isin(["TZA", "KEN", "UGA", "RWA", "ZMB", "COD"])]
    v = orig.groupby(["o", "y"]).v.sum().unstack() / 1e6
    names = {"TZA": "Tanzania", "KEN": "Kenya", "UGA": "Uganda", "RWA": "Rwanda", "ZMB": "Zambia", "COD": "DR Congo"}
    order = v[2023].sort_values().index
    yy = np.arange(len(order))
    b.barh(yy + 0.19, v.loc[order, 2010], height=0.36, color=C["gray"], label="2010")
    b.barh(yy - 0.19, v.loc[order, 2023], height=0.36, color=C["navy"], label="2023")
    for yv, o in zip(yy, order):
        b.text(v.loc[o, 2023] + 2, yv - 0.19, f"{v.loc[o, 2023]:.0f}", va="center", fontsize=5.8, color=C["ink2"])
        b.text(v.loc[o, 2010] + 2, yv + 0.19, f"{v.loc[o, 2010]:.0f}", va="center", fontsize=5.8, color=C["muted"])
    b.set_yticks(yy)
    b.set_yticklabels([names[o] for o in order], fontsize=6.5)
    b.grid(axis="y", visible=False)
    b.grid(axis="x", visible=True)
    b.set_xlim(0, 125)
    b.set_title("Recorded imports by\nregional origin, US$ m", fontsize=7.5)
    b.legend(fontsize=6, loc="lower right")
    chart_data(15, "a", "Map: places shown (schematic)", pd.DataFrame([(k, lon, lat) for k, (lon, lat) in CITIES.items()], columns=["Place", "Longitude", "Latitude"]).set_index("Place"), "Decimal degrees", "Routes on the map are schematic. The SGR Uvinza-Musongati (works launched August 2025) and its planned extension to Gitega (study stage) follow AfDB (2023) and CCTTFA (2025).")
    chart_data(15, "b", "Recorded imports by regional origin", v.loc[list(order)[::-1], [2010, 2023]].rename(index=names).rename_axis("Origin"), "US$ million")
    save(fig, "f14_corridor_map")
    NUM.update(tza_m_2010=v.loc["TZA", 2010], tza_m_2023=v.loc["TZA", 2023], ken_m_2010=v.loc["KEN", 2010],
               ken_m_2023=v.loc["KEN", 2023], uga_m_2023=v.loc["UGA", 2023], zmb_m_2023=v.loc["ZMB", 2023])


def fig_regional_sourcing(IM):
    reg = ["TZA", "KEN", "UGA", "ZMB", "RWA"]
    names = {"TZA": "Tanzania", "KEN": "Kenya", "UGA": "Uganda", "ZMB": "Zambia", "RWA": "Rwanda"}
    cols = {"TZA": C["orange"], "KEN": C["blue"], "UGA": C["aqua"], "ZMB": C["green"], "RWA": C["violet"]}
    nf = IM[IM.cat != "Fuel"]
    vs = nf.pivot_table(index="y", columns="o", values="v", aggfunc="sum")
    ws = nf.pivot_table(index="y", columns="o", values="q", aggfunc="sum")
    vsh = vs[reg].div(vs.sum(1), axis=0) * 100
    wsh = ws[reg].div(ws.sum(1), axis=0) * 100
    if PUBLIC:
        sub = nf[nf.o.isin(reg)]
        for df_, col in [(vsh, "v"), (wsh, "q")]:
            dm = (top_share(sub, ["y", "o"], col) > MAX_DOM).unstack().reindex_like(df_).fillna(False).astype(bool)
            df_[dm] = np.nan
            if dm.values.sum():
                SUPPRESSED.append(("regional sourcing " + col, int(dm.values.sum()), "dominance",
                                   [(r, c_) for r in dm.index for c_ in dm.columns if dm.loc[r, c_]]))
    nfirms = nf[nf.o.isin(reg)].groupby(["y", "o"]).f.nunique().unstack()
    fig, axs = plt.subplots(1, 3, figsize=(W_FULL, 2.45))
    yrs = list(vsh.index)
    for a, df, t in [(axs[0], vsh, "(a) Share of import value, %"),
                     (axs[1], wsh, "(b) Share of import tonnage, %"),
                     (axs[2], nfirms, "(c) Firms importing from origin")]:
        for o in reg:
            a.plot(df.index, df[o], color=cols[o], marker="o", ms=2, lw=1.3, label=names[o])
        a.set_title(t)
        a.set_ylim(0, None)
        year_axis(a, yrs, 3)
    axs[0].legend(fontsize=6, loc="upper left")
    fig.tight_layout(w_pad=1.2)
    for _p, _df, _t, _u in [("a", vsh, "Share of non-fuel import value by regional origin", "% of non-fuel imports"),
                            ("b", wsh, "Share of non-fuel import tonnage by regional origin", "% of non-fuel import weight"),
                            ("c", nfirms, "Firms importing from each regional origin", "Number of firms")]:
        chart_data(16, _p, _t, _df[reg].rename(columns=names).rename_axis("Year"), _u)
    save(fig, "f15_regional_sourcing")
    # composition of imports from Tanzania
    tz = IM[IM.o == "TZA"]
    early = tz[tz.y.between(2010, 2012)].groupby("cat").v.sum() / 3e6
    late = tz[tz.y.between(2021, 2023)].groupby("cat").v.sum() / 3e6
    n_e = tz[tz.y.between(2010, 2012)].groupby("cat").f.nunique()
    n_l = tz[tz.y.between(2021, 2023)].groupby("cat").f.nunique()
    t = pd.DataFrame({"early": early, "late": late, "n_e": n_e, "n_l": n_l}).reindex(IMPORT_CATS).fillna(0)
    t.loc[t.n_e < MIN_FIRMS, "early"] = np.nan
    t.loc[t.n_l < MIN_FIRMS, "late"] = np.nan
    if PUBLIC:   # dominance + secondary suppression on the pooled period cells
        tzp = tz[tz.y.between(2010, 2012) | tz.y.between(2021, 2023)].assign(
            per=lambda d_: np.where(d_.y <= 2012, "early", "late"))
        pv, _ = sdc_pivot(tzp, "per", "cat", "Tanzania composition", scale=3e6)
        t = t.reindex(columns=list(t.columns))
        for per in ["early", "late"]:
            t[per] = pv.loc[per].reindex(t.index)
        if COMBINED in pv:
            t.loc[COMBINED, ["early", "late"]] = [pv.loc["early", COMBINED] if "early" in pv.index else np.nan,
                                                   pv.loc["late", COMBINED]]
    t = t.sort_values("late", ascending=False)
    fig, a = plt.subplots(figsize=(W_FULL, 2.2))
    yy = np.arange(len(t))[::-1]
    a.barh(yy + 0.19, t.early, height=0.36, color=C["gray"], label="2010–12 average")
    a.barh(yy - 0.19, t.late, height=0.36, color=C["orange"], label="2021–23 average")
    for yv, e, l in zip(yy, t.early, t.late):
        if pd.notna(l):
            a.text(l + 0.6, yv - 0.19, f"{l:.1f}", fontsize=6, va="center", color=C["ink2"])
        if pd.notna(e):
            a.text(e + 0.6, yv + 0.19, f"{e:.1f}", fontsize=6, va="center", color=C["ink2"])
    a.set_yticks(yy)
    a.set_yticklabels([lab(i) for i in t.index], fontsize=6.8)
    a.grid(axis="y", visible=False)
    a.grid(axis="x", visible=True)
    a.set_title("Imports from Tanzania by product category, US$ million per year")
    a.legend(fontsize=6, loc="lower right")
    fig.tight_layout()
    chart_data(17, "", "Imports from Tanzania by product category", t[["early", "late"]].rename(index=lab, columns={"early": "2010-12 average", "late": "2021-23 average"}).rename_axis("Product category"), "US$ million per year", "Blank = fewer than 3 importers" + (" or one importer above 85% of the cell; the combined row groups cells that cannot be shown separately." if PUBLIC else "."))
    save(fig, "f16_tanzania_composition")
    NUM.update(tza_vsh_2010=vsh.loc[2010, "TZA"], tza_vsh_2023=vsh.loc[2023, "TZA"],
               tza_wsh_2010=wsh.loc[2010, "TZA"], tza_wsh_2023=wsh.loc[2023, "TZA"],
               ken_vsh_2010=vsh.loc[2010, "KEN"], ken_vsh_2023=vsh.loc[2023, "KEN"],
               tza_nf_2016=nfirms.loc[2016, "TZA"], tza_nf_2023=nfirms.loc[2023, "TZA"],
               tza_late_total=late.sum(), tza_early_total=early.sum(),
               tza_top_cat=t.index[0], tza_top_cat_val=t.late.iloc[0],
               tza_constr_late=t.loc["Construction materials and metals", "late"],
               tza_chem_late=t.loc["Other chemicals and plastics", "late"])


# ------------------------------------------------------------------ DRC (P6)
def reexport_flags(E, IM):
    imp = IM.groupby(["f", "y", "hs"]).v.sum().reset_index()[["f", "y", "hs"]]
    s0 = set(map(tuple, imp.values))
    s1 = set((f, y + 1, h) for f, y, h in imp.values)
    k = list(zip(E.f, E.y, E.hs))
    return np.array([(t in s0) or (t in s1) for t in k])


def fig_drc(E, IM):
    E = E.assign(reexp=reexport_flags(E, IM))
    d = E[E.d == "COD"]
    val, n = sdc_pivot(d, "y", "grp", "DRC by group")
    val = val.reindex(columns=EXPORT_GROUPS + ([COMBINED] if COMBINED in val else []))
    firms = d.groupby("y").f.nunique()
    # manufactured exports (agro-industry + manufactures) share going to DRC
    man = E[E.grp.isin(["Agro-industry", "Manufactures"])]
    drc_share_man = man[man.d == "COD"].groupby("y").v.sum() / man.groupby("y").v.sum() * 100
    # re-export share by destination group
    E["dgrp"] = E.d.map(lambda x: "DR Congo" if x == "COD" else ("EAC partners" if x in EAC5 else "Rest of world"))
    rx = E.groupby("dgrp").apply(lambda g: g.v[g.reexp].sum() / g.v.sum() * 100, include_groups=False)
    rxn = E[E.reexp].groupby("dgrp").f.nunique()
    rx_grp = E.groupby("grp").apply(lambda g: g.v[g.reexp].sum() / g.v.sum() * 100, include_groups=False)
    fig, axs = plt.subplots(1, 3, figsize=(W_FULL, 2.45), gridspec_kw=dict(width_ratios=[1.3, 1, 0.9]))
    a = axs[0]
    stack_bars(a, val, EXPORT_GROUPS, EXPORT_COLORS, width=0.75, lw=0.4)
    a.set_title("(a) Exports to DR Congo, US$ m")
    h, l = a.get_legend_handles_labels()
    a.legend(h[::-1], l[::-1], fontsize=5.6, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    a.set_ylim(0, 36)
    year_axis(a, list(val.index), 2)
    a = axs[1]
    a.plot(drc_share_man.index, drc_share_man.values, color=C["orange"], marker="o", ms=2.5)
    a.set_ylim(0, 100)
    a.set_title("(b) DRC share of processed and\nmanufactured exports, %")
    year_axis(a, list(drc_share_man.index), 3)
    a = axs[2]
    order = ["DR Congo", "EAC partners", "Rest of world"]
    a.bar(range(3), rx.reindex(order), color=[C["orange"], C["aqua"], C["gray"]], width=0.6)
    for i, v in enumerate(rx.reindex(order)):
        a.text(i, v + 1.2, f"{v:.0f}%", ha="center", fontsize=6.5, color=C["ink2"])
    a.set_xticks(range(3))
    a.set_xticklabels(["DRC", "EAC", "Rest of\nworld"], fontsize=6.5)
    a.set_ylim(0, max(rx) * 1.3)
    a.set_title("(c) Potential re-exports,\n% of export value")
    a.grid(axis="x", visible=False)
    fig.tight_layout(w_pad=1.2)
    chart_data(18, "a", "Exports to DR Congo by product group", val.dropna(axis=1, how="all").rename(columns=lab).rename_axis("Year"), "US$ million", "Blank = suppressed (fewer than 3 firms).")
    chart_data(18, "b", "DR Congo's share of processed and manufactured exports", drc_share_man.rename("DR Congo share").rename_axis("Year"), "%", "Processed and manufactured exports = agro-industry plus manufactures (Appendix A).")
    chart_data(18, "c", "Potential re-exports by destination", rx.reindex(order).rename("Potential re-exports").rename_axis("Destination"), "% of export value", "Exports of an HS6 product that the same firm imported in the same or previous year.")
    save(fig, "f17_drc")
    NUM.update(drc_x_2013=d[d.y == 2013].v.sum() / 1e6, drc_x_2023=d[d.y == 2023].v.sum() / 1e6,
               drc_firms_mean=firms.mean(), drc_firms_min=firms.min(), drc_firms_max=firms.max(),
               drc_man_share_mean=drc_share_man.mean(), drc_man_share_2023=drc_share_man[2023],
               rx_drc=rx["DR Congo"], rx_eac=rx["EAC partners"], rx_row=rx["Rest of world"],
               rx_all=E.v[E.reexp].sum() / E.v.sum() * 100,
               rx_mach=rx_grp.get("Machinery, vehicles and fuel"), rx_manuf=rx_grp.get("Manufactures"),
               drc_x_2021=d[d.y == 2021].v.sum() / 1e6, drc_x_2022=d[d.y == 2022].v.sum() / 1e6,
               drc_agro_share=(val["Agro-industry"].sum() / val.sum().sum()) * 100)
    # imports from DRC
    NUM["drc_m_mean"] = IM[IM.o == "COD"].groupby("y").v.sum().mean() / 1e6


# ---------------------------------------------------- unit values and mirror (P8)
def pink():
    x = pd.read_excel(EXT / "pink_monthly.xlsx", "Monthly Prices", header=4)
    x = x.rename(columns={x.columns[0]: "t"}).iloc[2:]
    x["date"] = pd.to_datetime(x.t.str.replace("M", "-") + "-01", errors="coerce")
    x = x.set_index("date")
    cols = {"Coffee, Arabica": "arabica", "Coffee, Robusta": "robusta", "Tea, Mombasa": "tea_mombasa",
            "Gold": "gold"}
    p = x[list(cols)].rename(columns=cols).apply(pd.to_numeric, errors="coerce")
    return p


def fig_unit_values(E, EM):
    p = pink()
    pa = p.groupby(p.index.year).mean()
    out = {}
    for name, sel, bench, conv in [("Coffee", E.h4 == "0901", "arabica", 1.0),
                                   ("Tea", E.h4 == "0902", "tea_mombasa", 1.0),
                                   ("Gold", E.h4 == "7108", "gold", 32.1507)]:
        g = E[sel].groupby("y").agg(v=("v", "sum"), q=("q", "sum"), n=("f", "nunique"))
        uv = g.v / g.q
        uv[g.n < MIN_FIRMS] = np.nan
        if PUBLIC:
            dm = (top_share(E[sel], ["y"]) > MAX_DOM).reindex(uv.index).fillna(False)
            uv[dm] = np.nan
            if dm.any():
                SUPPRESSED.append(("unit value " + name, int(dm.sum()), "years suppressed (dominance)"))
        ratio = uv / (pa.loc[uv.index, bench] * conv) * 100
        out[name] = (uv, pa.loc[uv.index, bench] * conv, ratio, g.n)
        if (g.n < MIN_FIRMS).any():
            SUPPRESSED.append(("unit value " + name, int((g.n < MIN_FIRMS).sum()), "years suppressed"))
    if PUBLIC:
        out = {k: v for k, v in out.items() if v[0].notna().sum() >= 3}
        NUM["uv_panels"] = list(out)
    fig, axs = plt.subplots(1, len(out), figsize=(W_FULL if len(out) == 3 else W_FULL * 0.72, 2.35))
    axs = np.atleast_1d(axs)
    labs = {k: (f"({'abc'[i]}) " + {"Coffee": "Coffee, US$/kg", "Tea": "Tea, US$/kg", "Gold": "Gold, US$ '000/kg"}[k],
                {"Coffee": "ICE arabica (Pink Sheet)", "Tea": "Mombasa auction (Pink Sheet)", "Gold": "LBMA gold (Pink Sheet)"}[k])
            for i, k in enumerate(out)}
    for a, (k, (uv, b, r, n)) in zip(axs, out.items()):
        sc = 1e3 if k == "Gold" else 1
        a.plot(b.index, b / sc, color=C["gray"], marker="o", ms=2.3, label=labs[k][1])
        a.plot(uv.index, uv / sc, color=C["blue"] if k != "Gold" else C["yellow"], marker="o", ms=2.5,
               label="Burundi export unit value")
        a.set_title(labs[k][0])
        a.set_ylim(0, None)
        a.legend(fontsize=5.8, loc="lower left")
        year_axis(a, list(uv.index), 3)
    fig.tight_layout(w_pad=1.3)
    for _p, _k in zip("abc", list(out)):
        _uv, _b, _r, _n = out[_k]
        _sc = 1e3 if _k == "Gold" else 1
        chart_data(20, _p, f"{_k}: export unit value vs world price", pd.DataFrame({"Burundi export unit value": _uv / _sc, labs[_k][1]: _b / _sc, "Ratio to world price (%)": _r}).rename_axis("Year"), "US$ '000 per kg" if _k == "Gold" else "US$ per kg", "Years with fewer than 3 exporters are suppressed (blank). World prices: World Bank Pink Sheet, annual averages of monthly prices.")
    save(fig, "f19_unit_values")
    _g = lambda k, i, f: getattr(out[k][i], f)() if k in out else np.nan
    NUM.update(coffee_ratio_mean=_g("Coffee", 2, "mean"), coffee_ratio_min=_g("Coffee", 2, "min"),
               coffee_ratio_max=_g("Coffee", 2, "max"), tea_ratio_mean=_g("Tea", 2, "mean"),
               gold_ratio_mean=_g("Gold", 2, "mean"), gold_ratio_min=_g("Gold", 2, "min"),
               gold_ratio_max=_g("Gold", 2, "max"))
    # coffee exporters' dispersion of unit values within year (firm-level, p10/p90)
    cf = E[E.h4 == "0901"].groupby(["y", "f"]).agg(v=("v", "sum"), q=("q", "sum"))
    cf["uv"] = cf.v / cf.q
    disp = cf.groupby("y").uv.apply(lambda s: s.quantile(0.9) / s.quantile(0.1))
    NUM["coffee_uv_p90p10_mean"] = disp.mean()


def fig_mirror(E, IM):
    d = json.load(open(EXT / "comtrade_mirror.json"))
    cm = pd.DataFrame([dict(r=M49.get(x["reporterCode"], str(x["reporterCode"])), flow=x["flowCode"],
                            cmd=x["cmdCode"], y=x["refYear"], v=x["primaryValue"]) for x in d])
    # partner-reported imports from Burundi (flow M) vs Burundi exports to that partner
    mirror_m = cm[(cm.flow == "M") & (cm.cmd == "TOTAL")].groupby(["r", "y"]).v.sum()
    mirror_x = cm[(cm.flow == "X") & (cm.cmd == "TOTAL")].groupby(["r", "y"]).v.sum()
    bx = E.groupby(["d", "y"]).v.sum()
    bm = IM.groupby(["o", "y"]).v.sum()
    parts_x = ["ARE", "CHE", "BEL", "DEU", "KEN", "UGA", "TZA", "RWA", "PAK", "GBR", "USA", "CHN", "SGP"]
    parts_m = ["CHN", "IND", "TZA", "KEN", "UGA", "BEL", "ARE", "ZMB", "JPN", "FRA", "SAU", "DEU", "EGY", "RWA", "USA", "ZAF"]
    rows = []
    for p in parts_x:
        for y in range(2013, 2024):
            if (p, y) in mirror_m.index and (p, y) in bx.index:
                rows.append(dict(p=p, y=y, own=bx[(p, y)], mir=mirror_m[(p, y)]))
    X = pd.DataFrame(rows)
    rows = []
    for p in parts_m:
        for y in range(2010, 2024):
            if (p, y) in mirror_x.index and (p, y) in bm.index:
                rows.append(dict(p=p, y=y, own=bm[(p, y)], mir=mirror_x[(p, y)]))
    M = pd.DataFrame(rows)
    # disclosure: need >=3 firms in Burundi-side cells
    nx = E.groupby(["d", "y"]).f.nunique()
    X = X[[nx.get((p, y), 0) >= MIN_FIRMS for p, y in zip(X.p, X.y)]]
    if PUBLIC:
        cells = set(zip(X.p, X.y))
        Ex = E[[(d_, y_) in cells for d_, y_ in zip(E.d, E.y)]]
        dmp = top_share(Ex, ["d"]) > MAX_DOM
        NUM["mirror_suppressed"] = sorted(dmp[dmp].index)
        X = X[~X.p.isin(NUM["mirror_suppressed"])]
    xs = X.groupby("p")[["own", "mir"]].sum()
    xs["ratio"] = xs.mir / xs.own * 100
    ms = M.groupby("p")[["own", "mir"]].sum()
    ms["ratio"] = ms.own / ms.mir * 100          # Burundi CIF imports / partner FOB exports
    xs = xs[xs.own > 5e6].sort_values("own", ascending=True)
    ms = ms[(ms.own > 20e6) & (ms.index != "SAU")].sort_values("own", ascending=True)
    names = {"ARE": "UAE", "CHE": "Switzerland", "BEL": "Belgium", "DEU": "Germany", "KEN": "Kenya",
             "UGA": "Uganda", "TZA": "Tanzania", "RWA": "Rwanda", "PAK": "Pakistan", "GBR": "UK", "USA": "USA",
             "CHN": "China", "SGP": "Singapore", "IND": "India", "ZMB": "Zambia", "JPN": "Japan", "FRA": "France",
             "SAU": "Saudi Arabia", "EGY": "Egypt", "ZAF": "South Africa"}
    fig, axs = plt.subplots(1, 2, figsize=(W_FULL, 3.0))
    for a, df, t, col in [(axs[0], xs, "(a) Partner-reported imports from Burundi\nas % of Burundi-reported exports", C["blue"]),
                          (axs[1], ms, "(b) Burundi-reported imports as % of\npartner-reported exports to Burundi", C["orange"])]:
        yy = np.arange(len(df))
        a.barh(yy, df.ratio.clip(upper=400), color=col, height=0.62)
        for yv, v, o in zip(yy, df.ratio, df.own):
            a.text(min(v, 400) + 4, yv, f"{v:.0f}%", va="center", fontsize=5.8, color=C["ink2"])
        a.axvline(100, color=C["ink2"], lw=0.7)
        a.set_yticks(yy)
        a.set_yticklabels([f"{names.get(i, i)}" for i in df.index], fontsize=6.5)
        a.set_xlim(0, 440 if df is xs else 260)
        a.grid(axis="y", visible=False)
        a.grid(axis="x", visible=True)
        a.set_title(t)
    fig.tight_layout(w_pad=2)
    for _p, _df, _t, _nt in [("a", xs, "Partner-reported imports from Burundi vs Burundi-reported exports", "Ratio = partner-reported imports / Burundi-reported exports. Pooled over 2013-2023 years in which both sides report, with at least 3 Burundian exporters."),
                             ("b", ms, "Burundi-reported imports vs partner-reported exports to Burundi", "Ratio = Burundi-reported imports (c.i.f.) / partner-reported exports (f.o.b.). Pooled over 2010-2023 years in which both sides report.")]:
        _o = _df.iloc[::-1].rename(index=names)
        chart_data(21, _p, _t, pd.DataFrame({"Burundi-reported": _o.own / 1e6, "Partner-reported": _o.mir / 1e6, "Ratio (%)": _o.ratio}).rename_axis("Partner"), "US$ million (pooled) / %", _nt + " Source: UN Comtrade.")
    save(fig, "f20_mirror")
    NUM.update(mirror_are=xs.ratio.get("ARE"), mirror_che=xs.ratio.get("CHE"), mirror_bel=xs.ratio.get("BEL"),
               mirror_ken=xs.ratio.get("KEN"), mirror_pak=xs.ratio.get("PAK"),
               mirror_m_tza=ms.ratio.get("TZA"), mirror_m_chn=ms.ratio.get("CHN"), mirror_m_ind=ms.ratio.get("IND"),
               mirror_m_ken=ms.ratio.get("KEN"), mirror_m_uga=ms.ratio.get("UGA"), mirror_m_are=ms.ratio.get("ARE"),
               mirror_m_zmb=ms.ratio.get("ZMB"), mirror_m_sau=ms.ratio.get("SAU"))
    # UAE-reported gold imports from Burundi (public) vs Burundi exports to UAE (all products)
    ug = cm[(cm.r == "ARE") & (cm.cmd == "7108") & (cm.flow == "M")].groupby("y").v.sum() / 1e6
    NUM["uae_gold_mirror"] = {int(k): round(v, 1) for k, v in ug.items()}
    NUM["bdi_x_to_are"] = {int(k): round(v / 1e6, 1) for k, v in E[E.d == "ARE"].groupby("y").v.sum().items()}
    return xs, ms


# -------------------------------------------------------------- AfCFTA (P9)
def fig_afcfta(E, IM, xm):
    E = E.assign(bloc=E.d.map(bloc))
    IM = IM.assign(bloc=IM.o.map(bloc))
    order = ["DR Congo", "EAC partners", "Other COMESA/SADC", "Other AfCFTA", "Rest of world"]
    xv, xn = sdc_pivot(E, "y", "bloc", "exports by bloc")
    xn = xn.reindex(columns=order)
    mv, _ = sdc_pivot(IM, "y", "bloc", "imports by bloc")
    extra = lambda v_: [COMBINED] if COMBINED in v_ else []
    xsh = xv.reindex(columns=order + extra(xv)).fillna(0)
    xsh = xsh.div(xsh.sum(1), axis=0) * 100
    msh = mv.reindex(columns=order + extra(mv)).fillna(0)
    msh = msh.div(msh.sum(1), axis=0) * 100
    # African destinations served
    afr_dest = E[E.d.isin(AFRICA)].groupby("y").d.nunique()
    fig, axs = plt.subplots(1, 3, figsize=(W_FULL, 2.6), gridspec_kw=dict(width_ratios=[1, 1, 0.95]))
    for a, df, t in [(axs[0], xsh, "(a) Exports by market tier, %"), (axs[1], msh, "(b) Imports by origin tier, %")]:
        if PUBLIC:
            stack_bars(a, df, order, BLOC_COLORS, width=0.75, lw=0.4)
        else:
            bottom = np.zeros(len(df))
            for c in order:
                a.bar(df.index, df[c], bottom=bottom, color=BLOC_COLORS[c], width=0.75, label=c,
                      edgecolor="white", linewidth=0.4)
                bottom += df[c].values
        a.set_ylim(0, 100)
        a.set_title(t)
        year_axis(a, list(df.index), 3 if len(df) > 11 else 2)
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h[::-1], l[::-1], loc="lower center", ncol=5, fontsize=6, bbox_to_anchor=(0.36, -0.04))
    a = axs[2]
    a.plot(xn.index, xn["Other COMESA/SADC"].fillna(0) + xn["Other AfCFTA"].fillna(0), color=C["green"], marker="o", ms=2.5,
           label="Exporters to Africa beyond\nDRC/EAC")
    a.plot(afr_dest.index, afr_dest.values, color=C["yellow"], marker="o", ms=2.5, label="African destinations served")
    a.set_ylim(0, None)
    a.set_title("(c) Reach into the wider\nAfrican market (counts)")
    a.legend(fontsize=5.8, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=1)
    year_axis(a, list(afr_dest.index), 3)
    fig.tight_layout(w_pad=1.1, rect=(0, 0.06, 1, 1))
    chart_data(22, "a", "Exports by market tier", xsh.loc[:, xsh.sum() > 0].rename(columns=lab).rename_axis("Year"), "% of annual exports")
    chart_data(22, "b", "Imports by origin tier", msh.loc[:, msh.sum() > 0].rename(columns=lab).rename_axis("Year"), "% of annual imports")
    chart_data(22, "c", "Reach into the wider African market", pd.DataFrame({"Exporters to Africa beyond DRC/EAC": xn["Other COMESA/SADC"].fillna(0) + xn["Other AfCFTA"].fillna(0), "African destinations served": afr_dest}).rename_axis("Year"), "Count", "Exporter counts are summed across the two tiers.")
    save(fig, "f21_afcfta")
    NUM.update(x_beyond_eac_africa=(xsh["Other COMESA/SADC"] + xsh["Other AfCFTA"]).mean(),
               m_beyond_eac_africa=(msh["Other COMESA/SADC"] + msh["Other AfCFTA"]).mean(),
               x_row_share=xsh["Rest of world"].mean(), m_africa_2010=(100 - msh.loc[2010, "Rest of world"]),
               m_africa_2023=(100 - msh.loc[2023, "Rest of world"]), afr_dest_mean=afr_dest.mean(),
               afr_dest_min=afr_dest.min(), afr_dest_max=afr_dest.max(),
               n_x_beyond_mean=(xn["Other COMESA/SADC"].fillna(0) + xn["Other AfCFTA"].fillna(0)).mean())
    # import intensity of exporters by main export group (2019-23)
    s = xm[(xm.x > 0) & (xm.y >= 2019)]
    imp_any = s.groupby("grp").apply(lambda g: (g.m > 0).mean() * 100, include_groups=False)
    ratio = s.groupby("grp").apply(lambda g: np.median(g.m / g.x), include_groups=False) * 100
    n = s.groupby("grp").f.nunique()
    t = pd.DataFrame({"n": n, "imp": imp_any, "ratio": ratio}).reindex(EXPORT_GROUPS)
    t = t[t.n >= MIN_FIRMS]
    NUM["exp_importing_share_1923"] = (s.m > 0).mean() * 100
    NUM["exp_import_ratio_median_1923"] = np.median(s.m / s.x) * 100
    NUM["exp_import_ratio_gt50_1923"] = (s.m / s.x > 0.5).mean() * 100
    # products exported to wider Africa (pooled, >=3 firms)
    w = E[E.bloc.isin(["Other COMESA/SADC", "Other AfCFTA"])]
    pr = w.groupby("h4").agg(v=("v", "sum"), n=("f", "nunique"), nd=("d", "nunique"))
    pr = pr[pr.n >= MIN_FIRMS].sort_values("v", ascending=False).head(8)
    NUM["wider_africa_top_hs4"] = {k: [round(r.v / 1e6, 1), int(r.n), int(r.nd)] for k, r in pr.iterrows()}
    NUM["wider_africa_dest_top"] = (w.groupby("d").v.sum() / w.v.sum() * 100).sort_values(ascending=False).head(6).round(1).to_dict()
    return t


# ------------------------------------------------------------ infographic (at a glance)
def fig_glance():
    N = NUM
    tiles = [
        (f"{N['cover_customs_2023']:.0f}%", "of recorded goods imports were\nmatched by recorded goods\nexports in 2023", C["red"], "External imbalance"),
        (f"{N['res_2023']:.1f}", f"months of imports covered\nby gross reserves in 2023\n({N['res_2013']:.1f} in 2013)", C["red"], "Forex scarcity"),
        (f"{N['x_top10_mean']:.0f}%", "of exports shipped by the\nten largest exporters\n(2013–23 average)", C["navy"], "Superstars"),
        (f"{N['one_year_share']:.0f}%", f"of the {N['n_exporters_1523']:,} exporters active\nin 2015–23 exported in\na single year only", C["navy"], "Churning"),
        (f"{N['p_ext_given_reg']:.0f}%", "of regional-only entrants\nlater reach a market outside\nDR Congo and the EAC", C["orange"], "No stepping stone"),
        (f"{N['tza_wsh_2023']:.0f}%", f"of non-fuel import tonnage\ncame from Tanzania in 2023\n({N['tza_wsh_2010']:.0f}% in 2010)", C["orange"], "Central Corridor"),
        (f"{N['drc_man_share_mean']:.0f}%", "of processed and manufactured\nexports go to DR Congo\n(2013–23 average)", C["aqua"], "DRC frontier"),
        (f"{N['mirror_are'] / 100:.1f}×", "UAE-reported imports from\nBurundi relative to Burundi-\nrecorded exports to the UAE", C["aqua"], "Missing dollars"),
    ]
    fig = plt.figure(figsize=(W_FULL, 3.35))
    for i, (big, txt, col, tag) in enumerate(tiles):
        r, c = divmod(i, 4)
        x0, y0, w, h = 0.005 + c * 0.25, 0.52 - r * 0.5, 0.235, 0.44
        ax = fig.add_axes([x0, y0, w, h])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.add_patch(plt.matplotlib.patches.FancyBboxPatch((0.02, 0.02), 0.96, 0.96,
                     boxstyle="round,pad=0,rounding_size=0.04", fc="#f7f6f2", ec="none"))
        ax.add_patch(plt.Rectangle((0.02, 0.9), 0.96, 0.08, fc=col, ec="none"))
        ax.text(0.08, 0.80, tag.upper(), fontsize=5.8, color=col, fontweight="bold", va="top")
        ax.text(0.08, 0.58, big, fontsize=19, color=C["ink"], fontweight="bold", va="center")
        ax.text(0.08, 0.25, txt, fontsize=5.9, color=C["ink2"], va="center", linespacing=1.35)
    chart_data(1, "", "Headline indicators", pd.DataFrame([(tag, big, txt.replace("\n", " ")) for big, txt, col, tag in tiles], columns=["Indicator", "Value", "Description"]).set_index("Indicator"), "")
    save(fig, "f00_glance")
