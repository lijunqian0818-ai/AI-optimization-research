"""Z_H -- holder-state variables (PLAN v0.7 sections 5.1-5.3a).

Inputs: P = close adjusted by the own preclose-chain factor (total-return
units), V = daily turnover as a fraction of TRADABLE (float) shares (BaoStock
`turn`/100).

PRIMARY DEFINITIONS (PLAN v0.7 rulings F-1, F-2, F-3; fixed before any
outcome was looked at; the record of the formula check is features.md)

* `zh_cgo_250` = (P_{t-2} - RP_{t-1}) / P_{t-2}: the working paper's timing
  (the price is lagged one period; one trading day here). `cgo(..., skip=1)`.
  Variants: `zh_cgo_250_nolag` = (P_{t-1} - RP_t) / P_{t-1} (the v0.6
  wording); `zh_cgo_500` (N = 500, same one-day lag); `zh_cgo_w260` (literal
  weekly transcription, `cgo_weekly`).
* `zh_ato_20_250` = mean(V, 20) / mean(V, 250), a ratio (not in logs).
  Variant: `zh_ato_20_250_log`. `zh_ato_short_20` is in the primary set (no
  literature source claimed).
* chip statistics: rolling 210-row window, exact mass V per day, NO initial
  mass, the distribution divided by the mass that turned over inside the
  window (`init="renormalise"`). `init="uniform_first_day"` (the v0.6
  placeholder) is a sensitivity option for robustness runs only; it never
  produces a second column. Mean cost primary, median the variant
  `zh_chip_cost_gap_median`.

FORMULA CHECK (done on 2026-11-15 against the NBER working-paper versions,
which are what could be opened; the journal versions were NOT opened, so a
difference between working paper and published article would not have been
seen; the PDF text was extracted without a renderer -- Greek letters and
sub/superscripts were lost -- and must be re-read on rendered pages, FC-A15):

* Grinblatt & Han, NBER working paper w8734 ("The Disposition Effect and
  Momentum", version of October 2001 -- the working-paper predecessor of the
  2005 JFE article cited as `grinblatt2005prospect`), section II.B, eq. (25):
      R_t = (1/k) sum_{n=1}^{260} ( V_{t-n} prod_{tau=1}^{n-1} [1 - V_{t-n+tau}] ) P_{t-n},
  k = the sum of the weights; weekly data; and (section II.A)
      g_{t-1} = (P_{t-2} - R_{t-1}) / P_{t-2}
  is the regressor for the week-t return ("we lag the market price by one
  week to avoid confounding market microstructure effects"; theory would use
  P_{t-1}). Declared deviations of the primary definition: (i) daily instead
  of weekly data, N = 250 days instead of 260 weeks; (ii) turnover is volume /
  tradable shares, G&H use volume / shares outstanding (PLAN 17.4 item 2);
  (iii) prices are our total-return series.

* Liu, Stambaugh & Yuan, NBER working paper w24458 ("Size and Value in
  China", March 2018), Appendix section 8 "Turnover": "A firm's abnormal
  turnover is calculated as the ratio of its average daily turnover over the
  past 20 days to its average daily turnover over the past 250 days", daily
  turnover = "share trading volume divided by its total shares outstanding".
  Declared deviation: tradable-share instead of total-share turnover (total
  shares are not in the bar source; PLAN 17.4 item 2).

Every formula below is a separate function so that it can be replaced.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from . import ops
from .config import (CGO_N_PRIMARY, CGO_N_VARIANT, CGO_SKIP, CGO_WEEKS_VARIANT, CHIP_WINDOW, CHIP_GRID,
                     CHIP_POST_SUSP_BLANK, CHIP_LONG_SUSP, CHIP_INIT_PRIMARY, ATO_SHORT, ATO_LONG)
from .registry import FeatureSpec, BAR_TIMING
from .timing import TradingCalendar, check_cutoff, truncate_bars, to_decision_index

_GH = ("Grinblatt & Han eq. (25) and section II: checked against NBER working paper w8734 (2001); journal version "
       "(JFE 2005) not compared; text extracted without a renderer, to be re-read (FC-A15). Declared deviations: "
       "daily data (N trading days for 260 weeks), tradable-share turnover, total-return prices")
_LSY = ("checked against NBER w24458 (factor-construction section and appendix 'Turnover'); journal version (JFE "
        "2019) not compared; denominator is tradable (float) shares, the original uses total shares (declared "
        "deviation, PLAN 17.4 item 2)")
_CYQ = ("turnover-decay chip distribution; no academic source; reference myhhub/stock cyq.py (Apache-2.0) read, "
        "re-implemented; rulings of PLAN v0.7 F-3: rolling window, exact mass V per day, no initial mass + "
        "renormalisation (primary), mean cost, band = quantile difference / P")


# ----------------------------------------------------------------------------
# turnover handling (PLAN 5.3a)
# ----------------------------------------------------------------------------
def cap_turnover(v: np.ndarray, mode: str = "cap") -> tuple[np.ndarray, int]:
    """V used inside the decay recursions. mode 'cap': V > 1 -> 1 (PLAN 5.3a,
    PLACEHOLDER); mode 'nan': V > 1 -> NaN, so every window that contains the
    day is dropped (the plan's sensitivity). V < 0 is always NaN. Returns the
    array and the number of stock-days with V > 1 (audit A19)."""
    v = np.asarray(v, dtype=np.float64).copy()
    n_gt1 = int(np.nansum(v > 1))
    v[v < 0] = np.nan
    if mode == "cap":
        v[v > 1] = 1.0
    elif mode == "nan":
        v[v > 1] = np.nan
    else:
        raise ValueError(mode)
    return v, n_gt1


def decay_weights(vw: np.ndarray) -> np.ndarray:
    """Rows = windows (oldest first). w_j = V_j * prod_{k > j} (1 - V_k):
    the share of today's holders whose shares last traded on day j."""
    one_minus = 1.0 - vw
    surv_incl = np.cumprod(one_minus[:, ::-1], axis=1)[:, ::-1]      # prod_{k >= j}
    surv_excl = np.ones_like(vw)
    surv_excl[:, :-1] = surv_incl[:, 1:]                             # prod_{k > j}
    return vw * surv_excl


# ----------------------------------------------------------------------------
# 5.1 capital-gains overhang
# ----------------------------------------------------------------------------
def reference_price(p: np.ndarray, v: np.ndarray, n: int) -> np.ndarray:
    """RP as of data date s: sum_{j=s-n+1..s} w_j P_j / sum_j w_j (eq. 25 with
    the window ending at s). NaN unless n rows are available and finite, or
    if no share traded in the window (k = 0)."""
    out = np.full(len(p), np.nan)
    if len(p) < n:
        return out
    vw = sliding_window_view(v, n)
    pw = sliding_window_view(p, n)
    with np.errstate(all="ignore"):
        w = decay_weights(vw)
        k = w.sum(axis=1)
        rp = (w * pw).sum(axis=1) / k
    ok = np.isfinite(vw).all(axis=1) & np.isfinite(pw).all(axis=1) & (k > 0)
    out[n - 1:] = np.where(ok, rp, np.nan)
    return out


def cgo(p: np.ndarray, v: np.ndarray, n: int, skip: int = CGO_SKIP) -> np.ndarray:
    """CGO as of data date s (decision day t = next(s)).

    skip = 1 (PRIMARY, PLAN v0.7 ruling F-2): the working paper's timing,
    (P_{s-1} - RP_{s-1}) / P_{s-1} = (P_{t-2} - RP_{t-1}) / P_{t-2} in the
    plan's notation, where the reference price is built from the n rows
    ending t-2. Needs n + 1 rows.
    skip = 0 (variant, the v0.6 wording): (P_s - RP_s) / P_s =
    (P_{t-1} - RP_t) / P_{t-1}; needs n rows."""
    rp = reference_price(p, v, n)
    with np.errstate(all="ignore"):
        g = (p - rp) / p
    return ops.ref(g, skip)


def cgo_weekly(p: np.ndarray, v: np.ndarray, dates: pd.DatetimeIndex, cal: TradingCalendar,
               n_weeks: int = CGO_WEEKS_VARIANT) -> np.ndarray:
    """Weekly variant `zh_cgo_w260`: a literal transcription of the working
    paper (PLAN v0.7 ruling F-2, section 5.1).

    Weeks are ISO calendar weeks. A week is complete on its last market
    trading day (the calendar is pre-open public information). Weekly
    turnover = sum of the daily V of the week, capped at 1; weekly price =
    the last adjusted close of the week. For data date s (decision day
    t = next(s)) let w0 be the last week complete by s, i.e. the last
    completed week before the decision day. With eq. (25) on weeks,

        R_{w0} = (1/k) sum_{n=1}^{260} V_{w0-n} prod_{tau=1}^{n-1} (1 - V_{w0-n+tau}) P_{w0-n}

    (the 260 completed weeks BEFORE w0), the value is

        g = (P_{w0-1} - R_{w0}) / P_{w0-1},

    the paper's regressor g_{t-1} for the return of week t = w0 + 1, the week
    of the decision day. The value is the same for every decision day of a
    calendar week. Needs 261 completed weeks (w0 and the 260 before it); NaN
    if any of the 260 weeks has a missing input or no share traded in them.
    """
    n = len(p)
    out = np.full(n, np.nan)
    if n == 0:
        return out
    iso = dates.isocalendar()
    wk = iso["year"].values.astype(np.int64) * 100 + iso["week"].values.astype(np.int64)
    ciso = cal.days.isocalendar()
    cwk = ciso["year"].values.astype(np.int64) * 100 + ciso["week"].values.astype(np.int64)
    last_of_week = pd.Series(cal.days, index=cwk).groupby(level=0).max()
    starts = np.r_[0, np.nonzero(wk[1:] != wk[:-1])[0] + 1]        # first row of each week
    ends = np.r_[starts[1:] - 1, n - 1]                            # last row of each week
    wv = np.minimum(np.add.reduceat(v, starts), 1.0)               # NaN propagates
    wp = p[ends]
    complete = dates[ends].values == last_of_week.loc[wk[ends]].values
    # g_w[k] = (P_{k-1} - R_k) / P_{k-1}, R_k from the n_weeks weeks before week k
    g_w = cgo(wp, wv, n_weeks, skip=1)
    comp = np.nonzero(complete)[0]
    if len(comp) == 0:
        return out
    j = np.searchsorted(ends[comp], np.arange(n), side="right") - 1   # last week complete by row i  (= w0)
    ok = j >= 0
    out[ok] = g_w[comp[j[ok]]]
    return np.where(np.isfinite(out), out, np.nan)


# ----------------------------------------------------------------------------
# 5.2 chip distribution
# ----------------------------------------------------------------------------
def tri_cdf(x: np.ndarray, lo: np.ndarray, hi: np.ndarray, mode: np.ndarray) -> np.ndarray:
    """CDF at x (shape (m,)) of triangular densities on [lo_j, hi_j] peaking
    at mode_j (shape (n,)). Returns (n, m). A one-price day (hi == lo) is a
    point mass: CDF = 1{x >= lo}."""
    x = x[None, :]
    lo, hi, mode = lo[:, None], hi[:, None], mode[:, None]
    width = hi - lo
    with np.errstate(all="ignore"):
        left = (x - lo) ** 2 / (width * (mode - lo))
        right = 1.0 - (hi - x) ** 2 / (width * (hi - mode))
    cdf = np.where(x <= mode, left, right)
    cdf = np.where(x <= lo, 0.0, cdf)
    cdf = np.where(x >= hi, 1.0, cdf)
    # degenerate shapes
    cdf = np.where((mode <= lo) & (x > lo) & (x < hi), right, cdf)    # peak at the low
    cdf = np.where((mode >= hi) & (x > lo) & (x < hi), left, cdf)     # peak at the high
    cdf = np.where(width <= 0, (x >= lo).astype(float), cdf)
    return cdf


def chip_distribution(lo, hi, mode, w, r0, grid: int = CHIP_GRID, init: str = CHIP_INIT_PRIMARY):
    """Chip mass on a grid for ONE window.

    lo, hi, mode: (W,) adjusted low / high / (O+H+L+C)/4 of the window's days,
    oldest first. w: decay weights of the days (mass added on day j that is
    still held), r0 = prod_j (1 - V_j) = the mass that did not trade inside
    the window. init: 'renormalise' (PRIMARY, PLAN v0.7 ruling F-3) -- no
    initial mass; the caller divides by the returned total = sum of w, the
    mass that turned over inside the window (what the reference
    implementation does, and the normalisation of the reference price);
    'uniform_first_day' (sensitivity, the v0.6 placeholder) -- r0 is spread
    uniformly on the first day's [low, high] (total mass exactly 1).

    Returns (edges (G+1,), cum (G+1,), total): cum[i] = mass below edges[i].
    The grid spans the window's [min low, max high] in G equal cells; mass per
    cell is exact (difference of CDFs at the edges), a point mass goes to the
    cell that contains it.
    """
    pmin, pmax = lo.min(), hi.max()
    edges = np.linspace(pmin, pmax, grid + 1)
    cdf = tri_cdf(edges, lo, hi, mode)
    mass = (w[:, None] * cdf).sum(axis=0)      # no BLAS call (bit-reproducibility)
    total = w.sum()
    if init == "uniform_first_day":
        width = hi[0] - lo[0]
        if width > 0:
            u = np.clip((edges - lo[0]) / width, 0.0, 1.0)
        else:
            u = (edges >= lo[0]).astype(float)
        mass = mass + r0 * u
        total = total + r0
    elif init != "renormalise":
        raise ValueError(init)
    mass[0] = 0.0          # all mass lies in [pmin, pmax]
    mass[-1] = total
    cum = np.maximum.accumulate(mass)
    return edges, cum, total


def _cum_at(price, edges, cum):
    """Mass at prices below `price` (piecewise-linear inside a cell)."""
    return np.interp(price, edges, cum)


def _quantile(target, edges, cum):
    """Smallest price at which the cumulative mass reaches `target`."""
    i = int(np.searchsorted(cum, target, side="left"))
    if i <= 0:
        return edges[0]
    if i >= len(cum):
        return edges[-1]
    return edges[i - 1] + (target - cum[i - 1]) / (cum[i] - cum[i - 1]) * (edges[i] - edges[i - 1])


def chip_stats(b: pd.DataFrame, window: int = CHIP_WINDOW, grid: int = CHIP_GRID,
               init: str = CHIP_INIT_PRIMARY, v_mode: str = "cap",
               long_susp: int = CHIP_LONG_SUSP, blank: int = CHIP_POST_SUSP_BLANK) -> pd.DataFrame:
    """Chip statistics as of each data date s (PLAN 5.2), from rows <= s.

    Outputs (P = adjusted close of s):
      pr        share of chip mass at prices below P
      cost_gap  (P - mean cost) / P; mean cost in closed form
                (triangle mean = (low + high + mode) / 3)
      cost_gap_median  (P - median cost) / P  [the reference implementation's
                "average cost" is the median; variant]
      band90, band70  (q_{.95} - q_{.05}) / P and (q_{.85} - q_{.15}) / P
      overhead  share of mass in (P, 1.1 P]
    NaN until `window` rows have elapsed since the first traded row, when any
    input in the window is missing, when the total mass is 0 (with
    init='renormalise': no share turned over inside the window), and for
    `blank` rows after a spell of more than `long_susp` consecutive non-traded
    rows (PLAN 5.3a, PLACEHOLDERS).
    """
    names = ["pr", "cost_gap", "cost_gap_median", "band90", "band70", "overhead"]
    n = len(b)
    res = {k: np.full(n, np.nan) for k in names}
    if n >= window:
        lo, hi, c = b["alow"].values, b["ahigh"].values, b["aclose"].values
        md = (b["aopen"].values + hi + lo + c) / 4.0
        v, _ = cap_turnover(b["V"].values, v_mode)
        traded = b["traded"].values
        first_traded = int(np.argmax(traded)) if traded.any() else n
        blocked = _post_suspension_block(traded, long_susp, blank)
        vw = sliding_window_view(v, window)
        with np.errstate(all="ignore"):
            wts = decay_weights(vw)
            r0 = np.prod(1.0 - vw, axis=1)
        fin = np.isfinite(lo) & np.isfinite(hi) & np.isfinite(md) & np.isfinite(v) & np.isfinite(c)
        fin_w = sliding_window_view(fin, window).all(axis=1)
        for i in range(window - 1, n):
            k = i - window + 1
            if k < first_traded or not fin_w[k] or blocked[i]:
                continue
            sl = slice(k, i + 1)
            edges, cum, total = chip_distribution(lo[sl], hi[sl], md[sl], wts[k], r0[k], grid, init)
            if not total > 0:
                continue
            p = c[i]
            res["pr"][i] = _cum_at(p, edges, cum) / total
            mean_cost = (wts[k] * (lo[sl] + hi[sl] + md[sl]) / 3.0).sum()
            if init == "uniform_first_day":
                mean_cost += r0[k] * (lo[k] + hi[k]) / 2.0
            mean_cost /= total
            res["cost_gap"][i] = (p - mean_cost) / p
            res["cost_gap_median"][i] = (p - _quantile(0.5 * total, edges, cum)) / p
            res["band90"][i] = (_quantile(0.95 * total, edges, cum) - _quantile(0.05 * total, edges, cum)) / p
            res["band70"][i] = (_quantile(0.85 * total, edges, cum) - _quantile(0.15 * total, edges, cum)) / p
            res["overhead"][i] = (_cum_at(1.1 * p, edges, cum) - _cum_at(p, edges, cum)) / total
    return pd.DataFrame(res, index=b.index)


def _post_suspension_block(traded: np.ndarray, long_susp: int, blank: int) -> np.ndarray:
    """True on the `blank` rows that follow a run of more than `long_susp`
    consecutive non-traded rows (and inside such a run from the point where it
    exceeds `long_susp`). Causal: row i depends on rows <= i."""
    n = len(traded)
    blocked = np.zeros(n, dtype=bool)
    run = 0
    remaining = 0
    for i in range(n):
        if not traded[i]:
            run += 1
            if run > long_susp:
                blocked[i] = True
                remaining = blank
        else:
            run = 0
            if remaining > 0:
                blocked[i] = True
                remaining -= 1
    return blocked


# ----------------------------------------------------------------------------
# 5.3 abnormal turnover
# ----------------------------------------------------------------------------
def abnormal_turnover(v: np.ndarray, short: int = ATO_SHORT, long: int = ATO_LONG) -> np.ndarray:
    """mean(V, last `short` days) / mean(V, last `long` days) (LSY 2019)."""
    with np.errstate(all="ignore"):
        r = ops.r_mean(v, short) / ops.r_mean(v, long)
    return np.where(np.isfinite(r), r, np.nan)


def abnormal_turnover_short(v: np.ndarray, n: int = ATO_SHORT) -> np.ndarray:
    """log( V_s / mean(V over the n days before s) ) (PLAN 5.3 short-window
    variant). NaN when either term is zero."""
    with np.errstate(all="ignore"):
        r = np.log(v / ops.ref(ops.r_mean(v, n), 1))
    return np.where(np.isfinite(r), r, np.nan)


# ----------------------------------------------------------------------------
# assembly
# ----------------------------------------------------------------------------
def specs() -> list[FeatureSpec]:
    S = FeatureSpec
    chip_f = ("turnover-decay chips, rolling W=210, G=150, triangular density on [low, high] peaking at (O+H+L+C)/4, "
              "no initial mass, divided by the mass turned over in the window; ")
    w = "RP = sum_n w_n P / sum_n w_n, w_n = V_{.-n} prod_{tau<n} (1 - V_{.-n+tau})"
    return [
        S("zh_cgo_250", "Z_H", "primary", "(P_{t-2} - RP_{t-1})/P_{t-2}; RP_{t-1} from the 250 rows ending t-2; " + w,
          "251", "close (adj), turn", CGO_N_PRIMARY + 1, BAR_TIMING,
          _GH + "; PRIMARY = the original's one-period lag (PLAN v0.7 F-2)"),
        S("zh_cgo_500", "Z_H", "variant", "same as zh_cgo_250 with N = 500 (same one-day lag)", "501",
          "close (adj), turn", CGO_N_VARIANT + 1, BAR_TIMING, _GH + "; pre-declared variant (window length)"),
        S("zh_cgo_250_nolag", "Z_H", "variant", "(P_{t-1} - RP_t)/P_{t-1}; RP_t from the 250 rows ending t-1 "
          "(the v0.6 wording, no extra lag)", "250", "close (adj), turn", CGO_N_PRIMARY, BAR_TIMING,
          _GH + "; pre-declared variant (PLAN v0.7 F-2)"),
        S("zh_cgo_w260", "Z_H", "variant", "(P_{w0-1} - R_{w0})/P_{w0-1}; w0 = last completed calendar week before "
          "t; R_{w0} = eq. (25) on the 260 completed weeks before w0 (weekly V = sum of daily V capped at 1, weekly "
          "P = last adjusted close of the week); constant within a week",
          "261 weeks", "close (adj), turn", 261 * 5, BAR_TIMING,   # approximate: holidays shorten weeks
          _GH + "; pre-declared variant: literal weekly transcription (PLAN v0.7 F-2); declared warm-up in rows is "
          "approximate"),
        S("zh_chip_pr", "Z_H", "primary", chip_f + "share of mass below P_{t-1}", "210", "O/H/L/C (adj), turn", 210,
          BAR_TIMING, _CYQ),
        S("zh_chip_cost_gap", "Z_H", "primary", chip_f + "(P_{t-1} - mean cost)/P_{t-1}", "210", "O/H/L/C (adj), turn",
          210, BAR_TIMING, _CYQ),
        S("zh_chip_band90", "Z_H", "primary", chip_f + "(q95 - q05)/P_{t-1}", "210", "O/H/L/C (adj), turn", 210,
          BAR_TIMING, _CYQ),
        S("zh_chip_band70", "Z_H", "primary", chip_f + "(q85 - q15)/P_{t-1}", "210", "O/H/L/C (adj), turn", 210,
          BAR_TIMING, _CYQ),
        S("zh_chip_overhead", "Z_H", "primary", chip_f + "share of mass in (P_{t-1}, 1.1 P_{t-1}]", "210",
          "O/H/L/C (adj), turn", 210, BAR_TIMING, _CYQ),
        S("zh_chip_cost_gap_median", "Z_H", "variant", chip_f + "(P_{t-1} - median cost)/P_{t-1}", "210",
          "O/H/L/C (adj), turn", 210, BAR_TIMING, _CYQ + "; pre-declared variant (median instead of mean)"),
        S("zh_ato_20_250", "Z_H", "primary", "mean(V, 20) / mean(V, 250) (a ratio, not in logs)", "250", "turn", 250,
          BAR_TIMING, _LSY + "; PRIMARY (PLAN v0.7 F-2)"),
        S("zh_ato_20_250_log", "Z_H", "variant", "log of zh_ato_20_250 (PLAN v0.6 section 5.3 as written)", "250",
          "turn", 250, BAR_TIMING, _LSY + "; pre-declared variant"),
        S("zh_ato_short_20", "Z_H", "primary", "log( V_{t-1} / mean(V_{t-21..t-2}) )", "21", "turn", 21, BAR_TIMING,
          "PLAN 5.3 short-window feature, in the primary set; no literature source claimed"),
    ]


PRIMARY = [s_.name for s_ in specs() if s_.role == "primary"]
VARIANTS = [s_.name for s_ in specs() if s_.role == "variant"]


def zh_on_data_dates(b: pd.DataFrame, cal: TradingCalendar, v_mode: str = "cap",
                     chip_init: str = CHIP_INIT_PRIMARY, weekly: bool = True) -> pd.DataFrame:
    """Z_H as of each data date s (rows <= s only). `chip_init` other than
    the primary 'renormalise' is for the pre-declared sensitivity run only;
    it replaces the chip columns, it never adds columns."""
    p = b["aclose"].values
    v, n_gt1 = cap_turnover(b["V"].values, v_mode)
    cols = {
        "zh_cgo_250": cgo(p, v, CGO_N_PRIMARY, skip=CGO_SKIP),
        "zh_cgo_500": cgo(p, v, CGO_N_VARIANT, skip=CGO_SKIP),
        "zh_cgo_250_nolag": cgo(p, v, CGO_N_PRIMARY, skip=0),
        "zh_cgo_w260": cgo_weekly(p, v, b.index, cal) if weekly else np.full(len(b), np.nan),
    }
    chips = chip_stats(b, init=chip_init, v_mode=v_mode)
    cols["zh_chip_pr"] = chips["pr"].values
    cols["zh_chip_cost_gap"] = chips["cost_gap"].values
    cols["zh_chip_band90"] = chips["band90"].values
    cols["zh_chip_band70"] = chips["band70"].values
    cols["zh_chip_overhead"] = chips["overhead"].values
    cols["zh_chip_cost_gap_median"] = chips["cost_gap_median"].values
    raw_v = b["V"].values           # ATO has no decay recursion: no cap (PLAN 5.3a "inside the recursions only")
    ato = abnormal_turnover(raw_v)
    cols["zh_ato_20_250"] = ato
    with np.errstate(all="ignore"):
        la = np.log(ato)
    cols["zh_ato_20_250_log"] = np.where(np.isfinite(la), la, np.nan)
    cols["zh_ato_short_20"] = abnormal_turnover_short(raw_v)
    out = pd.DataFrame(cols, index=b.index)
    out.attrs["n_V_gt_1"] = n_gt1
    out.attrs["chip_init"] = chip_init
    return out[[s.name for s in specs()]]


def zh_features(bars: pd.DataFrame, cal: TradingCalendar, cutoff, **kw) -> pd.DataFrame:
    """Z_H for decision days <= `cutoff`. Uses bar rows dated < cutoff only."""
    t = check_cutoff(cal, cutoff)
    return to_decision_index(zh_on_data_dates(truncate_bars(bars, t), cal, **kw), cal)
