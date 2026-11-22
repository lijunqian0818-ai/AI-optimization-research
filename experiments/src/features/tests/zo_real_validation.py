"""Structural validation of the Z_O raw tables on the full pull (read-only).

Task list TODO-F2. What is checked -- and nothing else:
  * inventory of the raw files and the strict coverage check (F-14);
  * parsing of every whitelisted field (type, missing share, value range);
  * dates: parseable, on / off the trading calendar, rows per year, the
    longest run of trading days without a record (the OA3 run-length figure);
  * INS: the cleaning rule, the forward roll of announcement dates, the share
    of back-filled rows (vendor entry time more than 30 days after the
    announcement) by announcement year, rows by disclosure regime of the rule
    calendar, missing share and range of the ratio used as intensity;
  * LHB: rows per stock-day, classes of the listing reason;
  * timing on real data, exactly: for each trial stock and class, the set of
    decision days on which the 1-day indicator is 1 must equal
    {event day + lag}, and no feature may depend on the vendor's entry time
    or on the transaction dates of an INS row.

NOT computed, anywhere: any relation between a feature (or an event) and a
later return, a label, an IC, a group return, a performance number. The only
price-like quantities touched are fields of the event tables themselves
(premium of a block trade over the same day's close, amounts) and their
ranges.

Whitelisted columns only (config.WHITELIST); no request is sent; nothing is
written to experiments/data/raw.

Usage (project root):
  experiments/.venv/Scripts/python.exe -X utf8 experiments/src/features/tests/zo_real_validation.py
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from features import config, panel, rules, store, zo          # noqa: E402
from features.bars import prepare_bars                        # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(ROOT, "experiments", "results", "feature_tests")
from engine import datacut as dc                               # noqa: E402

# v0.8 rerun (PLAN v0.8 C-8; the lead's constraint for the pilot round): nothing after 2021-12-31 is read
DATA_CUTOFF = dc.PILOT_CUTOFF
START, END = config.ZO_RAW_START, min(config.ZO_RAW_END, pd.Timestamp(DATA_CUTOFF))


def q(x: pd.Series) -> dict:
    x = pd.to_numeric(x, errors="coerce")
    v = x.dropna()
    if not len(v):
        return {"n": int(len(x)), "missing_share": 1.0}
    qs = v.quantile([0, 0.01, 0.5, 0.99, 1]).values
    return {"n": int(len(x)), "missing_share": float(x.isna().mean()), "min": float(qs[0]), "p01": float(qs[1]),
            "median": float(qs[2]), "p99": float(qs[3]), "max": float(qs[4]),
            "share_zero": float((v == 0).mean()), "share_negative": float((v < 0).mean()),
            "n_inf": int(np.isinf(v).sum())}


def inventory(root: str) -> dict:
    out = {}
    months = [p.strftime("%Y%m") for p in pd.period_range(START, END, freq="M")]
    for sub in ("lhb_detail", "lhb_jgmmtj", "dzjy_mrmx", "dzjy_mrtj"):
        files = sorted(os.path.basename(f)[:-8] for f in glob.glob(os.path.join(root, "zo", sub, "*.parquet")))
        files = [f for f in files if f.isdigit() and dc.period_ok(f, DATA_CUTOFF)]
        out[sub] = {"n_files": len(files), "first": files[0] if files else None, "last": files[-1] if files else None,
                    "missing_months_in_2008_01_to_cutoff": [m for m in months if m not in files]}
    files = sorted(os.path.basename(f)[:-8] for f in glob.glob(os.path.join(root, "zo", "ins_raw", "*.parquet")))
    years = [f for f in files if f.isdigit() and dc.period_ok(f, DATA_CUTOFF)]
    out["ins_raw"] = {"n_files": len(years), "first": years[0] if years else None, "last": years[-1] if years else None,
                      "missing_years_2008_to_cutoff": [str(y) for y in range(2008, END.year + 1) if str(y) not in years],
                      "missing_years_before_2008": [str(y) for y in range(int(years[0]), 2008) if str(y) not in years]
                      if years else []}
    tc = os.path.join(root, "zo", "ins_raw", "TOTAL_count.parquet")
    if False and os.path.exists(tc):     # v0.8: the upstream total count covers dates after the cut-off; not read
        out["ins_raw"]["upstream_total_count"] = int(pd.read_parquet(tc)["upstream_count"].iloc[0])
    return out


def run_lengths(cal, dates: pd.Series) -> dict:
    """Trading days in [START, END] without any record; the longest run."""
    d = cal.days[(cal.days >= START) & (cal.days <= END)]
    have = np.isin(d.values, pd.DatetimeIndex(dates.dropna().unique()).values)
    best, best_end, run = 0, None, 0
    for i, h in enumerate(have):
        run = 0 if h else run + 1
        if run > best:
            best, best_end = run, i
    first = d[have][0] if have.any() else None
    return {"trading_days_in_period": int(len(d)), "trading_days_without_a_record": int((~have).sum()),
            "longest_run_without_a_record": int(best),
            "longest_run_from": str(d[best_end - best + 1].date()) if best else None,
            "longest_run_to": str(d[best_end].date()) if best else None,
            "first_trading_day_with_a_record": str(first.date()) if first is not None else None,
            "oa3_criterion_no_run_of_20": bool(best < 20)}


def by_year(dates: pd.Series) -> dict:
    return {int(k): int(v) for k, v in dates.dt.year.value_counts().sort_index().items()}


def main() -> int:
    t0 = time.time()
    st = store.RawStore(data_cutoff=DATA_CUTOFF)
    cal = st.calendar()
    res: dict = {"run_at": time.strftime("%Y-%m-%d %H:%M:%S"), "raw_root": st.root, "data_cutoff": str(DATA_CUTOFF),
                 "statement": "structural checks only; no relation of any feature or event to a later return, no label, "
                              "no IC, no performance number is computed"}
    res["inventory"] = inventory(st.root)
    tables = st.zo_tables()
    # ---------------------------------------------------------------- coverage (F-14)
    try:
        res["strict_coverage"] = {"ok": True, "covered_trading_days": st.check_zo_coverage(tables, strict=True)}
    except zo.MissingRawFile as e:
        res["strict_coverage"] = {"ok": False, "error": str(e),
                                  "covered_trading_days_non_strict": st.check_zo_coverage(tables, strict=False)}
    res["dtypes"] = {k: {c: str(t) for c, t in getattr(tables, k).dtypes.items()} for k in ("lhb", "jg", "blk", "ins")}

    # ================================================================ LHB
    lhb = tables.lhb
    d = pd.to_datetime(lhb["上榜日"], errors="coerce")
    L = {"rows": int(len(lhb)), "date_unparseable": int(d.isna().sum()),
         "rows_on_non_trading_days": int((cal.pos_array(d.dropna()) < 0).sum()),
         "date_min": str(d.min().date()), "date_max": str(d.max().date()), "rows_by_year": by_year(d),
         "rows_outside_universe_codes": int(lhb["代码"].map(zo.to_bs_code).isna().sum()),
         "code_not_6_digits": int((~lhb["代码"].astype(str).str.fullmatch(r"\d{6}")).sum()),
         "exact_duplicate_rows": int(lhb.duplicated().sum()),
         "duplicate_code_date_reason": int(lhb.duplicated(["代码", "上榜日", "上榜原因"]).sum()),
         "run_length": run_lengths(cal, d)}
    for c in ("龙虎榜净买额", "龙虎榜买入额", "龙虎榜卖出额", "龙虎榜成交额", "市场总成交额", "净买额占总成交比", "成交额占总成交比"):
        L["field_" + c] = q(lhb[c])
    net_err = (lhb["龙虎榜净买额"] - (lhb["龙虎榜买入额"] - lhb["龙虎榜卖出额"])).abs()
    tot_err = (lhb["龙虎榜成交额"] - (lhb["龙虎榜买入额"] + lhb["龙虎榜卖出额"])).abs()
    L["identity_net_eq_buy_minus_sell_share_within_1_yuan"] = float((net_err <= 1.0).mean())
    L["identity_amount_eq_buy_plus_sell_share_within_1_yuan"] = float((tot_err <= 1.0).mean())
    L["reason_missing"] = int(lhb["上榜原因"].isna().sum())
    cls = lhb["上榜原因"].map(zo.reason_class)
    L["rows_by_reason_class"] = cls.value_counts().to_dict()
    L["distinct_reasons_not_in_frozen_table"] = int((~lhb["上榜原因"].isin(list(zo.load_reason_map()))).sum())
    inu = lhb["代码"].map(zo.to_bs_code).notna()
    L["rows_by_reason_class_in_universe_codes"] = cls[inu].value_counts().to_dict()
    sd = zo.lhb_stock_day(lhb, tables.jg)
    L["stock_days"] = int(len(sd))
    L["stock_days_with_more_than_one_row"] = int((sd["n_rows"] > 1).sum())
    L["stock_days_multi_day_rows_only"] = int((sd["multi"] & ~sd["has_single"]).sum())
    L["stock_days_with_single_and_multi_rows"] = int((sd["multi"] & sd["has_single"]).sum())
    L["stock_days_unclassified_rows_only"] = int((~sd["multi"] & ~sd["has_single"]).sum())
    L["stock_days_with_institutional_single_day_row"] = int((sd["inst_net"] != 0).sum())
    L["max_rows_per_stock_day"] = int(sd["n_rows"].max())
    res["lhb_detail"] = L
    jg = tables.jg
    dj = pd.to_datetime(jg["上榜日期"], errors="coerce")
    J = {"rows": int(len(jg)), "date_unparseable": int(dj.isna().sum()),
         "rows_on_non_trading_days": int((cal.pos_array(dj.dropna()) < 0).sum()),
         "date_min": str(dj.min().date()), "date_max": str(dj.max().date()), "rows_by_year": by_year(dj),
         "rows_outside_universe_codes": int(jg["代码"].map(zo.to_bs_code).isna().sum()),
         "exact_duplicate_rows": int(jg.duplicated().sum()), "run_length": run_lengths(cal, dj),
         "rows_by_reason_class": jg["上榜原因"].map(zo.reason_class).value_counts().to_dict()}
    for c in ("买方机构数", "卖方机构数", "机构买入总额", "机构卖出总额", "机构买入净额"):
        J["field_" + c] = q(jg[c])
    J["identity_net_eq_buy_minus_sell_share_within_1_yuan"] = float(
        ((jg["机构买入净额"] - (jg["机构买入总额"] - jg["机构卖出总额"])).abs() <= 1.0).mean())
    # institutional stock-days that have no row in the summary table
    k1 = set(zip(lhb["代码"], d.dt.date))
    k2 = set(zip(jg["代码"], dj.dt.date))
    J["stock_days"] = len(k2)
    J["stock_days_not_in_lhb_detail"] = len(k2 - k1)
    res["lhb_jgmmtj"] = J

    # ================================================================ BLK
    blk = tables.blk
    db = pd.to_datetime(blk["交易日期"], errors="coerce")
    B = {"rows": int(len(blk)), "date_unparseable": int(db.isna().sum()),
         "rows_on_non_trading_days": int((cal.pos_array(db.dropna()) < 0).sum()),
         "date_min": str(db.min().date()), "date_max": str(db.max().date()), "rows_by_year": by_year(db),
         "rows_outside_universe_codes": int(blk["证券代码"].map(zo.to_bs_code).isna().sum()),
         "code_not_6_digits": int((~blk["证券代码"].astype(str).str.fullmatch(r"\d{6}")).sum()),
         "exact_duplicate_rows_whitelisted_columns": int(blk.duplicated().sum()),
         "stock_days": int(blk.groupby(["证券代码", "交易日期"]).ngroups),
         "max_trades_per_stock_day": int(blk.groupby(["证券代码", "交易日期"]).size().max()),
         "run_length": run_lengths(cal, db)}
    for c in ("成交价", "折溢率", "成交量", "成交额", "成交额/流通市值"):
        B["field_" + c] = q(blk[c])
    B["by_year_missing_share_折溢率"] = {int(k): float(v) for k, v in blk["折溢率"].isna().groupby(db.dt.year).mean().items()}
    B["by_year_missing_share_成交额"] = {int(k): float(v) for k, v in blk["成交额"].isna().groupby(db.dt.year).mean().items()}
    with np.errstate(all="ignore"):
        ratio = blk["成交额"] / (blk["成交价"] * blk["成交量"])
    B["amount_over_price_times_volume"] = q(ratio)
    B["amount_unit_check_share_within_1pct_of_price_x_volume"] = float(((ratio - 1).abs() < 0.01).mean())
    B["amount_unit_check_share_within_1pct_of_price_x_volume_div_1e4"] = float(((ratio * 1e4 - 1).abs() < 0.01).mean())
    B["premium_abs_gt_0.3"] = int((blk["折溢率"].abs() > 0.3).sum())
    B["rows_amount_non_positive_or_missing"] = int((~(blk["成交额"] > 0)).sum())
    # per-day table against the per-trade table (both vendor tables; consistency of the pull)
    try:
        frames = [store.read_whitelisted(f, "dzjy_mrtj") for f in sorted(glob.glob(os.path.join(st.root, "zo", "dzjy_mrtj", "*.parquet")))
                  if os.path.basename(f)[:-8].isdigit()]
        tj = pd.concat([f for f in frames if len(f)], ignore_index=True)
        a = blk.groupby(["证券代码", "交易日期"]).agg(n=("成交额", "size"), amt=("成交额", "sum")).reset_index()
        m = a.merge(tj[["证券代码", "交易日期", "成交笔数", "成交总额"]], on=["证券代码", "交易日期"], how="outer", indicator=True)
        both = m[m["_merge"] == "both"]
        with np.errstate(all="ignore"):
            rr = both["amt"] / both["成交总额"]
        B["mrtj_crosscheck"] = {"rows_mrtj": int(len(tj)), "stock_days_only_in_mrmx": int((m["_merge"] == "left_only").sum()),
                                "stock_days_only_in_mrtj": int((m["_merge"] == "right_only").sum()),
                                "stock_days_in_both": int(len(both)),
                                "trade_count_equal_share": float((both["n"] == both["成交笔数"]).mean()),
                                "amount_ratio_mrmx_over_mrtj": q(rr)}
    except Exception as e:                                                   # noqa: BLE001
        B["mrtj_crosscheck"] = {"error": f"{type(e).__name__}: {e}"}
    res["dzjy_mrmx"] = B

    # ================================================================ INS
    ins = tables.ins
    I = {"rows": int(len(ins))}
    if "upstream_total_count" in res["inventory"]["ins_raw"]:
        I["rows_minus_upstream_total_count"] = int(len(ins) - res["inventory"]["ins_raw"]["upstream_total_count"])
    notice = pd.to_datetime(ins["NOTICE_DATE"], errors="coerce")
    endd = pd.to_datetime(ins["END_DATE"], errors="coerce")
    startd = pd.to_datetime(ins["START_DATE"], errors="coerce")
    ei = pd.to_datetime(ins["EITIME"], errors="coerce")
    I["field_missing_share"] = {c: float(ins[c].isna().mean()) for c in ins.columns}
    I["date_unparseable_given_present"] = {
        "NOTICE_DATE": int((notice.isna() & ins["NOTICE_DATE"].notna()).sum()),
        "END_DATE": int((endd.isna() & ins["END_DATE"].notna()).sum()),
        "START_DATE": int((startd.isna() & ins["START_DATE"].notna()).sum()),
        "EITIME": int((ei.isna() & ins["EITIME"].notna()).sum())}
    I["notice_has_clock_time_share"] = float((notice.dt.normalize() != notice).mean())
    I["notice_min"], I["notice_max"] = str(notice.min().date()), str(notice.max().date())
    I["rows_by_notice_year"] = by_year(notice.dropna())
    I["direction_values"] = ins["DIRECTION"].value_counts(dropna=False).to_dict()
    I["rows_outside_universe_codes"] = int(ins["SECURITY_CODE"].map(zo.to_bs_code).isna().sum())
    I["exact_duplicate_rows_whitelisted_columns"] = int(ins.duplicated().sum())
    I["year_file_matches_notice_year"] = "checked by the loader: files are keyed by announcement year"
    x, stats = zo.clean_ins(ins)
    I["cleaning"] = stats
    I["cleaning_dropped_notice_before_end_by_year"] = by_year(notice[(notice < endd)])
    # forward roll
    pos = cal.pos_array(x["notice"])
    off = pos < 0
    I["kept_notice_on_non_trading_day_share"] = float(off.mean())
    I["kept_notice_on_non_trading_day_share_by_year"] = {
        int(k): float(v) for k, v in pd.Series(off).groupby(x["notice"].dt.year.values).mean().items()}
    I["kept_notice_weekday_counts"] = x["notice"].dt.day_name().value_counts().to_dict()
    rpos = cal.roll_forward_pos(x["notice"])
    in_cal = rpos < len(cal)
    I["kept_rows_rolled_beyond_calendar"] = int((~in_cal).sum())
    gap = (cal.days[rpos[in_cal]].values - x["notice"].values[in_cal]).astype("timedelta64[D]").astype(int)
    I["roll_forward_calendar_days"] = pd.Series(gap).value_counts().sort_index().to_dict()
    I["roll_never_backward"] = bool((gap >= 0).all())
    usable = rpos[in_cal] + config.ZO_LAG["ins"]
    ok = usable < len(cal)
    first_use = cal.days[usable[ok]].values
    I["first_usable_day_strictly_after_notice_date_all"] = bool((first_use > x["notice"].values[in_cal][ok]).all())
    I["first_usable_minus_notice_calendar_days"] = q(pd.Series((first_use - x["notice"].values[in_cal][ok])
                                                               .astype("timedelta64[D]").astype(int)))
    # back-fill (vendor entry time; diagnostic only, never a feature)
    xe = pd.to_datetime(x["EITIME"], errors="coerce")
    lag_e = (xe - x["notice"]).dt.days
    I["eitime_missing_share_kept"] = float(xe.isna().mean())
    I["backfilled_gt30d_share_kept"] = float((lag_e > 30).mean())
    I["backfilled_gt30d_share_by_notice_year"] = {int(k): float(v) for k, v in (lag_e > 30).groupby(x["notice"].dt.year).mean().items()}
    I["entered_before_notice_date_share"] = float((lag_e < 0).mean())
    I["eitime_minus_notice_days"] = q(lag_e)
    I["eitime_distinct_values"] = int(xe.nunique())
    top = xe.dt.floor("D").value_counts().head(5)
    I["eitime_most_frequent_days"] = {str(k.date()): int(v) for k, v in top.items()}
    # delay between the end of the change and the announcement
    d_end = (x["notice"] - x["end"]).dt.days
    I["notice_minus_end_days"] = q(d_end)
    I["notice_minus_end_gt_30d_share"] = float((d_end > 30).mean())
    I["notice_minus_end_gt_365d_share"] = float((d_end > 365).mean())
    I["end_date_missing_share_kept"] = float(x["end"].isna().mean())
    # regimes of the rule calendar, on the event day (rolled announcement date)
    inw = in_cal & (cal.days[np.minimum(rpos, len(cal) - 1)].values >= np.datetime64(START)) \
        & (cal.days[np.minimum(rpos, len(cal) - 1)].values <= np.datetime64(END))
    ev_day = cal.days[rpos[inw]]
    reg = rules.ins_regime(ev_day)
    xr = x.loc[inw].assign(regime=reg, event_year=ev_day.year.values)
    I["kept_rows_with_event_day_in_2008_01_to_cutoff"] = int(inw.sum())
    I["kept_rows_event_day_before_2008"] = int((cal.days[np.minimum(rpos, len(cal) - 1)].values < np.datetime64(START)).sum())
    tab = xr.groupby(["regime", "DIRECTION"]).size().unstack(fill_value=0)
    I["rows_by_regime_and_direction"] = {config.INS_REGIME_NAMES[int(k)]: {c: int(v) for c, v in r.items()}
                                         for k, r in tab.iterrows()}
    I["regime_unknown_rows"] = int(np.isnan(reg).sum())
    days_in = pd.Series(rules.ins_regime(cal.days[(cal.days >= START) & (cal.days <= END)])).value_counts().sort_index()
    I["trading_days_by_regime"] = {config.INS_REGIME_NAMES[int(k)]: int(v) for k, v in days_in.items()}
    I["stocks_with_event_by_regime"] = {config.INS_REGIME_NAMES[int(k)]: int(v)
                                        for k, v in xr.groupby("regime")["SECURITY_CODE"].nunique().items()}
    I["CHANGE_FREE_RATIO_missing_share_by_regime"] = {
        config.INS_REGIME_NAMES[int(k)]: float(v) for k, v in xr["CHANGE_FREE_RATIO"].isna().groupby(xr["regime"]).mean().items()}
    I["backfilled_gt30d_share_by_regime"] = {
        config.INS_REGIME_NAMES[int(k)]: float(v)
        for k, v in ((pd.to_datetime(xr["EITIME"], errors="coerce") - xr["notice"]).dt.days > 30).groupby(xr["regime"]).mean().items()}
    # the ratio used as intensity, and the other numeric fields
    for c in ("CHANGE_FREE_RATIO", "AFTER_CHANGE_RATE", "CHANGE_NUM"):
        I["field_" + c + "_kept"] = q(x[c])
    I["CHANGE_FREE_RATIO_missing_share_by_notice_year"] = {
        int(k): float(v) for k, v in x["CHANGE_FREE_RATIO"].isna().groupby(x["notice"].dt.year).mean().items()}
    I["CHANGE_FREE_RATIO_gt_100"] = int((x["CHANGE_FREE_RATIO"] > 100).sum())
    I["CHANGE_FREE_RATIO_negative"] = int((x["CHANGE_FREE_RATIO"] < 0).sum())
    I["CHANGE_FREE_RATIO_zero"] = int((x["CHANGE_FREE_RATIO"] == 0).sum())
    I["CHANGE_FREE_RATIO_lt_AFTER_CHANGE_RATE_share"] = float(
        (x["CHANGE_FREE_RATIO"] < x["AFTER_CHANGE_RATE"] - 1e-9)[x["CHANGE_FREE_RATIO"].notna() & x["AFTER_CHANGE_RATE"].notna()].mean())
    # rounding-aware comparison of the two ratio columns (CHANGE_FREE_RATIO is printed with 2 decimals)
    both_r = x["CHANGE_FREE_RATIO"].notna() & x["AFTER_CHANGE_RATE"].notna()
    I["CHANGE_FREE_RATIO_lt_AFTER_CHANGE_RATE_minus_0.005_share"] = float(
        (x["CHANGE_FREE_RATIO"] < x["AFTER_CHANGE_RATE"] - 0.005)[both_r].mean())
    big = both_r & (x["AFTER_CHANGE_RATE"] > 0.05)
    with np.errstate(all="ignore"):
        I["CHANGE_FREE_RATIO_over_AFTER_CHANGE_RATE_where_latter_gt_0.05"] = q(
            (x["CHANGE_FREE_RATIO"] / x["AFTER_CHANGE_RATE"])[big])
    I["CHANGE_FREE_RATIO_decimals_share_with_at_most_2"] = float(
        ((x["CHANGE_FREE_RATIO"].dropna() * 100).round(6) % 1 == 0).mean())
    # sums per stock, announcement day and direction (what a 1-day window adds up), in percent of float shares
    sums = x.groupby(["SECURITY_CODE", "notice", "DIRECTION"])["CHANGE_FREE_RATIO"].sum(min_count=1)
    I["sum_CHANGE_FREE_RATIO_per_stock_day_direction"] = q(sums)
    I["sum_CHANGE_FREE_RATIO_per_stock_day_direction_gt_100"] = int((sums > 100).sum())
    I["sum_CHANGE_FREE_RATIO_per_stock_day_direction_gt_30"] = int((sums > 30).sum())
    # vendor entry time relative to the announcement date, in whole days (diagnostic)
    bins = pd.cut(lag_e, [-1e9, -4, -2, -1, 0, 1, 30, 1e9], labels=["<= -4", "-3..-2", "-1", "0", "1", "2..30", "> 30"],
                  right=True, include_lowest=True)
    I["eitime_minus_notice_days_bins"] = {str(k): int(v) for k, v in bins.value_counts(sort=False).items()}
    recent = x["notice"].dt.year >= 2020
    I["eitime_minus_notice_days_bins_notice_year_2020_on"] = {
        str(k): int(v) for k, v in bins[recent].value_counts(sort=False).items()}
    I["calendar_first_day"], I["calendar_last_day"] = str(cal.days[0].date()), str(cal.days[-1].date())
    long_roll = gap > 10
    I["rolled_more_than_10_calendar_days"] = int(long_roll.sum())
    I["rolled_more_than_10_calendar_days_notice_before_calendar_start"] = int(
        (x["notice"].values[in_cal][long_roll] < cal.days[0].to_datetime64()).sum())
    I["rolled_more_than_10_calendar_days_notice_from_2008"] = int(
        (x["notice"].values[in_cal][long_roll] >= np.datetime64(START)).sum())
    I["events_per_stock_announcement_day"] = q(x.groupby(["SECURITY_CODE", "notice"]).size())
    I["run_length_any_direction"] = run_lengths(cal, pd.Series(cal.days[rpos[in_cal]]))
    res["ins_raw"] = I

    # ================================================================ timing on real data (trial stocks)
    trial = []
    p = os.path.join(ROOT, "experiments", "results", "data_fetch", "trial_codes.txt")
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            s = line.split("#")[0].strip()
            if s:
                c = zo.to_bs_code(s.split(".")[-1])
                if c:
                    trial.append(c)
    T = {"n_trial_codes": len(trial), "per_class": {}, "mismatches": []}
    n_ev = {"lhb": 0, "blk": 0, "ins_buy": 0, "ins_sell": 0}
    n_ok = dict(n_ev)
    eitime_same = 0
    for code in trial:
        raw = st.raw_bars(code)
        try:
            far = cal.next(pd.to_datetime(raw["date"]).max())
        except KeyError:                          # the calendar ends at the data cut-off
            far = cal.days[-1]
        f = panel.build_stock_features(code, raw, cal, far, None, tables, ipo_date=st.ipo_date(code), groups=("Z_O",))
        tb = tables.for_code(code)
        dec = set(f.index)
        ev = {"lhb": cal.pos_array(pd.to_datetime(tb.lhb["上榜日"])) if len(tb.lhb) else np.zeros(0, int),
              "blk": cal.pos_array(pd.to_datetime(tb.blk["交易日期"])) if len(tb.blk) else np.zeros(0, int)}
        xi, _ = zo.clean_ins(tb.ins)
        rp = cal.roll_forward_pos(xi["notice"]) if len(xi) else np.zeros(0, int)
        ev["ins_buy"] = rp[(xi["DIRECTION"].values == "增持")] if len(xi) else rp
        ev["ins_sell"] = rp[(xi["DIRECTION"].values == "减持")] if len(xi) else rp
        col = {"lhb": "zo_lhb_ind_1", "blk": "zo_blk_ind_1", "ins_buy": "zo_ins_buy_ind_1", "ins_sell": "zo_ins_sell_ind_1"}
        lagc = {"lhb": "lhb", "blk": "blk", "ins_buy": "ins", "ins_sell": "ins"}
        for k in ev:
            lag = config.ZO_LAG[lagc[k]]
            pos = np.unique(ev[k][(ev[k] >= 0) & (ev[k] + lag < len(cal))])
            exp = {cal.days[q_ + lag] for q_ in pos} & dec
            exp = {t for t in exp if not np.isnan(f.at[t, col[k]])}
            got = set(f.index[f[col[k]] == 1.0])
            n_ev[k] += len(exp)
            n_ok[k] += len(exp & got)
            if exp != got:
                T["mismatches"].append({"code": code, "class": k, "expected_not_got": len(exp - got),
                                        "got_not_expected": len(got - exp)})
        # entry time and transaction dates never reach a feature
        if len(tb.ins):
            ins2 = tables.ins.copy()
            m = ins2["SECURITY_CODE"] == code.split(".")[1]
            ins2.loc[m, "EITIME"] = "1999-01-01 00:00:00"
            ins2.loc[m, "START_DATE"] = None
            t2 = zo.ZOTables(tables.lhb, tables.jg, tables.blk, ins2, tables.coverage)
            g = panel.build_stock_features(code, raw, cal, far, None, t2, ipo_date=st.ipo_date(code), groups=("Z_O",))
            a, b = f.values, g.values
            same = bool((((np.isnan(a) & np.isnan(b)) | (a.view(np.uint64) == b.view(np.uint64)))).all())
            eitime_same += int(same)
            if not same:
                T["mismatches"].append({"code": code, "class": "eitime_invariance"})
    T["per_class"] = {k: {"indicator_days_expected": n_ev[k], "indicator_days_matched": n_ok[k]} for k in n_ev}
    T["eitime_and_start_date_invariance_stocks_bit_identical"] = eitime_same
    T["stocks_with_ins_rows"] = int(sum(1 for c in trial if len(tables.for_code(c).ins)))
    res["timing_on_trial_stocks"] = T
    res["seconds"] = round(time.time() - t0, 1)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "zo_real_validation.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, default=str)
    brief = {
        "strict_coverage": res["strict_coverage"]["ok"],
        "rows": {k: res[k]["rows"] for k in ("lhb_detail", "lhb_jgmmtj", "dzjy_mrmx", "ins_raw")},
        "run_length": {"lhb": L["run_length"]["longest_run_without_a_record"], "blk": B["run_length"]["longest_run_without_a_record"],
                       "ins": I["run_length_any_direction"]["longest_run_without_a_record"]},
        "ins_cleaning": stats, "ins_backfilled_share": I["backfilled_gt30d_share_kept"],
        "ins_notice_non_trading_share": I["kept_notice_on_non_trading_day_share"],
        "ins_rows_by_regime": I["rows_by_regime_and_direction"],
        "timing": T["per_class"], "timing_mismatches": len(T["mismatches"]),
        "eitime_invariance": [T["eitime_and_start_date_invariance_stocks_bit_identical"], T["stocks_with_ins_rows"]],
    }
    print(json.dumps(brief, ensure_ascii=False, indent=1, default=str))
    return 1 if (T["mismatches"] or not res["strict_coverage"]["ok"]) else 0


if __name__ == "__main__":
    sys.exit(main())
