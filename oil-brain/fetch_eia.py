"""Download EIA weekly petroleum series (www.eia.gov history spreadsheets, no key) into data/EIA_weekly.csv.
Values are thousand barrels (stocks), thousand barrels/day (flows) or percent (refinery utilization).
Dates are the week-ending Friday; the report is released the following Wednesday 10:30 ET
(5 days later; later in holiday weeks), so a signal can use a week only from that Wednesday."""
import io, os, time, requests, pandas as pd
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
S = {"crude_ex_spr": "WCESTUS1", "spr": "WCSSTUS1", "cushing": "W_EPC0_SAX_YCUOK_MBBL",
     "production": "WCRFPUS2", "refinery_util": "WPULEUS3", "gasoline": "WGTSTUS1",
     "distillate": "WDISTUS1", "exports": "WCREXUS2", "imports": "WCRIMUS2", "product_supplied": "WRPUPUS2"}
out = {}
for name, sid in S.items():
    url = f"https://www.eia.gov/dnav/pet/hist_xls/{sid}w.xls"
    for k in range(3):
        try:
            x = requests.get(url, timeout=60, headers={"User-Agent": "research-bot"}); x.raise_for_status()
            df = pd.read_excel(io.BytesIO(x.content), sheet_name="Data 1", skiprows=2)
            s = df.set_index(df.columns[0]).iloc[:, 0]; s.index = pd.to_datetime(s.index)
            out[name] = s; print(name, len(s), s.index[0].date(), s.index[-1].date(), s.iloc[-1]); break
        except Exception as e:
            print(name, "retry", e); time.sleep(3)
pd.DataFrame(out).sort_index().to_csv(os.path.join(D, "EIA_weekly.csv"))
