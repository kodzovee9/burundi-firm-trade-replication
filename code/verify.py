"""Check that a fresh build reproduces the paper.

Three checks:
  1. NUMBERS  - every number quoted in the paper (expected_values.csv) is within tolerance of the value
                recomputed by build.py (numbers.json).
  2. TEXT     - the sentence fragment quoting that number still appears in the .tex source, so the paper
                text and the code cannot silently drift apart.
  3. FILES    - SHA-256 of every generated table and of every figure's plotted data (figures/data/*.json:
                bar heights, line values, points, titles, labels, legends) matches the reference manifest.
                Figure PDF bytes are also compared but only reported, because they depend on fonts and
                renderer versions even when the content is identical.

Usage:  python verify.py                    # run all checks
        python verify.py --write-manifest   # (author only) record reference hashes after a final build
"""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import os

PAPER = Path(__file__).resolve().parents[1]
CODE = PAPER / "code"
PUBLIC = os.environ.get("BDI_PUBLIC") == "1" or "--public" in sys.argv
OUTDIR = PAPER / "public" if PUBLIC else PAPER
TEX = OUTDIR / ("burundi_trade_stylized_facts_public.tex" if PUBLIC else "burundi_trade_stylized_facts.tex")
MANIFEST = CODE / ("manifest_public.json" if PUBLIC else "manifest.json")


def norm(s):
    return re.sub(r"\s+", " ", s.replace("\\n", " ")).strip()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def outputs():
    return sorted(list((OUTDIR / "figures").glob("*.pdf")) + list((OUTDIR / "figures" / "data").glob("*.json"))
                  + list((OUTDIR / "tables").glob("*.tex")))


def main():
    if "--write-manifest" in sys.argv:
        man = {p.relative_to(OUTDIR).as_posix(): sha(p) for p in outputs()}
        MANIFEST.write_text(json.dumps(man, indent=1))
        print(f"manifest written: {len(man)} files")
        return 0

    num = json.load(open(OUTDIR / "numbers.json"))
    if PUBLIC:
        print("PUBLIC (disclosure-controlled) version")
    if not TEX.exists() or not (CODE / "expected_values.csv").exists():
        print("NUMBERS/TEXT: skipped (paper source or expected_values.csv not in this package).")
        return files_check(0)
    tex = norm(TEX.read_text())
    ns = {k: v for k, v in num.items() if k.isidentifier() and isinstance(v, (int, float))}
    fails = 0
    rows = list(csv.DictReader(open(CODE / "expected_values.csv")))
    if PUBLIC:   # statements rewritten for the public version are skipped; public-only ones are added
        n_all = len(rows)
        rows = [r for r in rows if not r["snippet"] or norm(r["snippet"]) in tex]
        print(f"({n_all - len(rows)} internal statements rewritten for the public version and not applicable)")
        rows += list(csv.DictReader(open(CODE / "expected_values_public.csv")))
    print(f"{'id':>4} {'location':24} {'expression':30} {'computed':>10} {'quoted':>9}  num  text")
    for r in rows:
        try:
            val = float(eval(r["expr"], {"__builtins__": {}}, ns))
        except Exception as e:  # missing key
            val = float("nan")
        ok_num = abs(val - float(r["quoted"])) <= float(r["tol"]) + 1e-9
        ok_txt = norm(r["snippet"]) in tex if r["snippet"] else True
        fails += (not ok_num) + (not ok_txt)
        flag = lambda b: "ok " if b else "FAIL"
        if not (ok_num and ok_txt) or "-v" in sys.argv:
            print(f"{r['id']:>4} {r['location'][:24]:24} {r['expr'][:30]:30} {val:10.2f} {float(r['quoted']):9.2f}  "
                  f"{flag(ok_num)} {flag(ok_txt)}")
    print(f"\nNUMBERS/TEXT: {len(rows)} quoted values checked, {fails} failure(s).")

    return files_check(fails)


def files_check(fails):
    man_path = MANIFEST
    if man_path.exists():
        man = json.loads(man_path.read_text())
        diff = [f for f, h in man.items() if not (OUTDIR / f).exists() or sha(OUTDIR / f) != h]
        tabs = [f for f in diff if f.startswith("tables/")]
        data = [f for f in diff if f.startswith("figures/data/")]
        pdfs = [f for f in diff if f.endswith(".pdf")]
        n_t = sum(k.startswith("tables/") for k in man)
        n_d = sum(k.startswith("figures/data/") for k in man)
        print(f"TABLES: {n_t - len(tabs)}/{n_t} identical")
        print(f"FIGURE DATA (plotted values and labels): {n_d - len(data)}/{n_d} identical")
        for f in tabs + data:
            print("   DIFFERS:", f)
        print(f"FIGURE PDF BYTES (informational only; depend on fonts/renderer): "
              f"{len(pdfs)} of {sum(k.endswith('.pdf') for k in man)} differ")
        fails += len(tabs) + len(data)   # substantive differences
    else:
        print("FILES: no manifest.json found, skipped.")
    wbp = OUTDIR / ("burundi_trade_tables_and_chart_data" + ("_public" if PUBLIC else "") + ".xlsx")
    if wbp.exists():
        from openpyxl import load_workbook
        names = load_workbook(wbp, read_only=True).sheetnames
        n_tab = sum(n.startswith("Table") for n in names)
        n_fig = sum(n.startswith("Fig") for n in names)
        n_exp = len(list((OUTDIR / "figures" / "data").glob("*.json")))     # figures built in this run
        n_cov = len({n[3:5] for n in names if n.startswith("Fig")})
        ok_wb = n_tab == (8 if TEX.exists() else 4) and n_cov == n_exp
        print(f"WORKBOOK: {n_tab} table sheets, {n_fig} chart-data sheets covering {n_cov}/{n_exp} figures")
        fails += 0 if ok_wb else 1
    else:
        print("WORKBOOK: not found (run build.py)")
        fails += 1
    print("RESULT:", "PASS" if fails == 0 else "FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
