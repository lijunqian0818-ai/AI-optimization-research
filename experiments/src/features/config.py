"""Constants of the feature library (PLAN v0.7 sections 3.10, 3.11, 4.1, 5).

Every value that the plan marks PLACEHOLDER carries a status string here.
Values fixed by a ruling of PLAN v0.7 (Revision log, F-1 ... F-20) are marked
"PLAN v0.7 ruling F-n". Nothing in this file was tuned on data, and no rule
date, band or threshold of the exchanges is stored here: those are read from
the one rule calendar through `rules.py` (ruling F-20).
"""
from __future__ import annotations

import pandas as pd

# ---------------------------------------------------------------- B0 (PLAN 4.1)
B0_WINDOWS = (5, 10, 20, 30, 60)

# ---------------------------------------------------------------- Z_H (PLAN 5.1-5.3a)
CGO_N_PRIMARY = 250          # trading days (PLAN 5.1)
CGO_SKIP = 1                 # PLAN v0.7 ruling F-2: the original's one-period lag (one trading day here) is primary
CGO_N_VARIANT = 500          # pre-specified robustness definition (same one-day lag; F-2)
CGO_WEEKS_VARIANT = 260      # literal weekly transcription (Grinblatt-Han eq. 25 uses 260 weeks; F-2)
CHIP_WINDOW = 210            # PLAN 5.2 (default of the reference implementation)
CHIP_INIT_PRIMARY = "renormalise"          # PLAN v0.7 ruling F-3: no initial mass, divide by the mass turned over
CHIP_INIT_SENSITIVITY = "uniform_first_day"  # the v0.6 placeholder; robustness runs only, never a second column
CHIP_GRID = 150              # PLAN 5.2
CHIP_POST_SUSP_BLANK = 60    # PLACEHOLDER, PLAN 5.3a
CHIP_LONG_SUSP = CHIP_WINDOW // 2   # "suspension longer than W/2 days", PLACEHOLDER
ATO_SHORT = 20
ATO_LONG = 250

# ---------------------------------------------------------------- R (PLAN 5.4)
RH_RET_WINDOWS = (1, 5, 20, 60, 120, 250)       # stated in the plan
RH_MA_WINDOWS = (5, 20, 60, 120, 250)           # confirmed and frozen, PLAN v0.7 ruling F-15
RH_RANGE_WINDOWS = (20, 60, 120, 250)           # confirmed and frozen, PLAN v0.7 ruling F-15
RH_TURN_WINDOWS = (5, 20, 60, 120, 250)         # confirmed and frozen, PLAN v0.7 ruling F-15
RH_TURN_STD_WINDOWS = (20, 60, 250)             # confirmed and frozen, PLAN v0.7 ruling F-15
RH_TURN_CUM_WINDOWS = (20, 210, 250)            # confirmed and frozen, PLAN v0.7 ruling F-15
RH_HL_WINDOWS = (5, 20, 60, 250)                # confirmed and frozen, PLAN v0.7 ruling F-15
RH_UNDECAYED_WINDOWS = (210, 250)               # the two primary Z_H windows
RH_HIST_WINDOWS = (250, 210)                    # plan: windows used by Z_H
RH_HIST_BINS = 10                               # PLACEHOLDER, PLAN 5.4
# PLAN v0.7 ruling F-15: the cumulative-turnover bins are dropped (exactly collinear with the mean in equal bins)
RH_HIST_STATS = ("ret", "turn_mean", "vwp", "hl")

# ---------------------------------------------------------------- Z_O (PLAN 5.6)
ZO_LOOKBACKS = (1, 5, 20)    # PLACEHOLDER, PLAN 5.6.3
ZO_DAYS_SINCE_CAP = 60
ZO_PRIOR_LOOKBACK = 250      # PLAN v0.7 ruling F-5 (U60): look-back of `days_since` / `has_prior`, market trading days
ZO_ADV_WINDOW = 20           # PLAN v0.7 ruling F-7 (U40): the 20 most recent TRADED days ending t-1
# BLK premium (PLAN v0.8 ruling J-7, U64; task C-4): recomputed from our own bars as trade price / the
# unadjusted close of the trade day - 1; the vendor column 折溢率 is not used by any feature. Plausibility
# rule: a trade whose price lies outside [P_down, P_up] of the trade day (own preclose, rule-calendar band,
# the engine's limit-price function) or whose stock has no traded row that day is "implausible": it is left
# out of the amount-weighted premium and still counts for the indicator, days-since and amount intensity.
BLK_PREMIUM_SOURCE = "own_bars"                       # U64
BLK_PLAUSIBILITY_RULE = "inside_limit_band_and_traded_row"   # U64

# Availability lag in trading days (PLAN 5.6.2). An event of trading day s is
# usable for decision days t >= s + lag.
ZO_LAG = {"lhb": 2, "blk": 2, "ins": 2}
ZO_LAG_BASIS = {
    "lhb": "RC-18: disclosure conditions verified; the rule fixes no clock time of publication -> lag 2",
    "blk": ("RC-19: 'after the end of each trading day' verified for SZSE 2013/2026 and SSE 2023/2026 texts only; "
            "the clause for earlier years is NOT archived, so the plan's condition for lag 1 is not met -> lag 2"),
    "ins": "date-only stamp in the table -> lag 2; announcement date not verifiable from free data (OA10 not done)",
}

# Analysis start of each class = max(OA3 start, first day of the raw pull) (PLAN v0.7 ruling F-14).
# OA3: AUDIT_REPORT 3.3 found records from 2005 in all three tables, so the binding term is the start of
# the raw pull. The OA3 run-length check ("no run of 20 trading days without records") on the full pull is
# reported by tests/zo_real_validation.py; it is descriptive and does not move these dates by itself.
ZO_RAW_START = pd.Timestamp("2008-01-01")
ZO_RAW_END = pd.Timestamp("2026-06-30")
ZO_CLASS_START = {"lhb": ZO_RAW_START, "blk": ZO_RAW_START, "ins": ZO_RAW_START}
ZO_CLASS_START_STATUS = "max(OA3 start, 2008-01-01), PLAN v0.7 ruling F-14; OA3 formal check pending (FC-A8)"
# Production default of the coverage check (ruling F-14): a raw file missing from the snapshot inside the
# analysis period stops the pipeline. strict=False is for tests run while a pull is in progress only.
ZO_STRICT_COVERAGE = True

# INS intensities rest on the meaning of CHANGE_FREE_RATIO, inferred from column positions and pending the
# value check OA5 (PLAN v0.7 ruling F-10). If OA5 fails, set this to False: the INS intensity columns are
# then all-NaN (the columns stay in the catalogue; the INS indicators are kept).
INS_INTENSITY_ENABLED = True

# Diagnostic column (not a model feature; PLAN v0.7 rulings F-18 / E-16): 1 if a bar row inserted from the
# cross-check source lies in the last DIAG_XSRC_WINDOW rows ending t-1. 251 = the longest primary window
# (zh_cgo_250). The window length is the implementer's choice and is listed in the test report.
DIAG_XSRC_WINDOW = 251

# Regime dates, bands and thresholds (RC-6, RC-18, RC-20) are NOT stored here (PLAN v0.7 ruling F-20):
# see rules.py, which reads the rule calendar (experiments/src/engine/rule_calendar.py).
# Limit-count controls are NaN while their window contains any of a name's first FIRST_DAYS_NAN trading
# days, for every board and listing date (PLAN v0.7 ruling F-20; no registration-reform date is used).
FIRST_DAYS_NAN = 5
# (PLAN v0.8 ruling J-1, task C-3) The threshold of the proxy trigger "three consecutive trading days,
# cumulative deviation" (ro_trig_cum3_cnt_*) is the element `cum3` of the RC-18 rows of the rule calendar
# (unverified, PLAN 3.10 list item 22); the former copy RO_CUM3_THRESHOLD of this file is deleted.
INS_REGIME_NAMES = ("pre_20150708", "ban_20150708", "predisc_20160109", "predisc_ext_20170527", "predisc_blk_20240524")

# Proxy index for the "deviation" of the Dragon-Tiger criteria. The rule says
# "the corresponding category index"; which index was used in each year was
# NOT checked (PLAN 3.10 list item 20). Board proxy, labelled a proxy (PLAN v0.7, 5.4):
LHB_PROXY_INDEX = {("sse", "main"): "sh.000001", ("sse", "star"): "sh.000001",
                   ("szse", "main"): "sz.399001", ("szse", "chinext"): "sz.399006"}

# Fields of the vendor tables that a feature may read (OA2 whitelist).
WHITELIST = {
    "lhb_detail": ["代码", "上榜日", "龙虎榜净买额", "龙虎榜买入额", "龙虎榜卖出额", "龙虎榜成交额",
                   "市场总成交额", "净买额占总成交比", "成交额占总成交比", "上榜原因"],
    "lhb_jgmmtj": ["代码", "上榜日期", "买方机构数", "卖方机构数", "机构买入总额", "机构卖出总额",
                   "机构买入净额", "上榜原因"],
    "dzjy_mrmx": ["证券代码", "交易日期", "成交价", "折溢率", "成交量", "成交额", "成交额/流通市值"],
    "dzjy_mrtj": ["证券代码", "交易日期", "成交价", "折溢率", "成交笔数", "成交总量", "成交总额", "成交总额/流通市值"],
    # EITIME is read only to flag back-filled rows in diagnostics; it never enters a feature.
    # PLAN v0.7 ruling F-10: the mapping below is inferred from column POSITIONS in the upstream response and
    # is pending the value check OA5; if OA5 fails the INS intensity columns are dropped (INS_INTENSITY_ENABLED
    # = False) and the INS indicator columns are kept.
    # Field meaning per the AKShare source (stock_gdzjc_em.py, read locally): CHANGE_NUM = number of shares
    # changed, AFTER_CHANGE_RATE = change as a share of total shares, CHANGE_FREE_RATIO = change as a share
    # of float shares. The upstream column CHANGE_RATE is discarded by AKShare; its meaning is unknown (its
    # values look like a price change) and it is blacklisted.
    "ins_raw": ["SECURITY_CODE", "NOTICE_DATE", "DIRECTION", "CHANGE_NUM", "AFTER_CHANGE_RATE", "CHANGE_FREE_RATIO",
                "START_DATE", "END_DATE", "EITIME"],
}
# Ex-post / snapshot / name fields that must never be loaded (OA2).
BLACKLIST = {
    "lhb_detail": ["解读", "上榜后1日", "上榜后2日", "上榜后5日", "上榜后10日", "名称"],
    "lhb_jgmmtj": ["名称"],
    "dzjy_mrmx": ["证券简称", "买方营业部", "卖方营业部"],
    "dzjy_mrtj": ["证券简称"],
    "ins_raw": ["NEWEST_PRICE", "CHANGE_RATE_QUOTES", "CLOSE_PRICE", "CHANGE_RATE", "REAL_PRICE", "TRADE_AVERAGE_PRICE",
                "SECURITY_NAME_ABBR", "HOLDER_NAME"],
}
