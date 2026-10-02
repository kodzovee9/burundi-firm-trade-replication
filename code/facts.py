"""Numbers quoted in the paper text that are not produced by a figure or table function."""
import json

import numpy as np
import pandas as pd

from common import DYN_START, IMPORT_CATS, MAX_DOM, NUM, PUBLIC, REGIONAL_SET, monthly_exports, top_share, wdi


def text_facts(E, EM, IM):
    # Coffee destinations (Section 4), pooled 2013-2023
    c = E[E.h4 == "0901"]
    sh = c.groupby("d").v.sum() / c.v.sum() * 100
    NUM.update(coffee_dest_che=sh["CHE"], coffee_dest_bel=sh["BEL"], coffee_dest_deu=sh["DEU"])

    # Non-fuel import category shares (Section 4)
    nf = IM[IM.cat != "Fuel"]
    cs = nf.pivot_table(index="y", columns="cat", values="v", aggfunc="sum")
    cs = cs.div(cs.sum(axis=1), axis=0) * 100
    for cat in IMPORT_CATS[1:]:
        if cat not in cs:
            continue
        k = cat.split()[0].lower()
        NUM[f"mcat_mean_{k}"] = cs[cat].mean()
        NUM[f"mcat_2023_{k}"] = cs.loc[2023, cat]

    # Firm-identifier break (Section 3, Appendix B)
    fy = IM.groupby(["f", "y"]).v.sum().reset_index()
    S = {y: set(fy.loc[fy.y == y, "f"]) for y in fy.y.unique()}
    top10 = set(fy[fy.y == 2010].nlargest(100, "v").f)
    top16 = set(fy[fy.y == 2016].nlargest(100, "v").f)
    NUM.update(id_top100_2010_after2016=max(len(top10 & S[y]) for y in range(2016, 2024)),
               id_top100_2016_in_2017=len(top16 & S[2017]))

    # Fuel importers (Appendix B)
    fu = IM[IM.cat == "Fuel"].groupby("y").f.nunique()
    NUM.update(fuel_importers_2010_16=fu.loc[2010:2016].mean(), fuel_importers_2017_23=fu.loc[2017:2023].mean())

    # Exports to DR Congo: manufactures share (Section 10)
    d = E[E.d == "COD"]
    NUM["drc_manuf_share"] = d[d.grp == "Manufactures"].v.sum() / d.v.sum() * 100

    # Monthly export spikes (Section 5)
    mm = monthly_exports(EM)
    NUM["n_months_over40_2020_23"] = int((mm.loc["2020":"2023"] > 40).sum())

    # Years in which exporters as a group were net forex users (Section 8)
    x = E.groupby(["f", "y"]).v.sum().rename("x")
    mm = IM.groupby(["f", "y"]).v.sum().rename("m")
    xm = pd.concat([x, mm], axis=1).fillna(0).reset_index()
    ex = xm[xm.x > 0].groupby("y")[["x", "m"]].sum()
    NUM["years_exporters_net_users"] = [int(y) for y in ex.index[ex.m > ex.x]]

    # Mirror: UAE gold ranges (Section 12)
    ug = {int(k): v for k, v in NUM["uae_gold_mirror"].items() if 2013 <= int(k) <= 2023}
    bx = {int(k): v for k, v in NUM["bdi_x_to_are"].items()}
    NUM.update(uae_gold_min=min(ug.values()), uae_gold_max=max(ug.values()),
               bdi_x_are_min=min(bx.values()), bdi_x_are_max=max(bx.values()))

    # Stepping stone: persistence of firms starting in both market types (Section 6)
    E15 = E[E.y >= DYN_START]
    first = E15.groupby("f").y.min().rename("y0")
    E2 = E15.merge(first, on="f")
    E2 = E2[E2.y0 >= DYN_START + 1]
    start = E2[E2.y == E2.y0].groupby("f").d.apply(set)
    both = [f for f, s in start.items() if (s & REGIONAL_SET) and (s - REGIONAL_SET)]
    later = set(E2[E2.y > E2.y0].f)
    NUM["p_surv_both"] = np.mean([f in later for f in both]) * 100
    NUM["n_both_starters"] = len(both)

    # Exporter counts by period (abstract, Section 3) and BoP 2014 (Section 2)
    nx = E.groupby("y").f.nunique()
    NUM.update(nx_mean_2013_15=nx.loc[2013:2015].mean(), nx_mean_2020_23=nx.loc[2020:2023].mean(),
               nx_max_2020_23=nx.loc[2020:2023].max(), x_customs_min=E.groupby("y").v.sum().min() / 1e6,
               x_customs_max=E.groupby("y").v.sum().max() / 1e6,
               bop_m_2014=wdi("BM.GSR.MRCH.CD")[2014] / 1e6, bop_x_2014=wdi("BX.GSR.MRCH.CD")[2014] / 1e6)
    NUM["fuel_drop_pct"] = (1 - NUM["fuel_2017_23"] / NUM["fuel_2010_16"]) * 100

    # Vehicle and pharmaceutical importers (Section 7)
    for cat, k in [("Vehicles and transport equipment", "veh"), ("Pharmaceuticals", "pharma")]:
        n = IM[IM.cat == cat].groupby("y").f.nunique()
        NUM[f"{k}_importers_2010"], NUM[f"{k}_importers_2023"] = int(n[2010]), int(n[2023])

    # Wider-Africa destinations (Section 13)
    NUM["sdn_egy_share"] = NUM["wider_africa_dest_top"].get("SDN", 0) + NUM["wider_africa_dest_top"].get("EGY", 0)
    NUM["drc_xshare_2022"] = d[d.y == 2022].v.sum() / E[E.y == 2022].v.sum() * 100

    # Additional statements (Sections 2, 5, 9, 12; Table 1)
    ca = wdi("BN.CAB.XOKA.GD.ZS").loc[2010:2024]
    res = wdi("FI.RES.TOTL.MO")
    mx = monthly_exports(EM).dropna()
    tz = IM[IM.o == "TZA"]
    NUM.update(ca_min_abs_2010_24=-ca.max(), ca_max_abs_2010_24=-ca.min(), res_2009=res[2009],
               res_max_2016_23=res.loc[2016:2023].max(), monthly_x_p10=mx.quantile(0.1),
               monthly_x_p90=mx.quantile(0.9), n_rows_exp_m=len(EM),
               tza_food_2021_23=tz[tz.y.between(2021, 2023) & (tz.cat == "Food and agriculture")].v.sum() / 3e6,
               tza_constr_2010_12=tz[tz.y.between(2010, 2012) & (tz.cat == "Construction materials and metals")].v.sum() / 3e6)
    from figures_b import pink
    p = pink()
    pa = p.groupby(p.index.year).mean()
    t = E[E.h4 == "0902"].groupby("y").agg(v=("v", "sum"), q=("q", "sum"), n=("f", "nunique"))
    r = (t.v / t.q) / pa.loc[t.index, "tea_mombasa"] * 100
    r[t.n < 3] = np.nan
    if PUBLIC:
        r[(top_share(E[E.h4 == "0902"], ["y"]) > MAX_DOM).reindex(r.index).fillna(False)] = np.nan
    NUM.update(tea_ratio_2013_16=r.loc[2013:2016].mean(), tea_ratio_2019_21=r.loc[2019:2021].mean(),
               tea_ratio_2019_21_min=r.loc[2019:2021].min())
