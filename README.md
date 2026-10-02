# Burundi's firms in international trade: replication code

This repository holds the code that produces every figure, table and statistic in:

> Abalo, K. S. (2026). *Burundi's Firms in International Trade: Stylized Facts from Customs Microdata, 2010–2023*. Working paper in preparation.

The paper is not yet public and will be added here after clearance. **This repository contains code and openly licensed public inputs only. It contains no firm-level data and no results.**

The findings, interpretations and conclusions are those of the author. They do not necessarily represent the views of the World Bank, its Executive Directors, or the governments they represent.

---

## Data availability

### Confidential firm-level customs data (not included)

The analysis uses firm-level customs records for Burundi, compiled by the World Bank's **Exporter Dynamics Database (EDD)** project (Trade and International Integration Unit, Development Research Group; see Cebeci et al., 2012, and Fernandes, Freund and Pierola, 2016).
- The records were shared with the author under a confidentiality agreement.
- They **cannot be redistributed** and are not in this repository.
- Researchers who want access should contact the **EDD team at the World Bank Development Research Group**. The author cannot share the data.

The code expects three Stata files, placed by default in the folder that *contains* this repository (or in the folder named by the environment variable `BDI_DATA_DIR`):

| File | Unit of observation | Variables |
|---|---|---|
| `BDI_EXP.dta` | firm × HS6 × destination × year | `c` country, `y` year, `f` firm ID, `d` destination (ISO3), `hs` HS6 code, `v` value (US$), `q` weight (kg) |
| `BDI_EXP_monthly.dta` | firm × HS6 × destination × month | as above, plus `m` month |
| `BDI_IMP_monthly.dta` | firm × HS6 × origin × month | as above, with `o` origin (ISO3) instead of `d` |

### Public data (included, or downloaded at run time)

| Source | Use | Terms | In this repository |
|---|---|---|---|
| World Bank, World Development Indicators (API) | Macro context, balance-of-payments comparison | CC BY 4.0 | `ext/wdi_*.json` (vintage of September 2026) |
| World Bank Commodity Price Data (Pink Sheet) | Benchmark prices for coffee, tea and gold | CC BY 4.0 | `ext/pink_monthly.xlsx` |
| Natural Earth, 1:50m countries and lakes | Corridor map | Public domain | `ext/ne_*.geojson` |
| UN Comtrade public API | Partner-reported (mirror) trade | UN Comtrade terms of use | **Not redistributed.** Downloaded by `code/fetch_external.py` |

---

## Requirements

- **Python:** 3.11 or later. Tested with 3.14 on macOS. Packages are pinned in `code/requirements-lock.txt`.
- **LaTeX** is optional. It is used only when the paper source is present.

## How to run

```bash
./run_all.sh
```

The script does four things:
1. It creates a virtual environment (default `~/.venvs/burundi_trade`) and installs the pinned packages.
2. It checks that the three `.dta` files are present.
3. It downloads any missing public inputs, including the Comtrade mirror data.
4. It runs `code/build.py`, which writes all figures, tables, statistics and an Excel workbook of the chart data, and then `code/verify.py`.

To keep the data elsewhere, run:

```bash
BDI_DATA_DIR=/path/to/data ./run_all.sh
```

## Checking your results

`code/manifest.json` records SHA-256 checksums of the author's generated tables and of the data plotted in every figure. With the same EDD extract and the pinned environment, `verify.py` reports whether your build matches:

```
TABLES: 4/4 identical
FIGURE DATA (plotted values and labels): 22/22 identical
```

UN Comtrade data are downloaded at run time, so the mirror-statistics figure may differ slightly if Comtrade has revised its data.

## Code structure

| File | Purpose |
|---|---|
| `code/common.py` | Data loading, product and partner classifications, disclosure rule, chart style |
| `code/figures_a.py` | Macro context, coverage, trade structure, concentration, exporter dynamics |
| `code/figures_b.py` | Imports and forex, firm-level forex balance, corridors, DR Congo, unit values, mirror statistics, AfCFTA |
| `code/facts.py` | Other statistics quoted in the text |
| `code/workbook.py` | Excel workbook with the tables and the data behind each chart |
| `code/build.py` | Runs everything |
| `code/verify.py` | Checks outputs against the reference checksums |
| `code/fetch_external.py` | Downloads the public inputs |

## Disclosure control

All generated outputs are aggregates, and the code suppresses or merges any cell with fewer than 3 firms (`MIN_FIRMS` in `code/common.py`). That rule alone is **not** sufficient for publication. Anyone publishing outputs from the confidential data must also apply the EDD confidentiality conditions, including a dominance rule so that no single firm accounts for most of a published value.

## License

The code in this repository is released under the [MIT License](LICENSE).

The license covers the code only. The public inputs in `ext/` stay under their own terms (see *Data availability*). The confidential EDD data are not covered by it and are not included.

## References

- Cebeci, T., Fernandes, A. M., Freund, C., and Pierola, M. D. (2012). Exporter dynamics database. Policy Research Working Paper 6229, World Bank.
- Fernandes, A. M., Freund, C., and Pierola, M. D. (2016). Exporter behavior, country size and stage of development: Evidence from the exporter dynamics database. *Journal of Development Economics*, 119:121–137.
