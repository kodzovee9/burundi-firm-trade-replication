#!/usr/bin/env bash
# One-command replication of "Burundi's Firms in International Trade" (descriptive paper).
#   ./run_all.sh            build figures/tables/numbers, verify, compile the PDF
#   SKIP_PDF=1 ./run_all.sh  skip the LaTeX step
# The Python environment is created OUTSIDE OneDrive (default ~/.venvs/burundi_trade) to avoid syncing it.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
VENV="${VENV:-$HOME/.venvs/burundi_trade}"

echo "== 1/5 Python environment: $VENV"
if [ ! -x "$VENV/bin/python" ]; then
  "$PY" -m venv "$VENV"
  "$VENV/bin/pip" install --upgrade pip -q
  "$VENV/bin/pip" install -q -r code/requirements-lock.txt || "$VENV/bin/pip" install -q -r code/requirements.txt
fi

echo "== 2/5 Check confidential inputs"
for f in BDI_EXP.dta BDI_EXP_monthly.dta BDI_IMP_monthly.dta; do
  [ -s "${BDI_DATA_DIR:-..}/$f" ] || { echo "Missing or empty ${BDI_DATA_DIR:-..}/$f (set BDI_DATA_DIR, or check OneDrive sync)"; exit 1; }
done

echo "== 3/5 Public inputs (uses cached copies in ext/; add --refresh to re-download)"
(cd code && "$VENV/bin/python" fetch_external.py)

echo "== 4/5 Build figures, tables and numbers (log: code/build_log.txt)"
(cd code && "$VENV/bin/python" build.py > build_log.txt)

echo "== 5/5 Verify against the paper"
(cd code && "$VENV/bin/python" verify.py) || echo "!! verification reported differences (see above)"
if [ "${BDI_PUBLIC:-0}" = "1" ]; then
  echo "== Independent disclosure audit (public version)"
  (cd code && "$VENV/bin/python" audit_public.py) || echo "!! DISCLOSURE AUDIT FAILED - do not release"
fi

TEXDIR=.; TEXNAME=burundi_trade_stylized_facts
if [ "${BDI_PUBLIC:-0}" = "1" ]; then TEXDIR=public; TEXNAME=burundi_trade_stylized_facts_public; fi
if [ "${SKIP_PDF:-0}" != "1" ] && [ -f "$TEXDIR/$TEXNAME.tex" ]; then
  cd "$TEXDIR"
  echo "== Compile PDF"
  find . -maxdepth 1 \( -name "$TEXNAME.aux" -o -name "$TEXNAME.fdb_latexmk" \) -delete
  latexmk -pdf -interaction=nonstopmode -halt-on-error "$TEXNAME.tex" > latex_log.txt 2>&1 \
    && latexmk -c "$TEXNAME.tex" > /dev/null 2>&1 \
    && echo "PDF: $TEXDIR/$TEXNAME.pdf" \
    || echo "!! LaTeX failed; see $TEXDIR/latex_log.txt"
fi
