# Formula-check record of the Z_H features (PLAN v0.7 §5.1, §5.3, §5.3a; ruling F-1; freeze item FC-A15)

> Written 2026-11-15 by the researcher who implemented `zh.py`. This file records what was compared with what.
> Its content is taken from the header of `zh.py` and from §2.3 of
> `experiments/results/feature_tests/FEATURE_TEST_REPORT.md`; nothing was re-read for it and no claim was added.
> **Status: checked against working-paper versions only, from text extracted without a renderer. Not reviewed by
> another model. The re-reading on rendered pages (FC-A15) has NOT been done.**

## 1. Texts used

| Feature | Text that was opened | Where in the text | Text that was NOT opened |
|---|---|---|---|
| Reference price, capital-gains overhang (`zh_cgo_*`) | Grinblatt & Han, "The Disposition Effect and Momentum", NBER Working Paper 8734, draft of October 2001 (the working-paper predecessor of the article cited as `grinblatt2005prospect`; the title differs) | Section II.B, eq. (25); Section II (the definition of the regressor and the remark on the one-week lag) | The published article (Journal of Financial Economics, 2005) |
| Abnormal turnover (`zh_ato_20_250*`) | Liu, Stambaugh & Yuan, "Size and Value in China", NBER Working Paper 24458, draft of March 2018 | The factor-construction section of the main text; Appendix, item 8 "Turnover" | The published article (Journal of Financial Economics, 2019) |
| Chip distribution (`zh_chip_*`) | `myhhub/stock`, `instock/core/kline/cyq.py` (Apache-2.0; all 169 lines read; reference only, re-implemented) | whole file | — (the method has no academic source) |

Both PDFs were downloaded with `tools/fetch_resource.py pdf:` (free versions) and are listed in `resources/MANIFEST.md`.

## 2. How the text was read — the limitation

The machine has no PDF renderer. The text was extracted from the PDF streams with a script written for the purpose.
**Greek letters and sub- / superscripts were lost in the extraction.** The formulas below were reconstructed from the
extracted text and its context (the surrounding sentences, the order of the symbols, the verbal descriptions). A
transcription error in a subscript or a product limit would not necessarily have been noticed. **Both formulas must be
re-read on rendered pages before Freeze-1 (FC-A15; task TODO-F8).** The journal versions were not compared; a
difference between a working paper and its published version would not have been seen. If the user supplies the journal
versions (PLAN §17.4 item 3) and they differ, the journal definition becomes primary before Freeze-1; otherwise the
working-paper definitions are frozen and the paper states which version was used.

## 3. What the texts say (as reconstructed), and what is implemented

### 3.1 Reference price and capital-gains overhang

Reconstructed from w8734, eq. (25) (weekly data):

    R_t = (1/k) * sum_{n=1}^{260} ( V_{t-n} * prod_{tau=1}^{n-1} [1 - V_{t-n+tau}] ) * P_{t-n},

with k the sum of the weights (so that they add to one), V turnover and P price. Section II: the regressor for the
return of week t is

    g_{t-1} = (P_{t-2} - R_{t-1}) / P_{t-2},

and the text says that the market price is lagged by one week "to avoid confounding market microstructure effects"
(the theory would use P_{t-1}).

Implemented (`zh.reference_price`, `zh.cgo`, `zh.cgo_weekly`):

| Column | Role | Definition |
|---|---|---|
| `zh_cgo_250` | **primary** (ruling F-2) | (P_{t-2} − RP_{t-1}) / P_{t-2}, RP_{t-1} from the 250 rows ending t−2; the formula above transcribed period for period with a period of one trading day |
| `zh_cgo_500` | pre-declared variant | the same with N = 500 (same one-day lag) |
| `zh_cgo_250_nolag` | pre-declared variant | (P_{t-1} − RP_t) / P_{t-1}: the wording of PLAN v0.6, without the lag |
| `zh_cgo_w260` | pre-declared variant | literal weekly transcription: w0 = the last completed calendar week before the decision day; weekly turnover = sum of the daily turnover of the week, capped at 1; weekly price = last adjusted close of the week; R_{w0} from the 260 completed weeks before w0; value (P_{w0−1} − R_{w0}) / P_{w0−1}; constant over the decision days of a week |

Weights, normalisation, sign and denominator agree with eq. (25) as reconstructed.

### 3.2 Abnormal turnover

From w24458: the main text describes the measure as the "past month's share turnover divided by the past year's
turnover"; the appendix item "Turnover" says: "the ratio of its average daily turnover over the past 20 days to its
average daily turnover over the past 250 days", with daily turnover = share trading volume divided by total shares
outstanding.

Implemented (`zh.abnormal_turnover`): `zh_ato_20_250` = mean(V, 20) / mean(V, 250), a ratio — **primary** (ruling F-2);
`zh_ato_20_250_log` = its logarithm (the wording of PLAN v0.6, written from memory) — pre-declared variant.
`zh_ato_short_20` = log(V_{t−1} / mean(V over the 20 days before t−1)) is in the primary set; no source in the
literature is claimed for it.

## 4. Declared deviations from the originals

| # | Deviation | Applies to | Why |
|---|---|---|---|
| 1 | Daily data: N = 250 trading days in place of 260 weeks; the one-period lag is one trading day | `zh_cgo_250`, `zh_cgo_500`, `zh_cgo_250_nolag` | The decision frequency of the study is daily (PLAN §5.1). `zh_cgo_w260` keeps the weekly frequency |
| 2 | Turnover is volume over **tradable (float) shares** — the bar source's `turn` field. Both originals use total shares outstanding | all CGO columns, `zh_ato_*` | The bar source has no share-capital series. A share-capital pull is PLAN §17.4 item 2 (the user's decision; default: not fetched, deviation declared, no total-share variant computed) |
| 3 | Prices are the feature-level total-return series of PLAN §3.11 (close × own factor built from `preclose`) | all CGO columns | One adjustment rule for all features; no vendor factor is read |
| 4 | Turnover above 1 is capped at 1 inside the decay recursion (count reported; sensitivity: drop the windows) | CGO, chips | PLAN §5.3a; the weights (1 − V) are meaningless for V > 1. Not capped in `zh_ato_*` (no recursion) |

## 5. Chip distribution — differences from the reference implementation (no academic source)

Rulings of PLAN v0.7 F-3, made without computing any relation to returns: rolling 210-row window rebuilt for every
data day; the chips of day j carry exactly the mass V_j (the reference adds density heights, so the mass of a
one-price day depends on the grid); **no initial mass, the distribution divided by the mass turned over inside the
window** (primary; this is what the reference does) — the v0.6 placeholder (never-traded mass spread uniformly on the
first window day's range) is a sensitivity option of `chip_stats(init="uniform_first_day")` used in robustness runs
only; mean cost primary (closed form), the median — which the reference calls "average cost" — is the variant
`zh_chip_cost_gap_median`; band widths are (q95 − q05) / P_{t−1} and (q85 − q15) / P_{t−1}, not the reference's
(high − low) / (high + low).

## 6. Open items

- Re-read eq. (25) and Section II of w8734, and the appendix item "Turnover" of w24458, on rendered pages (FC-A15,
  TODO-F8) and correct this record if the reconstruction was wrong.
- Journal versions: not compared (PLAN §17.4 item 3).
- Total-share turnover: not available (PLAN §17.4 item 2).
