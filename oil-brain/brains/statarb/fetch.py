"""Download daily adjusted closes for ~118 large US stocks listed since before 2005, with a sector label.
List picked by hand from today's large caps (survivorship bias: all names survived to 2026)."""
import yfinance as yf, pandas as pd, json
SECT = {
 "IT": "AAPL MSFT INTC CSCO ORCL IBM QCOM TXN ADBE AMAT NVDA ADI MU HPQ ACN",
 "COMM": "T VZ CMCSA DIS GOOGL",
 "FIN": "JPM BAC C WFC GS MS AXP USB PNC BK SCHW MET AIG ALL TRV CB MMC",
 "HC": "JNJ PFE MRK ABT BMY LLY AMGN GILD MDT UNH CVS BDX SYK TMO CI",
 "ENE": "XOM CVX COP SLB OXY EOG HAL DVN VLO APA",
 "IND": "GE HON MMM CAT DE UNP BA LMT GD UPS FDX EMR ITW NOC CSX NSC",
 "STAP": "PG KO PEP WMT COST MO CL KMB GIS SYY KR",
 "DISC": "HD LOW MCD NKE SBUX TGT AMZN TJX F",
 "UTIL": "DUK SO D AEP EXC NEE",
 "MAT": "APD ECL NEM FCX SHW NUE",
 "RE": "SPG PSA EQR",
}
sect = {t: s for s, ts in SECT.items() for t in ts.split()}
df = yf.download(list(sect), start="2004-01-01", auto_adjust=True, progress=False, threads=True)
px = df["Close"]; vol = df["Volume"]
px.to_csv("data/close.csv"); vol.to_csv("data/volume.csv")
json.dump(sect, open("data/sectors.json", "w"), indent=0)
print(px.shape, px.index[0], px.index[-1]); print("first valid late:", px.apply(lambda s: s.first_valid_index()).sort_values().tail(5))
print("missing frac:", px.loc["2005":].isna().mean().sort_values().tail(5))
