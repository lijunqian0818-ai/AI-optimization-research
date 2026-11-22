"""Corporate actions and adjustment factors (A5, A16, A21, A23 data side; dividend-record completeness). No network.
Reference-price formula: SSE / SZSE Trading Rules as quoted in experiments/rule_verification.md section A5:
ref = [(prev_close - cash) + rights_price * ratio_rights] / (1 + ratio_shares)   (cash = pre-tax, per share)."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd

import load as L
from harness import OUT

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
TAB = OUT / "tables"; TAB.mkdir(exist_ok=True)
smp = L.sample()
core = smp[smp.tier == "core"].code.tolist()
SUB = ["600519", "000651", "600036", "601318", "000002", "300750", "688111", "000792", "300104", "600485", "600005", "001872"]
R = {}

# ---------------------------------------------------------------- event table per stock from each source
ev_rows = []
for c in core:
    b = L.bs_raw(c)
    if b is None or b.empty:
        continue
    prev_close = b.close.shift(1)
    f_em, f_sina, f_bs = L.fhps(c), (L.sina_div(c) if c in SUB else None), L.bs_factor(c)
    sf = L.sina_factor(c) if c in SUB else None
    em_hfq = L.em(c, "hfq"); em_raw = L.em(c)
    ex = {}
    if f_em is not None and not f_em.empty:
        g = f_em[f_em["除权除息日"].notna()]
        for _, r in g.iterrows():
            d = ex.setdefault(r["除权除息日"], {})
            d["em_cash10"] = d.get("em_cash10", 0) + (0 if pd.isna(r["现金分红-现金分红比例"]) else r["现金分红-现金分红比例"])
            d["em_shares10"] = d.get("em_shares10", 0) + (0 if pd.isna(r["送转股份-送转总比例"]) else r["送转股份-送转总比例"])
            d["em_record"] = r["股权登记日"]
    if f_sina is not None and not f_sina.empty:
        g = f_sina[f_sina["除权除息日"].notna()]
        for _, r in g.iterrows():
            d = ex.setdefault(r["除权除息日"], {})
            d["sina_cash10"] = d.get("sina_cash10", 0) + float(r["派息"] or 0)
            d["sina_shares10"] = d.get("sina_shares10", 0) + float(r["送股"] or 0) + float(r["转增"] or 0)
            d["sina_record"] = r["股权登记日"]
    if f_bs is not None and not f_bs.empty:
        fb = f_bs.sort_values("dividOperateDate").reset_index(drop=True)
        prevf = fb.backAdjustFactor.shift(1)
        for i, r in fb.iterrows():
            d = ex.setdefault(r.dividOperateDate, {})
            d["bs_back"] = r.backAdjustFactor
            d["bs_back_ratio"] = r.backAdjustFactor / prevf[i] if i > 0 else np.nan
    if sf is not None and not sf.empty:
        s2 = sf.sort_values("date").reset_index(drop=True)
        pv = s2.hfq_factor.shift(1)
        for i, r in s2.iterrows():
            d = ex.setdefault(r.date, {})
            d["sina_ratio"] = r.hfq_factor / pv[i] if i > 0 else np.nan
    # dates where the exchange reference price differs from the previous close
    ne = b.index[1:][(b.preclose.iloc[1:] - prev_close.iloc[1:]).abs() > 1e-9]
    for t in ne:
        ex.setdefault(t, {})["bs_preclose_ne_prevclose"] = True
    if em_hfq is not None and not em_hfq.empty and em_raw is not None and not em_raw.empty:
        idx = em_hfq.index.intersection(em_raw.index)
        emr = (em_hfq.loc[idx, "close"] / em_raw.loc[idx, "close"])
    else:
        emr = None
    for t, d in ex.items():
        if t < pd.Timestamp("2008-01-10") or t > b.index.max() or t not in b.index:
            d.update({"code": c, "date": t, "in_range": False}); ev_rows.append(d); continue
        pc, ref = prev_close.get(t, np.nan), b.preclose.get(t, np.nan)
        d.update({"code": c, "date": t, "in_range": True, "prev_close": pc, "bs_preclose": ref, "implied_ratio_exch": pc / ref if ref else np.nan})
        for src in ["em", "sina"]:
            if f"{src}_cash10" in d:
                cash, sh = d[f"{src}_cash10"] / 10.0, d[f"{src}_shares10"] / 10.0
                d[f"{src}_theo_ref"] = float(L.round_half_up((pc - cash) / (1 + sh)))
                d[f"{src}_theo_ratio"] = pc / ((pc - cash) / (1 + sh))
                d[f"{src}_theo_ratio_nocash"] = (1 + sh)
        if emr is not None and t in emr.index:
            before = emr[emr.index < t]
            if len(before):
                d["em_hfq_ratio"] = emr[t] / before.iloc[-1]
                d["em_hfq_level"] = emr[t]
        ev_rows.append(d)
ev = pd.DataFrame(ev_rows)
ev.to_csv(TAB / "A5_events.csv", index=False, encoding="utf-8-sig")
e = ev[ev.in_range == True].copy()
print("events in range:", len(e), "stocks", e.code.nunique())


def share(mask, base):
    n = int(base.sum())
    return {"n": n, "match": int((mask & base).sum()), "share": round(float((mask & base).sum() / n), 4) if n else None}


tol = 1e-3
has_em = e.get("em_theo_ratio").notna() if "em_theo_ratio" in e else pd.Series(False, index=e.index)
pure_cash = has_em & (e.em_shares10.fillna(0) == 0) & (e.em_cash10.fillna(0) > 0)
with_shares = has_em & (e.em_shares10.fillna(0) > 0)
out = {"n_events_union": int(len(e)), "n_with_em_record": int(has_em.sum()), "n_pure_cash": int(pure_cash.sum()), "n_with_bonus_or_transfer": int(with_shares.sum())}
# exchange reference price (BaoStock preclose) vs formula from Eastmoney records
out["bs_preclose_vs_formula_ref_cent"] = share((e.bs_preclose - e.get("em_theo_ref")).abs() < 0.0051, has_em)
for name, col in [("baostock_factor", "bs_back_ratio"), ("sina_hfq_factor", "sina_ratio"), ("eastmoney_hfq_price", "em_hfq_ratio")]:
    if col not in e:
        out[name] = "not available"; continue
    av = e[col].notna()
    o = {"events_with_factor_step": int(av.sum())}
    o["vs_exchange_ref (prev_close/preclose), all events"] = share(((e[col] / e.implied_ratio_exch - 1).abs() < tol), av & e.bs_preclose.notna())
    o["vs_formula_incl_cash, pure-cash events"] = share(((e[col] / e.em_theo_ratio - 1).abs() < tol), av & pure_cash)
    o["equals_1 (no step), pure-cash events"] = share(((e[col] - 1).abs() < 1e-6), av & pure_cash)
    o["vs_formula_incl_cash, share events"] = share(((e[col] / e.em_theo_ratio - 1).abs() < tol), av & with_shares)
    o["vs_formula_excl_cash, share events"] = share(((e[col] / e.em_theo_ratio_nocash - 1).abs() < tol), av & with_shares)
    o["pure-cash events without any factor step"] = int((pure_cash & ~av).sum())
    out[name] = o
R["A5"] = out
print(json.dumps(out, ensure_ascii=False, indent=1))
bad = e[has_em & ((e.bs_preclose - e.em_theo_ref).abs() >= 0.0051)]
print("ref-price mismatches (formula from EM records vs BaoStock preclose):"); print(bad[["code", "date", "prev_close", "bs_preclose", "em_cash10", "em_shares10", "em_theo_ref"]].head(40).to_string())
bad.to_csv(TAB / "A5_refprice_mismatch.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- completeness of event records across sources
cmpl = {}
e["ex_by_price"] = e.get("bs_preclose_ne_prevclose", pd.Series(False, index=e.index)).fillna(False).astype(bool)
e["in_em"] = has_em
e["in_bsf"] = e.get("bs_back").notna() if "bs_back" in e else False
e["in_sina"] = e.get("sina_cash10").notna() if "sina_cash10" in e else False
cmpl["price_implied_ex_dates (preclose != prev close)"] = int(e.ex_by_price.sum())
cmpl["of which in Eastmoney fhps"] = int((e.ex_by_price & e.in_em).sum())
cmpl["of which in BaoStock factor table"] = int((e.ex_by_price & e.in_bsf).sum())
cmpl["price-implied, in neither record source"] = int((e.ex_by_price & ~e.in_em & ~e.in_bsf).sum())
cmpl["Eastmoney events without price-implied ex-date"] = int((e.in_em & ~e.ex_by_price).sum())
sub = e[e.code.isin(SUB)]
cmpl["SUB: Eastmoney events"] = int(sub.in_em.sum()); cmpl["SUB: Sina events"] = int(sub.in_sina.sum())
cmpl["SUB: in both"] = int((sub.in_em & sub.in_sina).sum())
both = sub[sub.in_em & sub.in_sina]
cmpl["SUB: both, cash equal (1e-3 per 10 sh)"] = int(((both.em_cash10 - both.sina_cash10).abs() < 1e-3).sum())
cmpl["SUB: both, shares equal"] = int(((both.em_shares10 - both.sina_shares10).abs() < 1e-6).sum())
cmpl["SUB: both, record date equal"] = int((both.em_record == both.sina_record).sum())
# delisted names: which source has any dividend record
delisted = smp[smp.exch_delist_date.notna() & (smp.tier == "core")].code.tolist()
cmpl["delisted core names"] = len(delisted)
cmpl["delisted with Eastmoney fhps table"] = int(sum(L.fhps(c) is not None and not L.fhps(c).empty for c in delisted))
cmpl["delisted with BaoStock factor rows"] = int(sum(L.bs_factor(c) is not None and not L.bs_factor(c).empty for c in delisted))
cmpl["delisted in SUB with Sina dividend table"] = {c: (L.sina_div(c) is not None and not L.sina_div(c).empty) for c in SUB if c in delisted}
cmpl["delisted: price-implied ex-dates"] = int(e[e.code.isin(delisted)].ex_by_price.sum())
cmpl["delisted: price-implied ex-dates with BaoStock factor"] = int((e[e.code.isin(delisted)].ex_by_price & e[e.code.isin(delisted)].in_bsf).sum())
# record date = previous trading day of ex-date?
cal = L.calendar()
g = e[has_em & e.em_record.notna()]
prev_td = g.date.map(lambda t: cal[cal < t][-1])
cmpl["record date == trading day before ex-date (Eastmoney)"] = {"n": int(len(g)), "match": int((prev_td == g.em_record).sum())}
cmpl["Eastmoney events with ex-date but no record date"] = int((has_em & e.em_record.isna()).sum())
R["dividend_records"] = cmpl
print(json.dumps(cmpl, ensure_ascii=False, indent=1, default=str))
miss = e[e.ex_by_price & ~e.in_em]
print("price-implied ex-dates not in Eastmoney fhps:"); print(miss[["code", "date", "prev_close", "bs_preclose", "in_bsf", "in_sina", "bs_back_ratio"]].to_string())
miss.to_csv(TAB / "A21_exdates_not_in_em.csv", index=False, encoding="utf-8-sig")

# rights issues (600036): what do the sources show
ri = L.sina_div("600036", "配股")
print("Sina 配股 600036:"); print(None if ri is None else ri.to_string())
b = L.bs_raw("600036")
for a, z in [("2010-03-01", "2010-03-19"), ("2013-08-20", "2013-09-10")]:
    print(b.loc[a:z, ["open", "close", "preclose", "volume", "tradestatus"]].to_string())
bd = [L._get("bs_query_dividend_data", code=L.bs_code(c), year=y, yearType="operate") for c in ["600519", "600036", "000651"] for y in ["2015", "2023"]]
bd = pd.concat([x for x in bd if x is not None and not x.empty])
print("BaoStock dividend table columns:", list(bd.columns)); print(bd.to_string())
R["bs_dividend_fields"] = list(bd.columns)
R["bs_dividend_rows"] = int(len(bd))

# ---------------------------------------------------------------- Eastmoney hfq: multiplicative? ; BaoStock hfq vs raw*factor ; qfq negative prices
mm = []
for c in core:
    h, r = L.em(c, "hfq"), L.em(c)
    if h is None or r is None or h.empty or r.empty:
        continue
    idx = h.index.intersection(r.index)
    for f in ["close"]:
        ratio = h.loc[idx, f] / r.loc[idx, f]
        ratio_o = h.loc[idx, "open"] / r.loc[idx, "open"]
        steps = (ratio / ratio.shift(1) - 1).abs()
        mm.append({"code": c, "n": len(idx), "n_ratio_steps_gt_1e-3": int((steps > 1e-3).sum()), "min_ratio": float(ratio.min()), "max_ratio": float(ratio.max()),
                   "open_close_ratio_maxdiff": float(((ratio_o / ratio) - 1).abs().max()), "hfq_min_close": float(h.close.min())})
    q = L.em(c, "qfq")
    if q is not None and not q.empty:
        mm[-1]["qfq_min_close"] = float(q.close.min()); mm[-1]["qfq_nonpositive_days"] = int((q.close <= 0).sum())
        mm[-1]["qfq_last_equals_raw_last"] = bool(abs(q.close.iloc[-1] - r.close.iloc[-1]) < 1e-9)
mm = pd.DataFrame(mm)
mm.to_csv(TAB / "A5_em_hfq_shape.csv", index=False, encoding="utf-8-sig")
print(mm.to_string())
R["em_hfq_shape"] = {"stocks": int(len(mm))}
if len(mm):
    R["em_hfq_shape"].update({"max_open_close_ratio_diff": float(mm.open_close_ratio_maxdiff.max()),
                              "stocks_with_qfq": int(mm.get("qfq_min_close", pd.Series(dtype=float)).notna().sum()),
                              "qfq_nonpositive_days_total": int(mm.get("qfq_nonpositive_days", pd.Series(dtype=float)).fillna(0).sum())})
hh = []
for c in SUB:
    h, r, f = L.bs_hfq(c), L.bs_raw(c), L.bs_factor(c)
    if h is None or r is None or h.empty:
        continue
    row = {"code": c, "n": len(h)}
    if f is not None and not f.empty:
        fs = f.sort_values("dividOperateDate").set_index("dividOperateDate").backAdjustFactor
        fac = fs.reindex(r.index, method="ffill").fillna(1.0)
        rel = ((r.close * fac) / h.close - 1).abs()
        row.update({"raw_x_factor_vs_hfq_rel_lt_1e-4": float((rel < 1e-4).mean()), "max_rel": float(rel.max()), "first_factor_date": fs.index.min().date(), "n_factor_rows": len(fs)})
    else:
        row.update({"n_factor_rows": 0, "hfq_equals_raw": bool(((h.close - r.close).abs() < 1e-9).all())})
    e_h = L.em(c, "hfq")
    if e_h is not None and not e_h.empty:
        idx = h.index.intersection(e_h.index)
        ret_b = h.loc[idx, "close"].pct_change(); ret_e = e_h.loc[idx, "close"].pct_change()
        row["hfq_daily_return_bs_vs_em_absdiff_lt_1e-3"] = float(((ret_b - ret_e).abs() < 1e-3).mean())
        row["hfq_return_maxabsdiff"] = float((ret_b - ret_e).abs().max())
    hh.append(row)
hh = pd.DataFrame(hh); hh.to_csv(TAB / "A5_bs_hfq_consistency.csv", index=False, encoding="utf-8-sig")
print(hh.to_string())
R["bs_hfq_consistency"] = hh.to_dict("records")
json.dump(R, open(OUT / "analysis_corp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
