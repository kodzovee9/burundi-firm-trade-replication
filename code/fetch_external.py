"""Download the public (non-confidential) inputs used by build.py into paper/ext/.

The paper was built from the copies downloaded on 29 September 2026, which are shipped in paper/ext/.
Re-running this script replaces them with the latest vintages: WDI, Pink Sheet and Comtrade data are
revised over time, so a refresh can move some numbers slightly (see REPLICATION_GUIDE.md, section 6).

Usage:  python fetch_external.py            # download only files that are missing
        python fetch_external.py --refresh  # re-download everything
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

EXT = Path(__file__).resolve().parents[1] / "ext"
EXT.mkdir(exist_ok=True)
REFRESH = "--refresh" in sys.argv
UA = {"User-Agent": "Mozilla/5.0 (research replication)"}

WDI = ["PA.NUS.FCRF", "BM.GSR.MRCH.CD", "BX.GSR.MRCH.CD", "FI.RES.TOTL.MO", "BN.CAB.XOKA.GD.ZS",
       "NY.GDP.MKTP.CD", "FI.RES.TOTL.CD", "DT.ODA.ODAT.CD", "NY.GDP.PCAP.CD", "BN.CAB.XOKA.CD"]
PINK = ("https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/"
        "related/CMO-Historical-Data-Monthly.xlsx")
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
COMTRADE = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"


def get(url, tries=8, wait=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # rate limits (HTTP 429) and transient errors
            print(f"  retry {i + 1}/{tries}: {e}")
            time.sleep(wait)
    raise RuntimeError(f"failed: {url}")


def need(path):
    return REFRESH or not path.exists() or path.stat().st_size == 0


def main():
    for code in WDI:
        p = EXT / f"wdi_{code}.json"
        if need(p):
            print("WDI", code)
            p.write_bytes(get(f"https://api.worldbank.org/v2/country/BDI/indicator/{code}"
                              f"?format=json&date=2005:2025&per_page=100"))
    p = EXT / "pink_monthly.xlsx"
    if need(p):
        print("Pink Sheet")
        p.write_bytes(get(PINK))
    for name in ["ne_50m_admin_0_countries", "ne_50m_lakes"]:
        p = EXT / ("ne_countries.geojson" if "countries" in name else "ne_lakes.geojson")
        if need(p):
            print("Natural Earth", name)
            p.write_bytes(get(NE + name + ".geojson"))
    # UN Comtrade public preview API: one period per call, max 500 records per call.
    p = EXT / "comtrade_mirror.json"
    if need(p):
        out = []
        for y in range(2010, 2024):
            for flow, cmds in [("M", "TOTAL"), ("M", "0901,0902,7108"), ("M", "2615,2609,2611,2616"),
                               ("X", "TOTAL")]:
                raw = get(f"{COMTRADE}?period={y}&partnerCode=108&cmdCode={cmds}&flowCode={flow}")
                out += json.loads(raw).get("data", [])
                time.sleep(2.5)
            print("Comtrade", y, len(out))
        p.write_text(json.dumps(out))
    print("done:", sorted(x.name for x in EXT.iterdir()))


if __name__ == "__main__":
    main()
