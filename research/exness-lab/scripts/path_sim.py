"""OHLC path heuristic: bullish bar O->L->H->C, bearish O->H->L->C. Walk the segments in order, enter when the price
crosses the entry level (stop: crossing in the trade direction; limit: crossing against it), then exit at the first of
SL/TP touched after entry, else at the close. Returns % return (0 if no fill)."""
import numpy as np
def walk(o, h, l, c, side, kind, lvl, sl_d, tp_d, slip):
    out = np.zeros(len(o))
    for i in range(len(o)):
        if not np.isfinite(lvl[i]) or not np.isfinite(sl_d[i]): continue
        pts = [o[i], l[i], h[i], c[i]] if c[i] >= o[i] else [o[i], h[i], l[i], c[i]]
        inpos = False; e = sl = tp = None; res = None
        # entry at the open if the level is already passed
        if kind == "stop" and ((side > 0 and o[i] >= lvl[i]) or (side < 0 and o[i] <= lvl[i])) or \
           kind == "limit" and ((side > 0 and o[i] <= lvl[i]) or (side < 0 and o[i] >= lvl[i])) or kind == "open":
            inpos = True; e = o[i]
        if inpos: e = e * (1 + side * slip); sl = e - side * sl_d[i]; tp = e + side * tp_d[i]
        for a, b in zip(pts[:-1], pts[1:]):
            lo, hi = min(a, b), max(a, b); st = a
            if not inpos:
                if lo <= lvl[i] <= hi:
                    inpos = True; e = lvl[i] * (1 + side * slip) if kind == "stop" else lvl[i]
                    sl = e - side * sl_d[i]; tp = e + side * tp_d[i]
                    # remaining part of this segment after the entry
                    lo, hi = (min(lvl[i], b), max(lvl[i], b)); st = lvl[i]
                else: continue
            hs, ht = lo <= sl <= hi, lo <= tp <= hi
            if hs and ht: res = sl if abs(sl - st) <= abs(tp - st) else tp
            elif hs: res = sl
            elif ht: res = tp
            if res is not None: break
        if inpos:
            x = res if res is not None else c[i]
            out[i] = (x / e - 1) * side
    return out
