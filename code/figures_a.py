"""Macro context, data coverage, trade structure, superstars, exporter dynamics."""
import matplotlib.pyplot as plt
import matplotlib.ticker as mt
import numpy as np
import pandas as pd

from common import *  # noqa: F401,F403


def fig_macro():
    ca = wdi("BN.CAB.XOKA.GD.ZS").loc[2008:2024]
    res = wdi("FI.RES.TOTL.MO").loc[2008:2024]
    fx = wdi("PA.NUS.FCRF").loc[2008:2024]
    xb = wdi("BX.GSR.MRCH.CD").loc[2008:2024] / 1e6
    mb = wdi("BM.GSR.MRCH.CD").loc[2008:2024] / 1e6
    fig, axs = plt.subplots(2, 2, figsize=(W_FULL, 4.3))
    yrs = list(range(2008, 2025))
    a = axs[0, 0]
    a.bar(ca.index, ca.values, color=C["red"], width=0.62)
    a.axhline(0, color=C["axis"], lw=0.6)
    a.set_title("(a) Current account balance, % of GDP")
    year_axis(a, yrs, 3)
    a = axs[0, 1]
    a.plot(res.index, res.values, color=C["blue"], marker="o", ms=3)
    a.axhline(3, color=C["muted"], lw=0.6)
    a.text(2008.2, 3.15, "3-month adequacy benchmark", fontsize=6, color=C["muted"])
    a.set_title("(b) Gross reserves, months of imports")
    a.set_ylim(0, 7.8)
    year_axis(a, yrs, 3)
    a = axs[1, 0]
    a.plot(fx.index, fx.values, color=C["navy"], marker="o", ms=3)
    a.set_title("(c) Official exchange rate, BIF per US$")
    a.yaxis.set_major_formatter(mt.FuncFormatter(fmt_m))
    a.annotate("May 2023\ndevaluation", xy=(2023, fx[2023]), xytext=(2017.6, 2600), fontsize=6,
               color=C["ink2"], arrowprops=dict(arrowstyle="-", color=C["muted"], lw=0.6))
    year_axis(a, yrs, 3)
    a = axs[1, 1]
    a.plot(mb.index, mb.values, color=C["orange"], label="Goods imports")
    a.plot(xb.index, xb.values, color=C["blue"], label="Goods exports")
    a.fill_between(mb.index, xb.values, mb.values, color=C["orange"], alpha=0.08, lw=0)
    a.set_title("(d) Merchandise trade (BoP), US$ million")
    a.text(2024.3, mb.iloc[-1], "Imports", fontsize=6.5, color=C["ink2"], va="center")
    a.text(2024.3, xb.iloc[-1], "Exports", fontsize=6.5, color=C["ink2"], va="center")
    a.text(2016.5, 520, "Trade deficit", fontsize=6.5, color=C["orange"], ha="center")
    year_axis(a, yrs, 3)
    a.set_xlim(2007.4, 2026.4)
    fig.tight_layout(h_pad=1.6, w_pad=2.0)
    chart_data(2, "a", "Current account balance, % of GDP", ca.rename("Current account balance").rename_axis("Year"), "% of GDP", "Source: World Bank WDI (BN.CAB.XOKA.GD.ZS).")
    chart_data(2, "b", "Gross reserves, months of imports", res.rename("Gross reserves").rename_axis("Year"), "Months of imports", "Source: WDI (FI.RES.TOTL.MO). The chart shows a reference line at 3 months.")
    chart_data(2, "c", "Official exchange rate", fx.rename("Official exchange rate").rename_axis("Year"), "BIF per US$ (period average)", "Source: WDI (PA.NUS.FCRF).")
    chart_data(2, "d", "Merchandise trade (balance of payments)", pd.DataFrame({"Goods imports": mb, "Goods exports": xb, "Trade balance": xb - mb}).rename_axis("Year"), "US$ million", "Source: WDI (BM.GSR.MRCH.CD, BX.GSR.MRCH.CD). The shaded area in the chart is the trade balance.")
    save(fig, "f01_macro")
    NUM.update(ca_mean_2013_23=ca.loc[2013:2023].mean(), ca_2023=ca[2023],
               res_2013=res[2013], res_2015=res[2015], res_2023=res[2023], res_2010=res[2010], res_min=res.loc[2013:].min(),
               fx_2013=fx[2013], fx_2022=fx[2022], fx_2023=fx[2023], fx_2024=fx.get(2024),
               fx_dep_2013_22=(fx[2022] / fx[2013] - 1) * 100, fx_dep_22_24=(fx[2024] / fx[2022] - 1) * 100,
               xb_2023=xb[2023], mb_2023=mb[2023], cover_bop_2023=xb[2023] / mb[2023] * 100)


def fig_coverage(E, IM):
    xc = E.groupby("y").v.sum() / 1e6
    mc = IM.groupby("y").v.sum() / 1e6
    mc_nf = IM[IM.cat != "Fuel"].groupby("y").v.sum() / 1e6
    xb = wdi("BX.GSR.MRCH.CD") / 1e6
    mb = wdi("BM.GSR.MRCH.CD") / 1e6
    fig, axs = plt.subplots(1, 2, figsize=(W_FULL, 2.4))
    yx = list(range(2013, 2024))
    ym = list(range(2010, 2024))
    a = axs[0]
    a.plot(yx, xb.loc[yx], color=C["gray"], marker="o", ms=2.5, label="Balance of payments")
    a.plot(yx, xc.loc[yx], color=C["blue"], marker="o", ms=2.5, label="Customs (this dataset)")
    a.set_title("(a) Exports, US$ million")
    a.legend(loc="upper left")
    a.set_ylim(0, 320)
    year_axis(a, yx, 2)
    a = axs[1]
    a.plot(ym, mb.loc[ym], color=C["gray"], marker="o", ms=2.5, label="Balance of payments")
    a.plot(ym, mc.loc[ym], color=C["orange"], marker="o", ms=2.5, label="Customs, all goods")
    a.plot(ym, mc_nf.loc[ym], color=C["orange"], ls=(0, (1, 1.2)), lw=1.2, label="Customs, excl. fuel (HS 27)")
    a.set_title("(b) Imports, US$ million")
    a.legend(loc="upper left")
    a.set_ylim(0, 1250)
    year_axis(a, ym, 2)
    fig.tight_layout(w_pad=2)
    chart_data(3, "a", "Exports: customs data vs balance of payments", pd.DataFrame({"Balance of payments": xb.loc[yx], "Customs (this dataset)": xc.loc[yx]}).rename_axis("Year"), "US$ million", "BoP: WDI BX.GSR.MRCH.CD.")
    chart_data(3, "b", "Imports: customs data vs balance of payments", pd.DataFrame({"Balance of payments (f.o.b.)": mb.loc[ym], "Customs, all goods (c.i.f.)": mc.loc[ym], "Customs, excl. fuel (HS 27)": mc_nf.loc[ym]}).rename_axis("Year"), "US$ million", "BoP: WDI BM.GSR.MRCH.CD.")
    save(fig, "f02_coverage")
    cov_m = (mc / mb).loc[ym] * 100
    cov_x = (xc / xb).loc[yx] * 100
    NUM.update(cov_m_2010_16=cov_m.loc[2010:2016].mean(), cov_m_2017_23=cov_m.loc[2017:2023].mean(),
               cov_x_mean=cov_x.mean(), cov_x_2013=cov_x[2013], cov_x_2023=cov_x[2023],
               fuel_2010_16=(IM[(IM.cat == "Fuel")].groupby("y").v.sum().loc[2010:2016] / 1e6).mean(),
               fuel_2017_23=(IM[(IM.cat == "Fuel")].groupby("y").v.sum().loc[2017:2023] / 1e6).mean(),
               mc_2023=mc[2023], mb_2023=mb[2023], xc_2023=xc[2023], xb_2023b=xb[2023])
    # fuel: customs (EDD) versus central bank import statistics (BRB, compiled from OBR customs records)
    brb = pd.read_csv(EXT / "brb_fuel_imports.csv", index_col="year")
    brb["usd"] = brb.value_mbif / wdi("PA.NUS.FCRF").reindex(brb.index)
    fu = IM[IM.cat == "Fuel"].groupby("y").agg(v=("v", "sum"), q=("q", "sum"))
    for y in brb.index:
        NUM.update({f"brb_fuel_kt_{y}": brb.tonnes[y] / 1e3, f"brb_fuel_usd_{y}": brb.usd[y],
                    f"edd_fuel_kt_{y}": fu.q[y] / 1e6, f"edd_fuel_usd_{y}": fu.v[y] / 1e6})
    NUM["brb_fuel_kt_gap_2014_16"] = max(abs(fu.q[y] / 1e6 / (brb.tonnes[y] / 1e3) - 1) * 100 for y in range(2014, 2017))


def table_summary(E, IM):
    ex = E.groupby("y").agg(xv=("v", "sum"), nx=("f", "nunique"), px=("h4", "nunique"), dx=("d", "nunique"))
    im = IM.groupby("y").agg(mv=("v", "sum"), nm=("f", "nunique"), pm=("h4", "nunique"), om=("o", "nunique"))
    t = im.join(ex, how="left")
    t["xv"] /= 1e6
    t["mv"] /= 1e6
    t = t[["xv", "nx", "px", "dx", "mv", "nm", "pm", "om"]]
    t.index.name = "Year"
    hdr = [r" & \multicolumn{4}{c}{Exports} & \multicolumn{4}{c}{Imports} \\",
           r"\cmidrule(lr){2-5}\cmidrule(lr){6-9}",
           r"Year & US\$m & Firms & HS4 & Dest. & US\$m & Firms & HS4 & Origins \\"]
    f = {c: "{:,.0f}" for c in t.columns}
    f["xv"] = f["mv"] = "{:,.1f}"
    t2 = t.copy()
    t2.index = t2.index.astype(str)
    table_data(2, "Burundi's recorded trade: summary statistics by year", t.rename(columns={"xv": "Exports (US$ m)", "nx": "Exporters", "px": "Export products (HS4)", "dx": "Destinations", "mv": "Imports (US$ m)", "nm": "Importers", "pm": "Import products (HS4)", "om": "Origins"}), "Firm-level exports are available from 2013 only. HS4 = number of distinct 4-digit products.")
    latex_table(t2, "t02_summary", fmt=f, header_rows=hdr, col_format="lrrrrrrrr")
    NUM.update(n_exporters_total=E.f.nunique(), n_importers_total=IM.f.nunique(),
               nx_2013=ex.nx[2013], nx_2014=ex.nx[2014], nx_2020=ex.nx[2020], nx_2023=ex.nx[2023],
               nm_2010=im.nm[2010], nm_2016=im.nm[2016], nm_2022=im.nm[2022], nm_2023=im.nm[2023],
               n_rows_exp=len(E), n_rows_imp=len(IM), n_dest=E.d.nunique(), n_orig=IM.o.nunique(),
               n_hs6_exp=E.hs.nunique(), n_hs6_imp=IM.hs.nunique())


def fig_export_structure(E):
    val, n = sdc_pivot(E, "y", "grp", "export groups by year")
    val = val.reindex(columns=EXPORT_GROUPS + ([COMBINED] if COMBINED in val else []))
    sh = val.div(val.sum(1), axis=0) * 100
    reg, _ = sdc_pivot(E, "y", "region", "export regions by year")
    reg = reg.reindex(columns=REGIONS + ([COMBINED] if COMBINED in reg else [])).fillna(0)
    rsh = reg.div(reg.sum(1), axis=0) * 100
    yrs = list(val.index)
    fig, axs = plt.subplots(1, 2, figsize=(W_FULL, 2.9))
    if PUBLIC:
        LABELS["Other Asia and rest of world"] = "Asia, Middle East and rest of world"
    for a, df, cols, colors, title in [
        (axs[0], sh, EXPORT_GROUPS, EXPORT_COLORS, "(a) By product group, % of exports"),
        (axs[1], rsh, REGIONS, REGION_COLORS, "(b) By destination, % of exports")]:
        stack_bars(a, df, cols, colors)
        a.set_ylim(0, 100)
        a.set_title(title)
        year_axis(a, yrs, 2)
    h0, l0 = axs[0].get_legend_handles_labels()
    axs[0].legend(h0[::-1], l0[::-1], loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=6.2)
    h1, l1 = axs[1].get_legend_handles_labels()
    axs[1].legend(h1[::-1], l1[::-1], loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=6.2)
    fig.tight_layout(w_pad=2)
    _sdc = " Hatched 'combined' cells group a dominated cell with others (secondary suppression)." if PUBLIC else ""
    chart_data(4, "a", "Exports by product group", sh.dropna(axis=1, how="all").rename(columns=lab).rename_axis("Year"), "% of annual exports", "Blank = suppressed (fewer than 3 firms" + ("; or one firm above 85% of the cell)." if PUBLIC else ").") + _sdc + " Product groups are defined in Appendix A.")
    chart_data(4, "b", "Exports by destination", rsh.loc[:, rsh.sum() > 0].rename(columns=lab).rename_axis("Year"), "% of annual exports", "Suppressed cells are shown as 0." + _sdc)
    if PUBLIC:
        LABELS.pop("Other Asia and rest of world", None)
    save(fig, "f03_export_structure")
    NUM.update(**{f"xsh_{k[:6].replace(' ', '_')}": sh[k].mean() for k in EXPORT_GROUPS})
    NUM.update(coffee_share_mean=sh["Coffee"].mean(), gold_min_share_mean=sh["Gold and mineral ores"].mean(),
               top3_primary_mean=(sh["Coffee"] + sh["Tea and other agriculture"] + sh["Gold and mineral ores"]).mean(),
               agro_share_mean=sh["Agro-industry"].mean(), manuf_share_mean=sh["Manufactures"].mean(),
               drc_xshare_2013=rsh.loc[2013, "DR Congo"], drc_xshare_2023=rsh.loc[2023, "DR Congo"],
               gulf_xshare_mean=rsh["Gulf states"].mean(), eur_xshare_mean=rsh["Europe"].mean(),
               asia_xshare_mean=rsh[["Gulf states", "China", "India", "Other Asia and rest of world"]].sum(axis=1).mean(),
               xshare_years_primary=[int(y) for y in sh.index[(sh[["Coffee", "Tea and other agriculture", "Gold and mineral ores"]].notna().all(axis=1))]])
    # pooled HS4 table (pooled 2013-2023, cells >= 3 firms)
    p = E.groupby("h4").agg(v=("v", "sum"), n=("f", "nunique"), nd=("d", "nunique"))
    p["share"] = p.v / p.v.sum() * 100
    p = p.sort_values("v", ascending=False)
    names = {"0901": "Coffee", "7108": "Gold (unwrought)", "0902": "Tea", "1101": "Wheat/maize flour",
             "2402": "Cigarettes", "2615": "Niobium/tantalum ores", "2203": "Beer", "3401": "Soap",
             "2710": "Petroleum oils (re-exports)", "7210": "Coated flat steel", "2611": "Tungsten ores",
             "7214": "Iron/steel bars", "8703": "Motor cars (re-exports)", "2302": "Bran and residues",
             "7010": "Glass bottles and jars", "2609": "Tin ores", "0713": "Dried legumes",
             "1905": "Bakery products", "8704": "Goods vehicles (re-exports)", "0803": "Bananas",
             "0709": "Other vegetables", "4101": "Raw hides"}
    ok = p.n >= MIN_FIRMS
    if PUBLIC:
        dom = top_share(E, ["h4"]) > MAX_DOM
        ok &= ~dom.reindex(p.index).fillna(False)
        NUM["t3_dominated_in_top15"] = int(dom.reindex(p[p.n >= MIN_FIRMS].head(15).index).sum())
    top = p[ok].head(15).copy()
    top["cum"] = top.share.cumsum()
    top.insert(0, "Product", [names.get(i, i) for i in top.index])
    top.index = [f"{i}" for i in top.index]
    top.index.name = "HS4"
    top = top[["Product", "share", "cum", "n", "nd"]]
    table_data(3, "Top 15 export products, pooled 2013-2023", top.rename(columns={"share": "Share of exports (%)", "cum": "Cumulative share (%)", "n": "Firms", "nd": "Destinations"}), "Shares of total 2013-2023 exports. Firms and destinations are distinct counts over the period. Only products with at least three exporters are shown." + (" Products in which one firm accounts for more than 85% of pooled exports are not shown." if PUBLIC else ""))
    latex_table(top, "t03_top_exports", fmt={"share": "{:.1f}", "cum": "{:.1f}", "n": "{:,.0f}", "nd": "{:,.0f}"},
                header_rows=[r"HS4 & Product & Share (\%) & Cumulative (\%) & Firms & Destinations \\"],
                col_format="llrrrr")
    NUM.update(top5hs4_share=p.share.head(5).sum(), top10hs4_share=p.share.head(10).sum(),
               n_hs4_exported=len(p))


def fig_import_structure(IM):
    val, _ = sdc_pivot(IM, "y", "cat", "import categories by year")
    val = val.reindex(columns=IMPORT_CATS + ([COMBINED] if COMBINED in val else []))
    sh = val.div(val.sum(1), axis=0) * 100
    reg, _ = safe_pivot(IM, "y", "region", "import regions by year")
    reg = reg.reindex(columns=REGIONS).fillna(0)
    rsh = reg.div(reg.sum(1), axis=0) * 100
    yrs = list(val.index)
    fig, axs = plt.subplots(1, 2, figsize=(W_FULL, 3.1))
    for a, df, cols, colors, title in [
        (axs[0], sh, IMPORT_CATS, IMPORT_COLORS, "(a) By product category, % of imports"),
        (axs[1], rsh, REGIONS, REGION_COLORS, "(b) By origin, % of imports")]:
        if PUBLIC:
            stack_bars(a, df, cols, colors)
        else:
            bottom = np.zeros(len(df))
            for c in cols:
                a.bar(df.index, df[c].fillna(0), bottom=bottom, color=colors[c], width=0.78, label=c,
                      edgecolor="white", linewidth=0.5)
                bottom += df[c].fillna(0).values
        a.set_ylim(0, 100)
        a.set_title(title)
        year_axis(a, yrs, 2)
    for a in axs:
        h, l = a.get_legend_handles_labels()
        a.legend(h[::-1], l[::-1], loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=6.2)
    fig.tight_layout(w_pad=2)
    chart_data(5, "a", "Imports by product category", sh.dropna(axis=1, how="all").rename(columns=lab).rename_axis("Year"), "% of annual imports", "The fall in fuel after 2016 reflects the recording break (Section 3).")
    chart_data(5, "b", "Imports by origin", rsh[REGIONS].rename_axis("Year"), "% of annual imports", "Cells with fewer than 3 firms are suppressed (shown as 0).")
    save(fig, "f04_import_structure")
    NUM.update(fuel_msh_2010_16=sh.loc[2010:2016, "Fuel"].mean(), fuel_msh_2017_23=sh.loc[2017:2023, "Fuel"].mean(),
               food_msh_mean=sh["Food and agriculture"].mean(),
               capital_msh_2023=sh.loc[2023, ["Machinery and equipment", "Vehicles and transport equipment"]].sum(),
               china_msh_2023=rsh.loc[2023, "China"], eac_msh_2010=rsh.loc[2010, "EAC partners"],
               eac_msh_2023=rsh.loc[2023, "EAC partners"], gulf_msh_2010=rsh.loc[2010, "Gulf states"],
               gulf_msh_2023=rsh.loc[2023, "Gulf states"], eur_msh_2010=rsh.loc[2010, "Europe"],
               eur_msh_2023=rsh.loc[2023, "Europe"], india_msh_2013=rsh.loc[2013, "India"],
               india_msh_2023=rsh.loc[2023, "India"])


# ----------------------------------------------------------------- superstars (P3)
def concentration_series(df):
    out = {}
    for y, g in df.groupby("y"):
        fv = g.groupby("f").v.sum().sort_values(ascending=False)
        n, tot = len(fv), fv.sum()
        out[y] = dict(N=n, top1pct=fv.iloc[:max(1, int(np.ceil(n * .01)))].sum() / tot * 100,
                      top5pct=fv.iloc[:max(1, int(np.ceil(n * .05)))].sum() / tot * 100,
                      top10=fv.iloc[:10].sum() / tot * 100,
                      bottom50=fv.iloc[n // 2:].sum() / tot * 100,
                      HHI=((fv / tot) ** 2).sum() * 1e4, median=fv.median() / 1e3, mean=fv.mean() / 1e3)
    return pd.DataFrame(out).T


def fig_concentration(E, IM):
    ce = concentration_series(E)
    ci = concentration_series(IM)
    fig, axs = plt.subplots(1, 3, figsize=(W_FULL, 2.3))
    a = axs[0]
    for col, c, lab in [("top1pct", C["navy"], "Top 1%"), ("top5pct", C["blue"], "Top 5%"),
                        ("top10", C["orange"], "Top 10 firms")]:
        a.plot(ce.index, ce[col], color=c, marker="o", ms=2.3, label=lab)
    a.set_ylim(0, 100)
    a.set_title("(a) Exporters: share of exports, %")
    a.legend(loc="lower left", fontsize=6)
    year_axis(a, list(ce.index), 2)
    a = axs[1]
    for col, c, lab in [("top1pct", C["navy"], "Top 1%"), ("top5pct", C["blue"], "Top 5%"),
                        ("top10", C["orange"], "Top 10 firms")]:
        a.plot(ci.index, ci[col], color=c, marker="o", ms=2.3, label=lab)
    a.set_ylim(0, 100)
    a.set_title("(b) Importers: share of imports, %")
    year_axis(a, list(ci.index), 3)
    a = axs[2]
    a.plot(ce.index, ce.HHI, color=C["blue"], marker="o", ms=2.3, label="Exporters")
    a.plot(ci.index, ci.HHI, color=C["orange"], marker="o", ms=2.3, label="Importers")
    a.set_title("(c) Herfindahl index across firms")
    a.legend(loc="upper left", fontsize=6)
    year_axis(a, list(ci.index), 3)
    a.set_ylim(0, 1800)
    fig.tight_layout(w_pad=1.4)
    _lab = {"top1pct": "Top 1% of firms", "top5pct": "Top 5% of firms", "top10": "Top 10 firms"}
    chart_data(6, "a", "Exporters: share of exports by the largest firms", ce[list(_lab)].rename(columns=_lab).rename_axis("Year"), "% of annual exports")
    chart_data(6, "b", "Importers: share of imports by the largest firms", ci[list(_lab)].rename(columns=_lab).rename_axis("Year"), "% of annual imports")
    chart_data(6, "c", "Herfindahl index across firms", pd.DataFrame({"Exporters": ce.HHI, "Importers": ci.HHI}).rename_axis("Year"), "Index (0-10,000)")
    save(fig, "f05_concentration")
    NUM.update(x_top1pct_2013_16=ce.loc[2013:2016, "top1pct"].mean(), x_top1pct_2020_23=ce.loc[2020:2023, "top1pct"].mean(),
               x_top5pct_mean=ce.top5pct.mean(), x_top10_2013=ce.loc[2013, "top10"], x_top10_2023=ce.loc[2023, "top10"],
               x_top10_mean=ce.top10.mean(), x_bottom50_mean=ce.bottom50.mean(),
               x_hhi_2013_16=ce.loc[2013:2016, "HHI"].mean(), x_hhi_2020_23=ce.loc[2020:2023, "HHI"].mean(),
               m_top1pct_mean=ci.top1pct.mean(), m_top5pct_mean=ci.top5pct.mean(), m_hhi_mean=ci.HHI.mean(),
               x_median_k_2013=ce.loc[2013, "median"], x_median_k_2023=ce.loc[2023, "median"],
               x_mean_k_mean=ce["mean"].mean(), x_median_k_mean=ce["median"].mean(),
               m_median_k_mean=ci["median"].mean(), m_mean_k_2010_16=ci.loc[2010:2016, "mean"].mean(),
               m_mean_k_2018_23=ci.loc[2018:2023, "mean"].mean())
    return ce, ci


def fig_size_classes(E, IM):
    bins = [0, 1e4, 1e5, 1e6, 1e7, np.inf]
    labs = ["< $10k", "$10k–100k", "$100k–1m", "$1m–10m", "≥ $10m"]
    out = {}
    for name, df in [("Exporters", E), ("Importers", IM)]:
        fy = df.groupby(["f", "y"]).v.sum().reset_index()
        fy["cls"] = pd.cut(fy.v, bins, labels=labs, right=False)
        g = fy.groupby("cls", observed=False).agg(n=("v", "size"), v=("v", "sum"))
        out[name] = pd.DataFrame({"firms": g.n / g.n.sum() * 100, "value": g.v / g.v.sum() * 100})
        ncount = fy.groupby("cls", observed=False).f.nunique()
        if (ncount < MIN_FIRMS).any():
            SUPPRESSED.append(("size classes " + name, int((ncount < MIN_FIRMS).sum()), "flag"))
    fig, axs = plt.subplots(1, 2, figsize=(W_FULL, 2.3), sharey=True)
    for a, name in zip(axs, ["Exporters", "Importers"]):
        d = out[name]
        yy = np.arange(len(labs))[::-1]
        a.barh(yy + 0.2, d.firms, height=0.38, color=C["gray"], label="% of firm-years")
        a.barh(yy - 0.2, d.value, height=0.38, color=C["blue"] if name == "Exporters" else C["orange"],
               label="% of trade value")
        for yv, f_, v_ in zip(yy, d.firms, d.value):
            a.text(f_ + 1, yv + 0.2, f"{f_:.0f}", va="center", fontsize=6, color=C["ink2"])
            a.text(v_ + 1, yv - 0.2, f"{v_:.0f}", va="center", fontsize=6, color=C["ink2"])
        a.set_yticks(yy)
        a.set_yticklabels(labs)
        a.set_xlim(0, 75)
        a.grid(axis="y", visible=False)
        a.grid(axis="x", visible=True)
        a.set_title(f"({'a' if name == 'Exporters' else 'b'}) {name}, annual value per firm (pooled)")
        a.legend(loc="lower right", fontsize=6)
    fig.tight_layout(w_pad=1.5)
    for _p, _n in [("a", "Exporters"), ("b", "Importers")]:
        chart_data(7, _p, f"{_n}: firm-years and trade value by annual value per firm", out[_n].rename(columns={"firms": "% of firm-years", "value": "% of trade value"}).rename_axis("Annual value per firm"), "%", "Firm-years pooled over 2013-2023 (exports) and 2010-2023 (imports).")
    save(fig, "f06_size_classes")
    NUM.update(x_small_firms=out["Exporters"].firms.iloc[:2].sum(), x_small_value=out["Exporters"].value.iloc[:2].sum(),
               x_big_firms=out["Exporters"].firms.iloc[-1], x_big_value=out["Exporters"].value.iloc[-1],
               x_1m_firms=out["Exporters"].firms.iloc[-2:].sum(), x_1m_value=out["Exporters"].value.iloc[-2:].sum(),
               m_small_firms=out["Importers"].firms.iloc[0], m_small_value=out["Importers"].value.iloc[0],
               m_1m_firms=out["Importers"].firms.iloc[-2:].sum(), m_1m_value=out["Importers"].value.iloc[-2:].sum())


def fig_granular(E, EM):
    """Decompose annual export change into top-10 incumbents, other incumbents, entry, exit."""
    fy = E.groupby(["f", "y"]).v.sum().unstack(fill_value=0)
    yrs = list(fy.columns)
    rows = []
    for t0, t1 in zip(yrs[:-1], yrs[1:]):
        if t1 <= DYN_START:
            continue
        x0, x1 = fy[t0], fy[t1]
        tot0 = x0.sum()
        top = x0.sort_values(ascending=False).index[:10]
        inc = (x0 > 0) & (x1 > 0)
        topm = x0.index.isin(top) & inc
        rows.append(dict(y=t1,
                         top10=(x1[topm] - x0[topm]).sum() / tot0 * 100,
                         other=(x1[inc & ~topm] - x0[inc & ~topm]).sum() / tot0 * 100,
                         entry=x1[(x0 == 0) & (x1 > 0)].sum() / tot0 * 100,
                         exit=-x0[(x0 > 0) & (x1 == 0)].sum() / tot0 * 100,
                         total=(x1.sum() / tot0 - 1) * 100))
    d = pd.DataFrame(rows).set_index("y")
    # monthly lumpiness
    m = monthly_exports(EM)
    tot_y = EM.groupby("y").v.sum() / 1e6
    peak = m.groupby(m.index.year).max() / tot_y * 100
    fig, axs = plt.subplots(1, 2, figsize=(W_FULL, 2.55), gridspec_kw=dict(width_ratios=[1.1, 1]))
    a = axs[0]
    comps = [("top10", C["navy"], "Top-10 incumbents"), ("other", C["lightblue"], "Other incumbents"),
             ("entry", C["aqua"], "Entrants"), ("exit", C["red"], "Exiters")]
    pos = np.zeros(len(d))
    neg = np.zeros(len(d))
    for k, c, lab in comps:
        v = d[k].values
        b = np.where(v >= 0, pos, neg)
        a.bar(d.index, v, bottom=b, color=c, width=0.7, label=lab, edgecolor="white", linewidth=0.4)
        pos += np.where(v >= 0, v, 0)
        neg += np.where(v < 0, v, 0)
    a.plot(d.index, d.total, color=C["ink"], marker="D", ms=3, lw=0, label="Total change")
    a.axhline(0, color=C["axis"], lw=0.6)
    a.set_title("(a) Contributions to annual export growth, pp")
    a.legend(fontsize=5.8, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)
    year_axis(a, list(d.index), 2)
    a.set_ylim(-60, 80)
    a = axs[1]
    a.plot(m.index, m.values, color=C["blue"], lw=0.9)
    a.set_title("(b) Monthly exports, US$ million")
    a.set_ylim(0, None)
    a.grid(axis="x", visible=False)
    fig.tight_layout(w_pad=1.8)
    chart_data(8, "a", "Contributions to annual export growth", d.rename(columns={"top10": "Top-10 incumbents", "other": "Other incumbents", "entry": "Entrants", "exit": "Exiters", "total": "Total change"}).rename_axis("Year"), "Percentage points", "Top-10 incumbents are ranked on previous-year exports. Computed from 2016, when firm identifiers are consistent.")
    _m = m.copy()
    _m.index = _m.index.strftime("%Y-%m")
    chart_data(8, "b", "Monthly exports", _m.rename("Exports").rename_axis("Month"), "US$ million",
               ("Blank = suppressed: " + ", ".join(NUM.get("monthly_suppressed", [])) + " (one firm above 85% of a month's exports, plus secondary suppression).") if PUBLIC and NUM.get("monthly_suppressed") else "")
    save(fig, "f07_granular")
    # variance share of top-10 incumbent term
    cov = np.cov(d.top10, d.total)[0, 1] / d.total.var() * 100
    NUM.update(granular_var_share=cov, entry_contrib_mean=d.entry.mean(), exit_contrib_mean=d.exit.mean(),
               top10_abs_mean=d.top10.abs().mean(), other_abs_mean=d.other.abs().mean(),
               peak_month_share_mean=peak.mean(), peak_month_share_max=peak.max(),
               monthly_x_cv=m.std() / m.mean(), monthly_x_median=m.median(), monthly_x_max=m.max())
    return d


# ------------------------------------------------------------- exporter dynamics (P4)
REGIONAL = ["COD"] + EAC5


def exporter_panels(E):
    E = E[E.y >= DYN_START]
    fy = E.groupby(["f", "y"]).v.sum().reset_index()
    yrs = sorted(E.y.unique())
    S = {y: set(fy.loc[fy.y == y, "f"]) for y in yrs}
    return fy, yrs, S


def fig_entry_exit(E):
    fy, yrs, S = exporter_panels(E)
    rows = []
    for i, y in enumerate(yrs[1:], 1):
        prev, cur = S[yrs[i - 1]], S[y]
        ent = cur - prev
        rows.append(dict(y=y, N=len(cur), entry=len(ent) / len(cur) * 100, exit=len(prev - cur) / len(prev) * 100,
                         entrant_vshare=fy[(fy.y == y) & fy.f.isin(ent)].v.sum() / fy[fy.y == y].v.sum() * 100,
                         entrant_size=fy[(fy.y == y) & fy.f.isin(ent)].v.median() /
                         fy[(fy.y == y) & fy.f.isin(cur & prev)].v.median() * 100))
    d = pd.DataFrame(rows).set_index("y")
    # cohort survival: first appearance cohorts 2016-2022 (not exporting in 2015)
    first = fy.groupby("f").y.min()
    firstdest = E[E.y >= DYN_START].merge(first.rename("y0"), on="f")
    firstdest = firstdest[firstdest.y == firstdest.y0].groupby("f").d.apply(lambda s: set(s) <= set(REGIONAL))
    surv = {}
    for grp_name, sel in [("All entrants", None), ("Regional-only starters", True), ("Extra-regional starters", False)]:
        curves = []
        for y0 in range(DYN_START + 1, 2023):
            coh = set(first[first == y0].index)
            if sel is not None:
                coh = {f for f in coh if firstdest.get(f) == sel}
            if len(coh) < MIN_FIRMS:
                continue
            alive = coh
            c = {0: 100.0}
            for k in range(1, 2024 - y0):
                alive = alive & S[y0 + k]           # continuous survival
                c[k] = len(alive) / len(coh) * 100
            curves.append(pd.Series(c, name=y0))
        cm = pd.concat(curves, axis=1)
        surv[grp_name] = cm.mean(axis=1)[cm.count(axis=1) >= 3]
    fig, axs = plt.subplots(1, 2, figsize=(W_FULL, 2.5))
    a = axs[0]
    a.plot(d.index, d.entry, color=C["aqua"], marker="o", ms=2.5, label="Entry rate")
    a.plot(d.index, d.exit, color=C["red"], marker="o", ms=2.5, label="Exit rate")
    a.plot(d.index, d.entrant_vshare, color=C["gray"], marker="o", ms=2.5, label="Entrants' share of export value")
    a.set_ylim(0, 80)
    a.set_title("(a) Exporter turnover, %")
    a.legend(fontsize=6, loc="lower left")
    year_axis(a, list(d.index), 2)
    a = axs[1]
    cols = {"All entrants": C["ink"], "Regional-only starters": C["orange"], "Extra-regional starters": C["blue"]}
    for k, s in surv.items():
        a.plot(s.index, s.values, color=cols[k], marker="o", ms=2.5, label=k)
    a.set_title("(b) Continuous survival of entry cohorts, %")
    a.set_xlabel("Years since first export")
    a.set_ylim(0, 105)
    a.legend(fontsize=6)
    a.grid(axis="x", visible=False)
    fig.tight_layout(w_pad=2)
    chart_data(9, "a", "Exporter turnover", d[["entry", "exit", "entrant_vshare"]].rename(columns={"entry": "Entry rate", "exit": "Exit rate", "entrant_vshare": "Entrants' share of export value"}).rename_axis("Year"), "%", "Computed on 2015-2023 (consistent firm identifiers).")
    chart_data(9, "b", "Continuous survival of entry cohorts", pd.DataFrame(surv).rename_axis("Years since first export"), "% of cohort still exporting", "Average across the 2016-2022 entry cohorts. Points based on fewer than 3 cohorts are dropped.")
    save(fig, "f08_entry_exit")
    one_year = (fy.groupby("f").y.nunique() == 1)
    NUM.update(entry_rate_mean=d.entry.mean(), exit_rate_mean=d.exit.mean(),
               entrant_vshare_median=d.entrant_vshare.median(), entrant_rel_size=d.entrant_size.median(),
               surv1_all=surv["All entrants"].get(1), surv3_all=surv["All entrants"].get(3),
               surv1_reg=surv["Regional-only starters"].get(1), surv1_ext=surv["Extra-regional starters"].get(1),
               surv3_reg=surv["Regional-only starters"].get(3), surv3_ext=surv["Extra-regional starters"].get(3),
               one_year_share=one_year.mean() * 100, one_year_n=one_year.sum(), n_exporters_1523=len(one_year),
               all_years_n=(fy.groupby("f").y.nunique() == len(yrs)).sum())
    # all-years exporters share of value
    full = fy.groupby("f").y.nunique()
    fullset = full[full == len(yrs)].index
    NUM["all_years_vshare"] = fy[fy.f.isin(fullset)].v.sum() / fy.v.sum() * 100
    return d


def fig_stepping_stone(E):
    fy, yrs, S = exporter_panels(E)
    first = fy.groupby("f").y.min().rename("y0")
    E2 = E[E.y >= DYN_START].merge(first, on="f")
    E2 = E2[E2.y0 >= DYN_START + 1]    # exclude left-censored first year
    start = E2[E2.y == E2.y0].groupby("f").d.apply(
        lambda s: "Regional only" if set(s) <= set(REGIONAL) else ("Extra-regional only" if not (set(s) & set(REGIONAL)) else "Both"))
    later = E2[E2.y > E2.y0].groupby("f").d.apply(set)
    rows = []
    for f, st in start.items():
        L = later.get(f, set())
        rows.append(dict(f=f, start=st, survive=bool(L), reach_ext=bool(L - set(REGIONAL)),
                         reach_reg=bool(L & set(REGIONAL))))
    t = pd.DataFrame(rows)
    g = t.groupby("start").agg(n=("f", "size"), survive=("survive", "mean"), reach_ext=("reach_ext", "mean"),
                               reach_reg=("reach_reg", "mean")) * [1, 100, 100, 100]
    g = g.reindex(["Regional only", "Both", "Extra-regional only"])
    # destinations served per exporter by starting type (mean over years)
    fig, a = plt.subplots(figsize=(W_FULL, 1.95))
    yy = np.arange(len(g))[::-1]
    a.barh(yy + 0.22, g.survive, height=0.2, color=C["gray"], label="Exports again in any later year")
    a.barh(yy, g.reach_reg, height=0.2, color=C["orange"], label="Later exports to DRC/EAC")
    a.barh(yy - 0.22, g.reach_ext, height=0.2, color=C["blue"], label="Later exports outside DRC/EAC")
    for yv, row in zip(yy, g.itertuples()):
        for off, v in [(0.22, row.survive), (0, row.reach_reg), (-0.22, row.reach_ext)]:
            a.text(v + 0.8, yv + off, f"{v:.0f}", va="center", fontsize=6, color=C["ink2"])
    a.set_yticks(yy)
    a.set_yticklabels([f"{i}\n(n = {int(n):,})" for i, n in zip(g.index, g.n)], fontsize=6.8)
    a.set_xlim(0, 100)
    a.grid(axis="y", visible=False)
    a.grid(axis="x", visible=True)
    a.set_title("Where do new exporters go next? % of 2016–2022 entrants, by markets served in entry year")
    a.legend(fontsize=6, loc="center left", bbox_to_anchor=(1.0, 0.5))
    fig.tight_layout()
    chart_data(10, "", "Where do new exporters go next? 2016-2022 entrants, by markets served in their entry year", g.rename(columns={"n": "Entrants (number)", "survive": "Export again in any later year (%)", "reach_reg": "Later export to DRC/EAC (%)", "reach_ext": "Later export outside DRC/EAC (%)"}).rename_axis("Markets served in entry year"), "Number / %", "Regional = DR Congo, Kenya, Rwanda, South Sudan, Tanzania, Uganda.")
    save(fig, "f09_stepping_stone")
    NUM.update(reg_start_share=(start == "Regional only").mean() * 100,
               p_ext_given_reg=g.loc["Regional only", "reach_ext"], p_ext_given_ext=g.loc["Extra-regional only", "reach_ext"],
               p_surv_reg=g.loc["Regional only", "survive"], p_surv_ext=g.loc["Extra-regional only", "survive"],
               p_reg_given_ext=g.loc["Extra-regional only", "reach_reg"], n_entrants_1422=len(start))


def table_margins(E):
    fyd = E.groupby(["y", "f"]).agg(nd=("d", "nunique"), np_=("h4", "nunique"), v=("v", "sum")).reset_index()
    fyd["period"] = pd.cut(fyd.y, [2012, 2015, 2019, 2023], labels=["2013–15", "2016–19", "2020–23"])
    rows = {}
    for p, g in fyd.groupby("period", observed=True):
        ssd = (g.nd == 1) & (g.np_ == 1)
        rows[p] = {"Exporters per year": g.groupby("y").f.nunique().mean(),
                   "Mean exports per firm (US$ '000)": g.v.mean() / 1e3,
                   "Median exports per firm (US$ '000)": g.v.median() / 1e3,
                   "Products per firm (HS4, mean)": g.np_.mean(),
                   "Destinations per firm (mean)": g.nd.mean(),
                   "Single product & destination (% firms)": ssd.mean() * 100,
                   "Single product & destination (% value)": g.v[ssd].sum() / g.v.sum() * 100,
                   "Firms with 5+ destinations (% firms)": (g.nd >= 5).mean() * 100,
                   "Firms with 5+ destinations (% value)": g.v[g.nd >= 5].sum() / g.v.sum() * 100}
    t = pd.DataFrame(rows)
    t.index.name = "Indicator"
    t.columns = [str(c) for c in t.columns]
    table_data(4, "Exporter margins by period", t, "Averages over exporter-years in each period. Products at the HS 4-digit level.")
    latex_table(t, "t04_margins", fmt={c: "{:,.1f}" for c in t.columns},
                header_rows=[r"Indicator & 2013--15 & 2016--19 & 2020--23 \\"], col_format="lrrr")
    NUM.update(mean_k_2013_15=t.loc["Mean exports per firm (US$ '000)", "2013–15"],
               mean_k_2020_23=t.loc["Mean exports per firm (US$ '000)", "2020–23"],
               d5_value_min=t.loc["Firms with 5+ destinations (% value)"].min(),
               d5_value_max=t.loc["Firms with 5+ destinations (% value)"].max())
    NUM.update(ssd_share=((fyd.nd == 1) & (fyd.np_ == 1)).mean() * 100,
               nd_mean=fyd.nd.mean(), np_mean=fyd.np_.mean(),
               ssd_vshare=fyd.v[(fyd.nd == 1) & (fyd.np_ == 1)].sum() / fyd.v.sum() * 100,
               d5_firms=(fyd.nd >= 5).mean() * 100, d5_value=fyd.v[fyd.nd >= 5].sum() / fyd.v.sum() * 100)
