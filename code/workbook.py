"""Write all paper tables and the data behind every chart to one Excel workbook.

Tables 2-5 and all chart data come from the registries filled by build.py (TABLE_DATA, CHART_DATA);
hand-written Tables 1, 6, 7 and 8 are parsed from the paper's .tex source so they always match the PDF.
"""
import re
from datetime import date

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from common import CHART_DATA, OUT, PUBLIC, TABLE_DATA, TEX_FILE

TEX = TEX_FILE
OUT_XLSX = OUT / ("burundi_trade_tables_and_chart_data" + ("_public" if PUBLIC else "") + ".xlsx")

FONT = "Arial"
NAVY = "184F95"
F_TITLE = Font(name=FONT, size=12, bold=True, color=NAVY)
F_SUB = Font(name=FONT, size=9, italic=True, color="52514E")
F_HEAD = Font(name=FONT, size=10, bold=True, color="FFFFFF")
F_BODY = Font(name=FONT, size=10)
F_BOLD = Font(name=FONT, size=10, bold=True)
F_LINK = Font(name=FONT, size=9, color="0563C1", underline="single")
F_WARN = Font(name=FONT, size=9, bold=True, color="C0392B")
FILL_HEAD = PatternFill("solid", fgColor=NAVY)
FILL_BAND = PatternFill("solid", fgColor="F4F3EF")
THIN = Side(style="thin", color="C3C2B7")
SRC = "Source: Author's calculations based on Burundi firm-level customs data (World Bank Exporter Dynamics Database)."
CONF = ("PUBLIC VERSION - disclosure-controlled aggregates (at least 3 firms, no firm above 85% of any cell)."
        if PUBLIC else "CONFIDENTIAL - aggregates from EDD firm-level microdata - WBG internal use only (see Confidentiality Notice, 8 Oct 2024).")


# ------------------------------------------------------------------ LaTeX parsing
def clean(s):
    s = s.strip()
    for a, b in [(r"\%", "%"), (r"\$", "$"), (r"\&", "&"), ("$\\times$", "×"), ("$\\sim$", "≈"), ("$-$", "−"),
                 ("$\\rightarrow$", "→"), ("---", "—"), ("--", "–"), ("\\ ", " "), ("~", " "), ("``", '"'),
                 ("''", '"'), ("\\,", " ")]:
        s = s.replace(a, b)
    s = re.sub(r"\\(textit|textbf|emph)\{([^}]*)\}", r"\2", s)
    s = re.sub(r"\\multicolumn\{\d+\}\{[^}]*\}\{(.*)\}", r"\1", s)
    s = s.replace("{", "").replace("}", "").replace("$", "$")
    return re.sub(r"\s+", " ", s).strip()


def tex_table(caption_start):
    if not TEX.exists():
        return None, None
    tex = TEX.read_text()
    i = tex.index("\\caption{" + caption_start)
    cap = re.match(r"\\caption\{([^}]*)\}", tex[i:]).group(1)
    body = tex[i:tex.index("\\end{table}", i)]
    head = body[body.index("\\toprule") + 8:body.index("\\midrule")]
    rows = body[body.index("\\midrule") + 8:body.index("\\bottomrule")]
    cols = [clean(c) for c in head.replace("\\\\", "").split("&")]
    out = []
    for r in rows.split("\\\\"):
        r = r.replace("\\midrule", "").strip()
        if not r:
            continue
        cells = [clean(c) for c in r.split("&")]
        out.append(cells + [""] * (len(cols) - len(cells)))
    return clean(cap), pd.DataFrame(out, columns=cols).set_index(cols[0])


def captions():
    if not TEX.exists():
        return {}
    tex = TEX.read_text()
    figs = re.findall(r"\\fig\{(f\d\d)_[a-z_]+\}\{([^}]*)\}", tex)
    return {i + 1: clean(c) for i, (_, c) in enumerate(figs)}


# ------------------------------------------------------------------ sheet writer
def autosize(ws, ncols, first_width=None):
    for j in range(1, ncols + 1):
        col = get_column_letter(j)
        width = max((len(str(c.value)) for c in ws[col][5:] if c.value is not None), default=8)
        ws.column_dimensions[col].width = min(max(width + 2, 10), 60)
    if first_width:
        ws.column_dimensions["A"].width = first_width


def write_sheet(wb, name, title, df, unit="", note="", source=SRC, text_table=False):
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    ws["A1"] = title
    ws["A1"].font = F_TITLE
    ws["A2"] = f"Unit: {unit}" if unit else ""
    ws["A2"].font = F_SUB
    ws["A3"] = note
    ws["A3"].font = F_SUB
    ws["A4"] = source
    ws["A4"].font = F_SUB
    link = ws.cell(row=1, column=max(len(df.columns) + 1, 3) + 1, value="← Contents")
    link.hyperlink = "#'Contents'!A1"
    link.font = F_LINK
    r0 = 6
    headers = [df.index.name or ""] + list(df.columns)
    for j, h in enumerate(headers, 1):
        c = ws.cell(row=r0, column=j, value=str(h))
        c.font, c.fill = F_HEAD, FILL_HEAD
        c.alignment = Alignment(horizontal="left" if j == 1 or text_table else "center", vertical="center",
                                wrap_text=True)
    for i, (idx, row) in enumerate(df.iterrows(), 1):
        r = r0 + i
        vals = [idx] + list(row.values)
        is_section = text_table and all((v == "" or v is None) for v in vals[1:])
        for j, v in enumerate(vals, 1):
            if isinstance(v, (np.integer,)):
                v = int(v)
            elif isinstance(v, (np.floating, float)):
                v = None if not np.isfinite(v) else float(v)
            c = ws.cell(row=r, column=j, value=v)
            c.font = F_BOLD if (j == 1 and not text_table) or is_section else F_BODY
            c.border = Border(bottom=THIN)
            if j == 1:
                c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=text_table)
            if text_table:
                c.alignment = Alignment(wrap_text=True, vertical="top")
            elif isinstance(v, float):
                c.number_format = "#,##0.0" if abs(v) < 1e5 else "#,##0"
                if float(v).is_integer() and abs(v) >= 100:
                    c.number_format = "#,##0"
            elif isinstance(v, int) and j > 1:
                c.number_format = "#,##0"
            if i % 2 == 0:
                c.fill = FILL_BAND
    ws.freeze_panes = ws.cell(row=r0 + 1, column=2)
    autosize(ws, len(headers))
    if text_table:
        for j in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(j)].width = 22 if j == 1 else 45
    return ws


def build():
    wb = Workbook()
    toc = wb.active
    toc.title = "Contents"
    toc.sheet_view.showGridLines = False
    toc["A1"] = "Burundi's Firms in International Trade: Tables and chart data"
    toc["A1"].font = Font(name=FONT, size=14, bold=True, color=NAVY)
    toc["A2"] = CONF
    toc["A2"].font = F_WARN
    toc["A3"] = (f"Companion workbook to the paper (draft, September 2026). Generated by paper/code/build.py on "
                 f"{date.today():%d %B %Y}. One sheet per table and one per chart panel. Values are computed "
                 "(not typed) and match the paper; all cells aggregate at least 3 firms.")
    toc["A3"].font = F_SUB
    heads = ["Sheet", "Type", "Paper reference", "Title", "Unit"]
    for j, h in enumerate(heads, 1):
        c = toc.cell(row=5, column=j, value=h)
        c.font, c.fill = F_HEAD, FILL_HEAD
    entries = []

    # Tables 1-8 in paper order
    hand = {1: "The Burundi firm-level customs data", 6: "Challenges and opportunities", 7: "A research agenda",
            8: "Product and partner groupings"}
    for no in range(1, 9):
        name = f"Table{no:02d}"
        if no in hand:
            cap, df = tex_table(hand[no])
            if df is None:
                continue
            write_sheet(wb, name, f"Table {no}. {cap}", df, note="Text table reproduced from the paper.",
                        source="Source: " + TEX.name, text_table=True)
            entries.append((name, "Table", f"Table {no}", cap, ""))
        else:
            t = TABLE_DATA[no]
            write_sheet(wb, name, f"Table {no}. {t['title']}", t["df"], note=t["note"])
            entries.append((name, "Table", f"Table {no}", t["title"], ""))

    # Chart data, one sheet per panel
    caps = captions()
    # number figures in paper order among those actually built (some exhibits are internal-only)
    renum = {f: i + 1 for i, f in enumerate(sorted({r["fig"] for r in CHART_DATA}))}
    for rec in CHART_DATA:
        rec["fig"] = renum[rec["fig"]]
    for rec in sorted(CHART_DATA, key=lambda r: (r["fig"], r["panel"])):
        name = f"Fig{rec['fig']:02d}{rec['panel']}"
        ref = f"Figure {rec['fig']}" + (f", panel ({rec['panel']})" if rec["panel"] else "")
        title = f"{ref}. {caps.get(rec['fig'], '')}: {rec['title']}"
        src = "Source: World Bank, World Development Indicators." if rec["fig"] == 2 else SRC
        write_sheet(wb, name, title, rec["df"], unit=rec["unit"], note=rec["note"], source=src)
        entries.append((name, "Chart data", ref, f"{caps.get(rec['fig'], '')}: {rec['title']}", rec["unit"]))

    for i, e in enumerate(entries, 6):
        for j, v in enumerate(e, 1):
            c = toc.cell(row=i, column=j, value=v)
            c.font = F_BODY
            c.border = Border(bottom=THIN)
        toc.cell(row=i, column=1).hyperlink = f"#'{e[0]}'!A1"
        toc.cell(row=i, column=1).font = F_LINK
    for col, w in zip("ABCDE", [11, 11, 22, 95, 30]):
        toc.column_dimensions[col].width = w
    toc.freeze_panes = "A6"
    for ws in wb.worksheets:
        ws.sheet_properties.pageSetUpPr.fitToPage = True
    wb.save(OUT_XLSX)
    return OUT_XLSX, len(entries)
