"""Download SEC 'Insider Transactions Data Sets' (Form 3/4/5, quarterly zips 2006q1..now),
keep only Form 4 non-derivative open-market trades (codes P and S) for the ~800 largest
companies in today's SEC company_tickers.json (ordered by size), delete each zip after use.
Output: data/trades.csv.gz, data/issuers_seen.csv
"""
import io, json, os, time, zipfile, re
import pandas as pd
import requests

H = {"User-Agent": "research-bot contact@example.com"}
HERE = os.path.dirname(os.path.abspath(__file__))
RAW, DATA = os.path.join(HERE, "raw"), os.path.join(HERE, "data")

tick = json.load(open(os.path.join(DATA, "company_tickers.json")))
seen, cands = set(), []
for v in tick.values():
    if v["cik_str"] in seen:
        continue
    seen.add(v["cik_str"]); cands.append((v["cik_str"], v["ticker"], v["title"]))
cands = cands[:800]
pd.DataFrame(cands, columns=["cik", "ticker", "title"]).to_csv(os.path.join(DATA, "candidates.csv"), index=False)
CIKS = {c[0] for c in cands}

links = re.findall(r'href="([^"]*_form345\.zip)"', open(os.path.join(RAW, "links.txt")).read())
out, issuers = [], []
for ln in sorted(set(links)):
    q = ln.split("/")[-1][:6]
    f = os.path.join(DATA, f"part_{q}.csv.gz")
    if os.path.exists(f):
        out.append(pd.read_csv(f)); continue
    for attempt in range(3):
        r = requests.get("https://www.sec.gov" + ln, headers=H, timeout=120)
        if r.status_code == 200:
            break
        time.sleep(2)
    time.sleep(0.3)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    rd = lambda n, cols: pd.read_csv(z.open(n), sep="\t", usecols=cols, dtype=str, quoting=3,
                                     on_bad_lines="skip", encoding="latin-1")
    sub = rd("SUBMISSION.tsv", ["ACCESSION_NUMBER", "FILING_DATE", "DOCUMENT_TYPE", "ISSUERCIK",
                                "ISSUERTRADINGSYMBOL"])
    sub = sub[sub.DOCUMENT_TYPE == "4"].copy()
    sub["ISSUERCIK"] = pd.to_numeric(sub.ISSUERCIK, errors="coerce")
    issuers.append(sub.ISSUERCIK.dropna().astype(int).unique())
    sub = sub[sub.ISSUERCIK.isin(CIKS)]
    tr = rd("NONDERIV_TRANS.tsv", ["ACCESSION_NUMBER", "TRANS_DATE", "TRANS_CODE", "TRANS_SHARES",
                                   "TRANS_PRICEPERSHARE", "TRANS_ACQUIRED_DISP_CD",
                                   "SHRS_OWND_FOLWNG_TRANS"])
    tr = tr[tr.TRANS_CODE.isin(["P", "S"])]
    ow = rd("REPORTINGOWNER.tsv", ["ACCESSION_NUMBER", "RPTOWNERCIK", "RPTOWNER_RELATIONSHIP",
                                   "RPTOWNER_TITLE"])
    ow = ow.drop_duplicates("ACCESSION_NUMBER")  # first reporting owner per filing
    m = sub.merge(tr, on="ACCESSION_NUMBER").merge(ow, on="ACCESSION_NUMBER", how="left")
    m.to_csv(f, index=False, compression="gzip")
    out.append(m)
    print(q, len(sub), len(m), flush=True)
    del r, z
allt = pd.concat(out, ignore_index=True)
allt.to_csv(os.path.join(DATA, "trades.csv.gz"), index=False, compression="gzip")
if issuers:
    import numpy as np
    pd.Series(np.unique(np.concatenate(issuers))).to_csv(os.path.join(DATA, "issuers_seen.csv"), index=False)
print("total rows", len(allt))
