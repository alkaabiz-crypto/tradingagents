"""Download CFTC Commitments of Traders for WTI crude (NYMEX code 067651) into data/.
Legacy (commercial / non-commercial) and disaggregated (producer, swap, managed money)."""
import os, io, requests, pandas as pd
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
for name, ds, cols in [("COT_legacy_WTI", "6dca-aqww", "report_date_as_yyyy_mm_dd,open_interest_all,comm_positions_long_all,comm_positions_short_all,noncomm_positions_long_all,noncomm_positions_short_all"),
                       ("COT_disagg_WTI", "72hh-3qpy", "report_date_as_yyyy_mm_dd,open_interest_all,prod_merc_positions_long,prod_merc_positions_short,swap_positions_long_all,swap__positions_short_all,m_money_positions_long_all,m_money_positions_short_all")]:
    url = f"https://publicreporting.cftc.gov/resource/{ds}.csv"
    q = {"$select": cols, "$where": "cftc_contract_market_code='067651'", "$order": "report_date_as_yyyy_mm_dd", "$limit": 50000}
    df = pd.read_csv(io.StringIO(requests.get(url, params=q, timeout=120).text))
    df["date"] = pd.to_datetime(df.pop("report_date_as_yyyy_mm_dd")).dt.date
    df.set_index("date").to_csv(os.path.join(D, name + ".csv"))
    print(name, len(df), df.date.min(), df.date.max())
