"""Build all figures, tables and quoted numbers for the descriptive paper.

Run: python build.py   (from paper/code). Requires pandas, pyreadstat, matplotlib, geopandas, openpyxl.
"""
import sys

from common import NUM, PUBLIC, SUPPRESSED, load, save_numbers, set_style
import figures_a as A
import figures_b as B
import facts as F
import workbook as W

try:  # internal-only exhibits (not in the public package)
    import internal_exhibits as X
except ImportError:
    X = None


def main(only=None):
    set_style()
    from common import FIG, TAB
    for p in list(FIG.glob("*.pdf")) + list((FIG / "data").glob("*.json")) + list(TAB.glob("*.tex")):
        p.unlink()          # start clean so no stale exhibit survives
    E, EM, IM = load()
    A.fig_macro()
    A.fig_coverage(E, IM)
    A.table_summary(E, IM)
    A.fig_export_structure(E)
    A.fig_import_structure(IM)
    A.fig_concentration(E, IM)
    A.fig_size_classes(E, IM)
    A.fig_granular(E, EM)
    A.fig_entry_exit(E)
    A.fig_stepping_stone(E)
    A.table_margins(E)
    B.fig_monthly_imports(IM, E)
    B.fig_import_categories(IM)
    B.fig_importer_margins(IM)
    xm = B.fig_fx_balance(E, IM)
    B.fig_corridor_map(IM)
    B.fig_regional_sourcing(IM)
    B.fig_drc(E, IM)
    if X is not None and not PUBLIC:
        X.run(E, IM)
    B.fig_unit_values(E, EM)
    B.fig_mirror(E, IM)
    B.fig_afcfta(E, IM, xm)
    F.text_facts(E, EM, IM)
    B.fig_glance()
    save_numbers()
    if PUBLIC:
        import public_paper
        public_paper.write()
    path, n = W.build()
    print(f"workbook: {path.name} ({n} sheets + contents)")
    for k, v in NUM.items():
        print(f"{k:32s} {v:.2f}" if isinstance(v, float) else f"{k:32s} {v}")
    print("\nDISCLOSURE LOG:")
    for s in SUPPRESSED:
        print(" ", s)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
