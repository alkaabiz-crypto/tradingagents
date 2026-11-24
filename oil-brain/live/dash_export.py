"""Write the dashboard's data files (JSON {rows, meta}) from the live paper book and the tournament.

python3 oil-brain/live/dash_export.py  ->  live/dash/{book,equity,scoreboard,audit}.json
"""
import json, os, glob

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.dirname(HERE)
OUT = os.path.join(HERE, "dash"); os.makedirs(OUT, exist_ok=True)
st = json.load(open(os.path.join(HERE, "state.json")))
ALLOC = {"IEF_MONTH_END": 3000, "BTC_TREND": 2500, "ETH_TREND": 1500, "USO_FOLLOW": 3000}
NICE = {"IEF_MONTH_END": "Month-end Treasuries", "BTC_TREND": "Bitcoin trend", "ETH_TREND": "Ether trend",
        "USO_FOLLOW": "Follow big oil days"}
book = []
for k, s in st["sleeves"].items():
    tgt = s.get("target", 0)
    book.append(dict(strategy=NICE[k], symbol=s["symbol"], start_usd=ALLOC[k], equity_usd=s.get("equity", ALLOC[k]),
                     pnl_usd=round(s.get("equity", ALLOC[k]) - ALLOC[k], 2),
                     position="Long" if tgt > 0 else "Short" if tgt < 0 else "Cash",
                     reason=s.get("reason", ""), price_date=s.get("last_date", "")))
ta_path = os.path.join(HERE, "ta_state.json")
if os.path.exists(ta_path):
    ta = json.load(open(ta_path)); last = ta["history"][-1] if ta.get("history") else {}
    for bk, nm in (("long_only", "TradingAgents verdicts (long-only)"), ("long_short", "TradingAgents verdicts (long/short)")):
        tg = {t: (max(v, 0) if bk == "long_only" else v) for t, v in ta["target"].items()}
        held = ", ".join(f"{t} {v:+.1f}" for t, v in tg.items() if v) or "all cash"
        book.append(dict(strategy=nm, symbol="SPY QQQ NVDA XLE GLD", start_usd=5000, equity_usd=last.get(bk, 5000),
                         pnl_usd=round(last.get(bk, 5000) - 5000, 2), position="Long" if any(v > 0 for v in tg.values()) else "Cash",
                         reason=f"targets: {held}; buy-and-hold ${last.get('benchmark', 5000):,.0f}", price_date=ta.get("last_mark", "")))
meta = [{"label": "Paper book updated", "value": st.get("updated", "")},
        {"label": "Started", "value": st["start"]}, {"label": "Rules", "value": "oil-brain/live/paper_book.py"}]
json.dump({"rows": book, "meta": meta}, open(os.path.join(OUT, "book.json"), "w"), indent=1)
json.dump({"rows": st["history"], "meta": meta}, open(os.path.join(OUT, "equity.json"), "w"), indent=1)

score = []
for f in sorted(glob.glob(os.path.join(OB, "brains", "*", "scorecard.json"))):
    s = json.load(open(f)); b = s.get("best") or {}
    score.append(dict(brain=s["brain"], rules=s.get("rules_tried"), best_rule=(s.get("best_rule") or "")[:140],
                      post_sharpe=b.get("post"), t_stat=b.get("t_post"),
                      winners=len(s.get("winners") or []), candidates=len(s.get("candidates") or [])))
sw = json.load(open(os.path.join(OB, "swarm", "swarm_summary.json")))
score.append(dict(brain="swarm", rules=sw["rules"], best_rule="BTC above its 100-day average (4 BTC trend rules beat the luck bar)",
                  post_sharpe=1.35, t_stat=4.69, winners=sw["n_swarm_winners"], candidates=0))
json.dump({"rows": score, "meta": [{"label": "Luck bar (best of 2,784 rules, 95%)", "value": sw["luck_bar_t95"]},
                                   {"label": "Source", "value": "oil-brain/brains/*/scorecard.json, oil-brain/swarm/swarm_summary.json"}]},
          open(os.path.join(OUT, "scoreboard.json"), "w"), indent=1)

audit = [
    dict(rule="Month-end Treasuries (IEF, last 3 days)", verdict="Weak", sharpe_after_costs=0.60, t_stat=2.97,
         note="Real before costs (t 5.4); thin after costs; needs closing-price fills"),
    dict(rule="Bitcoin trend (28-day / 100-day)", verdict="Weak", sharpe_after_costs=1.09, t_stat=3.76,
         note="Cuts crashes (-48% vs -67% since 2022); no extra return since 2022"),
    dict(rule="Ether trend (28-day)", verdict="Weak", sharpe_after_costs=0.82, t_stat=2.42,
         note="60% of profit from 5 months"),
    dict(rule="Credit appetite -> oil (HYG-LQD -> USO)", verdict="Rejected", sharpe_after_costs=0.53, t_stat=2.33,
         note="Two oil shocks (2020, 2026); flat for a decade"),
]
json.dump({"rows": audit, "meta": [{"label": "Source", "value": "oil-brain/audit/AUDIT.md"}]},
          open(os.path.join(OUT, "audit.json"), "w"), indent=1)
print("wrote", sorted(os.listdir(OUT)))
