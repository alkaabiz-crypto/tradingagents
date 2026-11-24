"""Fetch data for the earnings brain (run once).

Universe: fixed list of ~90 large US stocks chosen 2026-11-24 from today's S&P 100-type names that
were public before 2005. SURVIVORSHIP BIAS: the list is built from today's survivors; long/short
rules are less affected than long-only ones, but the bias is real and stated in BRAIN.md.

Earnings dates: SEC EDGAR 8-K filings with Item 2.02 (Results of Operations), from
data.sec.gov submissions JSON (acceptanceDateTime, Eastern time despite the 'Z').
Prices: Yahoo daily auto-adjusted closes 2004-now.
"""
import json, os, time, urllib.request
import pandas as pd
import yfinance as yf

H = os.path.dirname(os.path.abspath(__file__))
DD = os.path.join(H, "data")
UA = {"User-Agent": "research-bot contact@example.com"}
UNIVERSE = """AAPL MSFT NVDA AMZN GOOGL JPM JNJ XOM PG HD CVX MRK PFE KO PEP WMT CSCO INTC ORCL IBM
T VZ BAC WFC C GS MS AXP UNH ABT MDT AMGN GILD BMY LLY TMO DHR MMM HON CAT DE GE BA LMT RTX UNP
UPS FDX NKE MCD SBUX TGT LOW COST DIS CMCSA QCOM TXN ADBE CRM ACN BNY USB MO CL KMB GIS EMR ADP
NEE DUK SO EXC COP SLB OXY EOG MET AIG ALL TRV SPG BKNG AMD MU AMAT ADI INTU NFLX EBAY BIIB VRTX
ISRG""".split()


# Older CIKs of the same business before holding-company reorganisations / renames.
EXTRA_CIK = {"GOOGL": [1288776], "XOM": [34088], "MDT": [64670], "DIS": [1001039],
             "ACN": [1134538], "ORCL": [777676], "BNY": [9626]}


def get(url):
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            print("retry", url, e)
            time.sleep(2 + 2 * i)
    raise RuntimeError(url)


def filings(cik):
    j = get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
    frames = [pd.DataFrame(j["filings"]["recent"])]
    for f in j["filings"].get("files", []):
        time.sleep(0.15)
        frames.append(pd.DataFrame(get("https://data.sec.gov/submissions/" + f["name"])))
    df = pd.concat(frames, ignore_index=True)
    return df


def main():
    tick = json.load(open(os.path.join(DD, "company_tickers.json")))
    cikmap = {v["ticker"]: int(v["cik_str"]) for v in tick.values()}
    rows = []
    for t in UNIVERSE:
        cache = os.path.join(DD, "sub", t + ".csv")
        if os.path.exists(cache):
            df = pd.read_csv(cache)
        else:
            df = pd.concat([filings(c) for c in [cikmap[t]] + EXTRA_CIK.get(t, [])],
                           ignore_index=True)
            os.makedirs(os.path.dirname(cache), exist_ok=True)
            df[["form", "items", "acceptanceDateTime", "filingDate"]].to_csv(cache, index=False)
        cik = cikmap[t]
        m = df["form"].isin(["8-K", "8-K/A"]) & df["items"].astype(str).str.contains("2.02")
        d = df.loc[m & (df["form"] == "8-K"), ["acceptanceDateTime", "filingDate", "items"]].copy()
        d["ticker"] = t
        rows.append(d)
        print(t, cik, len(d), d["filingDate"].min() if len(d) else None)
        time.sleep(0.15)
    ev = pd.concat(rows, ignore_index=True)
    ev.to_csv(os.path.join(DD, "edgar_202.csv"), index=False)
    px = yf.download(UNIVERSE + ["SPY"], start="2004-01-01", auto_adjust=True, progress=False)
    px["Close"].to_csv(os.path.join(DD, "close.csv"))
    px["Open"].to_csv(os.path.join(DD, "open.csv"))
    print(px["Close"].notna().sum().sort_values().head(10))


if __name__ == "__main__":
    main()
