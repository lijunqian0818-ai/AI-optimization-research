"""Analysis of the cached price / adjustment / corporate-action pulls (no network).
Writes experiments/results/data_audit/analysis_prices.json and per-item CSV tables. Descriptive only: no model, no backtest."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd

import load as L
from harness import OUT

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
R = {}
smp = L.sample()
cal = L.calendar()
codes = smp.code.tolist()
core = smp[smp.tier == "core"].code.tolist()
TAB = OUT / "tables"
TAB.mkdir(exist_ok=True)


def tdays_between(a, b):
    """number of market trading days strictly after a and up to b (inclusive)"""
    return int(((cal > a) & (cal <= b)).sum())


# ------------------------------------------------------------------ A1 / A14: delisted names
rows = []
for _, r in smp.iterrows():
    c = r.code
    b, e = L.bs_raw(c), L.em(c)
    row = {"code": c, "tier": r.tier, "cats": r.cats, "exch_delist_date": r.exch_delist_date, "bs_ipo": r.ipoDate, "bs_out": r.outDate}
    sn_ = L.sina(c)
    for nm, d in [("bs", b), ("em", e), ("sina", sn_)]:
        if d is None:
            row.update({f"{nm}_rows": None}); continue
        if d.empty:
            row.update({f"{nm}_rows": 0}); continue
        row.update({f"{nm}_rows": len(d), f"{nm}_first": d.index.min().date(), f"{nm}_last": d.index.max().date()})
        tr = d[d.volume > 0]
        if len(tr):
            row.update({f"{nm}_last_traded": tr.index.max().date(), f"{nm}_last_close": float(tr.close.iloc[-1])})
    if b is not None and not b.empty:
        lo = max(pd.Timestamp(r.ipoDate), cal[0])
        hi = b.index.max()
        exp = cal[(cal >= lo) & (cal <= hi)]
        row["bs_missing_market_days"] = int(len(exp.difference(b.index)))
        row["bs_expected_days"] = int(len(exp))
        if isinstance(r.exch_delist_date, str):
            dd = pd.Timestamp(r.exch_delist_date)
            lt = pd.Timestamp(row.get("bs_last_traded")) if row.get("bs_last_traded") else None
            row["bs_last_row_minus_delist_caldays"] = int((b.index.max() - dd).days)
            if lt is not None:
                row["bs_tdays_last_trade_to_delist"] = tdays_between(lt, dd)
    if e is not None and not e.empty and b is not None and not b.empty:
        bt = b[(b.volume > 0)].index
        row["em_traded_days_missing_vs_bs"] = int(len(bt.difference(e.index)))
        row["em_days_not_in_bs"] = int(len(e.index.difference(b.index)))
    if sn_ is not None and not sn_.empty and b is not None and not b.empty:
        bt = b[(b.volume > 0)].index
        row["sina_traded_days_missing_vs_bs"] = int(len(bt.difference(sn_.index)))
        row["sina_days_not_in_bs_traded"] = int(len(sn_.index.difference(bt)))
    rows.append(row)
a1 = pd.DataFrame(rows)
a1.to_csv(TAB / "A1_coverage.csv", index=False, encoding="utf-8-sig")
dl = a1[a1.exch_delist_date.notna()]
R["A1"] = {
    "n_delisted_sampled": int(len(dl)),
    "bs_with_history": int((dl.bs_rows.fillna(0) > 0).sum()),
    "bs_history_complete_no_missing_days": int((dl.bs_missing_market_days == 0).sum()),
    "bs_last_row_equals_exchange_delist_date": int((dl.bs_last_row_minus_delist_caldays == 0).sum()),
    "bs_last_row_minus_delist_caldays_dist": dl.bs_last_row_minus_delist_caldays.value_counts().sort_index().to_dict(),
    "em_attempted": int(dl.em_rows.notna().sum()), "em_with_history": int((dl.em_rows.fillna(0) > 0).sum()),
    "em_not_fetched": int(dl.em_rows.isna().sum()),
    "em_last_equals_bs_last_traded": int((dl.em_last.astype(str) == dl.bs_last_traded.astype(str)).sum()) if "em_last" in dl else None,
    "sina_attempted": int(dl.sina_rows.notna().sum()) if "sina_rows" in dl else 0,
    "sina_with_history": int((dl.sina_rows.fillna(0) > 0).sum()) if "sina_rows" in dl else 0,
    "sina_complete_vs_bs_traded_days": int(((dl.sina_traded_days_missing_vs_bs == 0)).sum()) if "sina_traded_days_missing_vs_bs" in dl else 0,
    "sina_last_equals_bs_last_traded": int((dl.sina_last.astype(str) == dl.bs_last_traded.astype(str)).sum()) if "sina_last" in dl else None,
    "sina_missing_days_total": int(dl.sina_traded_days_missing_vs_bs.fillna(0).sum()) if "sina_traded_days_missing_vs_bs" in dl else None,
    "sina_extra_days_total": int(dl.sina_days_not_in_bs_traded.fillna(0).sum()) if "sina_days_not_in_bs_traded" in dl else None,
    "tdays_last_trade_to_delist_dist": dl.bs_tdays_last_trade_to_delist.describe().to_dict() if "bs_tdays_last_trade_to_delist" in dl else None,
}
print("A1", json.dumps(R["A1"], default=str, ensure_ascii=False))
print(dl[[c for c in ["code", "exch_delist_date", "bs_rows", "bs_first", "bs_last", "bs_last_traded", "bs_last_close", "bs_missing_market_days",
          "bs_tdays_last_trade_to_delist", "em_rows", "sina_rows", "sina_first", "sina_last", "sina_traded_days_missing_vs_bs", "sina_days_not_in_bs_traded"] if c in dl]].to_string())

# ------------------------------------------------------------------ A4 / A10 / A17: cross-source agreement
def cmp_fields(x, y, fields, scale=None):
    idx = x.index.intersection(y.index)
    out = {"n": len(idx)}
    for f in fields:
        a, b = x.loc[idx, f].astype(float), y.loc[idx, f].astype(float)
        if scale and f in scale:
            b = b * scale[f]
        ok = (a.notna() & b.notna())
        rel = ((a - b).abs() / a.abs().replace(0, np.nan))[ok]
        rel = rel.fillna((a - b).abs()[ok])   # a == 0: absolute difference
        out[f + "_n"] = int(ok.sum())
        out[f + "_agree_1e-4"] = int((rel < 1e-4).sum())
        out[f + "_agree_1e-2"] = int((rel < 1e-2).sum())
        out[f + "_exact"] = int(((a - b).abs()[ok] < 5e-7).sum())
        out[f + "_maxrel"] = float(rel.max()) if len(rel) else None
    return out


rows4, disc = [], []
for c in codes:
    b, e = L.bs_raw(c), L.em(c)
    if b is None or b.empty:
        continue
    bt = b[b.volume > 0]
    for nm, d, fields, scale in [("em", e, ["open", "high", "low", "close", "volume", "amount", "turn"], {"volume": 100.0}),
                                 ("sina", L.sina(c), ["open", "high", "low", "close", "volume", "amount"], None),
                                 ("tx", L.tx(c), ["open", "high", "low", "close", "volume", "amount"], None)]:
        if d is None or d.empty:
            continue
        o = cmp_fields(bt, d, [f for f in fields if f in d.columns], scale)
        o.update({"code": c, "pair": "bs_vs_" + nm})
        rows4.append(o)
        if nm == "em":
            idx = bt.index.intersection(d.index)
            for f in ["open", "close", "high", "low"]:
                bad = idx[((bt.loc[idx, f] - d.loc[idx, f]).abs() > 1e-4 * bt.loc[idx, f].abs())]
                for t in bad:
                    disc.append({"code": c, "date": t.date(), "field": f, "bs": bt.loc[t, f], "em": d.loc[t, f]})
a4 = pd.DataFrame(rows4)
a4.to_csv(TAB / "A4_cross_source.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(disc).to_csv(TAB / "A4_price_discrepancies_bs_em.csv", index=False, encoding="utf-8-sig")
R["A4"] = {}
for pair, g in a4.groupby("pair"):
    o = {"stocks": int(len(g)), "stock_days": int(g.n.sum())}
    for f in ["open", "high", "low", "close", "volume", "amount", "turn"]:
        if f + "_n" in g and g[f + "_n"].sum() > 0:
            n = g[f + "_n"].sum()
            o[f] = {"n": int(n), "share_rel<1e-4": round(float(g[f + "_agree_1e-4"].sum() / n), 6),
                    "share_rel<1e-2": round(float(g[f + "_agree_1e-2"].sum() / n), 6), "max_rel": float(g[f + "_maxrel"].max())}
    R["A4"][pair] = o
R["A4"]["n_price_discrepancy_rows_bs_em"] = len(disc)
print("A4", json.dumps(R["A4"], ensure_ascii=False, indent=1))
if disc:
    dd = pd.DataFrame(disc)
    print(dd.groupby("code").size().sort_values(ascending=False).head(12).to_string())
    print(dd.head(25).to_string())

# ------------------------------------------------------------------ A8 / A12 / A22: suspension flag, open on no-trade days
agg = {k: 0 for k in ["stock_days", "susp_flag", "zero_vol", "flag_and_posvol", "noflag_and_zerovol", "susp_open_eq_preclose", "susp_ohlc_flat",
                      "susp_rows", "blank_volume_rows", "blank_open_rows", "traded", "open_outside_low_high", "open_missing_traded",
                      "em_rows_on_bs_susp_days", "bs_susp_days_with_em_fetched", "em_zero_vol_rows", "sina_rows_on_bs_susp_days", "bs_susp_days_with_sina"]}
odd = []
for c in codes:
    b = L.bs_raw(c)
    if b is None or b.empty:
        continue
    agg["stock_days"] += len(b)
    fl, zv = b.tradestatus == 0, ~(b.volume > 0)
    agg["susp_flag"] += int(fl.sum()); agg["zero_vol"] += int(zv.sum())
    agg["flag_and_posvol"] += int((fl & ~zv).sum()); agg["noflag_and_zerovol"] += int((~fl & zv).sum())
    s = b[fl]
    agg["susp_rows"] += len(s)
    agg["susp_open_eq_preclose"] += int(((s.open - s.preclose).abs() < 1e-9).sum())
    agg["susp_ohlc_flat"] += int(((s.open == s.close) & (s.high == s.low) & (s.open == s.high)).sum())
    agg["blank_volume_rows"] += int(b.volume_blank.sum()); agg["blank_open_rows"] += int(b.open_blank.sum())
    t = b[~zv]
    agg["traded"] += len(t)
    agg["open_outside_low_high"] += int(((t.open > t.high + 1e-9) | (t.open < t.low - 1e-9)).sum())
    agg["open_missing_traded"] += int((t.open.isna() | (t.open <= 0)).sum())
    for t0 in b.index[(~fl & zv) | (fl & ~zv)]:
        odd.append({"code": c, "date": t0.date(), **b.loc[t0, ["open", "high", "low", "close", "preclose", "volume", "amount", "tradestatus"]].to_dict(),
                    "volume_blank": bool(b.loc[t0, "volume_blank"])})
    e = L.em(c)
    if e is not None and not e.empty:
        agg["bs_susp_days_with_em_fetched"] += int(fl.sum())
        agg["em_rows_on_bs_susp_days"] += int(len(b.index[fl].intersection(e.index)))
        agg["em_zero_vol_rows"] += int((~(e.volume > 0)).sum())
    sn = L.sina(c)
    if sn is not None and not sn.empty:
        agg["bs_susp_days_with_sina"] += int(fl.sum())
        agg["sina_rows_on_bs_susp_days"] += int(len(b.index[fl].intersection(sn.index)))
pd.DataFrame(odd).to_csv(TAB / "A8_flag_volume_disagreements.csv", index=False, encoding="utf-8-sig")
R["A8_A12"] = agg
print("A8/A12", json.dumps(agg, indent=1))
print(pd.DataFrame(odd).head(40).to_string())

# long suspensions (A15, data side)
ls = []
for c in codes:
    b = L.bs_raw(c)
    if b is None or b.empty:
        continue
    fl = (b.tradestatus == 0).astype(int)
    grp = (fl != fl.shift()).cumsum()
    for _, g in b[fl == 1].groupby(grp[fl == 1]):
        if len(g) > 20:
            after = b.loc[b.index > g.index[-1]]
            pre = b.loc[b.index < g.index[0]]
            ls.append({"code": c, "start": g.index[0].date(), "end": g.index[-1].date(), "tdays": len(g),
                       "close_before": pre.close.iloc[-1] if len(pre) else None, "carried_close_first": g.close.iloc[0], "carried_close_last": g.close.iloc[-1],
                       "first_open_after": after.open.iloc[0] if len(after) else None, "first_preclose_after": after.preclose.iloc[0] if len(after) else None,
                       "first_pct_after": after.pctChg.iloc[0] if len(after) else None, "resumed": len(after) > 0})
ls = pd.DataFrame(ls)
ls.to_csv(TAB / "A15_long_suspensions.csv", index=False, encoding="utf-8-sig")
R["A15"] = {"n_long_suspensions_gt20d": int(len(ls)), "n_stocks": int(ls.code.nunique()) if len(ls) else 0,
            "carry_changes_within_suspension": int((ls.carried_close_first != ls.carried_close_last).sum()) if len(ls) else 0,
            "preclose_after_ne_carried_close": int(((ls.first_preclose_after - ls.carried_close_last).abs() > 1e-9).sum()) if len(ls) else 0}
print("A15", R["A15"]); print(ls.to_string())

# ------------------------------------------------------------------ A6 / A7 / A12: preclose, limit bands, open at limit
def band(code, date, is_st, n_listed):
    """Rule calendar of PLAN section 3.4 (rules themselves are [tbv, RV5]; this only applies them). Returns band or None (no limit)."""
    bd = L.board(code)
    if bd == "star":
        return None if n_listed <= 5 else 0.20
    if bd == "chinext":
        if date >= pd.Timestamp("2020-08-24"):
            # registration-based IPOs (listed on/after 2020-08-24) have no limit in the first 5 days
            return 0.20
        return 0.05 if is_st else 0.10
    if is_st:
        return 0.10 if date >= pd.Timestamp("2026-07-06") else 0.05
    return 0.10


lim_rows, viol, a6 = [], [], {k: 0 for k in ["days", "preclose_eq_prev_close", "preclose_ne_prev_close", "ne_on_bs_factor_date", "ne_not_on_factor_date"]}
agg7 = {k: 0 for k in ["days_checked", "high_above_up", "low_below_down", "close_eq_up", "close_eq_down", "open_eq_up", "open_eq_down",
                       "excluded_first_days", "excluded_resumption_like"]}
ne_unexpl = []
for c in codes:
    b = L.bs_raw(c)
    if b is None or b.empty:
        continue
    b = b.copy()
    f = L.bs_factor(c)
    fdates = set(pd.to_datetime(f.dividOperateDate)) if f is not None and not f.empty else set()
    prev_close = b.close.shift(1)
    tr = b.volume > 0
    cmpd = b.iloc[1:]
    eq = (cmpd.preclose - prev_close.iloc[1:]).abs() < 1e-9
    a6["days"] += len(cmpd); a6["preclose_eq_prev_close"] += int(eq.sum()); a6["preclose_ne_prev_close"] += int((~eq).sum())
    for t in cmpd.index[~eq]:
        if t in fdates:
            a6["ne_on_bs_factor_date"] += 1
        else:
            a6["ne_not_on_factor_date"] += 1
            ne_unexpl.append({"code": c, "date": t.date(), "prev_close": prev_close[t], "preclose": b.preclose[t], "open": b.open[t], "close": b.close[t],
                              "volume": b.volume[t], "tradestatus": b.tradestatus[t], "core": c in core})
    ipo = pd.Timestamp(smp.set_index("code").ipoDate[c])
    n_listed = pd.Series(np.arange(1, len(b) + 1), index=b.index) if b.index[0] <= ipo + pd.Timedelta(days=5) else pd.Series(10 ** 6, index=b.index)
    reg_ipo = (L.board(c) == "star") or (L.board(c) == "chinext" and ipo >= pd.Timestamp("2020-08-24")) or (L.board(c) == "main" and ipo >= pd.Timestamp("2023-04-10"))
    for t in b.index[tr]:
        nl = int(n_listed[t])
        if nl == 1 or (reg_ipo and nl <= 5):
            agg7["excluded_first_days"] += 1
            continue
        bd = band(c, t, b.isST[t] == 1, nl)
        if bd is None:
            agg7["excluded_first_days"] += 1
            continue
        pc = b.preclose[t]
        up, dn = float(L.round_half_up(pc * (1 + bd))), float(L.round_half_up(pc * (1 - bd)))
        # rule_verification.md A5: if the difference is below one tick, the limit is preclose +/- one tick
        if up - pc < 0.01 - 1e-9:
            up = round(pc + 0.01, 2)
        if pc - dn < 0.01 - 1e-9:
            dn = round(pc - 0.01, 2)
        agg7["days_checked"] += 1
        hv, lv = b.high[t] > up + 1e-9, b.low[t] < dn - 1e-9
        agg7["high_above_up"] += int(hv); agg7["low_below_down"] += int(lv)
        agg7["close_eq_up"] += int(abs(b.close[t] - up) < 1e-9); agg7["close_eq_down"] += int(abs(b.close[t] - dn) < 1e-9)
        agg7["open_eq_up"] += int(abs(b.open[t] - up) < 1e-9); agg7["open_eq_down"] += int(abs(b.open[t] - dn) < 1e-9)
        if hv or lv:
            viol.append({"code": c, "date": t.date(), "isST": b.isST[t], "band": bd, "preclose": pc, "up": up, "dn": dn, "open": b.open[t],
                         "high": b.high[t], "low": b.low[t], "close": b.close[t], "n_listed": nl, "prev_tradestatus": b.tradestatus.shift(1)[t],
                         "on_factor_date": t in fdates})
viol = pd.DataFrame(viol)
viol.to_csv(TAB / "A6_A7_limit_band_violations.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(ne_unexpl).to_csv(TAB / "A6_preclose_ne_prevclose_unexplained.csv", index=False, encoding="utf-8-sig")
R["A6"] = a6
R["A7"] = agg7
R["A7"]["violation_rows"] = int(len(viol))
R["A7"]["violation_share"] = float(len(viol) / max(agg7["days_checked"], 1))
print("A6", a6); print("A7", agg7)
if len(viol):
    print(viol.groupby("code").size().sort_values(ascending=False).head(15).to_string())
    print(viol.head(60).to_string())
print(pd.DataFrame(ne_unexpl).head(30).to_string())

# ------------------------------------------------------------------ A19: turnover range
t_rows = {"days": 0, "turn_gt_100pct": 0, "turn_lt_0": 0, "turn_blank_traded": 0, "max_turn": 0.0}
for c in codes:
    b = L.bs_raw(c)
    if b is None or b.empty:
        continue
    t = b[b.volume > 0]
    t_rows["days"] += len(t); t_rows["turn_gt_100pct"] += int((t.turn > 100).sum()); t_rows["turn_lt_0"] += int((t.turn < 0).sum())
    t_rows["turn_blank_traded"] += int(t.turn.isna().sum()); t_rows["max_turn"] = max(t_rows["max_turn"], float(t.turn.max()))
R["A19"] = t_rows
print("A19", t_rows)

# ------------------------------------------------------------------ A10: turnover definition
rows10 = []
for c in codes:
    b, e, sn = L.bs_raw(c), L.em(c), L.sina(c)
    if b is None or b.empty:
        continue
    t = b[(b.volume > 0) & (b.turn > 0)]
    row = {"code": c}
    if e is not None and not e.empty:
        idx = t.index.intersection(e.index[e.turn > 0])
        rel = ((t.loc[idx, "turn"] - e.loc[idx, "turn"]).abs() / t.loc[idx, "turn"])
        # Eastmoney turnover is rounded to 0.01 percentage points: tolerance = max(1%, half a unit of rounding)
        tol_ok = (t.loc[idx, "turn"] - e.loc[idx, "turn"]).abs() <= np.maximum(0.01 * t.loc[idx, "turn"], 0.00501)
        row.update({"em_n": len(idx), "em_rel_lt_1pct": int((rel < 0.01).sum()), "em_within_rounding_or_1pct": int(tol_ok.sum()), "em_median_ratio": float((e.loc[idx, "turn"] / t.loc[idx, "turn"]).median())})
    if sn is not None and not sn.empty and "outstanding_share" in sn:
        idx = t.index.intersection(sn.index[sn.outstanding_share > 0])
        implied = t.loc[idx, "volume"] / (t.loc[idx, "turn"] / 100.0)
        ratio = implied / sn.loc[idx, "outstanding_share"]
        row.update({"sina_n": len(idx), "bs_implied_shares_over_sina_outstanding_median": float(ratio.median()),
                    "share_within_1pct": float(((ratio - 1).abs() < 0.01).mean()) if len(idx) else None,
                    "sina_turn_vs_bs_rel_lt_1pct": float((((sn.loc[idx, "turnover"] * 100 - t.loc[idx, "turn"]).abs() / t.loc[idx, "turn"]) < 0.01).mean()) if len(idx) else None})
    rows10.append(row)
a10 = pd.DataFrame(rows10)
a10.to_csv(TAB / "A10_turnover.csv", index=False, encoding="utf-8-sig")
R["A10"] = {}
if "em_n" in a10:
    R["A10"]["bs_vs_em"] = {"n": int(a10.em_n.sum()), "share_rel<1%": float(a10.em_rel_lt_1pct.sum() / a10.em_n.sum()),
                            "share_within_rounding_or_1%": float(a10.em_within_rounding_or_1pct.sum() / a10.em_n.sum())}
if "sina_n" in a10:
    g = a10[a10.sina_n > 0]
    R["A10"]["bs_implied_float_vs_sina_outstanding"] = g[["code", "sina_n", "bs_implied_shares_over_sina_outstanding_median", "share_within_1pct", "sina_turn_vs_bs_rel_lt_1pct"]].to_dict("records")
print("A10", json.dumps(R["A10"], indent=1, ensure_ascii=False))

json.dump(R, open(OUT / "analysis_prices.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("written analysis_prices.json")
