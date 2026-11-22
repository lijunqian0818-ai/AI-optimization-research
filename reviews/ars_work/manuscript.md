# Research design under review (pre-experiment; no results exist)

## Part A. Stated research question and hypotheses (v3)

## v3 调整方向（2026-11-15，关卡 1 用户决定"调整方向后继续"）

**以本节为准；与上文冲突处作废。** 依据：`literature/positioning.md`、`reviews/novelty_check_1.md`。

**主问题（RQ-v3）：** 在 A 股日频、只做多、T+1、含成本与真实可成交性的条件下，叠加在多因子信号之上的选择性交易（出手 / 弃权）带来的表观改善，来自哪里——选股、择时，还是市场暴露、执行成本与资金利用率的变化？持有人状态变量 Z（筹码成本 / 资本利得悬挂、异常换手等）对此有没有增量价值？

**两个评价问题（分开回答）**
- Q-总价值：部署后的策略是否改善投资者结果？对照是同初始资金、同执行规则、同成本模型的可行策略。
- Q-选股：在给定暴露下，选择器是否改善了选股？对照是日内匹配入场数、投入资金、预设风险特征的选择；归因基准是把候选门控的资金配置时间表套到未门控的基础组合上。

**假设（预先设定，可证伪）**
- H-A（归因）：已有弃权方法（置信度过滤、已到期表现门控、通用亏损预测）在指定绩效指标上的表观改善，大部分可被暴露与成本感知的对照复现。用预先设定的等价界判断"增量选股价值在经济意义上很小"。
- H-Z（析因）：Z 的价值按 2×2 析因检验——基础预测器含 / 不含 Z × 门控含 / 不含 Z，再加"同样特征直接按期望净收益选股"。对照中包含构造 Z 所用的价格与换手原料。
- H-T（理论，待核对后才承诺）：在标签最迟 H 天到期、同日多股任意相关、重叠持仓的交易流上，对"入场时条件亏损概率的平均"给出时间一致的监控界。只在核对 CSA / A-RCPS / 延迟反馈文献后确认不是已知推论时才作为定理；否则放附录。
- H-M（机制支线，限时两周）：最小的行为卖压模型能否推出关于持有期 × 卖压持续性 × 流动性的、能与竞争解释区分的联合限制。止损标准：推不出可识别的预测。

**措辞约束**
- Z 称为"持有人状态 / 行为变量"，不称"对手私有信息的度量"。
- 不写"首次把弃权 / 扑克思维用于股票交易"；扑克只作动机。
- 理论只说"监控"，不说"保证不亏"。亏损频率是次要指标；主要指标预先指定为净组合表现、亏损幅度、换手、被弃交易的收益。
- 强化学习是可选对比基线，不是卖点。

**目标会议 / 期刊（暂定）：** ACM ICAIF 或 Journal of Financial Data Science。



## Part B. Experiment plan (experiments/PLAN.md, v0.4)

# Experiment Plan (DRAFT v0.4)

> Authors: researcher (Task B; v0.1, v0.2, v0.3, and this synchronisation revision v0.4). Date: 2026-11-15. Status: **draft for Gate 2; nothing has been run on market data, no model has been fitted, nothing was downloaded or installed for this revision.** v0.4 synchronises the plan with the final theory files and does not redesign any experiment; every change from v0.3 is listed in "Revision log (v0.3 → v0.4)" at the end (items T1–T9 and a consistency check); the older logs are kept below it.
> Governing documents: `00_idea/research_question.md` (section "v3" governs), **`theory/setup.md` (abstract setting: G_t, F_t, A1, A1-G, A2–A5, A4-D, d_label, d — governs all abstract definitions), `theory/instantiation_ashare.md` (A-share operational conventions; cited below as "I-§n"; its §8 is the checklist this revision implements; by its own header everything in it is an unverified modelling assumption or a convention), `theory/theorems.md` (statements and status table)**, `reviews/proof_check_3.md` (items X1–X12, K1–K2), `reviews/plan_review_1.md` (items P1–P12), `experiments/data_feasibility_opponent_actions.md` (interface probe, audit items OA1–OA9), `literature/opponent_action_variables.md` (**its author states that every paper in it was read at abstract or bibliographic level only; no full text**), `literature/positioning.md` §2, `resources/DOWNLOAD_LIST.md`.
> **Status of the theory this plan refers to (sources: the status table of `theory/theorems.md`, `reviews/proof_check_3.md` §4, `STATUS.md`). No result is called a theorem in the sense of `CLAUDE.md` rule 3, and nothing below is "proved"; "Theorem 1" etc. are labels of `theorems.md`.**
> - Theorem 1(a)(b)(c), Corollaries 1.1 and 1.2, Proposition 2, the identity of Lemma 3, Remark 4: label in `theorems.md` `自查通过` (author's label); the lead records them as "GPT 审过（半独立）、Gemini 审过（Flash）". Three external review rounds (GPT, semi-independent; Gemini Flash) reported no error in their proofs or constants. **The revisions made after round 3 (moving the operational layer out of `setup.md`, A1-G, A2(b), the accounting reading of Lemma 3) have not been re-reviewed.** `theory/prior_theorems_audit.md` judges Theorem 1 essentially a corollary of known results; the novelty of Proposition 2 is unverified.
> - **Corollary 1.3: `草稿`.** In round 3 the two reviewers disagreed (Gemini Flash: correct; GPT: counterexample under a missing-data fallback). It was rewritten with certified bracket labels and assumption CERT; the rewrite is unreviewed. Every use of Corollary 1.3 below is **conditional on the result surviving review**.
> - The A-share instantiation (execution model, valuation tree, lags, distributions) is not part of any statement; whether A1–A5 hold for our trade stream is an audit question (§2.4), not a reviewed result.
> - If a later review changes a statement, the experiments citing it are revised before they are run.
> Conventions: "UNVERIFIED" = not checked against a primary source or not measured on real data. "[rule: tbv]" = an exchange / regulator rule that must be verified against the official text (audit items RV1–RV13, §2.4). "PLACEHOLDER" = a value proposed here that the user must confirm before any outcome is looked at (collected in §17). "ESTIMATE" = computed from formulas and assumed sample sizes, not from data. "Pending user confirmation at Gate 2" = a design proposal of the lead / researcher that the user may veto. **This plan makes no statement about what any result will be.**
> **Standing qualifier (T1).** The backtest has daily bars only. All fills in it are **retrospective synthetic fills under rule SF** (§3.1–3.2; I-§2.4) with the artificial filtration F_t^syn. Every monitoring quantity (H-T) and every statement citing Theorem 1 or its corollaries on market data refers to **the synthetic fill stream, not to an executable strategy**, and must be worded so.

---

## 1. Scope and non-goals

**What the paper tests.**
1. *Attribution (H-A).* On A-share daily, long-only, T+1 data with costs and tradability constraints: is the apparent improvement of selective trading (trade / abstain on top of a multi-factor signal) attributable to within-batch stock selection, to the exposure schedule, or to costs? Two questions are kept apart: Q-total (value of the deployed strategy) and Q-select (selection among the same order opportunities). Estimands: §8.
2. *Two feature groups, tested separately (H-Z).*
   - **Z_H — holder-state variables**: capital-gains overhang, chip-distribution statistics, abnormal turnover (§5.1–5.3). Unchanged from v0.2.
   - **Z_O — observable actions of other identifiable participants** (pending user confirmation at Gate 2; free data only, per the user's decision relayed by the lead on 2026-11-15): Dragon–Tiger list disclosures, block trades, executed insider / large-shareholder share changes (§5.6).
   The confirmatory question for each group is whether adding it to the **gate** changes within-batch selection at fixed nominations (§7, §8.4).
3. *Monitoring (H-T).* Behaviour of the delayed-feedback interval of Theorem 1 on simulated streams with known truth (§12.1) and, descriptively, on the **synthetic fill stream** of the daily-bar backtest (rule SF, filtration F_t^syn; §3.1–3.2). On market data the interval's target is r_T^entry of that synthetic stream; it is **not** a statement about an executable strategy (I-§2.4), and every sentence about it carries the words "under the synthetic execution model". **The interval is not used to compare methods** (§9.4: estimated half-width about 0.17–0.22 at the end of the hold-out).
4. *Mechanism side-track (H-M).* **ON HOLD — pending lead / user decision** (unchanged from v0.2; not scheduled).

**Non-goals.**
- Not a search for a profitable strategy or a strong factor set.
- **No claim that Z_H or Z_O measures anybody's private information.** Z_O records publicly disclosed actions; the plan does not model a game, does not solve for an equilibrium and **claims no game-theoretic contribution**. Poker is motivation only.
- No claim of "first abstention approach to stock trading"; theory statements are about monitoring, never about "not losing".
- Maximum drawdown and portfolio CVaR are empirical metrics only.
- Reinforcement learning is an optional round-2 baseline.
- No intraday or order-book data, no shorting, no leverage, no hedging, no market-impact model beyond proportional slippage, no live trading. **Default: no timestamped opening-auction data are obtained (they are not free); the user may decide otherwise (§17 U35).** Consequently no claim is made that any backtested order would have filled in the market.
- **Out of scope for this paper** (possible future extension if licensed data become available): restricted-share unlock schedules and pre-disclosed selling / buying plans (§5.6.4).

---

## 2. Data plan and audit checklist

Nothing in this section has been measured except what `experiments/data_feasibility_opponent_actions.md` reports (40 probe calls, 32 succeeded; values not cross-checked against any second source). **No modelling starts before the audit report is written and the lead has reviewed it.**

### 2.1 Sources (user decisions of 2026-11-15: AKShare primary; no Tushare)
- **Primary: AKShare** (free, no token): daily bars, turnover, dividends, suspension records, and — if available — historical index constituents and ST status. Which fields are point-in-time is UNVERIFIED (first audit task). `akshare` 1.20.63 is already installed in `experiments/.venv` (done by the feasibility probe, not by this revision).
- **Cross-check source 1: BaoStock** (free, registration-free; not yet installed). Whether BaoStock and AKShare share an upstream for any field is **UNVERIFIED** (audit item A17); agreement between two feeds with a common upstream is not independent validation.
- **Cross-check source 2 (soft): `hf-dataset:ellendan/a-share-prices`** (approved; MIT). Its card does not state the data source, whether prices are adjusted, or whether delisted stocks are included (`literature/resources.md`): provenance UNVERIFIED. If the audit finds that it is Tushare-derived it moves to the "optional" group below.
- **Tushare-derived datasets are not dependencies.** `hf-dataset:joshuaxql/qlib_data` (card: source Tushare) and the release asset of `github:chenditc/investment_data` (`DOWNLOAD_LIST.md`: derived from Tushare / AKShare / Yahoo / BaoStock) are **removed from every hard or fallback dependency** of this plan. They remain only as "optional cross-check, usable if and only if the user separately confirms" (§17 U32).
- **How cross-checking works without them.** (i) AKShare versus BaoStock field by field, read together with A17; (ii) AKShare's alternative upstream interfaces for the same field (Eastmoney / Sina / Tencent, where they exist; UNVERIFIED which do); (iii) internal consistency (limit bands, ex-date arithmetic, constituent counts); (iv) hand checks of sampled records against exchange / CSDC / company announcements, with the announcement URL stored; (v) the adversarial accounting cases A14–A16. Limit prices have no free external reference unless `ellendan/a-share-prices` passes its provenance check; otherwise A7 is checked by (iii) and (iv) only and this is stated as a limitation.
- **Z_O data** (§5.6): AKShare only. **There is no second free source** for Dragon–Tiger and block-trade values (BaoStock: no corresponding interface found, not verified on its site); executed share changes have three upstreams (Eastmoney, SSE, 10jqka). Values are therefore checked only by OA5 sampling against announcements.
- All raw pulls are stored as local Parquet / raw JSON with pull timestamp and library version; raw files are never modified.

### 2.2 Period (proposal, to be confirmed after the audit)
- Raw data from 2008-01-01 (warm-up for 250-day windows and chip distributions).
- Evaluation period 2010-01-01 to **2026-06-30**. The end date is chosen so that the sample ends before the main-board ST price-limit change of 2026-07-06 (§3.4) and is fixed before any result is seen. PLACEHOLDER: the user may prefer a different start (e.g. 2012) if the audit shows early-year data are poor.
- Development segment: 2010-01-01 to 2021-12-31. Final frozen hold-out: 2022-01-01 to 2026-06-30 (§4.4).

### 2.3 Universe (proposal)
- **Point-in-time union of CSI 300 and CSI 500 constituents** on each date (membership as of the information available before that day's open). Reason: limits survivorship bias if historical membership is available, keeps local compute small, and avoids the least liquid names where daily fills are least credible.
- Exclusions applied point-in-time, using only information available before the decision: listed fewer than 60 trading days (PLACEHOLDER; also keeps IPO no-limit days out, §3.4); Beijing Stock Exchange; B-shares.
- ST / *ST names: kept in the *data* (they may be held when they become ST), excluded from the *candidate set for new entries* (primary). Sensitivity: include them.
- Delisted names must be present for the dates on which they were members. Whether the free sources provide them is UNVERIFIED and is audit item A1.
- **Warm-up of feature windows (addition to §2.2; P12).** Primary windows (250 days) need raw data from 2008 for features starting about 2009 (dates UNVERIFIED). The 500-day CGO variant needs about two years and the 260-week variant about five years of history: with raw data from 2008 they are complete only from about 2010 and 2013 respectively. Rule: a feature is NaN until its full window is available; no partial-window values. If the audit shows AKShare history before 2008 is usable, the raw pull starts in 2005-01; otherwise each variant's first valid date is reported and its analyses start there.

### 2.4 Audit checklist

| # | Audit item | How it is checked | Pass criterion (PLACEHOLDER thresholds) | If it fails |
|---|---|---|---|---|
| A1 | **Delisted stocks are retrievable (first task)** | Take a hand-compiled list of >= 30 A-share codes known to have been delisted between 2010 and 2025 (from exchange announcements; list stored with sources). Query each in BaoStock and AKShare. | >= 95% of the list return a full daily history up to the delisting date in AKShare (primary); the BaoStock result is reported alongside | F1, then F2, then F3 (below) |
| A2 | Historical index constituents are point-in-time | Query CSI 300 and CSI 500 membership on >= 40 dates spread over 2010–2026; compare counts (300 / 500), turnover between rebalances, and agreement with the cross-check source and with a sample of official rebalance announcements | Counts exact on >= 95% of dates; membership on sampled dates matches the cross-check source for >= 98% of names; a stock known to have left the index is absent after its removal date | Use constituent intervals from the cross-check source (needs approval); else F2 / F3 |
| A3 | Survivorship in the assembled panel | Fraction of ever-members that have no price history; fraction that end before 2026 | No ever-member lacks price history for its membership dates (after A1 fallback); report the number of delisted / removed names | Report as a limitation with a bound on affected stock-days; if > 1% of member stock-days are missing, trigger F2 / F3 |
| A4 | Price fields agree across the two sources | Field-by-field comparison of unadjusted O/H/L/C, volume, amount on the full panel | Relative difference < 1e-4 on >= 99.5% of stock-days per field; every remaining discrepancy cluster explained (e.g. unit conventions: shares vs lots, yuan vs thousand yuan) | Resolve by third source; unexplained disagreements > 0.5% => F2 / F3 |
| A5 | Adjustment factors and corporate actions | Reconstruct the adjustment factor from unadjusted vs adjusted series; compare with AKShare dividend / split records and the cross-check source on >= 200 ex-dates; check that adjusted returns on ex-dates equal the total return implied by cash dividend and share changes | Ex-date total return matches within 1e-3 on >= 99% of sampled events; no unexplained jump > limit-implied bound on non-ex-dates | Rebuild factors from dividend records ourselves; otherwise F2 / F3 |
| A6 | `preclose` is the exchange reference price | Check `preclose` against prior close and ex-date reference prices; check that realised daily range respects limits computed from `preclose` | Violations of the computed limit band on < 0.1% of stock-days, each explained (IPO days, resumptions, rule changes) | Use the cross-check source's limit table; document the rule calendar gaps |
| A7 | Limit-up / limit-down prices can be computed | Compute limit prices from `preclose`, board, ST flag and the rule calendar (§3.4) with exchange rounding; compare with a source that carries limit prices | Match to the cent on >= 99.5% of compared stock-days | Use the external limit table directly (needs approval) |
| A8 | Suspension flag is reliable | `tradestatus == 0` vs zero volume vs AKShare suspension records | Agreement on >= 99.5% of stock-days; a suspended day never has positive volume | Define suspension as zero volume (document) |
| A9 | ST flag is point-in-time | `isST` history against a sample of >= 50 ST designation / removal announcements | Dates match within 1 trading day on >= 95% of events | Exclude ST by an alternative list (cross-check source `joshuaxql/qlib_data`, needs approval), or run the "ST included" variant as primary and document |
| A10 | Turnover definition | Compare `turn` with volume / float shares where float shares are available; compare BaoStock `turn` with AKShare turnover | The definition (free-float vs total shares; percent vs fraction) is identified unambiguously; cross-source relative difference < 1% on >= 99% of stock-days | Z is recomputed under both definitions; the one used is fixed before modelling and reported |
| A11 | Timestamps and look-ahead | Confirm every field used at decision time for day t is from day t-1 or earlier; confirm constituent and ST information is as known before the open of day t, not back-filled | Code-level check plus a shuffled-future test: features recomputed after truncating the data at t-1 are bit-identical | Fix; no exception allowed |
| A12 | Opening-price field supports the synthetic fill rule SF (§3.2) | Share of stock-days where `open` equals the computed limit-up / limit-down price; share with missing `open`; share of traded days with `open` outside [low, high]; how each source fills `open` on a day without trades. **Daily bars cannot show whether the opening auction matched (I-§2.4 items 1–3); this item does not test that** | Descriptive (no threshold); must be reported before the execution convention is frozen | If `open` is unreliable there is **no entry rule covered by the instantiation to fall back on** (VWAP-type entries are "not covered", I-§7): stop and report to the lead / user before any result is seen (§3.2) |
| A13 | Reproducibility of the pull | Re-pull a 5% random sample one week later | Identical values except documented upstream revisions | Snapshot is frozen with hashes; revisions logged |

**Fallbacks (in order of preference; F2 and F3 need a user decision):**
- **F1.** Combine sources: take delisted histories, constituent intervals or a missing field from whichever approved free source has them (BaoStock, or cross-check source 2). Each such substitution is logged per field and reported to the lead (see §2.1).
- **F2.** Restrict the claim: narrower universe or shorter period where the audit passes (e.g. CSI 300 only, or 2015 onward), with the restriction stated as a limitation. Results on a universe with known survivorship bias would be labelled as such and not used for the primary claims.
- **F3.** **Obtain better data through the user's university** (e.g. a CSMAR / Wind / RESSET-type licensed database with delisted stocks, point-in-time constituents, and official limit prices). This contradicts the original "free data only" constraint and is the user's decision (open question in §16). Tushare is **not** an option: the user decided on 2026-11-15 not to use it (AKShare instead, no token).

The audit report (`experiments/results/data_audit/AUDIT.md`) lists every item with measured numbers, pass / fail, and the fallback taken.

**Changes to the table above in v0.3.** A9's fallback no longer uses `joshuaxql/qlib_data` unless U32 is confirmed; without it the fallback is the hand-compiled ST announcement sample plus the "ST included" variant as primary. A2 / A5 / A7 use cross-checks (i)–(iv) of §2.1. Additional items:

| # | Audit item | How it is checked | Pass criterion (PLACEHOLDER) | If it fails |
|---|---|---|---|---|
| A14 | **Delisting and terminal value (adversarial cases)** | For >= 20 delisted names from the A1 list: last traded date and price, treatment after delisting in each source, any terminal recovery recorded; hand-compute the P&L of a position held through delisting under the convention of §3.9 and compare with the ledger | Ledger equals the hand computation in every case; the terminal-value convention is applied identically in all strategies | Fix; cases that cannot be reconstructed are listed and bounded (value 0 versus last traded price) |
| A15 | **Long suspensions** | >= 20 suspensions longer than 20 trading days (including ones ending in a limit-down sequence): carry-forward mark, adjustment across the suspension, first tradable open, O1 versus O2 labels | Hand computation = ledger in every case | Fix; no exception |
| A16 | **Dividends, splits, bonus and rights issues** | >= 30 hand-checked events of each type present in the universe: share count, cash received, adjusted return on the ex-date, ledger wealth before / after | Wealth change over the ex-date equals the hand computation within 1e-6 relative | Rebuild adjustment from event records; otherwise F2 / F3 |
| A17 | **Independence of the two feeds** | From source code / documentation: upstream of each field in AKShare and BaoStock; fields with a common upstream are flagged | Descriptive; every field is labelled "independent second source" or "same upstream" in the audit report | Fields without an independent source are hand-checked on a sample (iv) and reported as such |
| A18 | **OA-next and label freezing in the data pipeline** (I-§4; setup A2(b), A3) | Every input of the O1 tree for an entry of day t (prices and flags of days ≤ t+H, event records, cost inputs) is present in a data set truncated at the decision point of day t + d_label = t+H+1; labels are computed once from that truncation and stored. Late upstream corrections are measured by A13 / OA6. **Limit: we hold one downloaded file, not a point-in-time store; "available at day t+H+1" can be checked only as "a function of the downloaded file" (I-§2.4 item 6, I-§4)** | Labels recomputed from data truncated at day t+H+1 equal the stored labels on 100% of entries; no stored label is ever overwritten (hash check); the number of labels set by outcome M is reported | A3 with d = H + 1 is not supported for the affected stream; reported, and the monitor is not run on it until resolved. Labels are **not** recomputed with a later deadline (§3.3) |
| A19 | **Turnover above one and chip initialisation** | Count stock-days with turnover fraction V > 1 or V < 0; inspect a sample | Count reported; the handling rule of §5.2a is applied; no silent clipping | — |
| A20 | **Complete accounting reconciliation on real data** | Criteria R1–R4 of §3.9 on the pilot panel | As §3.9 | Stop (pilot criterion) |
| A21 | **Completeness of the corporate-event calendar** (added v0.4; I-§3 "Limits" (i), I-§9 unresolved) | The O1 tree detects a missing field, not a missing event. For >= 100 sampled stock-years: events in the source versus company / exchange announcements (URLs stored); plus every non-ex-date price jump beyond the limit band found by A6 | No sampled event of classes S-a–S-e missing; every unexplained jump traced | Affected names / periods listed; their labels are flagged and the share reported; F2 / F3 if not rare |
| A22 | **Meaning of the vendor's suspension flag** (added v0.4; I-§2.4 item 4) | From documentation and >= 30 hand-checked suspension days (incl. intraday suspensions / resumptions where announcements exist): does the flag mean whole-day suspension only? | The flag's coverage is identified unambiguously and written into `conventions.py` | Condition (S1) is implemented as "bar exists with positive volume" only, and the flag is reported as unusable |
| A23 | **Adjustment factor versus share-and-cash tracking** (added v0.4; I-§3 rule (4), I-§9 unresolved "ex-distribution") | On the A16 events: does the vendor factor encode exactly S-a–S-c, and are adjusted prices ex-distribution? | Factor-implied and share-and-cash wealth agree within the R2 tolerance on 100% of sampled events | **Share-and-cash tracking is the primary method in any case (§3.8 (iii)); the factor is never substituted for it** unless this item passes |
| A24 | **Frequency of fallback outcomes** (added v0.4; I-§3 rule (3)) | Count of entries per O1 branch (S-d, S-e, P1–P4) and, separately, of outcomes U and M, on the pilot panel and later on every stream | Descriptive; reported before the freeze. No threshold is set here | If U + M are not rare the label is driven by a convention; every result using O1 says so |

**Exchange / regulator rules to be verified against the official texts before modelling (added v0.4, T9; the 13 items of I-§9).** None has been checked; no rule original was opened for this or any earlier revision. For each item the audit must archive the official text (URL, document title, effective dates, retrieval date) **for every sub-period of 2010–2026 in which the rule differed**, and record in `AUDIT.md` whether the convention of §3 matches it. "Source" names the official site to consult; **the document titles are written from general knowledge and are UNVERIFIED — locating the right document is part of the item.** News reports and the summaries in the Appendix do not count. General rule on failure: a convention that contradicts the official text is changed **before any outcome is seen** and the change is logged; where the text cannot be found for a sub-period, the item is reported "UNVERIFIED for that period" and the consequence in the last column applies.

| # | Rule (I-§9 number) | Used in | Official source to consult | If the text contradicts the convention, or cannot be found |
|---|---|---|---|---|
| RV1 | (1) Opening call auction timetable; order-entry and cancellation windows | §3.1 submission time and information cut-off (U37) | SSE (sse.com.cn) and SZSE (szse.cn) Trading Rules, all versions in force during the sample | Cut-off and submission time in U37 are changed to the official windows; if they differ by period, a per-period table is used |
| RV2 | (2) Allocation of volume among orders at the auction clearing price | Whole-fill assumption of SF / EM (§3.2) | Same Trading Rules (call-auction matching principle) | SF stays a modelling assumption either way (it cannot be validated from daily bars); the paper states what the rule says and that queue position is not modelled |
| RV3 | (3) Which price is published as the daily open when the auction has no match; whether the open equals the auction price when it has one | SF fill price; O1 branches P2 / P3 (§3.8 (iii)) | Same Trading Rules (definition of the opening price) | If the open can differ from the auction price on a matched day, P2 / P3 cannot be merged from daily bars: O1 is then defined on "the published open" only and described as such; the fill price is called "published open", not "auction price" |
| RV4 | (4) Definition of the pre-open / ex-rights reference price | Limit prices (§3.4); O1 branch P4; A6 | Same Trading Rules (ex-rights / ex-dividend reference price) | Limit prices and P4 are recomputed from the official formula; if not reproducible from free data, P4 entries get outcome M |
| RV5 | (5) Price-limit rules by board and status; days without limits | §3.4 rule calendar; (S2) | SSE / SZSE Trading Rules; STAR Market and ChiNext trading provisions; the 2020, 2023 and 2026 revision notices; CSRC (csrc.gov.cn) for the registration-reform rules | Rule calendar corrected. Segments or periods whose rule cannot be established are excluded from the candidate set (logged) |
| RV6 | (6) T+1 | H >= 1; §3.3 | SSE / SZSE Trading Rules | If any instrument in the universe is exempt, it is listed; H >= 1 is kept for all |
| RV7 | (7) Kinds of suspension (whole-day, intraday, auction-covering) and when they are announced | C_t rule (§3.5); (S1); O1 branch P1; A22 | SSE / SZSE Trading Rules and Listing Rules (suspension and resumption chapters); exchange suspension notices | If announcement timing is not available in free data, C_t uses the day-(t−1) status only (the primary rule of §3.5 already does) |
| RV8 | (8) Delisting stages and the pre-delisting trading period | Listing-status check of the O1 tree; ledger terminal value (§3.9); A14 | SSE / SZSE Listing Rules (delisting chapters), all versions; CSRC delisting-reform documents | Cases not classifiable as S-d / S-e are outcome U (label 1) as already specified; the ledger convention (U33) is unchanged and the count reported |
| RV9 | (9) Record date versus ex-date | Entitlement rule for distributions (§3.8 (iii), §3.9) | CSDC (chinaclear.cn) rules on distribution of entitlements; SSE / SZSE Trading Rules | The entitlement window "record dates t … t+H−1" is restated in terms of the official relation; if free data lack record dates, they are derived from ex-dates by the verified relation, else outcome M |
| RV10 | (10) Dividend withholding rules | Withholding rate (U41) | Ministry of Finance / State Taxation Administration / CSRC notices on differentiated dividend tax (mof.gov.cn, chinatax.gov.cn) | U41 is reset to the rate the official text implies for the holding periods in the plan; holding-period dependence remains unmodelled (stated limitation) |
| RV11 | (11) Treatment and value of unexercised rights | S-c convention "not subscribed, valued at zero" | SSE / SZSE rights-issue business rules; CSDC | The convention is kept as a conservative choice and labelled so; the number of affected entries is reported |
| RV12 | (12) Board-lot and odd-lot rules | Lot-rounding robustness run (U39) | SSE / SZSE Trading Rules; STAR Market provisions (minimum order size) | The lot-rounding run uses the official lot sizes per board; the primary run (fractional shares) is unaffected and stays labelled a simplification |
| RV13 | (13) Fee schedule: stamp duty, transfer fee, minimum commission | §3.6 | MoF / STA announcements (stamp duty); CSDC and exchange fee schedules (transfer fee, handling fees); commission is broker-specific (no official rate) | Cost calendar corrected by date; components whose history cannot be established are set to the highest rate found in the period (conservative, logged) |

**Audit items for Z_O (merged from `data_feasibility_opponent_actions.md` §6; thresholds are that file's placeholders).**

| # | Item | How | Pass criterion (PLACEHOLDER) | If it fails |
|---|---|---|---|---|
| OA1 | Disclosure timing | Variables with an announcement date (executed share changes): share with announcement date >= event date and the gap distribution. Variables without one (Dragon–Tiger, block trades): **find and archive the exchange rule text** that fixes the publication time, for every sub-period of the sample; the descriptions in `opponent_action_variables.md` §3 are marked there as not verified against originals | Announcement date missing <= 1%; announcement before event <= 0.5%, each explained. Rule original archived for the whole sample period | The class is used only with the extra lag of §5.6.2, or dropped from Z_O |
| OA2 | Removal of ex-post fields | Every column of every table labelled "known at disclosure / computed ex post / current snapshot"; features read through a whitelist | 100% of feature inputs are "known at disclosure". Not on the whitelist: "上榜后 N 日", "解读" (contains success rates), "最新价", "涨跌幅" of the share-change table, names | The table is not used |
| OA3 | History depth and yearly coverage | Per class and year: share of trading days with any record; share of the universe with a record | No run of 20 trading days with zero market-wide records; the class's analysis start is fixed at its measured start (probe: 2012-01 retrieved; 2010–2011 untested) | Start later than 2013-01 ⇒ the class is not in the confirmatory feature group |
| OA4 | Delisted stocks retained | 30 names from the A1 list; record counts versus matched surviving names | Share with records >= 90% of that of matched survivors | Class labelled "survivorship-affected", exploratory only |
| OA5 | Completeness / value check | Executed share changes: 50 stocks compared across Eastmoney, SSE, 10jqka. Dragon–Tiger and block trades (single upstream): 30 records each against exchange disclosures by hand | Match rate >= 95% | Class labelled "not cross-checked"; not used for the confirmatory test |
| OA6 | Revision / back-fill detection | Full pull at audit start; second pull of the same history >= 30 days later | Changed rows (older than 60 days at first pull) <= 0.5% | First snapshot frozen; change rate reported. **This detects revisions after our first pull only; back-filling before it (the share-change table carries entry timestamps of 2019 for records of the 1990s) cannot be detected from free data — stated limitation** |
| OA7 | Endogeneity of coverage | Per day: size, liquidity, volatility, prior return of names with versus without a record | Descriptive; event-trigger controls and coverage indicators enter the control set R_O (§5.6.3) | — |
| OA8 | Interface stability | Two batches of 200 requests on different days; failure and retry rates; empty responses handled as "no record" | Success after retry >= 99%; identical rows on both days | Alternative upstream, or drop the class |
| OA9 | Point-in-time codes | Codes in each table mapped to the daily-bar codes (the probe saw current 920-codes and current short names on old records) | One-to-one mapping for SSE / SZSE main board, ChiNext, STAR; names never used as features or filters | Mapping table; unmapped rows dropped and counted |

### 2.5 Fetch budget and rate limits (ESTIMATES; all calls through AKShare unless stated)

| Data | Interface (as probed) | Requests (ESTIMATE) | Basis |
|---|---|---|---|
| Daily bars, adjustment, per stock | per-stock history calls | 6,000–8,000 | about 2,000–2,500 ever-members of CSI 300 ∪ CSI 500 since 2008 (count UNVERIFIED) × up to 3 calls |
| Dividends, suspensions, ST, constituents | UNVERIFIED which interfaces | up to 5,000 | per-stock or per-date; unknown until the audit |
| BaoStock cross-check | own client | 4,000–6,000 queries | same names, 2 queries each |
| Dragon–Tiger daily summary | `stock_lhb_detail_em(start, end)` | about 200 | one call per calendar month 2010-01 to 2026-06 (198 months) |
| Dragon–Tiger institutional statistics | `stock_lhb_jgmmtj_em(start, end)` | about 200 | same |
| Block trades | `stock_dzjy_mrmx`, `stock_dzjy_mrtj` | about 400 | monthly windows, two tables |
| Executed share changes | `stock_ggcg_em("全部")` | 1 call ≈ 295 upstream pages | 147,458 rows / 500 per page (probe) |
| OA6 second pull of Z_O tables | as above | about 800 + 295 pages | repeat after >= 30 days |
| OA4 / OA8 sampling | per-stock and small batches | <= 1,500 | 30 + 30 names; 2 × 200 per class |
| **Not budgeted (excluded)** | seat-level Dragon–Tiger detail (hundreds of thousands of calls); margin detail (about 8,000); northbound per stock; shareholder counts per stock | 0 | §5.6.4 |

Rules: one connection per upstream host; **>= 1.5 s between requests** (the spacing used in the probe; PLACEHOLDER); on failure, retries after 5 / 20 / 60 s, at most 3, then the request goes to a resume list (the probe saw 8 failures in 40 calls, including time-outs of szse.cn); checkpoint after every request; daily cap 3,000 requests per upstream host (PLACEHOLDER); every raw response stored with its timestamp; an empty upstream answer is recorded as "no record" (AKShare raises `TypeError` in that case and must be wrapped). Number of upstream pages behind one AKShare call is UNVERIFIED for the date-window interfaces. At these settings the base pull takes an estimated 2–5 days of wall time, the Z_O pull under one day. The whole budget is a Gate-2 item (§17 U24).

---

## 3. Execution and accounting conventions (to be frozen before any outcome is seen)

Proposals implementing the checklist of `theory/instantiation_ashare.md` §8 (items 1–13; cited "I-§8.n"). After Gate 2, the rule audit RV1–RV13 and audit item A12, they are written to `experiments/src/common/conventions.py` and its hash is recorded in every result file. Every statement about A-share trading rules is **[rule: tbv]** (§2.4, RV1–RV13). A change after the freeze alters the estimand or voids the guarantee and is logged (I-§8 preamble).

### 3.1 Two information times; the declared filtration (T1, T2; setup §1, A1, A1-G; I-§2.1, I-§2.4; I-§8.1–8.2)

- **G_t — pre-submission information.** Data dated ≤ t−1 (through the close of t−1) plus the pre-open public information of day t that the pipeline actually holds: trading calendar, the day's price limits computed from the reference price, corporate events effective on day t. **Everything a strategy chooses for day t is a function of G_t:** the candidate set C_t, the base ranking, the nominated list, every gate / filter / scaling decision, every random draw (RND; seeds fixed in advance), and the complete specification of every order — name, quantity, order type, limit price — and the capacity cap of (S3). At most one buy order per name per day and at most M = K buy orders per day; the cap is enforced on submitted orders.
- **Fills are determined afterwards**, by rule SF of §3.2. No strategy can condition on them on day t.
- **Declared post-fill filtration (case (b) of I-§2; daily bars only):**
  F_t^syn := all data dated ≤ t−1, the pre-open public information of day t, and the day-t **open, traded flag and suspension flag** of all names (and hence the synthetic fills of day t).
  It is increasing in t. It is an **artificial** information set: on a day on which a name had no opening-auction match it contains facts that became known only later that day (I-§2.4). The phrase "information at the opening-auction match" is **not** used anywhere in this project's results; case (a) of I-§2.3 would need timestamped auction data, which are not free (default: not obtained; §17 U35).
- **Which abstract assumption this supports.** A1-G is an implementation requirement on the order-generation code, enforced by the truncation test (A11; §13 criterion 3): recomputing every order from data truncated at G_t reproduces it bit for bit. A1 is claimed only with respect to (F_t^syn). The monitoring target is therefore r_T^entry **of the synthetic fill stream, defined with F_t^syn** (setup §5 item 5).
- **Confirmation for T2 (every selection uses G_t only).** Checked item by item in this revision: C_t (§2.3, §3.5: status through t−1 only); base scores and nominations (§4: features through t−1); thresholds and calibration maps (§4.3: previous year); gates CONF, LOSS, LOSS-LR, NET-K, NET-U, SCORE, VOL, LIQ, TREND (§6.1: features through t−1); PERF and all online states (labels frozen by day t−1 at the latest, i.e. entries of day s ≤ t − d_label; returns through the close of t−1); VT (G0's returns through t−1); E-const-dev (previous year); order quantities (sleeve cash at the close of t−1, limit-up price from the reference price, §3.7); strata of §8.3 (data through t−1); RND draws; the placement and permuted-Z controls of §7.3. **Not strategies and labelled as such:** E-const-expost and E-sched (ex-post attribution references), the hindsight diagnostic of §11. One change was needed: v0.3 let C_t exclude names "suspended on day t", which is not in G_t unless announcement timestamps exist (§3.5).

### 3.2 Synthetic fill rule SF, entry price, and the fill-determination sensitivity (T1; I-§2.4; I-§8.3–8.4)

**All fills in the backtest are retrospective synthetic fills.** They are called that in every table, figure and sentence.

> **SF (primary).** A buy order for stock i on day t, generated from G_t, is recorded as a **synthetic fill in full at the daily open of day t** if
> (S1) the daily bar of day t exists, has positive volume and is not flagged as a whole-day suspension (meaning of the flag: A22);
> (S2) the daily open is not the upper price limit computed from the reference price (§3.4);
> (S3) the order size does not exceed the capacity cap, a function of G_t (§3.7, U40).
> Otherwise it is recorded as **not filled** and cancelled (never carried to a later day). Sell orders: the same with the lower price limit in (S2). **Of the day-t bar SF reads only the traded flag, the suspension flag and the open** — never the high, low, close or the size of the volume.

- No partial fills: one entry is one whole position (a "lot") with a single entry price. The same rule is applied to every strategy, comparator, reference path and label.
- **Benchmark entry price = the published daily open.** Slippage and fees are booked as costs (§3.6) and never applied to the price.
- **Consequence (i) — what the monitoring results are about.** Theorem 1 and Corollaries 1.1–1.2 (statuses: header) are applied to the synthetic fill stream with filtration F_t^syn. A real order may not have filled where SF records a fill (no auction match, limited auction volume, queue position) or may have filled at another price; μ_t is conditional on F_t^syn, not on what a trader knew at the match. **Binding wording for RESULTS.md and the paper:** "for the synthetic fill stream under SF (filtration F_t^syn)" / "under the synthetic execution model"; never "for the strategy", "executable", "tradable", or "at the opening auction match". The same qualifier applies to fill rates, to "blocked" buys and exits (blocked *as defined by SF*, not in the market; I-§6.2) and to every trade-level table.
- **Consequence (ii) — limit-up and no-match days are approximated, and the size of the approximation error is not estimable from daily bars** (I-§2.4: it needs at least a sample of auction data). What can be done with daily bars is a sensitivity to the fill determination, pre-specified here:

| Fill determination | Buy recorded as filled iff (sell side mirrored at the lower limit) | Role |
|---|---|---|
| **SF** | (S1) ∧ (S2) ∧ (S3) | primary |
| **SF-strict** (conservative) | (S1) ∧ open ≤ reference price × (1 + 0.8 × limit band) ∧ order size ≤ one tenth of the primary cap. 0.8 and 1/10 are PLACEHOLDERS (U36) | sensitivity |
| **SF-loose** | (S1) only (fills also at the limit price, no cap) | sensitivity |

  Both variants read the same three fields of the day-t bar and G_t only. They are applied to the **frozen** models, thresholds and orders of the primary run (only the fill layer, the ledger and everything computed from them are re-run; no refit). Reported for each: fill rate by method and reason; θ_sel, ψ_H, ψ_O with unadjusted intervals; ΔAR and its attribution terms; the Theorem 1 interval at the end of the window. **Pre-fixed reading:** if the verdict category of any card C1–C4 (§9.3 wording) differs between SF-strict and SF-loose, the primary result is reported together with the sentence "sensitive to the synthetic fill determination". The variants are exploratory and never replace the primary specification. **Limit of this analysis, to be printed with it:** all three rules are retrospective; none can identify days without an auction match, so the sensitivity bounds the dependence on (S2) / (S3), not the gap between synthetic and real fills.
- **Delay robustness:** SF applied one day later (signal one day stale).
- **VWAP entry — outside the theory.** I-§7 lists entry rules with fills spread over the day as "not covered". v0.3's VWAP timeline is kept only as an empirical robustness run for Q-total and Q-select: entry at the day-t VWAP proxy (`amount / volume`; units UNVERIFIED until A4), blocked if the name did not trade or traded at one price equal to limit-up all day; exit by the primary rule. **No Theorem 1 quantity, no O1 label of §3.8 and no monitoring interval is computed on it;** results go in a separate table labelled "not covered by any theory result" and are never pooled.
- **If audit item A12 fails** (unreliable `open`): v0.3 made the VWAP timeline primary in that case. That is no longer possible, because no covered entry rule would remain. The pipeline stops and the lead / user decide before any outcome is seen (§17 U44).

### 3.3 T+1, holding period, exit, and the two lags (T3; setup A2(b), A3, §4; I-§4; I-§8.6–8.7)
- Shares bought on day t cannot be sold on day t **[rule: tbv, RV6]**. **H = 5 trading days (PLACEHOLDER)**; robustness H in {1, 10, 20}. H, d_label and d count **market trading days** of the exchange calendar (not a stock's own trading days).
- **Scheduled exit: the opening auction of day t+H**, by the liquidation policy LP of §3.8 (iv). No stop-loss, take-profit or discretionary exit.
- **Label-finalisation lag d_label = H + 1, fixed now.** Every O1 label of an entry of day t is computed **once**, from the data snapshot of day t + d_label (data available before the decision point of day t+H+1), stored, and **never recomputed or revised** — not when later data arrive, not when an upstream value is corrected, not for any other monitoring lag (setup A2(b); I-§3 "Snapshot"). The label needs facts known only at the close of day t+H (branches P3 / P4), which is why the lag this label supports is H + 1.
- **Monitoring lag d = H + 1, fixed now, deterministic (lead's decision; the user may veto, §17 U25).** d ≥ d_label, so A3 holds with d if every label is in the declared information set of day t + d_label; that is the availability assumption OA-next of I-§4, **an audit item (A18), not an established fact**, and with one downloaded file it can hold only "as a function of the downloaded file". Lanes are residue classes mod d of the market trading-day index. H = 1, 5, 10, 20 ⇒ d_label = d = 2, 6, 11, 21.
- **d is never chosen or changed after data are seen** (setup §4: the radius is not monotone in d). No analysis in this plan uses a second monitoring lag. If one were ever wanted, it would be a separately declared analysis **on the same frozen labels** (setup §4), never a recomputation of labels with a later data deadline.
- **No statement in this plan says that O1 has lag H.** A lag of H would need a different label that uses auction-time information only ("O1-auction", I-§4), which requires timestamped auction data; it is not specified and not used. v0.3's "d = H under OA-open" row and remarks are deleted.

### 3.4 Price limits (rule calendar) — every row [rule: tbv, RV5]
Limit prices are computed from the day's reference price (the unadjusted `preclose` as adjusted by the exchange for events effective that day; definition **[rule: tbv, RV4]**), rounded to 0.01 yuan (exact exchange rounding rule UNVERIFIED; checked empirically in A7). The reference price and hence the limits are pre-open public information (G_t).

| Segment | Daily limit | Source / status |
|---|---|---|
| Main board, non-ST | 10% | News reports of the 2023 registration reform state the limit stays at 10% from the 6th trading day (https://wallstreetcn.com/articles/3680934). Exchange rule text not opened. |
| Main board ST / *ST | 5% through 2026-07-03; **10% from 2026-07-06** | News reports of the SSE / SZSE rule revision published 2026-04-24, effective 2026-07-06 (https://www.news.cn/fortune/20260706/21958d63bab64ce180cc97d1a6af6b50/c.html). Exchange rule text not opened. Outside the proposed sample (ends 2026-06-30). |
| ChiNext | 10% before 2020-08-24, 20% from 2020-08-24 | Date taken from `literature/resources.md`; UNVERIFIED by me |
| STAR Market | 20% since launch | Launch date and rule UNVERIFIED |
| New listings | No limit in the first 5 trading days (STAR, ChiNext under registration; main board after the 2023 reform); older main-board IPO first-day rules differed | Same news source as row 1; effective dates and pre-2023 rules UNVERIFIED. Made irrelevant by the >= 60-trading-day listing filter. |
| Beijing Stock Exchange | 30% | News report; excluded from the universe |

- **Buy not filled (synthetic):** (S1), (S2) or (S3) of §3.2 fails. A non-filled buy is **cancelled, not retried**; the money stays in cash for that slot. It is an unfilled order: not an entry (A_{ti} = 0), no label, recorded only in the order ledger (§3.8 (i)).
- **Sell not filled (synthetic):** the sell-side form of (S1)–(S3) fails on the exit day. The sale is re-submitted at each following opening auction (LP, §3.8 (iv)).
- These rules do not model queue priority at the limit or auction volume (**[rule: tbv, RV2]**); (S2) is conservative only in never crediting a buy at limit-up. Sensitivity: §3.2 table.

### 3.5 Suspension
- **Candidate set (changed in v0.4 for G_t-measurability).** A name is removed from C_t if it was suspended on day t−1 (a fact dated ≤ t−1). A name that traded on day t−1 and is suspended on day t receives an order if nominated; the order is recorded as not filled by (S1). Consequence, stated: a name resuming on day t is not a candidate on its resumption day. Using pre-open suspension / resumption announcements instead would need announcement timestamps, whose availability in the free data is UNVERIFIED (**[rule: tbv, RV7]**; A22); if the audit finds them, the refinement is a logged change made before any outcome is seen.
- **Suspended while held:** valued by branch P1 of the O1 tree for the label (§3.8 (iii)) and at the last traded close, restated for later corporate events, in the ledger; cannot be sold; LP re-submits the sale at each following auction.

### 3.6 Transaction cost model (defaults) and benchmark-price accounting (T4; I-§8.8; Lemma 3 of theorems.md)

| Component | Default | Status |
|---|---|---|
| Stamp duty (seller only) | 0.10% of sale value through 2023-08-27; **0.05% from 2023-08-28**; applied by date | Halving effective 2023-08-28 from news of the MoF / STA announcement (https://www.news.cn/2023-08/28/c_1212260850.htm, https://www.cls.cn/detail/1445329). The prior 0.1% seller-only rate "since September 2008" is from the same reports; the exact 2008 date is UNVERIFIED. Whether the rate changed again after 2024 was not found; UNVERIFIED. **[rule: tbv, RV13]** |
| Transfer fee (both sides) | 0.002% through 2022-04-28; 0.001% from 2022-04-29 | From news of the CSDC announcement (https://www.yicai.com/news/101396958.html). Pre-2015 schedule UNVERIFIED; magnitude negligible. **[rule: tbv, RV13]** |
| Brokerage commission (both sides) | 0.025% (2.5 bps) per side, PLACEHOLDER; minimum 5 yuan per order ignored in the primary run | **UNVERIFIED** — broker-specific. The user should supply the rate of a realistic account. |
| Modelled execution shortfall ("slippage"; both sides) | 5 bps per side of the benchmark-price trade value, PLACEHOLDER | **UNVERIFIED** — not estimated from data. Sensitivity in §11. |
| Withholding on cash distributions | **20% of the announced cash per share, PLACEHOLDER (U41)**; fixed in advance, not holding-period dependent | The rate is written from memory of the differentiated dividend-tax rule for short holdings and is **UNVERIFIED** (**[rule: tbv, RV10]**). v0.3 ignored dividend tax; I-§5 requires a rate fixed in advance. Sensitivity 0% / 10% |
| Financing costs | None (no leverage) | — |
| Lot size | Ignored in the primary run (fractional shares); robustness run with lot rounding at a notional capital (**[rule: tbv, RV12]**) | Simplification |

Round-trip cost at defaults after 2023-08-28: 2 x (2.5 + 5 + 0.1) + 5 = about 20 bps; before: about 25 bps.

**Benchmark-price accounting — one rule for every strategy, comparator and reference path (lead decision of 2026-11-15, `STATUS.md`).**
1. **Same instant, same price.** At every valuation instant all strategies (gate G, baseline B, the attribution references E-sched and E-const-expost, the standard orders of §8.3) value holdings, pre-trade holdings, cost bases, marks and returns at the **same benchmark price**: the published daily open at the trade instant, the close at the end-of-day valuation. No strategy has its own "execution price".
2. **Every economic cost exactly once, through the cost term C.** Explicit charges (stamp duty, transfer fee, commission) and the modelled shortfall are debited as costs. **Slippage is never also applied to a price**, a return, a cost basis or a mark. Execution-price accounting (kept in `theorems.md` only as an alternative under its condition (EX)) is not used.
3. **Trades are share-based.** trade_t = (s_t − s_{t−}) ∘ p_t, where s_{t−} is the vector of pre-trade share counts **after the corporate actions effective by that instant** (bonus shares, splits, consolidations: multiplier applied), s_t the post-trade share counts, p_t the benchmark price on the same (ex-entitlement) terms. Traded amount = |trade_t|; every cost rate is applied to it. A cost is **never** computed from the difference of two consecutive days' position values. The return-based shortcut h_t − h_{t−1} ∘ (1 + R) may be used only with the ex-distribution, share-adjusted price return (I-§8.8); the code uses the share formula. The formulas are used for strictly positive prices and multipliers and for multiplier- and cash-type corporate actions only (round-3 item X11); anything else is class U (§3.8 (iii)).
4. **Cash distributions are booked separately** in the cash ledger by the entitlement rule of §3.8 (iii) and are **never a trade** (traded amount 0, cost 0).
5. **Costs are debited at the trade** (start of the period). P&L uses total returns.
6. **Wealth recursion with a non-zero cash return (robustness run only; round-3 item K1).** With costs debited at the trade, the ledger must satisfy W_{T+1} − W_1 = Π + Σ_t ρ_t (W_t − c_t), with Π, ρ_t and W_t (wealth at the start of period t, before that period's trade) as defined in Lemma 3 of `theorems.md`, which governs. **Not** Π + Σ_t ρ_t W_t. In the primary run the cash return is zero (W4) and the two coincide.

### 3.7 Capital allocation, order specification, cash (T2, T6)
- **Sleeves: H + 1 (not H).** Sleeve j trades on days t ≡ j (mod H+1): it buys at the open of t, sells at the open of t+H, and its sale proceeds are cash at the close of t+H, available for its next purchase at the open of t+H+1. **No purchase is funded by proceeds of a sale in the same auction** (whether that is possible is UNVERIFIED; the plan does not rely on it). The H-sleeve design is a labelled sensitivity (§11).
- **Slots.** Each day the base strategy nominates its top-K names (K = 30, PLACEHOLDER). S_t = orders submitted, n_t = synthetic fills; S_t <= K, so M = K. One order per name per day (I-§8.3).
- **Pre-determined order quantity.** Slot cash = (the trading sleeve's cash at the close of t-1) / K. For a submitted name i the order is a limit order at the day-t limit-up price P_i^up (§3.4) for q_i = slot cash / (P_i^up (1 + κ)) shares, κ = buy-side shortfall plus fee rate. Quantities depend only on G_t and are always affordable. Fractional shares in the primary run; 100-share lots as robustness.
- **Consequence, by arithmetic only:** an ungated sleeve is invested for H of every H+1 days and each filled slot invests about open / P^up of its cash, so the ungated strategy's invested fraction is of the order of (H/(H+1)) × 0.9 ≈ 0.75 at H = 5 on 10%-limit boards (ESTIMATE; depends on fills and opening gaps). The same rule applies to every strategy and comparator. An idealised "notional at the open" sizing (not implementable as a pre-auction order) is a labelled sensitivity.
- **Rejected or unfilled slots — primary ("cash") rule:** the money stays in the sleeve's cash until its next trading day. **"Refill" variant (secondary):** the sleeve's cash is split equally among submitted names, at most 3 slots per name (PLACEHOLDER), as **one** order per name; quantities are still fixed pre-auction.
- Cash return 0 in the primary run (W4 of Lemma 3). Non-filled exits tie up capital; the sleeve's next orders are sized from its actual cash. No leverage, no shorting.

**Order-and-fill policy: default values for the items I-§6.3 / I-§9 list as external inputs (T6). All are PLACEHOLDERS pending user confirmation (§17); none is left open, because the backtest cannot be implemented otherwise. Under SF several of them do not change any simulated number (I-§6.1: "order type and limit price do not enter the simulation"); they are fixed anyway so that the simulated policy is a complete, nameable policy.**

| Item | Default (PLACEHOLDER) | Enters the simulation? | §17 |
|---|---|---|---|
| Buy order type and limit price | Limit order at the day's upper price limit P^up, opening call auction only | Only through the quantity q_i (sizing at P^up) | U38 |
| Sell order type and limit price | Limit order at the day's lower price limit, for the entire remaining quantity of the lot, opening call auction only | No | U38 |
| Information cut-off and submission time | Inputs: data dated ≤ t−1 plus the pre-open public information held by the pipeline; nominal cut-off 09:00 and submission 09:15 exchange time on day t. **Both clock times are written from general knowledge of the auction timetable and are UNVERIFIED ([rule: tbv, RV1])**; with daily data they act only as a declaration of which data may be read | Only as the definition of G_t | U37 |
| Unfilled remainder | Cancelled at the end of the opening auction; **not** left in the continuous session. Buys are not retried; sells are re-submitted at the next opening auction | Yes | U39 |
| Partial fills | **None** under SF (all-or-nothing). If fill-level data are ever used: an entry exists if any shares fill, the lot is the filled quantity, sales allocated to lots first-in-first-out by entry day, charges and shortfall pro rata to value sold, a lot partly sold at a deadline counts as not sold (I-§6.3) — and the remaining external inputs must be fixed in writing first | Not in this plan | U39 |
| Board lots / odd lots | Fractional shares (primary); robustness: buy quantities rounded down to 100 shares, sells of the whole lot **[rule: tbv, RV12]** | Robustness only | U39 |
| Capacity cap of (S3) / (E4) | Order value (quantity × limit price for buys; quantity × previous close for sells) ≤ **1% of the name's average daily traded amount over the 20 trading days ending t−1**, evaluated at notional capital W_0 = 10 million yuan (U19). An order above the cap is recorded as not filled, reason "cap". Sensitivity: no cap; one tenth of the cap (SF-strict) | Yes; it is the only place where the notional capital affects fills | U40 |
| Same security, several lots | Each entry is its own lot, identified by (entry day, name, sleeve). A name already held may be nominated and bought again (new lot). A buy order and a sell order in the same name on the same day are separate orders and are **not netted** | Yes | U42 |
| Several lots of one security due for sale on the same day (a retried exit meeting a scheduled one) | The capacity condition is applied to their **total**; the synthetic fill is all-or-nothing for the total (I-§6.1), so no allocation among lots is needed; proceeds and costs go to each lot (and its sleeve) pro rata to shares sold | Yes | U42 |
| Minimum commission per order | Ignored (primary); included in the lot-rounding robustness run | Robustness only | U1 |
| Broker allocation and fee records | Not applicable (no live trading) | No | — |

The standard order of §8.3 (1 yuan of slot cash) is checked against the cap at the notional slot size W_0 / ((H+1) K), so that ρ_{ti} stays a function of the name and the day only.

### 3.8 Correspondence with the theory files (`setup.md` and `instantiation_ashare.md` govern)

**(i) Executed entry = synthetic fill (I-§8.3).** A_{ti} = 1 iff a buy order in i is recorded as filled by SF on day t; n_t, N_T count synthetic fills; A_{ti} ≤ O_{ti} (A1-G). Unfilled orders have no position and **no label**, and appear only in the **order ledger** (per day and gate: S_t, n_t, non-fills by reason: (S1), (S2), (S3)). **The denominator of every loss rate is the number of executed entries N_T, never the matured entries only. The fill rate is reported next to every loss rate and every trade-level table.**

**(ii) The executed set is the gate's selection composed with the synthetic fill filter.** μ_t is the expected loss count given F_t^syn; it is not the loss probability assessed with G_t when the order was chosen (setup §5 item 5). The fill filter can act differently on different gates. Reported, not corrected: fill rate by gate and reason; characteristics of filled versus unfilled orders; paper outcome of unfilled orders (labelled non-executable); the fill-determination sensitivity of §3.2. A per-submitted-order tabulation (non-fills counted with outcome 0) may be shown as a **descriptive table only**: submission-based entries are a different estimand that I-§7 does not specify, so no label of §3.8, no Theorem 1 quantity and no interval is computed for it.

**(iii) Label O1 — primary: the decision tree of I-§3, implemented exactly as written there (T5; I-§8.5). The text of I-§3 governs; the summary below is for orientation.**
- *Label.* L^mark_{ti} = 1 iff net proceeds at the mark < cost basis; ties are not losses. Cost basis = shares acquired × entry benchmark price (the day-t open) + buy-side explicit charges + modelled buy-side shortfall. Net proceeds at the mark = position value at the mark − sell-side explicit charges − modelled sell-side shortfall, as if the whole position were sold at the mark. O1 is a **valuation at the scheduled exit instant (the opening auction of day t+H)**; it does not say the position could have been sold.
- *Snapshot.* One data snapshot only: the data as of day t + d_label = t+H+1 (§3.3).
- *Step 1 — events and listing status over (t, t+H].* Share-and-cash tracking of the holding state (security j, shares q, cash D): S-a cash dividend to which the position is entitled (D += q × net cash per share); S-b bonus shares / capitalisation / split / consolidation with published multiplier φ > 0 (q := qφ); S-c rights issue (**not subscribed, valued at zero**; q unchanged; **[rule: tbv, RV11]**); S-d removal against cash only on published terms (holding becomes cash); S-e exchange for exactly one listed successor at a published ratio (at most once per entry); **U — anything else, any unclassifiable event, any S-d / S-e event of a successor, or a security no longer listed at day t+H without S-d / S-e ⇒ L^mark := 1, flagged.**
- *Step 2 — price rule at the opening auction of day t+H* (four mutually exclusive cases): **P1** suspended for the auction → last close at which j traded before the suspension, restated to ex-entitlement terms; **P2** auction match → that price, also at a price limit; **P3** no auction match, traded later that day → the official open as published; **P4** no trade at all that day → the day's pre-open reference price. **With daily bars P2 and P3 cannot be told apart; both are implemented as "the published open of day t+H when the stock traded that day", admissible only if the published open equals the auction price whenever the auction matched ([rule: tbv, RV3]).** Tentative value = q·m + D.
- *Step 3 — validation.* The tentative value is accepted only if every input of Steps 1–2 and of the cost model is in the snapshot. **Global override M ("missing input"): if any needed input is absent at any step, L^mark := 1, flagged; M overrides a tentative value.**
- *Cash distributions — by entitlement (I-§5; I-§8.9).* A distribution is attributed to a position iff the position holds the shares at the **close of the record date**, in the quantity held at that close, **whatever the payment date** (record date versus ex-date: **[rule: tbv, RV9]**); amount = announced cash per share net of the fixed withholding rate (U41); an entitled but unpaid amount is a receivable. O1: record dates from day t to day t+H−1. O2 and the deadline labels: record dates from day t to the day before the sale. Ledger and attribution: the same rule; cash ledger, never a trade.
- *Fallback conventions, copied from I-§3 and labelled as what they are.* **"U ⇒ loss", "M ⇒ loss" and "rights not subscribed, valued at zero" are conservative conventions chosen by the theory task, not facts; they turn data problems into recorded losses.** No entry is dropped. No label is revised after day t + d_label. **Reported: the number of entries per branch (S-d, S-e, P1–P4) and, separately, of U and M (A24); if U + M are not rare, every result using O1 states that the label is driven by a convention.** A vendor adjustment factor replaces share-and-cash tracking only if A23 passes. The tree can detect a missing field, not an event missing from the vendor's calendar (A21).
- **There is no "O1-close" variant (T7).** It was removed from the theory (I-§7): a close-mark label would need its own price rule, availability assumption and P&L relation. The plan does not supply them and reports no close-marked label.

**(iv) Label O2 — executable liquidation under the liquidation policy LP (I-§6.1).** For entry (t,i) a sell order for the entire remaining quantity of the lot is submitted to the opening auction of day t+H and of every later trading day until the quantity is zero; under SF the day's order is filled in full at that day's open or not at all (single sale; same-day lots of one security: §3.7). L^liq_{ti} = 1 iff total net proceeds of the sale plus entitled distributions minus sell-side charges are strictly below the cost basis. **Completion convention: L^liq := 1 if the lot is never fully liquidated or if a class-U event occurs before it is.** Events during an extended liquidation: the Step 1 classification over the whole period from day t to the liquidation day. The liquidation delay has no deterministic bound: **nothing guarantees A3 for any fixed lag, and Theorem 1 is not applied to O2.** No non-informative-censoring assumption, no resolved-only estimator; unresolved positions at a reporting date are counted and bounded both ways. O1 = O2 for an entry if its scheduled sale is recorded as filled for the whole lot at the valuation price (branch P2) with the same cost basis, charges and distribution rule; the share with O1 ≠ O2 therefore measures non-filled exits **as defined by SF**, not exits blocked in the market (I-§6.2).
- **Deadline (bracket) labels for Corollary 1.3 — `草稿`; conditional on the result surviving review (I-§6.4; I-§8.11).** Deadline D = H + 10 (PLACEHOLDER, U16), d_label^D = d_D = D + 1, fixed in advance. S_{ti} = 1 iff LP has liquidated the **whole** lot at or before the opening auction of day t+D. **Certification** V_{ti} = 1 iff S_{ti} = 1 and the snapshot of day t + d_label^D contains the complete and final record of that liquidation (every sale, every event with its amounts, every entitled distribution, all cost inputs); L^cert = 1{net proceeds < cost basis} from the certified record. **L^lo := V·L^cert, L^hi := 1 − V·(1 − L^cert): a missing or incomplete record gives lower label 0 and upper label 1. The O1 fallback M ("missing ⇒ loss") is not used for these labels.** The interval is computed through a common revealed set J_T (A4-D) with P_T^D = N_T − |J_T|. Assumption CERT (a record that passes the completeness test is complete and final) is not audited; in the backtest the sale record is produced by the simulation, so CERT can fail only through wrong or revised market-data inputs. If the corollary survives review, the interval [max{0,(K^lo_T − B*_T)/N_T}, min{1,(K^hi_T + P_T^D + B*_T)/N_T}] (radius with d_D; exact form as in `theorems.md`, which governs) is reported with (K^hi_T − K^lo_T)/N_T. **No claim is made that this residual width is an identification limit or that it does not shrink.** If the corollary does not survive, only the deterministic counts are reported.

**(v) Which label enters which quantity** (statuses: header; "synthetic stream" = synthetic fills under SF, filtration F_t^syn).

| Quantity | Label / outcome | Theory item |
|---|---|---|
| Monitoring interval, K_T, P_T (synthetic stream) | O1 (tree of I-§3), d_label = d = H + 1 | Theorem 1(a)–(c), Cor. 1.1 (three review rounds, no error reported; post-round-3 revisions not re-reviewed) |
| Deterministic bracket for the realised loss fraction | O1 | Cor. 1.2 (bracket needs A4 only; same status) |
| Width bound P_T <= dM | O1 with A5 (ledger records each frozen label when its snapshot is available; A18) | Cor. 1.1(b) |
| Dependence diagnostic (§9.5) | O1 | Prop. 2 (reference scenario only) |
| Training target of LOSS gates; frozen labels used by online rules | O1 (always defined; includes U / M fallbacks, counted) | — |
| Interval for the O2 target | L^lo, L^hi (certified) | **Cor. 1.3 — `草稿`; conditional on the result surviving review** |
| Deployed wealth, daily returns, attribution terms | Ledger cash flows (LP exits), benchmark-price accounting | Lemma 3, identity only, for the additive statistic (§8.2); wealth reading needs W1–W4 |
| Per-order return ρ of the confirmatory statistic (§8.3) | Round trip under SF and LP (O2 exit); unresolved at the data end: marked, flagged | none (empirical only) |
| Share with O1 ≠ O2; exit-delay distribution; share unsold at deadline | both | Cor. 1.3 (conditional) |

**(vi) Accounting for the monitor (A4, A5; I-§8.10).** K_T = executed entries through T whose O1 label is revealed and equals 1; P_T = executed entries whose O1 label is not revealed. **"Revealed" means that the frozen final value (computed from the snapshot of day t + d_label) is recorded in the ledger; provisional marks are never used, and a recorded label is never corrected.** Pending labels are counted both ways (P_T enters the upper endpoint). Computed from information available at T only (truncation test). The matured-only rate K_T/(N_T − P_T) is covered by no statement and is **not reported as an estimate of anything covered by the theory**; it appears only as the labelled not-valid comparator Cmp-N.

### 3.9 Two-interval accounting and reconciliation (P2; T4)

**Intervals.** Each trading day t is split at the opening auction:
- *overnight* interval (close of t-1 → open of t): holdings h_t^{on} = positions carried from the close of t-1, valued at that close; return vector x_t^{on} = total return from the close of t-1 to the open of t, including share changes effective on day t and cash distributions to which a holder at the close of the record date is entitled (net of the withholding rate U41; this presumes the record date is the trading day before the ex-date, **[rule: tbv, RV9]**);
- *auction*: all trades of day t are booked at the benchmark price (the open); costs c_t (fees, stamp duty, modelled shortfall) are debited here on traded amounts (§3.6 items 2–3, 5);
- *intraday* interval (open → close of t): holdings h_t^{id} = positions after the auction trades, valued at the open; x_t^{id} = close_t / open_t − 1.
A suspended name has x = 0 in both intervals. **The same two return vectors and the same benchmark prices serve every strategy and reference** (§3.6 item 1), whether a given name is an entry, a continuing position or an exit in that strategy: an entry appears only in h^{id} of its entry day, an exit only in h^{on} of its exit day. Returns are rebuilt from unadjusted prices and event records with net cash amounts; a vendor's adjusted series (gross of withholding) is used only as a cross-check at withholding 0 (A5, A23).

**Daily identity.** With zero cash return, W_t − W_{t−1} = (h_t^{on})'x_t^{on} + (h_t^{id})'x_t^{id} − c_t for every strategy (wealth W at closes). Lemma 3 is applied **to each interval separately** (2T periods) and the terms are summed; because the lemma's identity holds for arbitrary holding vectors, this is an application of it, not an extension (the reading is the plan's, not a statement of `theorems.md`; it is enforced by tests R1–R2 and flagged to the lead, §16.2). With a non-zero cash return (robustness run) the ledger is tested against the recursion of §3.6 item 6.

**Terminal and special cases.** Positions open at the end of the window are marked at the last close and reported as "open at end". In the **ledger**, a position hit by a class-U event or a delisting not covered by S-d / S-e is valued at its last traded price until the event / delisting date and at **0 thereafter (PLACEHOLDER U33, conservative convention; sensitivity: last traded price)**; free data on post-delisting recoveries are UNVERIFIED (A14, **[rule: tbv, RV8]**). Rights issues: not subscribed, valued at zero, in the ledger as in the label.

**Reconciliation — acceptance criteria (PLACEHOLDER tolerances).** Two computations are implemented in separate modules: (L) a **share ledger** (share counts × unadjusted prices + cash; dividends, splits and rights as explicit events); (A) the **return-based attribution track** above.
- **R1 (algebra).** Lemma 3 residual per interval and in total <= 1e-10 × W_0. A non-zero residual is a code error.
- **R2 (ledger).** For every strategy and day, |ΔW^{(A)}_t − ΔW^{(L)}_t| <= 1e-6 × W_{t−1}; cumulated over the window <= 1e-4 × W_0.
- **R3 (explanation).** Every day exceeding the daily tolerance is listed and traced to a specific event; an unexplained excess is a failure.
- **R4 (stress cases on constructed price panels, expected values computed by hand in the test file).**
  - **No-trade cases added in v0.4 (T4): (a) a position held unchanged across a cash-dividend record / ex-date; (b) a position held unchanged across a 2-for-1 split (share multiplier 2, price halves). In both, for every strategy and for the reference path h^E, the traded amount must be exactly 0 and the cost exactly 0; in (a) the cash ledger increases by q × net cash per share; in (b) q doubles and wealth is unchanged.** Also: (c) an unchanged position through a pure price move (traded amount 0).
  - **"Every cost once" (added v0.4):** one buy and one sell with non-zero shortfall — the wealth change equals the benchmark-price P&L minus fees minus shortfall, with the shortfall appearing once (not also in the entry or exit price).
  - **Non-zero cash return with costs debited at the trade (added v0.4; the round-3 counterexample):** initial cash 100, cost 1 debited at the start of the period, cash return 10%, no risky holding ⇒ end wealth 108.9 (not 109).
  - Rights issue (not subscribed, zero value); suspension spanning the scheduled exit (P1); limit-down sequence with non-filled exits; delisting / class-U event; a label hitting outcome M (label 1, flagged); **the same stock entered by one strategy and exited by another on the same day**; two lots of one name due for sale on the same day (§3.7); a stock held by one strategy only; positions open at the window end; a day with zero baseline exposure.
- R1–R4 must pass in `common` (constructed panels) and again on the pilot panel (A20) before any experiment that reports attribution.
- **Cohort-level statement about PERF, qualified.** "PERF's cohort-level composition term is zero" is asserted by a test **only under its conditions**: the cohort's holdings in PERF and in the baseline are proportional over the cohort's whole life (same names filled, same exit dates). The test first checks proportionality; where it fails, a non-zero term is reported and explained, not classified as a bug.

---

## 4. Base strategy

### 4.1 Features (implemented by us in pandas / numpy; **Qlib is not required at run time**)
- **B0 — Alpha158-style price–volume features**, re-implemented from the public definitions in Qlib's `qlib/contrib/data/handler.py` (MIT; reference only, on `DOWNLOAD_LIST.md`). Families: candlestick shape ratios (KMID, KLEN, KUP, KLOW, ...), and rolling statistics over windows {5, 10, 20, 30, 60} of return (ROC), moving average ratio (MA), volatility (STD), regression slope / R-squared / residual (BETA, RSQR, RESI), rolling max / min / quantiles / rank, RSV, price–volume correlations (CORR, CORD), up / down day counts and sums (CNTP, SUMP, ...), and volume analogues (VMA, VSTD, WVMA, VSUMP, ...). The exact list is fixed in `experiments/src/base_strategy/features.md` before training. Agreement with Qlib's own output cannot be tested locally (pyqlib has no Python 3.14 wheel); it is checked only by unit tests against hand-computed values. This is a stated limitation, not a claim of exact Alpha158 replication.
- **R — raw ingredients of Z** (§5.4). Always included whenever Z is excluded, so that "without Z" never means "without the price history and turnover Z is built from".
- Cross-sectional preprocessing per day: winsorise at the 1st / 99th percentile, then rank-transform or z-score (one choice, fixed before training). Missing values: left as NaN for LightGBM; median-imputed plus a missing indicator for the linear model.
- Fundamentals (PE, PB) from BaoStock are **not** used in the primary run (point-in-time validity UNVERIFIED).

### 4.2 Target and models
- Target: the H-day forward return under the execution convention of §3 (open of t to open of t+H), cross-sectionally demeaned and ranked per day.
- **Model 1 (primary): LightGBM** regression on the cross-sectional rank target; LambdaRank variant only as a robustness check. CPU only.
- **Model 2: regularised linear model** (ridge on rank-transformed features; elastic net as part of its tuning budget). Purpose: show whether conclusions depend on the base learner.
- The base strategy takes the top-K by predicted score among tradable candidates each day (§3.7).

### 4.3 Frozen annual deployment algorithm (rewritten: P6)

One algorithm, written here, is used unchanged in the development evaluation, in the null simulation (§10.2) and in the hold-out. It separates four kinds of quantity.

| Quantity | When it is set | What it may use |
|---|---|---|
| **Hyper-parameters** (all of them: tree / regularisation parameters, number of boosting rounds, learning rate, EWMA half-lives, filter look-backs, feature preprocessing choices) | **Once**, in the tuning stage, then frozen for every later year including the hold-out | Tuning years only (below). **No early stopping at deployment**: the number of rounds is a frozen hyper-parameter |
| **Model parameters** (fit) | Refit at the start of each calendar year Y | Expanding window of samples whose label windows end before the cut-off; purge + embargo of d = H + 1 days |
| **Calibration maps** (isotonic map of CONF; probability calibration of classifiers) | Start of each year Y | The deployed model's out-of-sample scores on year Y−1 with **matured** labels only ("matured" throughout §4 and §6 = the label's frozen value, computed from the snapshot of entry day + d_label, is recorded by the time it is used, §3.3; a frozen label is used as recorded and never recomputed) |
| **Thresholds** (to reach target coverage c) | Start of each year Y; not adjusted within the year | Quantile of the deployed model's out-of-sample scores on the nominated names of year Y−1 (uses no labels) |
| **Online states** (PERF's EWMA, volatility estimates of VT / VOL / TREND) | Daily, by their fixed update rule | Data through the close of t−1; labels matured by then |

**Schedule (PLACEHOLDER years, §17 U7).**
1. *Base predictor.* Tuning: for v in {2011, 2012}, fit on data through v−1, score year v; choose the configuration by mean validation RankIC; freeze. Deployment: for each Y >= 2013, fit on data through Y−1 with the frozen configuration, predict Y. Base scores are converted to within-day ranks before any gate uses them, so that scores of different annual models are comparable.
2. *Gates and learned filters.* For deployment year Y: **fit on base out-of-sample data through Y−2; calibrate and set thresholds on year Y−1 (out of sample for that fit); deploy over Y.** Tuning: validation years v in {2015, 2016} (fit 2013..v−2, calibrate v−1, evaluate v); one configuration per method by the common criterion of §6.3; freeze.
3. *Development evaluation years:* 2017–2021. *Hold-out:* 2022-01 to 2026-06. In the hold-out the same refit / calibration / threshold updates continue; e.g. the 2024 thresholds use the scores of 2023 and the 2024 calibration uses 2023 labels that have matured. **That use of past hold-out-period labels is part of the frozen algorithm and involves no choice by a person; no hyper-parameter, search space, feature list or rule is changed after the freeze.** This removes the contradiction in v0.2 between "validate on Y−1" and "no re-tuning in the hold-out".
4. The tuning years 2015–2016 are reported separately and labelled "tuning years (selection-biased)"; they enter no development estimate, power calculation or test.
- **Purging and embargo:** samples whose label window overlaps a cut-off are removed; a further gap of H + 1 trading days (cf. `lopezdeprado2018advances`).
- **Training population of gates:** names ranked in the base top-K_tr on each day, K_tr = 3K (PLACEHOLDER), with labels / returns from standard counterfactual orders (§8.3); gates are applied to the top-K. Same population for LOSS, LOSS-LR and NET-K; NET-U trains on all of C_t.
- **Known weaknesses, stated:** tuning rests on two validation years each (2015 contains the mid-2015 crash); the deployed gate model is one year stale (fit through Y−2); thresholds assume the score distribution of Y−1 carries to Y — realised coverage is reported and will differ from c.

### 4.4 Final frozen hold-out
- **2022-01-01 to 2026-06-30.** Not touched (no fit, plot or summary of strategy outcomes) until all of the following are done and recorded by the lead in `STATUS.md`: conventions (§3), feature lists, model classes, frozen hyper-parameters, the algorithm of §4.3, estimands and test cards (§8), every parameter of §17, and the analysis code are frozen and hashed; **the reconciliation tests R1–R4 pass; `synth_validation` passes; the complete-null pipeline simulation passes its criterion (§10.2)**; `power_precheck` has been reported to the user.
- The hold-out is run **once** per pre-specified configuration. Anything changed after unblinding is reported as post hoc.
- Caveat: the hold-out is frozen with respect to our code; the broad history of 2022–2026 is public knowledge.

---

## 5. Feature groups Z_H and Z_O, and their controls

Two groups, never merged in a confirmatory contrast. **Z_H = holder-state variables** (§5.1–5.3, definitions unchanged from v0.2). **Z_O = observable actions of other identifiable participants** (§5.6). Every feature for the day-t decision uses data available by the close of t-1 under the timing rules stated for it.

**Z_H inputs:** P = adjusted close, V = daily turnover as a fraction of tradable shares (definition per audit A10).

### 5.1 Capital-gains overhang (Grinblatt–Han style; `grinblatt2005prospect`)
- Reference price: RP_t = (1/k_t) * sum_{n=1}^{N} [ V_{t-n} * prod_{tau=1}^{n-1} (1 - V_{t-n+tau}) ] * P_{t-n}, where k_t normalises the weights to sum to one.
- CGO_t = (P_{t-1} - RP_t) / P_{t-1}.
- **NOT CHECKED AGAINST THE ORIGINAL.** The formula above (weights, normalisation, the timing of P and RP, the sign and denominator of CGO) is written from memory of Grinblatt & Han (2005) and **must be checked line by line against the paper before any code is written**; the check (page / equation number, and every deviation) is recorded in `experiments/src/base_strategy/features.md`. Until then the definition is UNVERIFIED and may change. Known deviation: the original uses weekly data over about five years; we use daily data. Primary N = 250 trading days; variants N = 500 and a weekly 260-week version are pre-specified robustness definitions, not tuning choices.
- Fields: adjusted close, turnover. Suspended days contribute V = 0.

### 5.2 Chip-distribution statistics (turnover-decay method, own numpy implementation)
Algorithm as documented in `literature/resources.md` F1 (reference: `myhhub/stock`, `instock/core/kline/cyq.py`, Apache-2.0; read as reference after approval, re-implemented, source credited):
- Price grid of G cells (default 150) over the window's [min low, max high]; window W = 210 trading days (the reference defaults).
- Each day: existing chips c(p) <- c(p) * (1 - V_t); then add mass V_t spread over [low_t, high_t] with a triangular density peaking at (O+H+L+C)/4; a one-price day adds a point mass.
- Outputs at t-1: **profit ratio** PR = share of chip mass at prices below P_{t-1}; **average-cost gap** (P_{t-1} - mean cost) / P_{t-1}; **90% and 70% cost-band width** relative to price (concentration); **overhead supply** = share of mass in (P, 1.1 P].
- Fields: adjusted O/H/L/C, turnover. Validation: where permitted, compare with AKShare `stock_cyq_em` on its most recent ~90 days for a sample of stocks (needs `py_mini_racer`; Python 3.14 wheel UNVERIFIED; optional).
- Note: 5.1 and the average-cost gap are close relatives; their correlation is reported, and they are treated as one feature group, not as independent evidence.

### 5.3 Abnormal turnover
- ATO_t = mean(V over the last 20 trading days) / mean(V over the last 250 trading days), in logs. **NOT CHECKED AGAINST THE ORIGINAL.** The definition is meant to follow the abnormal-turnover measure of Liu, Stambaugh & Yuan (2019, `liu2019size`); the windows (20 / 250 days), the use of logs and the frequency are written from memory, are UNVERIFIED, and **must be checked against the paper before any code is written** (check recorded in `features.md` as for §5.1). If the original differs, the original definition becomes primary and the one above a labelled variant.
- Short-window variant: log( V_{t-1} / mean(V over the prior 20 days) ).
- Fields: turnover.

### 5.2a Implementation details of §5.1–5.2 that must be fixed before coding (P12)
- **Turnover outside [0, 1].** The decay weights (1 − V) are meaningless for V > 1. Rule (PLACEHOLDER): V is capped at 1 inside the recursions only, the number of capped stock-days is reported (A19), and a sensitivity drops those stock-days' windows instead. No other clipping.
- **Initial chip mass.** The recursion starts W days before the first feature date with all mass spread uniformly on the first day's [low, high] (PLACEHOLDER; the reference implementation's choice is to be read first, `myhhub/stock`, Apache-2.0); features are NaN until W days have elapsed since the first traded day, and for 60 days after a suspension longer than W/2 days (PLACEHOLDER).
- **Warm-up of variants:** §2.2.
- The formulas of §5.1 (CGO) and §5.3 (abnormal turnover) remain **NOT CHECKED AGAINST THE ORIGINAL; implementation is blocked until they are checked line by line against Grinblatt & Han (2005) and Liu, Stambaugh & Yuan (2019)** and the check is recorded in `experiments/src/base_strategy/features.md`.

### 5.4 Control groups (rewritten: P8)

"Without Z" never means "without the raw material of Z". The control set is R = R_H ∪ R_O and is in **every** feature set of every learned method.

- **R_H-sum (as v0.2):** returns over {1, 5, 20, 60, 120, 250} days; price relative to rolling means and to the undecayed turnover-weighted average price; position in the rolling range; turnover levels, means, standard deviations, cumulative turnover; high–low range statistics — same fields and look-backs as Z_H.
- **R_H-hist (new, matched-window history control):** for each window length used by a Z_H feature (250 and 210 days in the primary definitions), the window is cut into 10 consecutive equal bins (PLACEHOLDER) and, per bin: cumulative return, mean turnover, cumulative turnover, bin volume-weighted price relative to P_{t-1}, mean (high − low)/close. This gives a learner the time-ordered price / turnover path over exactly the windows Z_H consumes, at bin resolution.
- **R_O (new, event-trigger and coverage controls for Z_O), computed from daily bars for every stock** on the same look-backs as Z_O ({1, 5, 20} days): daily return and its deviation from the index return, amplitude (high − low)/preclose, turnover, closed-at-limit-up / limit-down flags, counts of days in the look-back meeting each proxy trigger threshold (thresholds as in the exchange rules once OA1 has archived them; until then UNVERIFIED), largest one-day traded amount relative to its 60-day mean. Purpose: the Dragon–Tiger list is published only for stocks with extreme price / turnover on the day, so "being listed" must be separated from the price–volume event that causes the listing.
- **What the controls do and do not license (interpretation narrowed).** A Z contrast is a **pipeline feature intervention**: "adding the group to this pipeline, which already contains R, changed the statistic". It shows incremental value **over these summaries**, not over arbitrary functions of the same raw history; R_H-hist reduces but does not close that gap (bin resolution; variants with longer windows).

### 5.5 Diagnostics reported before any gate uses Z
Missingness and coverage by year; cross-sectional distributions; correlation of each Z feature with |base score|, with R, and between the two groups. If a group is related to |score|, contrasts are additionally reported with the group residualised on |score| and R; **the residualising regression is fitted on the training window of the same annual fit only** and applied forward (never on the full sample).

### 5.6 Z_O — observable actions of other identifiable participants (new; pending user confirmation at Gate 2)

Evidence base, stated with its depth: `literature/opponent_action_variables.md` reports published A-share studies for each class below, **all read at abstract or bibliographic level only** (no full text); `data_feasibility_opponent_actions.md` reports that the interfaces answered for single dates / stocks, with **no check of value correctness**. Neither file is an externally reviewed result. The plan makes no directional prediction for any class (the literature file itself records mixed directions, e.g. for insider sales).

#### 5.6.1 Classes (free data; AKShare)
| Class | Source table | Raw fields allowed (whitelist, OA2) | Not used |
|---|---|---|---|
| **LHB — Dragon–Tiger list** | `stock_lhb_detail_em` (daily summary), `stock_lhb_jgmmtj_em` (institutional seats, daily) | listing date; net buy, buy, sell amounts of the disclosed seats; their share of the day's traded amount; number of buying / selling institutional seats; institutional net buy amount; listing reason code | "上榜后 N 日" returns, "解读", names; seat-level detail (not fetched) |
| **BLK — block trades** | `stock_dzjy_mrtj` (per stock-day), `stock_dzjy_mrmx` (per trade) | trade date; price premium / discount to the close; traded amount and its share of float market value; number of trades | broker-office names (mostly "机构专用" in recent years per the probe) |
| **INS — executed share changes of large shareholders and insiders** | `stock_ggcg_em` | announcement date; direction; change as a share of total and of float shares; change start / end dates | "最新价", "涨跌幅" (current snapshot); `stock_hold_management_detail_em` (no announcement date) |

INS: **only information available after the announcement date is used; the event is dated by its announcement, never by the transaction dates.** The table was back-filled (OA6); the announcement-date field cannot be verified from free data except on the OA5 sample.

#### 5.6.2 Availability rule (fixed per class by the audit, before any modelling)
An event disclosed on trading day s is usable for decisions of day **t >= s + 1** if and only if OA1 has archived an exchange rule text showing publication after the close of s and before the next open for the whole sample period of that class; otherwise, and always for INS (date-only announcement stamp), **t >= s + 2**. The descriptions of disclosure timing in the two input files are marked there as not verified against rule originals and are not relied on. The alternative lag is a labelled sensitivity.

#### 5.6.3 Encoding (events are sparse; Z4)
For each class and each look-back W in {1, 5, 20} trading days (PLACEHOLDER), per stock-day:
- **event indicator** 1{at least one usable event in the last W days};
- **days since the last usable event**, capped at 60, set to 0 when there is none (the indicator distinguishes the cases);
- **intensity**, 0 when there is no event: LHB — signed net buy of disclosed seats and signed institutional net buy, each divided by the stock's 20-day average traded amount; BLK — traded amount / float market value, and the amount-weighted discount; INS — signed change as a share of float shares, summed over the look-back, buys and sells separately.
No value is imputed: "no event" is the value 0 with indicator 0. Before a class's measured start date (OA3) all its features are NaN and the class's analysis starts there. A per-class "data exist on this date" indicator is part of R_O.

#### 5.6.4 Classes not included, with reasons
- **Northbound per-stock holdings:** daily disclosure ended in 2024-08 (data file: series 2017-03-16 to 2024-08-16; exchange notice original not opened), i.e. inside the hold-out. Not used.
- **Margin trading:** not in Z_O. The literature file reports (abstracts only) no stable incremental predictability once turnover is controlled, and classifies it as a leverage / crowding state rather than an action of an identifiable informed party. **Researcher's judgement on the suggested negative control: not in round 1.** Reasons: it would cost about 8,000 requests plus a coverage-restricted sub-sample analysis; it is not a known null (one abstract-level study), so a non-null outcome would be uninterpretable as a pipeline check; the false-positive behaviour of the pipeline is tested directly by §10.2. It is listed as an optional, unscheduled exploratory item (§17 U31).
- **Shareholder counts:** a holder-state variable, and the probed table starts in 2013 and failed for a delisted name. Not used in either group in round 1.
- **Pledges, site visits, buy-backs:** not used (snapshot / coverage problems in the data file).
- **Restricted-share unlock schedules and pre-disclosed selling / buying plans: out of scope for this paper; possible future extension if licensed data become available** (user decision relayed by the lead, 2026-11-15: free data only). Free data cannot support them point-in-time: no structured interface for plan announcements; the unlock table lacks an announcement date and looked incomplete for a delisted name. No experiment in this plan uses them.

#### 5.6.5 Consequences of sparsity for inference (Z4)
- Results for Z_O are reported on **(a) the full sample** (the confirmatory statistic, §8.4 card C4) and **(b) the event sub-sample** — nominated stock-days with at least one Z_O indicator equal to 1, a set fixed by pre-decision information — which is exploratory.
- Share of nominated stock-days in the event sub-sample, by year and class, is reported first (UNVERIFIED; no estimate is offered).
- Power: the two gates of card C4 can submit different orders only where their scores differ. If they differ on a share q of orders, the full-sample statistic equals q times the mean difference on the changed orders; a small q therefore shrinks the detectable full-sample effect. q and the resulting minimum detectable effect are measured in `power_precheck` on development data and reported before the freeze. No value of q is assumed here.

---

## 6. Gates, filters and baselines

Feature sets: **"−Z" = B0 + R + base score**; "+Z_H" adds Z_H; "+Z_O" adds Z_O; "+Z_H+Z_O" adds both. The nominated list of the confirmatory analysis is always the top-K of the **base(−Z)** predictor (features B0 + R).

### 6.1 Round 1 (extended: P4, P5)

"Within-batch?" = the method chooses a strict subset of the day's nominated names on some days, so the Q-select statistic of §8.3 is informative for it.

| ID | Method | Definition | Within-batch? | Enters |
|---|---|---|---|---|
| G0 | Ungated | Submit all K nominated orders | no | reference |
| SCORE | **Top-⌈cK⌉ by base score** (new) | Each day submit the ⌈cK⌉ highest-ranked nominated names | yes (fixed count) | Q-total, Q-select |
| CONF | Calibrated-confidence filter | Submit a name if the calibrated probability of a positive net H-day return (isotonic map of the base rank score, §4.3) exceeds a global threshold. Differs from SCORE through the global threshold (daily count varies) and ties | yes | Q-total, Q-select, **card C1** |
| LOSS-LR(−Z) | **Regularised logistic loss classifier** (new) | L2-penalised logistic regression for L^{(1)} = 1 on the −Z features (rank-transformed, median-imputed with missing indicators); submit if predicted loss probability <= threshold | yes | Q-total, Q-select |
| LOSS(−Z) | Generic loss predictor | LightGBM classifier for L^{(1)} = 1 on −Z features | yes | Q-total, Q-select, **cards C2, C3, C4** |
| LOSS(+Z_H), LOSS(+Z_O) | Same class, grid and budget; feature group added | — | yes | **card C3; card C4** |
| LOSS(+Z_H+Z_O); LOSS(+perm Z_H), LOSS(+perm Z_O) | Both groups; capacity-matched nuisance controls (§7.3) | — | yes | exploratory |
| NET-K(−Z / +Z_H / +Z_O) | **Net-return selection on the base top-K** (new) | LightGBM regression of the standard order's net return ρ (§8.3; already cost-adjusted) on the same features, **same training population (top-K_tr), same nominated list, same coverage denominator K, same randomisation pool** as LOSS; submit if prediction >= threshold | yes | Q-total, Q-select (architecture comparison with LOSS at matched opportunities) |
| NET-U(−Z / …) | **End-to-end net-return selection on the full candidate set** | Same regression trained on all of C_t; each day submit the names of C_t with prediction >= threshold, at most K. Coverage denominator: K (threshold set so that mean orders per day = cK). Randomisation pool: C_t, stratified as in §8.3 | own pool | **Reported separately as an end-to-end benchmark; never in a contrast with top-K gates other than Q-total** |
| VOL, LIQ | **Rule filters** (new) | Submit a nominated name unless its 20-day return volatility is above (VOL) / its 20-day average traded amount is below (LIQ) a threshold set to reach coverage c | yes | Q-total, Q-select |
| TREND | **Market-trend filter** (new) | Submit the full list if the trailing L-day return of the CSI 300 ∪ 500 equal-weight index of the universe is >= a threshold, else nothing; L and the threshold are frozen hyper-parameters | no (all-or-nothing) | Q-total, exposure-schedule attribution |
| PERF | Matured-performance gate | EWMA of the daily cross-sectional RankIC of the base score from labels matured by t−1; full list if EWMA >= threshold, else nothing (after `sanderink2026alpha`; the paper must be re-read before coding) | no (all-or-nothing) | Q-total, exposure-schedule attribution |
| VT | **Feasible exposure control** (new) | All K orders, each slot scaled by s_t = min(1, σ* / σ̂_{t−1}), σ̂ = realised volatility of G0's daily return over the last 60 days through t−1; σ* frozen in the tuning stage so that mean s_t = c on the tuning years. Never above 1 (no leverage) | no | Q-total, exposure-schedule attribution |
| E-const-dev | **Implementable constant scaling** (new) | All K orders, each slot scaled by λ_Y = min(1, mean invested fraction of gate g / that of G0 over year Y−1), fixed at the start of year Y (first year: tuning years). One per gate | no | Q-total comparator |
| E-const-expost | Ex-post constant scaling | G0's holdings scaled by λ = Σ_t e_t^G / Σ_t e_t^B over the evaluation window. **Uses the evaluation window: an attribution reference, not a strategy an investor could have chosen; if λ > 1 it violates the no-leverage rule and is shown as a reference only** | no | level / timing split (§8.2) |
| E-sched | Exposure-schedule reference (Lemma 3, h^E = e^G w^B) | Need not be feasible | — | attribution |
| RND | Stratified random selection at matched order opportunities | Monte-Carlo draws (200 repetitions, PLACEHOLDER) of the gate's per-stratum submitted counts from the nominated list, passed through the same sizing and fill rules. **Used only for path-dependent portfolio metrics; the confirmatory statistic uses the exact expectation of this draw (§8.3)** | — | descriptive |

Coverage: thresholds target c in {0.3, 0.5, 0.7} of nominated orders (primary c = 0.5, PLACEHOLDER) by the rule of §4.3; realised submission and executed coverage are reported.

### 6.2 Round 2 — postponed until round 1 is reported and the user agrees
SGR threshold (`geifman2017selective`); ISA (`zhang2023abstain`); SelectiveNet (`geifman2019selectivenet`); Deep Gamblers (`ziyin2019deepgamblers`); evidence gate (`mohammadpourazari2026safe`); CSA-style calibration (`khosravi2026csa`) and A-RCPS (`xu2024arcps`); ACI / online CRC (`gibbs2021aci`, `angelopoulos2022crc`); PPO / DQN agents; DEUP-style error predictor. Each needs its source re-read before implementation. The reviewer's priority (cheap controls and the checks of §10.2, §12.1 before any neural / RL baseline) is adopted.

### 6.3 Tuning: rules, and what is and is not claimed (rewritten: P6)
1. Same information cut-offs, purge, embargo and deployment algorithm (§4.3) for every method.
2. **Search.** Every learned method gets T = 30 random-search configurations (PLACEHOLDER) from a search space committed to the repository before the first trial; methods with fewer meaningful configurations (SCORE: none; CONF, VOL, LIQ, TREND, PERF, VT: small grids) are searched exhaustively over at most T points.
3. **One selection criterion for all methods:** mean, over the two tuning years and five seeds, of the per-order statistic θ_sel of §8.3 at the target coverage for within-batch methods, and of the annualised arithmetic return AR (§8.1) for all-or-nothing / scaling methods (PLACEHOLDER; frozen at Gate 2). Validation log-loss is **not** a common criterion (it is undefined for regressors and rule filters) and is logged only as a diagnostic.
4. Seeds {0,…,4} for every stochastic method; none dropped. No method-specific rescue.
5. **What "equal budget" does not establish, stated in the paper:** equal trial counts are not equal optimisation effort or equal coverage of search spaces of different size. Two-stage systems use a tuned base model plus a tuned gate (the base is tuned once and shared by all top-K methods); NET-U has one tuned stage. The return-rank base objective plus a loss-classification gate differs from NET in objective as well as in architecture; NET-K exists to hold the opportunity set fixed, not to equalise objectives.
6. **Reported for every method:** the search space, the number of configurations actually distinct, CPU time of tuning and of one refit, the chosen configuration, and the validation score distribution over trials.
7. **Tuning-budget sensitivity (development years only, exploratory):** the whole tuning stage repeated with T in {10, 30, 60} (PLACEHOLDER) and NET-U additionally with 2T; reported: whether the ordering of methods on the development evaluation years changes. Never run on the hold-out.
8. Trial logs are kept in `experiments/results/<name>/tuning/`.

---

## 7. Factorial design for Z_H and Z_O (rewritten: Z5, P8)

### 7.1 Cells
Base predictor feature set b ∈ {−Z, +Z_H, +Z_O}; gate (LOSS) feature set g ∈ {−Z, +Z_H, +Z_O, +Z_H+Z_O}. **Confirmatory cells use b = −Z only**, so all three gates choose from the same nominated lists:

| Cell | Base | Gate | Role |
|---|---|---|---|
| (−,−) | −Z | LOSS(−Z) | reference of both Z contrasts; also card C2 |
| (−,H) | −Z | LOSS(+Z_H) | **confirmatory, card C3** |
| (−,O) | −Z | LOSS(+Z_O) | **confirmatory, card C4** |
| (−,HO) | −Z | LOSS(+Z_H+Z_O) | exploratory: are the groups substitutes or complements in the gate |
| (H,−), (O,−) | +Z_H / +Z_O | LOSS(−Z) | exploratory: group in the base predictor. The gate sees the +Z base score, so "gate without Z" means "no direct Z features", not "no Z information"; nominated lists differ from the reference |
| (H,H), (O,O) | +Z | LOSS(+same group) | exploratory |
| N-K, N-U | — | NET-K / NET-U with −Z, +Z_H, +Z_O | exploratory: one-stage selection |
| Ungated(+Z_H), Ungated(+Z_O) vs Ungated(−Z) | — | — | exploratory: cross-sectional return information with no abstention |

### 7.2 Contrasts
| Contrast | Question | Status |
|---|---|---|
| (−,H) − (−,−) | Does adding Z_H to the gate change within-batch selection at fixed nominations? | **Confirmatory (C3)** |
| (−,O) − (−,−) | Same for Z_O | **Confirmatory (C4)** |
| (−,HO) − (−,H) − (−,O) + (−,−) | Interaction of the two groups in the gate | Exploratory |
| (H,−) − (−,−), (O,−) − (−,−) | Group in the base predictor (changes nominations; Q-total and descriptive only) | Exploratory |
| Fixed-nomination placement (§7.3 b) | Same information in the score versus as gate features, nominations held fixed | Exploratory |
| NET-K(+Z) − NET-K(−Z); NET-K − LOSS at the same feature set | One-stage value of the group; architecture at matched opportunities | Exploratory |
| All of the above with R_H-hist or R_O removed | How much of an apparent effect the stronger controls absorb — a warning about weaker controls, not evidence for Z | Exploratory |

### 7.3 Controls required by P8 — applied to both groups
(a) **Matched-window history controls** R_H-hist and R_O are in every feature set (§5.4).
(b) **Fixed-nomination placement experiment.** Nominations from base(−Z); gate LOSS(−Z) receives, as one extra feature, the within-day rank score of the base(+Z_H) (resp. +Z_O) predictor. Compared with (−,H) (resp. (−,O)) and with (−,−): the group's information routed through a score versus given to the gate directly, on identical nominated lists.
(c) **Capacity-matched nuisance control.** LOSS(+perm Z_x): the gate receives the Z_x columns after an independent permutation across the nominated-training population within each day (for Z_O, within day and class, so that the number of events per day is preserved), re-drawn per seed. Same number of features, marginal distributions and missingness as Z_x, no stock-specific content. Reported: θ_sel of LOSS(+perm Z_x) minus that of LOSS(−Z). If this nuisance contrast is itself distinguishable from zero, the corresponding confirmatory contrast is reported with the warning that feature count / tuning, not content, may drive it.
(d) **Residualisation** only with regressions fitted on training data (§5.5).

### 7.4 Interpretation rules fixed in advance
- A contrast is described as "adding the group to the gate of this pipeline changed / did not detectably change within-batch selection, given controls R". It is not described as evidence about private information, about a game, or about arbitrary uses of the raw history.
- An effect present under Q-total but not under Q-select is reported as an exposure effect. An effect present only when a control set is removed is reported as "not incremental to the controls".
- For Z_O, full-sample and event-sub-sample results are shown side by side (§5.6.5).

---

## 8. Estimands (rewritten: P1, P2, P3)

Three different quantities are defined and never interchanged. A = 242 trading days per year is a fixed annualisation constant (convention).

### 8.1 Deployed-strategy outcomes (Q-total)
For a feasible strategy a with wealth W_t^a at closes (W_0 common) and daily return r_t^a = W_t^a / W_{t−1}^a − 1:
- **(D-wealth) terminal wealth ratio** TW^a = W_T^a / W_0 and **CAGR^a** = (TW^a)^{A/T} − 1. Descriptive; block-bootstrap intervals from resampled daily returns, compounded. **Not decomposed and not used in any test.**
- **(D-add) annualised arithmetic return** AR^a = (A/T) Σ_t r_t^a. Additive over days; its scale does not drift as wealth compounds. This is the Q-total statistic: ΔAR = AR^G − AR^{comparator}, comparators G0, E-const-dev (feasible), SCORE, VT.
- Q-total compares **feasible strategies only**, with the same initial capital, execution rules, cost model and dates. Q-total contrasts are descriptive (unadjusted intervals); none is in the confirmatory family.

### 8.2 Additive attribution of ΔAR (Lemma 3 on two intervals per day)
- Wealth-normalised holdings h̃_t^{a,•} = h_t^{a,•} / W_{t−1}^a for • ∈ {on, id} (§3.9), exposures e_t^{a,•} = 1'h̃_t^{a,•} (invested fraction), weights w_t^{a,•} = h̃_t^{a,•} / e_t^{a,•}, cost rate c̃_t^a = c_t^a / W_{t−1}^a. Then r_t^a = (h̃_t^{a,on})'x_t^{on} + (h̃_t^{a,id})'x_t^{id} − c̃_t^a exactly, and Lemma 3 applied to the 2T intervals gives
  Σ_t (r_t^G − r_t^B) = Σ_{t,•} (e_t^{G,•} − e_t^{B,•}) (w_t^{B,•})'x_t^{•} [exposure-schedule] + Σ_{t,•} e_t^{G,•} (w_t^{G,•} − w_t^{B,•})'x_t^{•} [aggregate composition] − Σ_t (c̃_t^G − c̃_t^B) [cost].
  Multiplying by A/T gives a split of ΔAR. Lemma 3's wealth reading uses the sufficient conditions W1–W4 (self-financing, total returns, all costs, zero cash return); the primary ledger is written to satisfy them and this is **tested** by R2–R4, not assumed. Holdings, returns and costs follow benchmark-price accounting (§3.6: same price for all strategies at each instant, every cost once through the cost term, share-based trades, distributions in the cash ledger). With a non-zero cash return (robustness) the split is reported as "additive excess return as defined" and the ledger is checked against W_{T+1} − W_1 = Π + Σ_t ρ_t (W_t − c_t) (§3.6 item 6).
- **Conventions (fixed; Lemma 3 qualifications 1 and 5):** interaction booked under composition (reference h^E = e^G w^B); the other ordering as a labelled sensitivity. When e_t^{B,•} = 0: w_t^{B,•} = equal weight on the baseline's nominated lists of the cohorts it would hold in that interval; if there is none, 0. Days with zero baseline exposure are counted.
- **The reference's notional cost** C^E is computed from the trades implied by the path h^E with the share-based traded-amount formula of §3.6 item 3 (pre-trade shares after corporate actions; cash distributions are not trades) and the same cost rates as every real strategy; h^E need not be feasible, and its trades are never executed (convention fixed in advance, I-§8.13).
- **"Aggregate composition" is not the Q-select estimand.** It contains every difference between w^G and w^B: within-batch selection, the mix of overlapping entry cohorts (which changes whenever a gate skips or thins a day), sector / size / liquidity tilts. It is reported descriptively under that name. A cohort-level version (identity applied per entry cohort and summed; exact by additivity) is exploratory, with the qualification of §3.9 for PERF.
- **Level / timing sub-split of the exposure-schedule term** (exploratory, ex post): with λ of E-const-expost, level = (λ − 1) Σ e^B (w^B)'x, timing = Σ (e^G − λ e^B)(w^B)'x.
- Not decomposed: CAGR, Sharpe ratio, drawdown, CVaR, loss frequency.

### 8.3 Within-batch selection at matched order opportunities (Q-select)
- **Standard order and its return.** For every nominated name i on day t, ρ_{ti} = net P&L, per yuan of slot cash, of one standard order of 1 yuan of slot cash placed by the rules of §3 (pre-determined quantity from G_t, synthetic fill rule SF, exit by LP with re-submission after non-filled exits, benchmark-price accounting with the full cost model, entitlement-based distributions). ρ_{ti} = 0 if the order is recorded as not filled (the yuan stays in cash). ρ_{ti} depends on the name and the day only, not on the gate or on any strategy's wealth: **a standardised cohort comparison at fixed initial yuan.** Orders unresolved at the end of the data are valued at the last mark and flagged.
- **Matched order opportunities, not matched exposure.** The comparator has the same number of submitted orders, the same yuan per order and the same per-stratum counts on each day. It does **not** equalise invested exposure of deployed strategies (fills, blocked exits and sleeve wealth differ); the term "matched exposure" is not used for it.
- **Strata (PLACEHOLDER, fixed before results):** liquidity tercile × volatility tercile within the day's nominated list, from data through t−1.
- **Per-day excess.** With Sub_t^g the names gate g submits, S_t^g = |Sub_t^g|, S_{t,s}^g its count in stratum s, and ρ̄_{t,s} the mean of ρ over all nominated names of stratum s:
  u_t^g = Σ_{i ∈ Sub_t^g} ρ_{ti} − Σ_s S_{t,s}^g ρ̄_{t,s}.
  The second sum is the exact expectation of the first under a uniformly random choice of S_{t,s}^g names from each stratum, so no Monte-Carlo draw and no coarsening of strata is needed. u_t^g = 0 by construction on days with S_t^g ∈ {0, K}; such days carry no selection information and are counted.
- **Statistic.** θ_sel^g = Σ_t u_t^g / Σ_t S_t^g over decision days of the evaluation window: the order-weighted mean net return of the gate's orders in excess of a stratified random choice from the same nominated list, in return units per order (reported in bps). A ratio of sums; inference resamples the pairs (u_t, S_t) by date (§10).
- **Translation to capital (descriptive only):** θ_sel × (realised coverage) × A/(H+1) approximates the annual additive contribution per unit of capital; at c = 0.5 and H = 5, 5 bps per order ≈ 1.0% per year.
- Variants (exploratory): per filled yuan instead of per ordered yuan; gross of costs; capital-weighted by actual slot cash; unstratified; fill-matched pool.
- Stated limitation: by construction this statistic gives no credit for avoiding whole days. Timing value is assessed only under Q-total and the exposure-schedule term.

### 8.4 Cards of the confirmatory tests

All four: hold-out window, primary H, K, c, cost model and conventions; seed-averaged series (u_t and S_t averaged over the five seeds); nominated lists from base(−Z); return ρ from simulated round trips — synthetic fill under SF, exit by LP (O2 exit), benchmark-price accounting; label O1 enters only as the LOSS training target; date-block bootstrap of §10; one Holm family. **All four cards are statements about the backtest under the synthetic execution model of §3.2; the fill-determination sensitivity (§3.2, §11) is reported beside them.** None of them uses a theory result.

**Card C1 — H-A, CONF**
- *Estimand:* θ_sel^{CONF} (§8.3). *Comparator:* exact stratified-random expectation from the same nominated list, same per-stratum order counts. *Weighting:* per ordered yuan, order-weighted over days.
- *Null hypothesis (equivalence test):* H0: |θ_sel^{CONF}| >= Δ_ord, with Δ_ord the per-order equivalence bound (§9.3). *Alternative:* |θ_sel^{CONF}| < Δ_ord.
- *Test statistic:* t_L = (θ̂ + Δ_ord)/ŝe, t_U = (Δ_ord − θ̂)/ŝe; p_eq = max{1 − Φ(t_L), 1 − Φ(t_U)} (§10). *Labels used:* ρ from O2 exits.

**Card C2 — H-A, LOSS(−Z)**
- As C1 with θ_sel^{LOSS(−Z)}. Additional label use: O1 as the classifier's training target.

**Card C3 — H-Z, holder-state group in the gate**
- *Estimand:* ψ_H = θ_sel^{LOSS(+Z_H)} − θ_sel^{LOSS(−Z)}, both gates on the same nominated lists, each relative to its own exact stratified expectation. *Comparator:* LOSS(−Z), same model class, grid, budget, coverage target.
- *Null hypothesis (difference test, two-sided):* H0: ψ_H = 0. *Test statistic:* z = ψ̂_H / ŝe(ψ̂_H); p = 2(1 − Φ(|z|)). *Labels:* O1 for training both gates; ρ from O2 exits.

**Card C4 — H-Z, other-participant-action group in the gate**
- As C3 with ψ_O = θ_sel^{LOSS(+Z_O)} − θ_sel^{LOSS(−Z)}, **full sample** from the later of the hold-out start and the Z_O analysis start (OA3). Included only if at least one Z_O class passes OA1–OA5 before modelling; the classes included are fixed at the audit.

**Size of the confirmatory family: m = 4 (C1–C4), Holm at family-wise level 5%.** If no Z_O class passes the audit, C4 is dropped before any outcome is seen and m = 3. Nothing else is confirmatory: not Q-total, not the aggregate composition term, not NET, SCORE, LOSS-LR, VOL, LIQ, PERF, TREND, VT, not the event sub-sample, not any monitoring quantity.

**What v0.2 tested instead, and why it changed:** v0.2 put the *aggregate* Lemma 3 composition term (which mixes cohort mix and tilts with selection) into the H-A tests and four differently readable Z contrasts into the family (m = 6). The cards above test the within-batch quantity that Q-select is defined as.

---

## 9. Metrics (pre-specified)

### 9.1 Primary descriptive metrics
| Metric | Definition |
|---|---|
| P1 Net performance of the deployed strategy | **AR (annualised arithmetic return, §8.1) — the Q-total statistic**; terminal wealth ratio and CAGR beside it, never substituted for it |
| P2 Loss magnitude, trade level | Mean of min(net trade return, 0) and expected shortfall (mean of the worst 5% of net trade returns) over executed trades, **in three separate columns: resolved O2 returns only (with the count of unresolved trades); a "marked hybrid" (resolved at their exit, unresolved at the last mark) named as such; O1-marked returns.** Each in equal-weight and **capital-weighted** form. The pooled tail statistic is recomputed on each bootstrap resample of **date blocks of trade records**; it is never an average of daily tail statistics |
| P3 Maximum drawdown | Of the daily net wealth curve (empirical; interval labelled indicative only) |
| P4 Turnover | Annualised one-way traded amount (change in corporate-action-adjusted share count × benchmark price, §3.6 item 3; cash distributions are not trades) / average wealth; total cost paid |
| P5 Return of abstained and of unfilled orders | Mean ρ of nominated names the gate did not submit; separately, the paper outcome of submitted-but-unfilled orders (non-executable, descriptive) |

### 9.2 Secondary
θ_sel for every within-batch method; aggregate attribution terms (§8.2); loss fraction among executed trades (O1 and O2 separately), with its uncertainty computed for the ratio Σ_t X_t / Σ_t n_t by resampling the pairs (X_t, n_t); realised submission and executed coverage; invested fraction; synthetic fill rate by reason ((S1), (S2), (S3)), shown next to every loss rate; number of entries per O1 branch (S-d, S-e, P1–P4) and of outcomes U and M; Theorem 1 interval over time for the synthetic fill stream — form (b) primary, forms (a) and (c) beside it, δ = 0.10 (PLACEHOLDER); bracket of Cor. 1.2; Cor. 1.3 interval with the count of uncertified records (`草稿`; conditional on review); P_T; §9.5 diagnostics; Sharpe and Sortino ratios; CVaR(5%) of daily returns; holding time including non-filled exits (as defined by SF); share with O1 ≠ O2; base RankIC series; participation rate at a notional W_0 (PLACEHOLDER 10 million yuan).

### 9.3 Economic equivalence bounds and wording (rewritten: P10)
- **Bound for cards C1, C2: Δ_ord = 5 bps per order (PLACEHOLDER).** Two candidate rules, one chosen at Gate 2: (a) cost-anchored — an effect smaller than a plausible error in the round-trip cost assumption (±5 bps per round trip gives 5 bps per order directly); (b) investor-anchored — the smallest per-order difference that would change the user's decision (via the translation of §8.3). The bound is fixed before development results are examined and is not widened after `power_precheck`.
- **Equivalence p-value:** p_eq = max of the two one-sided p-values (cards C1, C2). It enters the Holm procedure together with the two difference-test p-values of C3, C4. A (1 − 2α)-interval inside the bound is an *individual* level-α TOST and is **not** by itself a family-adjusted verdict; intervals are shown at the unadjusted level and at the level implied by the test's Holm step, both labelled.
- **Wording, binding for RESULTS.md and the paper:**
  - "economically negligible (within ±Δ)" — **only** when the equivalence null is rejected after the Holm adjustment;
  - "a difference was detected" — only when a difference null is rejected after adjustment (direction then reported as estimated);
  - "no detectable difference; inconclusive" — in every other case. "Z adds nothing", "no incremental value" and similar are not used for a failure to reject.
- Exploratory bounds for other statistics (ΔAR within ±1.0% per year; expected shortfall within ±25 bps) are shown with unadjusted TOST results and labelled exploratory.
- Operational form of H-A: for CONF and LOSS(−Z), the verdicts of C1, C2; next to them, descriptively, ΔAR versus G0 and E-const-dev with the three attribution terms. PERF and TREND (no within-batch selection by construction): Q-total and exposure-schedule terms only.

### 9.4 Expected width of the monitoring interval (ESTIMATE — formulas of theorems.md evaluated; no data; re-evaluated for v0.4: **unchanged**)

**Inputs (assumptions).** One sleeve buys per day, at most K = 30 orders: M = 30; n_t = 30 (synthetic fill rate set to 1; UNVERIFIED) or 15 at c = 0.5. **d_label = d = H + 1** (fixed, §3.3), label O1 by the tree of §3.8 (iii). Days (242 per year; calendar counts UNVERIFIED): hold-out ≈ 1,090; development evaluation 2017–2021 ≈ 1,215; a monitor run continuously over both ≈ 2,305. N ≈ 32,700 executed (synthetic) entries in the hold-out (ungated). **What the interval is about:** the target r_T^entry of the synthetic fill stream under SF, filtration F_t^syn (§3.1–3.2), not an executable strategy.

**What changed against v0.3 (T1–T3): nothing in the inputs, so the numbers are unchanged.** d = H + 1 and M = K = 30 are as before; the introduction of d_label = H + 1 changes when labels are frozen, not the lanes; the assumed N rests on a fill rate of 1, as before. The formulas were re-evaluated in a throwaway script for this revision and reproduce every cell of the table below. Two things could move the *realised* widths, neither of which is estimable now: the capacity cap (S3) and the fill-determination variants of §3.2 lower n_t (at constant n_t the half-width hardly depends on its level: 0.219 / 0.173 at n_t = 15 against 0.221 / 0.175 at n_t = 30; irregular n_t widens it, see the all-or-nothing line below). **Deleted in v0.4:** the information row "d = H = 5" and the remark that d = H would be valid under OA-open — O1 as defined does not support lag H (§3.3; I-§4).

**Formula.** Half-width B_T/N_T (form (a)) or B*_T/N_T (form (b)), B_T = Σ_j b(Q_{j,T}), Q_{j,T} = Σ_{t ≡ j (mod d)} n_t², b(q) = sqrt(2^{⌊log₂ q⌋} L_k), b*(q) = min_k (1/2) sqrt(2^k L_k)(1 + q/2^{k+1}), L_k = log(2 d c_0 (k+1)²/δ). With constant n_t the half-width depends on T and d, not on K.

**Estimated half-widths, δ = 0.10, constant n_t = 30, form (a) / form (b).**

| H (d = H + 1) | Hold-out, T ≈ 1,090 | Development evaluation, T ≈ 1,215 | Continuous 2017–2026H1, T ≈ 2,305 |
|---|---|---|---|
| 1 (2) | 0.099 / 0.096 | 0.127 / 0.091 | 0.067 / 0.066 |
| **5 (6), primary** | **0.221 / 0.175** | **0.198 / 0.167** | **0.149 / 0.121** |
| 10 (11) | 0.293 / 0.243 | 0.263 / 0.231 | 0.197 / 0.169 |
| 20 (21) | 0.404 / 0.345 | 0.363 / 0.325 | 0.272 / 0.238 |

- Evaluated with a throwaway script (not in the repository; this revision may change only this file); **`synth_validation` must reproduce the table as its first output.**
- n_t = 15 instead of 30 changes the primary cells by at most 0.003 (the small change comes from the dyadic epochs of the radius). δ = 0.05: 0.228 / 0.180 in the primary hold-out cell.
- All-or-nothing stream (n_t = 30 on a random half of the days; five simulated patterns): primary hold-out cell 0.31–0.33 / 0.24–0.25.
- Form (b) over time at the primary setting: half-width >= 0.5 until about day 128, >= 0.25 until about day 525, 0.175 at day 1,090. Pending-label term: P_T/N_T ≈ d/T ≈ 0.006 (under A5).
- Corollary 1.1's closed-form bound at the primary hold-out setting: 0.25. Proposition 2's lower bound on the full width in its block environment with these (d, M, N): about 0.026, against a full width of about 0.36 for form (b); the gap is constants and logarithms and is not shown to be necessary.

**Consequences (unchanged in substance from v0.2).**
1. Total width at the end of the hold-out about 0.36 (form (b)) to 0.45 (form (a)); wider at every earlier date; [0,1] for about the first half-year of a run.
2. **The interval is not used to compare gates, to rank methods, or in any test.** No claim of the form "the gate lowers the monitored loss probability" will rest on it.
3. Its role: (a) how much a daily trade stream can say without dependence assumptions (with Proposition 2 as the worst-case reference); (b) a validity contrast with the matured-only Wald interval and with valid comparators (§12.1); (c) bookkeeping through Cor. 1.2.
4. Positioning consequence for the lead / user: an appendix-level, "limits of evidence" role.
5. Realised widths are computed from the ledger and reported whatever they are.

### 9.5 Dependence diagnostic (experiment `dependence_diag`; corrected: P11)
**Purpose.** To describe the dependence of the O1 labels on the real stream. Independence (N effective trades) and Proposition 2's block environment (N/(Md)) are **two reference scenarios, not bounds between which the empirical value must fall**.
**Quantities.**
1. *Same-day dependence:* one-way random-effects intraclass correlation of the labels with days as groups, **on the raw labels (not day-demeaned)**, using the ANOVA estimator for unequal group sizes; overall and by year. Day-level over-dispersion of X_t given n_t.
2. *Cross-day dependence:* autocorrelation of X_t/n_t at lags 1..2d; label correlation between entries with overlapping versus non-overlapping holding windows.
3. *Effective sample size:* N_eff = p̂(1 − p̂)/V̂ with p̂ = Σ X_t / Σ n_t and V̂ the variance of that **ratio**, from a date-block bootstrap of the pairs (X_t, n_t) at block lengths {d, 2d, 4d, 8d} (shown as a function of block length) and from a delta-method long-run variance (Bartlett kernel) as a cross-check.
4. *Hypothetical width* z·sqrt(p̂(1 − p̂)/N_eff), labelled as not valid, next to the Theorem 1 half-width.
**Limits printed with the results.** Time variation of μ_t inflates measured dependence and cannot be separated from it; the diagnostic cannot certify a restricted dependence class and **licenses no narrower interval**; block-bootstrap variances assume approximate stationarity. No size or direction is predicted.

---

## 10. Statistical inference

- **Unit of resampling: the trading (decision) date.** Every statistic is a function of date-indexed records — daily returns r_t, per-day attribution contributions, pairs (u_t, S_t), pairs (X_t, n_t), or the day's trade records for pooled trade-level statistics — so within-day dependence is preserved. Trade-level quantities are attached to their entry date; individual trades are never resampled.
- **Method:** paired stationary block bootstrap over dates, applied jointly to all strategies' records, 10,000 resamples (PLACEHOLDER). Ratio statistics (θ_sel, loss fractions) are recomputed as ratios of resampled sums. Path-dependent metrics are recomputed on each resampled path.
- **Block length (corrected: P10).** Mean block length ℓ(H) = 4(H + 1) trading days: 8, **24**, 44, 84 for H = 1, **5**, 10, 20 (PLACEHOLDER). Sensitivity: 2(H + 1) and 8(H + 1) (12 and 48 at H = 5). Every length used satisfies the stated minimum 2(H + 1) for its H; v0.2's fixed set {10, 20, 40, 60} did not. At H = 20 the hold-out contains about 13 blocks of mean length 84: intervals for H = 20 are labelled unreliable.
- **Standard errors and p-values.** ŝe = bootstrap standard deviation of the statistic; one-sided and two-sided p-values from the normal approximation with ŝe (cards, §8.4); percentile intervals are shown beside them. Whether this procedure has its nominal error rates on this kind of data is **not assumed**; it is checked in §10.2, and the procedure may be changed there (before the hold-out) if it fails.
- **Limitations, to be written into the paper:** block bootstrap assumes approximate stationarity and weak dependence beyond the block length, which regime shifts and rule changes violate; drawdown intervals are indicative only; there is one realised market history.
- **Random seeds.** Five seeds for every stochastic component. Seed variation measures optimisation and sampling randomness only; mean ± standard deviation over seeds is reported in its own column and never merged with a bootstrap interval. All seeds are shown; the seed-averaged series is the unit of bootstrap inference.
- **Multiple comparisons.**
  - **Confirmatory family: the four tests of §8.4 (C1, C2 equivalence; C3, C4 difference). Holm step-down on their four p-values (p_eq for C1, C2) at family-wise level 5%; m = 4** (m = 3 if C4 is dropped at the audit).
  - Everything else is exploratory: labelled, reported in full, unadjusted intervals. A data-snooping-robust comparison across all methods (reality-check / SPA type) is optional; references not in the bibliography.
- The hold-out confirmatory analysis is run once. Development and hold-out results are never pooled for a confirmatory test. (Bootstrap references — Politis & Romano; Künsch — are not in `paper/references.bib`; literature-scout must add them before they are cited.)

### 10.1 Prior power calculation (experiment `power_precheck`; development evaluation years only; reported before the freeze)
For each card, on 2017–2021, with the frozen algorithm and the **same statistic and the same bootstrap as the test**:
1. Compute the statistic's bootstrap standard error SE_dev at block lengths 2(H+1), 4(H+1), 8(H+1); use the largest.
2. Predict SE_ho = SE_dev × sqrt(T_dev / T_ho) (T_dev ≈ 1,215, T_ho ≈ 1,090; ESTIMATES of day counts). For C4, T_ho and T_dev are counted from the Z_O start date, and the share q of orders on which the two gates differ is reported (§5.6.5).
3. Normal-approximation requirements, by arithmetic: equivalence with 80% power at a true effect of zero needs Δ_ord >= 2.93 SE_ho unadjusted and 3.52 SE_ho at the strictest Holm step (α/4); the minimum detectable difference at 80% power is 2.80 SE_ho unadjusted and 3.34 SE_ho at the strictest step.
4. Report per card: SE_ho, minimum detectable effect, the smallest bound with 80% equivalence power, and the power at the bound of §17.

Illustration by arithmetic only: with Δ_ord = 5 bps, 80% equivalence power needs SE_ho <= 1.7 bps per order (1.4 bps at the strictest step). The actual standard error is UNVERIFIED.

Limits: assumes development-period dependence and volatility carry over; normal approximation; the development years also informed the design (not the hyper-parameters, §4.3). A planning aid, not a result.

**Pre-declared consequences.** If predicted power at the chosen bounds is below 50% (PLACEHOLDER) for most of the family, the user is told before the hold-out is opened and chooses between: proceeding with the tests labelled "low prior power"; reframing the hold-out analysis as estimation without confirmatory verdicts; widening the data (logged change to §2). Bounds are not widened after this calculation. **"Inconclusive" is a possible outcome of every test and is reported as such.**

### 10.2 Complete-null simulation of the full pipeline (experiment `null_pipeline`; **mandatory before the hold-out is opened**)

**Question.** Do tuning, calibration, thresholding, the matched-opportunity statistic, the block bootstrap and the Holm step, run end to end, reject true null hypotheses about as often as advertised?

**Data.** Development evaluation years 2017–2021 with their tuning years; real prices, real nominated lists, the frozen algorithm of §4.3 including the gate tuning stage, re-run inside every replication. The base predictor and hence the nominated lists are held fixed (all four cards are within-nomination statements); this is a stated limit of the simulation's scope. The hold-out is not used.

**Null worlds.**
- **W-swap (preserves all dependence of outcomes).** In each replication a uniformly random bijection π of stock identities is drawn and the gate-specific feature panel (all −Z, Z_H and Z_O features except the base score) of stock i is replaced by that of π(i) for the whole history. Outcomes, base scores, nominations, strata and their time-series dependence are untouched; the features given to the LOSS gates carry no stock-specific relation to the outcomes. True values: θ_sel = 0 for every LOSS gate, ψ_H = ψ_O = 0. (Handling of names whose swapped partner has no data on a date: left missing; detail fixed in the experiment's README before running.) CONF is not nulled in this world because it uses only the base score.
- **W-perm (covers CONF as well).** Within each (day, stratum) cell of the nominated-training population, the outcome records (ρ and the O1 label) are permuted among names, in training, calibration and evaluation data alike. True values: θ_sel = 0 for every gate including CONF. Limitation: independent daily permutations break the dependence between a name's outcomes on neighbouring days, so this world may be more favourable to the bootstrap than reality; W-swap does not have this defect but does not cover CONF.
- **Boundary versions W-swap+Δ, W-perm+Δ.** The per-order bound Δ_ord is added to ρ of every order submitted by a gate (u_t ← u_t + Δ_ord S_t), which puts θ_sel exactly on the boundary of the equivalence nulls of C1, C2 and leaves ψ_H, ψ_O at 0. Needs no additional fits. In W-perm+Δ all four nulls are true; in W-swap+Δ those of C2–C4.

**Replications.** B_null = 400 per world (PLACEHOLDER), seeds fixed in advance; inside each replication the bootstrap uses 2,000 resamples (PLACEHOLDER; fewer than in the real analysis, stated).

**Recorded.** Per replication and card: the p-value; rejection at nominal 5% unadjusted and after Holm; coverage of the nominal 90% interval for the true value. Across replications: per-test rejection rate, family-wise rate, each with an exact binomial (Clopper–Pearson) 95% interval; the power of the equivalence tests at θ = 0 (from the worlds without Δ), as a by-product.

**Pass criterion (fixed now).** For the true nulls of each boundary world: (i) the number of replications with at least one Holm-adjusted false rejection is **at most 27 of 400** — 28 or more is the smallest count that an exact one-sided binomial test at 5% treats as evidence that the family-wise rate exceeds 5%; (ii) the same count limit for each test's unadjusted rejections at nominal 5%. With B_null = 400 this check detects a true rate of 10% with probability about 0.98 and a true rate of 8% with probability about 0.79 (binomial arithmetic); passing therefore does not establish a rate of at most 5%, it fails to find a rate that is clearly above it. For B_null = 200 the limit would be 15 and those probabilities about 0.86 and 0.54.

**If it fails.** The inference procedure (block length, studentised or percentile-t bootstrap, effective-degrees-of-freedom correction) is revised **using null-world and development data only**, every change is logged, and the simulation is repeated with fresh seeds. If no procedure passes, the user is told and chooses between reporting the hold-out as estimation without confirmatory verdicts, or stopping. The hold-out stays closed throughout.

**Cost (ESTIMATE, unmeasured).** About 200 gate fits per replication (three LOSS gates × 30 configurations × 2 tuning years, plus 15 deployment refits; one seed) × 400 replications × 2 worlds ≈ 160,000 small LightGBM fits on roughly 50–150 thousand rows each: of the order of 100–400 CPU-hours at an assumed 2–10 s per fit, to be run in the background over several days and parallelised over cores. If the pilot's measured fit time puts this beyond the local machine, the fallback, chosen before any null result is seen, is B_null = 200 with the full pipeline (not a reduced pipeline).

---

## 11. Robustness (all pre-specified; all exploratory)

| Dimension | Variants |
|---|---|
| Costs | Slippage 0 / 5 / 10 / 20 bps per side; commission 1 / 2.5 / 5 bps; stamp duty held at 0.10% and at 0.05% throughout; gross run |
| Execution timeline | Synthetic fill at the open of t (primary); at the open of t+1; **VWAP entry of §3.2 — outside the theory: separate table, Q-total and Q-select only, no label of §3.8 and no monitoring quantity** |
| **Synthetic fill determination (T1)** | SF (primary) versus **SF-strict** (conservative) versus **SF-loose**, as defined in §3.2, applied to the frozen orders of the primary run; reported: fill rates, θ_sel, ψ_H, ψ_O, ΔAR and attribution, Theorem 1 interval at the window end, and whether any card's verdict category differs between strict and loose. Capacity cap: none / 1% / 0.1% of the 20-day average traded amount. Retried versus cancelled buys. **All three determinations are retrospective; the gap to real auction fills is not measured by this row** |
| **Hindsight diagnostic (not a strategy)** | Entries whose day-t **close** is at limit-up, or one-price limit days, removed after the fact. **This uses fields of the day-t bar that SF may not read (close, high, low) and is outside F_t^syn. It is not a strategy, no Theorem 1 quantity is computed on it, and it is never called "conservative execution"**; it only shows how sensitive trade statistics are to such trades |
| Funding and sizing | H + 1 pre-funded sleeves with pre-determined quantities (primary); H sleeves with same-auction funding (feasibility UNVERIFIED); notional-at-open sizing (idealised) |
| Holding period | H in {1, 5, 10, 20}, always d_label = d = H + 1 (each H defines its own entries and its own frozen labels; this is not a change of lag on a given label) |
| Market state | Regimes fixed from data through t−1: trailing 60-day index return sign × trailing 60-day index volatility above / below its expanding median; calendar sub-periods |
| Liquidity / universe | Liquidity terciles; CSI 300 versus CSI 500 if membership passes the audit; ST included; listing-age filter 20 / 60 / 120 days |
| Coverage / allocation | c in {0.3, 0.5, 0.7}; cash rule versus refill rule; K in {20, 30, 50} |
| Base learner | LightGBM versus ridge |
| Z_H definitions | CGO window 250 / 500 / weekly (each from its first valid date, §2.2); chip window 120 / 210; turnover definition (A10); turnover-cap rule (§5.2a) |
| Z_O definitions | Availability lag s+1 versus s+2; look-backs; each class alone; full sample versus event sub-sample; with and without R_O |
| Controls | With / without R_H-hist; permuted-Z nuisance control; fixed-nomination placement (§7.3) |
| Labels | O1 (decision tree, primary) versus O2; O1 with entries of outcome U / M shown separately (the label itself is not changed); withholding rate 0% / 10% / 20%; per-submitted-order tabulation (descriptive table only, §3.8 (ii)); deadline D in {H, H+5, H+10, H+20}, each with its own pre-fixed d_D = D + 1 (Cor. 1.3, `草稿`, conditional on review). **No close-marked label (O1-close was removed from the theory, §3.8 (iii)).** |
| Attribution conventions | Interaction under composition versus under exposure; zero-baseline-exposure convention versus w^B = 0; aggregate versus cohort-level; ledger terminal value after delisting / class-U events 0 versus last price |
| Q-select statistic | Per ordered versus per filled yuan; net versus gross; equal versus capital weights; stratified versus unstratified; fill-matched pool |
| Monitoring | δ in {0.05, 0.10}; forms (a), (b), (c); run continuously from 2017 versus restarted at the hold-out start. **Neither d nor d_label is varied; labels are never recomputed with another deadline** |
| Tuning | Budget sensitivity of §6.3 item 7 (development years only) |
| Lots / capital | Fractional shares versus 100-share lots at W_0 = 1 / 10 / 100 million yuan |
| Bootstrap | Block lengths 2(H+1), 4(H+1), 8(H+1) |

Robustness runs never change which specification is primary.

---

## 12. Experiment-to-claim map

Statuses as in the header (source: theorems.md status table). "Empirical only" = theorems.md contains no result for it. A real-data experiment never "confirms" a theorem.

| Experiment | Type | Hypothesis (v3) | Result in `theorems.md` used or checked | Produces | Depends on |
|---|---|---|---|---|---|
| `synth_validation` (§12.1) | Theory validation, synthetic | H-T | Theorem 1(a)(b)(c); Cor. 1.1(a)(b); Cor. 1.2; **Cor. 1.3 (conditional on the result surviving review)**; Prop. 2 (illustration of its construction only); Lemma 3 (identity; benchmark-price accounting cases of R4) with two-interval accounting; Remark 4 (all-loss environment). Statuses: header — none has been re-reviewed after the round-3 revisions | §9.4 table reproduced; any-time failure frequencies with binomial intervals; width scaling; comparator intervals; attribution-recovery and reconciliation tables | numpy only; can start now |
| `data_audit` | Prerequisite | — | Empirical only (preconditions of A1 with F_t^syn, A1-G, A2(b), and of OA-next / A3 / A5; rule texts behind the conventions of §3) | `AUDIT.md`: A1–A24, **RV1–RV13**, OA1–OA9 | `akshare`, `baostock`, pandas stack |
| `common` | Infrastructure | — | Lemma 3 (R1), ledger reconciliation (R2–R4), Cor. 1.2 bracket and truncation tests as unit tests | Backtester, share ledger, attribution track, order ledger, cost model, monitor, bootstrap | Conventions frozen |
| `pilot` (§13) | Pipeline check | — | Empirical only | Go / no-go; measured fill rates, run times, widths, fit times for §10.2 | `data_audit`, `common` |
| `base_strategy` | Prerequisite | — | Empirical only | Feature stores B0, R, Z_H, Z_O; base predictions; G0; §5.5 diagnostics | `data_audit`, `common` |
| `gates_round1` | Application | **H-A** (cards C1, C2 on the hold-out only) | Lemma 3 for the attribution of ΔAR; the Q-select statistic and all tests are empirical only | Q-total tables for all round-1 methods; θ_sel for within-batch methods; attribution; P1–P5; order-ledger reports | `base_strategy` |
| `z_factorial` | Application | **H-Z** (cards C3, C4 on the hold-out only) | Empirical only (Lemma 3 for the descriptive attribution of cells) | Cells and contrasts of §7; nuisance and placement controls; Z_O full sample and event sub-sample | `base_strategy` |
| `monitoring_real` | Descriptive; not confirmatory; not used to compare methods | **H-T** | Theorem 1(b) primary, (a), (c), label O1 (decision tree), d_label = d = H + 1; Cor. 1.1; Cor. 1.2; **Cor. 1.3 (`草稿`; conditional)**. **Applied to the synthetic fill stream under SF with filtration F_t^syn only; validity on that stream further depends on the audit items A11, A18, A21–A24** | Interval series per synthetic stream; branch / U / M counts; no coverage claim (truth unobserved); no statement about an executable strategy | `base_strategy`, `gates_round1` |
| `dependence_diag` (§9.5) | Diagnostic | H-T | Prop. 2 as one reference scenario; estimates empirical only | ICC, autocorrelations, N_eff by block length | `base_strategy`, `gates_round1` |
| `power_precheck` (§10.1) | Planning, development years | H-A, H-Z | Empirical only | SE_ho, minimum detectable effects, equivalence power per card | development runs of `gates_round1`, `z_factorial` |
| `null_pipeline` (§10.2) | **Mandatory check before the hold-out** | H-A, H-Z | Empirical only | Per-test and family-wise false-rejection rates in the null worlds; pass / fail | development runs; frozen algorithm |
| `robustness` | Exploratory | H-A, H-Z, H-T | Lemma 3 (convention sensitivity); Theorem 1 / Cor. 1.1 across H and δ; Cor. 1.3 (conditional) | Tables of §11 | `gates_round1`, `z_factorial` |
| `mechanism_sidetrack` | **ON HOLD — pending lead / user decision** | H-M | Empirical only (Worksheet 5 is not a result) | Nothing is run | lead / user decision |
| `gates_round2` | Postponed | H-A extended | Empirical only | Extended baseline table | user approval; extra packages |
| `holdout_final` | Confirmatory (C1–C4); descriptive otherwise | H-A, H-Z, H-T | As in the rows above | One run of the frozen code on 2022-01 to 2026-06 | Freeze recorded in `STATUS.md`; **R1–R4, `synth_validation` and `null_pipeline` passed; `power_precheck` reported** |

**Parallelism.** `synth_validation` and `common` are independent of the data work. After `base_strategy`: `gates_round1`, `z_factorial`, and the G0 parts of `monitoring_real` and `dependence_diag` can be run by separate instances writing to their own directories. `power_precheck` and `null_pipeline` follow the development runs; `holdout_final` is last and single-instance.

### 12.1 Synthetic validation protocol (rewritten as an executable protocol: P9)

The existing scripts in `theory/checks/` already test any-time violation over whole paths and outcome-dependent revelation times; they do not have adaptive selection, variable n_t, binomial uncertainty statements or valid comparators (lead's note in `plan_review_1.md`). This revision cannot change them (only this file); `synth_validation` is the paper-grade version and the lead may ask the theory task to back-port the additions.

**Environments (each has an analytically known μ_t; all satisfy A1–A3 with the stated d; labels are generated once and frozen, d_label = d, so A2(b) holds by the simulator's construction; in a simulation F_t is the simulator's own filtration, so the synthetic-fill qualifier of §3.2 does not arise).**
| ID | Construction | Known target |
|---|---|---|
| E1 | Given F_t, labels of day t independent Bernoulli(p_t) | μ_t = n_t p_t |
| E2 | Same-day common shock: ξ_t | F_t ~ Beta with mean p_t and intraclass correlation ρ ∈ {0.2, 0.6, 1}; labels conditionally i.i.d. Bernoulli(ξ_t) | μ_t = n_t p_t |
| E3 | Block environment of Proposition 2 (all labels of a d-day block equal one Bernoulli(p) draw, unknown until the block ends), p ∈ {0.3, 0.5} | μ_t = n_t p |
| E4 | Overlapping horizons: L_{ti} = 1{Σ_{s=t}^{t+H−1} ε_s + η_{ti} < θ_t}, ε_s i.i.d. N(0, σ_m²) market shocks disclosed day by day, η_{ti} i.i.d. N(0, σ_η²), θ_t F_t-measurable; σ_η = 0 gives identical same-day labels and strong cross-day dependence | μ_t = n_t Φ(θ_t / sqrt(H σ_m² + σ_η²)) |
| E5 | All-loss and all-win environments | μ_t = n_t, 0 |
| E6 | (Cor. 1.3, `草稿`; conditional on review) E4 plus a day-level "stuck" event of F_t-measurable probability π_t; stuck positions are unsold at the deadline and have L^liq = 1, others have L^liq = the E4 label and are sold before the deadline at an outcome-dependent time. **Added in v0.4 (certified labels, I-§6.4): each sold entry's record is independently "not certified" with probability 0.05 (PLACEHOLDER), giving L^lo = 0, L^hi = 1 while L^liq is unchanged. The withdrawn "missing ⇒ loss" fallback is not used for bracket labels anywhere** | μ_t^{liq} = n_t [π_t + (1 − π_t) q_t], q_t the E4 probability |

p_t, θ_t, π_t follow a two-state Markov regime or are chosen by the policy.

**Selection policies (all F_t-measurable; n_t ≤ M).** Π1 constant n_t; Π2 n_t uniform on {0,…,M}; Π3 history-adaptive (n_t = M after a favourable revealed lane outcome, 1 otherwise; regime of p_t chosen from revealed outcomes); Π4 range-adversarial (n_t = M whenever the policy's own running deviation Σ(μ − X) over revealed days is in the top decile of its past values, else 1); Π5 zero-entry stretches of geometric length after revealed loss clusters; Π6 permanent stop at the first time the running interval excludes a pre-set reference value.

**Revelation patterns (all within the lag bound).** Rv1 every label at lag d; Rv2 wins as soon as determined, losses withheld to lag d; Rv3 the reverse.

**Grid.** d ∈ {2, 6, 11, 21}; M ∈ {1, 30}; horizon T_max ∈ {250, 1,090, 2,305}; δ ∈ {0.05, 0.10}. A list of at most 60 configurations (environment × policy × revelation × d × M × T_max), written to a file committed before the first run; it must include E3 and E4 with σ_η = 0 at every d, and Π4, Π5, Π6 at the primary (d, M).

**Replications.** R = 10,000 per configuration for T_max ≤ 1,090 and 2,000 for T_max = 2,305 (PLACEHOLDER), seeds fixed. Monte-Carlo standard error of a failure frequency at the nominal level: 0.003 (R = 10,000, δ = 0.10), 0.007 (R = 2,000).

**What is measured, per replication.** The indicator that **at any T ≤ T_max with N_T > 0** the target lies outside the interval — separately for form (a), form (b), the upper bound alone and the lower bound alone (each against δ/2), and for the Cor. 1.3 interval in E6; the first failure time; the Cor. 1.2 bracket (must hold on every path); width paths.

**Reported.** Failure frequency with an exact (Clopper–Pearson) 95% interval per configuration; the §9.4 table; realised width against Cor. 1.1(a) and, where A5 holds, (b).

**Decision rule.** A configuration is **flagged** if the lower end of its exact 99.9% interval (PLACEHOLDER; an allowance for looking at up to 60 configurations and several interval forms) lies above the nominal level. A frequency above nominal but within Monte-Carlo error is not a failure. A flag triggers, in order: code review, an independent re-implementation of the interval, and — if it persists — escalation to the lead as a high-priority theory issue. Frequencies far below nominal are reported as conservativeness.

**Comparators.**
- *Cmp-V1 (valid at a fixed time under A1–A3):* lane-wise Azuma–Hoeffding bound with the deterministic range M at one pre-specified T*, radius Σ_j M sqrt(m_j log(2d/δ)/2) with m_j the number of lane-j days up to T*. Its validity follows from the conditional Hoeffding lemma of proofs §1.2 (part of the proof of Theorem 1; status: header) with a constant range; it is checked for coverage at T* only. It shows what time-uniformity and the predictable range clock cost or gain.
- *Cmp-V2 (time-uniform; validity to be confirmed):* lane-wise normal-mixture boundary on the same range clock (method of mixtures; Howard et al., arXiv:1810.08240). **Not a result of theorems.md; the boundary formula is to be taken from the source after literature-scout has verified it, and the theory task must confirm that it applies to our lane martingales before the comparator is labelled valid.** Until then it is labelled "candidate".
- *Cmp-N (not valid under A1–A3; shown as such):* matured-only rate with a Wald interval; day-clustered Wald interval.

**Proposition 2.** In E3 the realised width of our interval is plotted against sqrt(Md/N) and the variance identity is checked. This **illustrates the construction; a simulation cannot establish a lower bound over all procedures.**

**Lemma 3 and accounting.** Constructed price panels with the stress cases R4 of §3.9; a planted exposure-timing rule and a planted within-batch selection rule; expected: R1–R4 pass, the planted timing rule has θ_sel statistically indistinguishable from zero and the planted selection rule does not (frequencies over 1,000 panels with binomial intervals).

**Cost (ESTIMATE):** several CPU-hours; run in the background.

---

## 13. Pilot (first step after Gate 2)

**Purpose:** test the pipeline and the accounting and measure what the full plan needs; not evidence for or against any hypothesis.

**Scope.** CSI 300 point-in-time constituents; 2012–2019 (inside the development segment; the hold-out is not touched); H = 5, K = 20; LightGBM with default hyper-parameters, no search; seeds {0, 1, 2}; methods G0, SCORE, CONF, LOSS(−Z), LOSS(+Z_H), LOSS(+Z_O), E-const-dev, VT at c = 0.5; Z_H: CGO (N = 250) and chip profit ratio; Z_O: whichever classes have passed OA1–OA3 by then.

**Success criteria (correctness and feasibility only).**
1. Audit items needed for this subset pass, or fallbacks are in place.
2. Reconciliation R1–R4 (§3.9) pass on the pilot panel.
3. Truncation tests pass (no feature, order quantity, gate decision or monitored quantity changes when future data are removed).
4. Planted-effect test on real prices: a synthetic gate with look-ahead selection gives θ_sel clearly different from zero; a synthetic rule that only scales exposure at random gives θ_sel = 0 exactly (it submits all or none) and a composition term whose size is reported.
5. Measured: synthetic fill rates by method and reason ((S1), (S2), (S3)) under SF, SF-strict and SF-loose; entries per O1 branch and counts of outcomes U and M (A24); realised invested fraction against the arithmetic of §3.7; share of days with S_t ∈ {0, K}; frequency of non-filled exits; share with O1 ≠ O2; share unsold at deadline D and share of uncertified records; Z_O event frequencies; realised Theorem 1 half-widths against §9.4; run times and fit times (input to the cost estimate of §10.2); bootstrap standard errors (rough input to §10.1).

**Stop / rework.** Any unfixable failure of 1–4 ⇒ stop and report. Fallback F2 / F3 needed, or estimated full-run cost beyond the local machine ⇒ ask the user. **Outcome-based results are not stop criteria** ("no detectable Z effect in the pilot", "gates do not differ from G0"). Pilot outcome numbers are not used to choose the confirmatory specification except through the feasibility items above; any change prompted by the pilot is logged.

**Disclosure:** the pilot period lies in the development segment; the paper states that pilot data were seen first.

---

## 14. Compute and dependencies

### 14.1 Local machine (Windows 11, Python 3.14, CPU)
Round 1 needs no GPU. **No GPU or cloud compute is requested.** `akshare` 1.20.63 installed on 3.14 in `experiments/.venv` (feasibility probe). Compatibility of `baostock` and `lightgbm` with 3.14 is UNVERIFIED; a separate Python 3.12 is outside the 2026-11-15 approval and needs a user decision.

### 14.2 Dependencies (approval status per `resources/DOWNLOAD_LIST.md`; nothing was downloaded or installed for this revision)

| Item | Needed for | Hard? |
|---|---|---|
| `akshare` (pip; installed) | Primary data source, all Z_O data | **Hard** |
| `baostock` (pip) | Cross-check for the audit; fallback F1 | **Hard for the audit as designed** |
| `pandas`, `pyarrow`, `scipy`, `scikit-learn`, `matplotlib`, `lightgbm` (pip) | Everything; base model and gates | **Hard** |
| `hf-dataset:ellendan/a-share-prices` | External reference for limit prices / turnover (A7, A10) | **Soft**; provenance UNVERIFIED; without it, cross-checks (i)–(v) of §2.1 |
| `github:microsoft/qlib`, `github:myhhub/stock` (read only) | Alpha158 definitions; chip-distribution reference | Soft |
| `github:chenditc/investment_data` release asset; `hf-dataset:joshuaxql/qlib_data` | — | **Not a dependency (Tushare-derived). Optional cross-check only if the user separately confirms (U32)** |
| `mapie`, `stable-baselines3`, selective-prediction repos | Round 2 only | Not needed for round 1 |
| `tushare`, `pyqlib`, `alphalens-reloaded`, `open_spiel`, `rlcard` | — | Not used |

No third-party code is run: round-1 methods are re-implemented; repositories are read-only references. Bulk market-data pulls through `akshare` / `baostock` follow the budget of §2.5, which the user is asked to confirm.

### 14.3 Run-time estimates (**ESTIMATES; nothing measured**)
| Step | Estimate | Basis |
|---|---|---|
| Base data pull, two sources | 2–5 days wall time at the rate limits of §2.5 | 10,000–19,000 requests at >= 1.5 s plus retries and daily caps |
| Z_O pull (three classes, two passes 30 days apart) | under one day each pass | about 800 calls + 295 pages per pass |
| Features B0, R, Z_H, Z_O | 1–4 hours | Chip recursion and binned history are the slowest |
| `base_strategy` (30 trials × 5 seeds × 2 tuning years, then 14 annual refits × 5 seeds × 3 feature sets) | 10–50 CPU-hours | 1–10 minutes per fit, unmeasured |
| `gates_round1`, `z_factorial` | 5–30 hours each | Many small fits; bootstrap |
| `null_pipeline` | 100–400 CPU-hours (the largest item) | §10.2 |
| `synth_validation` | several CPU-hours | §12.1 |
| `robustness` | 10–40 hours | Refits only for H and Z variants |
| `monitoring_real`, `dependence_diag`, `power_precheck` | minutes each | Stored ledgers |
| `pilot` | 2–6 hours after data are available | Reduced scope |

Anything expected to exceed 10 minutes runs in the background with logs in `experiments/results/<name>/logs/`. If measured costs exceed the local machine, the user is asked; any reduction of budgets applies to all methods equally.

---

## 15. Threats to validity, and how outcomes will be described

### 15.1 Threats
- **Data quality.** Free scraped sources; possible survivorship bias, wrong adjustment factors, back-filled fields, upstream revisions; the two feeds may share upstreams (A17). Aggregate agreement rates can hide errors concentrated in distress events; hence A14–A16.
- **Z_O data.** Single free upstream for two classes; values checked only on small hand samples; the share-change table is back-filled and its announcement dates cannot be verified at scale; disclosure-timing rules not yet checked against exchange originals; listing criteria changed over time (UNVERIFIED); events are sparse and concentrated in extreme price–volume days.
- **Execution realism — retrospective synthetic fills.** Daily bars carry no auction timestamps: whether the opening auction matched, the auction volume and intraday suspensions are not observable, so every fill is a synthetic fill under SF and the declared filtration F_t^syn is artificial (it contains facts that on no-match days became known only later that day). All backtest results, and the monitoring results in particular, hold "under the synthetic execution model"; they are not results about an executable strategy. The distance between synthetic and real auction fills cannot be estimated from daily bars (it would need auction data, U35); the SF-strict / SF-loose sensitivity does not measure it. Whole fills, the capacity cap, the constant shortfall, the order-policy defaults of §3.7 and the clock times of U37 are placeholders; limit orders at the limit-up price with pre-determined quantities leave part of each slot uninvested.
- **Operational assumptions behind the theory's assumptions are unaudited.** A1 (with F_t^syn), A1-G, A2(b), A3 (OA-next), A4 / A5 hold for our stream only if the audit items A11, A18, A21–A24 pass; with one downloaded file, point-in-time availability can be checked only as a function of that file. The 13 rule items RV1–RV13 are unverified until the audit archives the official texts.
- **Labels partly set by convention.** Outcomes U and M and the rights-issue rule record data problems as losses (conservative conventions); their frequency is unknown until the pilot. The withholding rate on distributions is a fixed placeholder, not the holding-period-dependent tax.
- **Costs.** Commission and slippage are unverified placeholders.
- **Single history / low power.** About 1,090 hold-out days; intervals may be too wide for either a difference or equivalence, most of all for the sparse Z_O group.
- **Non-stationarity and rule changes** (stamp duty 2023, ChiNext limits 2020, registration reform 2023, disclosure-rule changes); the block bootstrap does not model them.
- **Researcher degrees of freedom.** Many design choices; one primary specification, frozen placeholders, everything else exploratory. The estimand of the confirmatory tests was changed between v0.2 and v0.3 in response to review, before any data were seen; this is disclosed.
- **Thin tuning data.** Hyper-parameters are chosen once on two validation years; the choice is noisy. It is the same for all methods.
- **Attribution depends on conventions** (interval split, interaction ordering, zero-exposure weights, reference costing, delisting value).
- **"Aggregate composition" is not selection, and θ_sel is not all of selection:** stratification controls only liquidity and volatility terciles; sector and other tilts within strata remain in θ_sel.
- **Selection by tradability.** Entries are fills; executed-trade statistics describe the gate composed with the fill mechanism.
- **Controls for Z are summaries.** A Z contrast is incremental to R as defined, not to every function of the raw history.
- **Label and theory mismatch.** Theorem 1 is applied to O1 (a valuation at the scheduled exit, not a sale); O1 = O2 only for entries whose scheduled sale is recorded as filled at the valuation price; the only bridge to O2 otherwise is Corollary 1.3, a draft on which the two external reviewers disagreed.
- **Monitoring interval is wide** (§9.4) and is not evidence for or against any gate.
- **Theory status.** Three external review rounds (GPT, semi-independent; Gemini Flash) reported no error in Theorem 1, Corollaries 1.1–1.2, Proposition 2 or the identity of Lemma 3, but the revisions made after round 3 were not re-reviewed, so none may be called a theorem in the paper yet; Corollary 1.3 is a draft; the A-share instantiation was never reviewed in its present form; Theorem 1 is, per the internal audit, essentially a corollary of known results; novelty was assessed by no reviewer.
- **Null simulation scope.** Base stage held fixed; W-perm weakens temporal dependence; a pass is absence of detected excess, not proof of nominal error rates.
- **Implementation risk.** Own backtester and re-implementations. Mitigation: independent ledger, reconciliation, truncation and planted-effect tests, code release.
- **Generalisation.** One market, one frequency, long-only, one family of base signals.

### 15.2 How each possible outcome will be described (wording fixed in advance; corrected: P10)
- **Q-total:** estimates of ΔAR against G0, E-const-dev, SCORE, VT with intervals; described as measured. No confirmatory verdict.
- **H-A (C1, C2):** "economically negligible within ±Δ_ord" only if the equivalence null is rejected after Holm. If the adjusted interval lies entirely outside the bound, H-A is contradicted for that gate and this is reported as a finding against our own hypothesis. Otherwise: "inconclusive".
- **H-Z (C3, C4):** "a difference was detected" (with its estimated sign) only if the difference null is rejected after Holm. Otherwise: **"no detectable difference; inconclusive"**. The sentence "Z adds nothing" (or equivalent) is not used on the basis of a failure to reject; a statement of negligible incremental value would require an equivalence test, which is not in the confirmatory family and would be exploratory.
- **Monitoring (H-T):** the width limitation is known from the formulas and stated whatever the data show. On simulated streams, a flagged configuration (§12.1 rule) is escalated; a frequency within Monte-Carlo error of nominal is not. **On market data every sentence has the form "for the synthetic fill stream under SF (filtration F_t^syn), the interval for the entry-time conditional loss-probability average of the O1 label was …"**; the words "the strategy's loss probability", "executable", "at the opening-auction match" and "risk control" are not used; the counts of labels set by U / M and the outcome of audit items A18, A21–A24 are printed with the interval. If the fill-determination sensitivity (§3.2) changes a reported conclusion, that is stated in the same paragraph.
- **All market-data results (Q-total, H-A, H-Z):** described as backtest results under the synthetic execution model, with the SF-strict / SF-loose comparison beside the primary numbers.
- **H-M:** on hold.
- Unfavourable or anomalous results, failed runs and every deviation from this plan go into `experiments/RESULTS.md`.

---

## 16. Open questions (Gate 2)

### 16.1 For the user
1. **Z_O (§5.6):** confirm the group as proposed — Dragon–Tiger summary and institutional-seat statistics, block trades, executed share changes; free data only — and its exclusions (northbound, margin, shareholder counts). Events are sparse, so the Z_O test may be the least powerful of the four.
2. **Lead's decisions the user may veto:** O1 by the decision tree at the scheduled exit instant (U26); d_label = d = H + 1 fixed in advance (U25); benchmark-price accounting (§3.6).
2a. **Auction data (new, U35):** obtain timestamped opening-auction data (not free) so that fills are executable in the sense of I-§2.3, or — default — keep daily bars with retrospective synthetic fills and word every result accordingly?
2b. **Order-and-fill policy defaults (new, U36–U44):** information cut-off and submission time, order types and limit prices, treatment of unfilled remainders and lots, capacity cap, withholding rate, same-security lots, fallback conventions, and what to do if the `open` field fails A12. All are placeholders chosen so that the backtest is implementable.
3. **Fetch budget and rate limits (§2.5, U24)**, including whether approving `akshare` / `baostock` covers pulls of this size.
4. **Execution design (U27):** H + 1 pre-funded sleeves and pre-determined limit orders leave roughly a quarter of capital uninvested in the ungated strategy (arithmetic estimate). Accept, or supply evidence on same-auction funding so that the H-sleeve design can be primary?
5. **If the base-data audit fails** (delisted stocks, point-in-time constituents): restrict the claim (F2) or obtain licensed base data (F3)? (This is the base-price data question of `research_question.md`, separate from the Z_O decision already taken.)
6. **Parameters of §17**, in particular commission, slippage, Δ_ord and its rule, H, K, the period split including tuning years, c, tuning budget and criterion.
7. **Cost of the mandatory checks:** `null_pipeline` is estimated at 100–400 CPU-hours. Accept, or reduce B_null to 200 (weaker check)?
8. **Role of the monitoring result** (appendix-level "limits of evidence"); **mechanism side-track** (on hold); **round 2** (wanted at all?).
9. **Separate Python 3.12** if `baostock` or `lightgbm` fails on 3.14.
10. **Acceptance of possible outcomes:** every confirmatory test can end "inconclusive", and `power_precheck` may show this before the hold-out is opened.

### 16.2 For the lead / theory task
1. The two-interval, wealth-normalised application of Lemma 3 (§3.9, §8.2), the cohort-level form and the level / timing split are plan-level uses of the lemma; if they are to appear in the paper as identities they should be added to theorems.md and reviewed.
2. Zero-baseline-exposure convention (§8.2): fixed by the plan; confirm or replace before the freeze.
3. Comparator Cmp-V2 (§12.1) needs a verified source formula and a statement from the theory task that it applies.
4. Back-porting adaptive selection, variable n_t, binomial intervals and Cmp-V1 into `theory/checks/` (not done here: this revision may change only PLAN.md).
5. Rule originals to be archived before the freeze: the 13 items RV1–RV13 of §2.4 (the list of I-§9), disclosure timing of Dragon–Tiger, block-trade and share-change information (OA1), listing criteria of the Dragon–Tiger list by period.
6. Bibliography to be verified before citation: bootstrap references; Grinblatt & Han 2005; Liu–Stambaugh–Yuan 2019; Howard et al.; Azuma–Hoeffding source; the Z_O literature (currently abstract-level reading only).
7. This version (v0.4) has been reviewed by nobody. v0.2 was reviewed by GPT only; whether the ARS methodology review was run on v0.3 is not known to the author of this revision (`STATUS.md`: waiting for the user's confirmation of the reviewer configuration).
8. Open points of v0.4 for the theory task: (a) the two-interval scheme values holdings at closes as well as at opens, whereas I-§8.8 names the opening price as the benchmark — the plan reads "same benchmark price at each instant" as covering both instants; (b) the ledger's terminal-value convention for class-U events (U33) is the plan's, since I-§3 defines only the label; (c) the standard order of §8.3 is checked against the capacity cap at a notional slot size, deployed strategies at their actual order size; (d) the VWAP run and the per-submitted-order table are kept as descriptive items outside the theory — delete them if the lead prefers.

---

## 17. Parameters the user must confirm (all PLACEHOLDERS unless marked "decided by the lead"; none may be changed after any outcome is seen)

| # | Parameter | Placeholder | How to set it | Pre-specified sensitivity | Where |
|---|---|---|---|---|---|
| U1 | Commission per side | 2.5 bps | UNVERIFIED, broker-specific; user supplies | 1 / 2.5 / 5 bps | §3.6 |
| U2 | Slippage per side | 5 bps | UNVERIFIED, not estimated; user chooses | 0 / 5 / 10 / 20 bps | §3.6 |
| U3 | **Equivalence bound of the confirmatory tests C1, C2** | Δ_ord = ±5 bps per order (≈ ±1.0% per year of capital at c = 0.5, H = 5) | Rule (a) cost-anchored or (b) investor-anchored (§9.3); fixed before development results are examined | ±2.5 / ±10 bps (exploratory) | §8.4, §9.3 |
| U4 | Exploratory bounds | ΔAR ±1.0% per year; expected shortfall ±25 bps | As U3 | — | §9.3 |
| U5 | Holding period H | 5 trading days | User's horizon; the monitoring half-width grows with H (§9.4) | 1 / 5 / 10 / 20 | §3.3 |
| U6 | Names nominated per day K (= M) | 30 | Diversification versus slot size | 20 / 30 / 50 | §3.7 |
| U7 | Periods | Evaluation 2010-01 to 2026-06; base tuning years 2011–2012; gate tuning years 2015–2016; development evaluation 2017–2021; hold-out 2022-01 to 2026-06 | After the audit | Start 2012 if early data fail the audit (logged) | §2.2, §4.3 |
| U8 | Primary coverage c | 0.5 | Tolerance for idle capital | 0.3 / 0.5 / 0.7 | §6.1 |
| U9 | Tuning budget; seeds | T = 30 configurations per learned method; seeds {0,…,4} | Compute; reductions apply to all methods | Budget sensitivity T in {10, 30, 60} (U34) | §6.3 |
| U10 | Tuning criterion | θ_sel at target coverage (within-batch methods); AR (all-or-nothing / scaling methods); mean over tuning years and seeds | One rule for all; frozen at Gate 2 | — | §6.3 |
| U11 | Listing-age filter | 60 trading days | Convention | 20 / 60 / 120 | §2.3 |
| U12 | Refill rule cap | 3 slots per name | Concentration tolerance | — | §3.7 |
| U13 | RND repetitions; bootstrap resamples; mean block length | 200; 10,000; 4(H+1) days | Monte-Carlo error versus time | Blocks 2(H+1), 8(H+1) | §6.1, §10 |
| U14 | Strata of the matched-opportunity comparison | Liquidity tercile × volatility tercile of the nominated list | Fixed before results | Unstratified (exploratory) | §8.3 |
| U15 | Monitoring level δ | 0.10 two-sided | Convention | 0.05 | §9.2 |
| U16 | Deadline D (Cor. 1.3; conditional on review) | H + 10; d_D = D + 1 | Fewer stuck entries versus larger lag | H, H+5, H+10, H+20 | §3.8 |
| U17 | *(withdrawn)* pilot threshold for coarsening strata | — | Not needed: the exact stratified expectation requires no coarsening (§8.3) | — | — |
| U18 | Minimum prior power before consulting the user | 50% for most of the family | Convention | — | §10.1 |
| U19 | Notional capital for participation / lot reports | 10 million yuan | User's account size | 1 / 10 / 100 million | §9.2 |
| U20 | Refit frequency; cash return | Annual; 0 | Compute; money-market series UNVERIFIED | Money-market rate | §4.3, §3.7 |
| U21 | Execution conventions | Opening auction only; synthetic fill rule SF; non-filled buys cancelled; cash rule primary; ST excluded from new entries; names suspended on t−1 not candidates on t | Realism; rule calendar re-checked against originals first (RV1–RV13) | §11 | §3 |
| U22 | **Z_O group (pending user confirmation)** | Classes LHB, BLK, INS from free AKShare data; a class enters only if it passes OA1–OA5 | User's view of the research direction; audit | Each class alone | §5.6 |
| U23 | Z_O availability lag and look-backs | s+1 if the rule original is archived for the whole period, else s+2 (always s+2 for INS); look-backs {1, 5, 20} days | Fixed at the audit, before modelling | The other lag | §5.6.2–3 |
| U24 | **Fetch budget and rate limits** | §2.5: about 10,000–19,000 base requests, about 2,500–3,500 for Z_O including the second pass; >= 1.5 s spacing; 3 retries; 3,000 requests per host per day | User's tolerance for load on free upstreams and for wall time | — | §2.5 |
| U25 | **Label-finalisation lag and monitoring lag — decided by the lead; the user may veto** | d_label = H + 1 (labels frozen from the snapshot of entry day + H + 1, never recomputed) and d = H + 1 (valid if OA-next holds, audit item A18); neither is changed after data are seen | Fixed in advance by the label's information needs (I-§4). A lag of H would need a different label and timestamped auction data; not offered | none (neither lag is varied) | §3.3, §9.4 |
| U26 | **O1 definition — decided by the lead / theory task (`instantiation_ashare.md` §3); the user may veto** | Decision tree at the opening auction of day t+H: events S-a–S-e, price rule P1–P4, validation; **fallbacks U ⇒ loss, M ⇒ loss, rights not subscribed and valued at zero (conservative conventions, U43)** | — | none on the label; counts of U / M reported (the close-marked variant O1-close no longer exists) | §3.8 |
| U27 | Funding and order sizing | H + 1 pre-funded sleeves; limit orders at limit-up with quantity fixed pre-auction | Evidence on same-auction funding and on actual order types | H sleeves; notional-at-open | §3.7 |
| U28 | Gate training population; history-control bins | Top-3K names; 10 bins per window | Sample size versus relevance; resolution | — | §4.3, §5.4 |
| U29 | Null simulation | B_null = 400 per world; 2,000 bootstrap resamples inside; pass: at most 27 replications with a false rejection | Compute (100–400 CPU-hours, ESTIMATE) | B_null = 200 with limit 15 if compute forces it | §10.2 |
| U30 | Synthetic validation | R = 10,000 (2,000 at the longest horizon); at most 60 configurations; flag rule with exact 99.9% intervals | Monte-Carlo precision versus time | — | §12.1 |
| U31 | Margin-trading negative control | **Default: not run** (researcher's judgement, §5.6.4) | User may request it as an exploratory appendix item (about 8,000 requests) | — | §5.6.4 |
| U32 | Tushare-derived cross-check datasets | **Default: not used** (`joshuaxql/qlib_data`, `chenditc/investment_data` release asset) | Only if the user separately confirms that redistributed Tushare-derived files are acceptable for cross-checking | — | §2.1 |
| U33 | Accounting tolerances; ledger terminal value | R2: 1e-6 of wealth per day, 1e-4 of W_0 cumulated; in the ledger, positions hit by a delisting or class-U event valued 0 afterwards (conservative convention) | Precision of reconstructed returns (audit); evidence on recoveries | Last traded price | §3.9 |
| U34 | Tuning-budget sensitivity | T in {10, 30, 60}; NET-U also 2T; development years only | Compute | — | §6.3 |
| U35 | **Timestamped opening-auction data (new in v0.4; user decision)** | **Default: not obtained.** The backtest uses daily bars with retrospective synthetic fills (SF, F_t^syn); every monitoring result is worded "under the synthetic execution model" | Such data are not free (source, price and coverage UNVERIFIED; nothing was searched for this revision). With them, fills could be defined by EM with F_t = information up to the auction match (I-§2.3), or at least the SF-versus-real gap could be measured on a sample | — (if obtained: a logged change of §3.1–3.2 before any outcome is seen) | §3.1–3.2 |
| U36 | Fill-determination sensitivity thresholds (new) | SF-strict: no fill if the open is above reference price × (1 + 0.8 × limit band) (mirrored for sells), cap one tenth of U40; SF-loose: (S1) only | Convention; how conservative the user wants the strict variant | — | §3.2, §11 |
| U37 | Information cut-off and order-submission time (new; placeholder pending RV1) | Data dated ≤ t−1 plus pre-open public information; nominal cut-off 09:00, submission 09:15 exchange time. **Clock times UNVERIFIED** | Official auction timetable (RV1); the user's actual workflow | — | §3.1, §3.7 |
| U38 | Order types and limit prices (new; placeholder) | Buy: limit order at the day's upper limit; sell: limit order at the day's lower limit, whole remaining lot; opening call auction only; one buy order per name per day | The order types a realistic account would use | — (does not change simulated fills under SF except through sizing) | §3.7 |
| U39 | Unfilled remainders, partial fills, lots (new; placeholder) | Remainder cancelled at the end of the auction, not left in the continuous session; no partial fills under SF; fractional shares, with a 100-share lot-rounding robustness run | RV1, RV2, RV12; fill-level data would need the I-§6.3 inputs fixed in writing | Lot rounding at W_0 = 1 / 10 / 100 million | §3.7 |
| U40 | Capacity cap of (S3) (new; placeholder) | Order value ≤ 1% of the 20-day average daily traded amount through t−1, at notional capital U19 | Account size; tolerance for market-impact risk. UNVERIFIED as a description of auction liquidity (auction volume is not in daily bars) | No cap; 0.1% | §3.2, §3.7 |
| U41 | Withholding rate on cash distributions (new; placeholder) | 20%, fixed, not holding-period dependent. **UNVERIFIED (written from memory; RV10)** | Official dividend-tax rule; the user's tax situation | 0% / 10% | §3.6, §3.8 |
| U42 | Same-security lots (new; placeholder) | Each entry its own lot (entry day, name, sleeve); re-entry into a held name allowed; same-day buy and sell not netted; several lots due on one day: all-or-nothing on the total, proceeds pro rata to shares; FIFO by entry day if fill-level data are ever used | I-§6.1, I-§6.3; the user may prefer to forbid re-entry | Re-entry forbidden (exploratory) | §3.7 |
| U43 | Fallback conventions of the labels (copied from `instantiation_ashare.md`; conservative conventions, not facts) | O1: unsupported event (U) ⇒ label 1; missing input (M) ⇒ label 1; rights not subscribed, valued at zero. O2: never fully liquidated or class-U event ⇒ label 1. Deadline labels: uncertified record ⇒ lower label 0, upper label 1 | The user may veto; a change alters the estimand and must go back to the theory task | none on the labels; counts reported | §3.8 |
| U44 | If the `open` field fails audit item A12 (new) | **Default: stop and ask.** No fallback entry rule is specified (v0.3's "VWAP becomes primary" is withdrawn because VWAP entries are outside the instantiation) | Options at that point: licensed or auction data (U35 / F3); restrict the universe or period (F2); drop the market-data monitoring analysis | — | §3.2, A12 |

Not in this table by the user's decision (relayed by the lead, 2026-11-15): obtaining unlock-schedule or pre-disclosure data through a university database — out of scope for this paper (§5.6.4).

---

## Appendix: sources consulted for trading rules (opened 2026-11-15; all are news reports, no exchange or ministry original text was opened)
- Stamp duty halved from 2023-08-28: https://www.news.cn/2023-08/28/c_1212260850.htm ; https://www.cls.cn/detail/1445329
- Transfer fee 0.001% both sides from 2022-04-29: https://www.yicai.com/news/101396958.html ; https://m.cls.cn/detail/1001120
- Main-board limits and first-5-day rule under the 2023 registration reform: https://wallstreetcn.com/articles/3680934
- Main-board ST limit 5% -> 10% effective 2026-07-06: https://www.news.cn/fortune/20260706/21958d63bab64ce180cc97d1a6af6b50/c.html
- These were read through search-result summaries, not the full pages; before the conventions are frozen, the rule calendar must be re-checked against SSE / SZSE / CSDC / MoF originals. No instructions addressed to automated agents were encountered.
- **Added in v0.4:** again no rule original was opened and no web page was read. The 13 rule items of `instantiation_ashare.md` §9 are now audit items RV1–RV13 (§2.4); the sources named there are the official sites to consult, with document titles written from general knowledge (UNVERIFIED).
- **Added in v0.3:** no rule original was opened for this revision either. Disclosure-timing statements for Dragon–Tiger, block-trade, margin and share-change data in `literature/opponent_action_variables.md` §3 and `experiments/data_feasibility_opponent_actions.md` are marked by their authors as not verified against originals (with the exceptions those files list); this plan does not rely on them and makes their verification audit item OA1.

---

## Revision log (v0.3 → v0.4, 2026-11-15, researcher) — synchronisation with the final theory setting

Only this file was changed. Nothing was run on data, fitted, downloaded or installed; no web page or rule text was opened. Inputs: `theory/setup.md` (abstract, final), `theory/instantiation_ashare.md` (§8 checklist, §9 open items), the status table of `theory/theorems.md`, `reviews/proof_check_3.md` §2(i) and §4, `STATUS.md`. **No experiment was redesigned:** the experiment list, estimands, test cards C1–C4, the Holm family, baselines, tuning rules, periods and budgets are as in v0.3. What changed is the execution / label / accounting layer under them, the wording of what the monitoring results are about, the audit list, and §17.

| # | Where | What was done | Reason; reservations |
|---|---|---|---|
| **T1** (X1) | Header (standing qualifier), §1 item 3 and non-goals, §3.1, §3.2, §3.4, §8.3, §8.4, §9.2, §9.4, §11 (new row), §12 (`monitoring_real`), §13, §15.1, §15.2, §17 U35 / U36 / U44, A12 | Backtest fills are named **retrospective synthetic fills** under rule **SF** (S1)–(S3), copied from I-§2.4; SF reads only the traded flag, suspension flag and open of the day-t bar. Declared filtration F_t^syn, stated to be artificial. Consequence (i): every monitoring result on market data is about the synthetic fill stream, with binding wording and a list of phrases that may not be used. Consequence (ii): limit-up / no-match handling is an approximation; a pre-specified sensitivity SF-strict versus SF-loose with a pre-fixed reading. New user decision U35 (timestamped auction data; default: not obtained) | Daily bars have no auction timestamps, so an entry indicator built from "traded and open not at the limit" is not measurable at the auction match. **Reservations:** the thresholds of SF-strict (80% of the band, one tenth of the cap) are my placeholders — the instantiation asks only for "sensitivity to the limit and capacity conditions". The sensitivity cannot measure the gap between synthetic and real fills (said in the text). It is applied to frozen orders without refitting the gates, to keep it a fill-layer comparison |
| **T2** (X2) | §3.1 (G_t, F_t^syn, item-by-item confirmation), §3.5, §3.7, §8.3 | G_t (names, quantities, order type, limit price, cap) separated from F_t^syn. All gates, baselines, random comparators, thresholds, strata and order quantities were checked against G_t; the list is in §3.1 | **One real change:** v0.3 removed names "suspended on day t" from C_t, which is not G_t-measurable without announcement timestamps. Now only names suspended on t−1 are removed; an order for a name suspended on t is recorded as not filled. Side effect (stated): a name is not a candidate on its resumption day. E-const-expost, E-sched and the hindsight diagnostic use later information and remain labelled as references / diagnostics, not strategies |
| **T3** (X3) | §3.3, §3.8 (iii) "Snapshot", §3.8 (vi), §4.3 (definition of "matured"), A18, §9.4, §11 (holding-period and monitoring rows), U25 | d_label = H + 1: each label computed once from the snapshot of entry day + d_label, stored, never recomputed. Monitoring lag d = H + 1, deterministic, fixed in advance. Searched the whole text for any "recompute labels with another d": **none remains.** Deleted: the "d = H under OA-open" argument (§3.3), the information row "d = H = 5" and its remark (§9.4), and "valid under OA-open and OA-next" (U25) | I-§4: O1 needs facts known only at the close of t+H, so it does not support lag H, and "no statement in this project should say that O1 has lag H". Varying H in the robustness table is kept: each H has its own entries and its own frozen labels, with d_label = d = H + 1 |
| **T4** | §3.6 (six numbered rules), §3.9 (intervals, terminal cases, R4), §8.2, §9.1 (P4) | Benchmark-price accounting: same price for all strategies at each instant; fees and modelled shortfall only through the cost term, each once; traded amount = change in corporate-action-adjusted share count × benchmark price (replaces v0.3's "× execution price"); cash distributions in the cash ledger, never a trade; costs debited at the trade; wealth recursion Π + Σ_t ρ_t (W_t − c_t) for a non-zero cash return. R4 gains: dividend with no trade and 2-for-1 split with no trade (traded amount and cost exactly 0), a "shortfall counted once" case, and the round-3 counterexample (100, cost 1, 10% ⇒ 108.9) | Lead decision of 2026-11-15; round-3 items K1, X11. **Reservations:** (a) I-§8.8 names "the opening price" as the benchmark; the two-interval scheme also values holdings at closes — read here as "same price at each instant" (§16.2 item 8a). (b) "W1–W4 hold by construction" of v0.3 replaced by "tested by R2–R4". (c) Returns are now rebuilt from unadjusted prices and events with net-of-withholding cash, so vendor adjusted series are a cross-check only |
| **T5** | §3.8 (iii), §3.9 terminal cases, A21–A24, §11 (labels row), U26, U43 | O1 is the decision tree of I-§3 (Step 1 S-a–S-e / U and listing status; Step 2 P1–P4; Step 3 validation with override M), share-and-cash tracking; distributions by entitlement (holder at the close of the record date, any payment date, fixed withholding), identical for O1, O2, deadline labels and the ledger. Fallbacks copied and labelled conservative conventions: U ⇒ loss, M ⇒ loss, rights not subscribed and valued at zero. Branch / U / M counts reported | I-§3, I-§5, I-§8.5, I-§8.9. **Reservations:** the tree governs the *label*; for the *ledger* I kept v0.3's terminal value 0 after a delisting and extended it to class-U events (plan's convention, U33). With daily bars P2 and P3 are merged, admissible only if RV3 confirms the published open equals the auction price on matched days. v0.3 ignored dividend tax; a fixed withholding rate is now required — 20% is a placeholder written from memory (U41, RV10) |
| **T6** | §3.7 (order-and-fill policy table), §17 U37–U42, U44 | Every item listed as an external input in I-§6.3 / I-§9 has a default, marked PLACEHOLDER pending user confirmation: buy limit at the upper limit, sell limit at the lower limit for the whole lot; cut-off 09:00 / submission 09:15 (UNVERIFIED clock times, RV1); remainder cancelled after the auction; no partial fills under SF (FIFO and pro-rata rules of I-§6.3 recorded for fill-level data); fractional shares with a lot-rounding robustness run; capacity cap 1% of the 20-day average traded amount at the notional capital; each entry its own lot, re-entry allowed, no netting, same-day lots all-or-nothing on the total with pro-rata proceeds | Without values the backtest cannot be implemented. **Reservations:** all values are mine; under SF several do not change any simulated number (I-§6.1). The cap makes fills depend on the notional capital (the only scale-dependent element); the standard order of §8.3 is checked at a notional slot size |
| **T7** (X9) | §3.8 (iii), §11, U26; also §3.2 (VWAP), §3.8 (ii) | **O1-close deleted** everywhere as a variant. Two further items that the instantiation lists as not covered were demoted rather than deleted: the VWAP entry run (now: Q-total / Q-select table only, no label of §3.8, no monitoring quantity, "not covered by any theory result") and the "submission-based alternative" (now a descriptive per-submitted-order table without any interval). v0.3's rule "VWAP becomes primary if A12 fails" is withdrawn (U44: stop and ask) | I-§7. I chose deletion for O1-close (the plan has no closing price rule to offer). The lead may prefer to delete the VWAP run and the per-order table as well (§16.2 item 8d) |
| **T8** | Header, §3.8 (v), §12 (three rows), §12.1 (E6, Cmp-V1), §15.1, §9.2 | Status text rewritten: three external rounds (GPT, semi-independent; Gemini Flash) reported no error in Theorem 1, Cor. 1.1, Cor. 1.2, Prop. 2, the Lemma 3 identity; revisions after round 3 not re-reviewed; nothing called a theorem or "proved"; Cor. 1.3 `草稿` with the reviewers' disagreement stated and every use "conditional on the result surviving review"; E6 updated to certified bracket labels | **Note:** the `theorems.md` table still carries the author's label `自查通过` for the reviewed items, while `STATUS.md` records "GPT 审过（半独立）、Gemini 审过（Flash）"; both are quoted in the header. A search of the plan found no occurrence of "theorem (proved)" or equivalent in v0.3 |
| **T9** | §2.4 (table RV1–RV13), §12 (`data_audit`), §16.2 item 5, Appendix | The 13 rule items of I-§9 are audit items with: where the rule is used, the official source to consult (SSE, SZSE, CSRC, CSDC, MoF / STA sites), and the handling if the text contradicts the convention or cannot be found. Added A21 (event-calendar completeness), A22 (meaning of the suspension flag), A23 (adjustment factor versus share-and-cash), A24 (frequency of U / M) from the "unresolved" list of I-§9 | **No official text was opened.** Document titles in the "source" column are from general knowledge and UNVERIFIED; finding the right document for each sub-period is part of each item |

**Consistency check against `setup.md` / `instantiation_ashare.md` (whole file re-read; old revision logs below were left as historical record and still contain superseded statements).**

*Conflicts found and removed in this revision:*
1. §3.1 (v0.3): "F_t = all public information up to and including the opening-auction match" — not supportable with daily bars → F_t^syn.
2. §3.2 / A12 (v0.3): VWAP as a "variant timeline" with lag statements citing "setup §3.3" (a section that no longer exists) and as fallback primary → outside the theory; U44.
3. §3.3, §9.4, U25 (v0.3): "d = H valid under OA-open" → deleted.
4. §3.5 (v0.3): C_t using the day-t suspension status → day t−1 status.
5. §3.6, §9.1 P4 (v0.3): "× execution price" → benchmark price; "dividend tax ignored" → fixed withholding rate.
6. §3.8 (v0.3): O1 described as "opening price, else carry-forward" → decision tree; "O1-close" → deleted; deadline labels without certification → certified labels, P_T → P_T^D; references to "setup §3.1–3.3" → I-§ references.
7. §3.8 (ii), §11 (v0.3): submission-based alternative presented as an option of setup §3.1 → descriptive table outside the theory.
8. §8.2 (v0.3): "W1–W4 hold by construction" → tested.
9. §12, §12.1, §15.1 (v0.3): "`自查通过`, re-review pending" → status per T8.
10. §3.8 (vi), §9.4 Cmp-N: matured-only rate — already labelled not covered; now also "not reported as an estimate of anything covered by the theory" (I-§8.10).

*Remaining points where the plan is not literally identical to the theory files, or where I am not sure (none could be resolved inside this file):*
- (a) Two-interval accounting uses close and open valuations; I-§8.8 speaks of the opening price only (§16.2 item 8a).
- (b) The overnight-return construction assumes the record date is the trading day before the ex-date; I-§5 defines entitlement by record date and marks the relation [rule: tbv] (RV9). If RV9 fails, §3.9's interval definition must be restated.
- (c) G_t in the plan is a subset of the G_t allowed by I-§2.1 (announced suspensions are not used because their timestamps are unverified). Not a conflict; it changes C_t relative to v0.3.
- (d) The ledger's value for class-U events is the plan's convention; I-§3 defines the label only.
- (e) LOSS / NET training uses labels and returns of *standard counterfactual orders* for the top-K_tr names (§4.3), most of which are never submitted. These are training targets, not executed entries, and enter no theory quantity; the instantiation does not discuss them.
- (f) The refill variant submits one order of up to three slots per name; consistent with "one order per name per day", but the capacity cap then binds more often — unmeasured.
- (g) I-§8.13 asks that the cost model applied to the reference's never-executed trades be fixed in advance: done in §8.2, not reviewed.
- (h) Statements about what `theorems.md` Lemma 3 defines as Π, ρ_t, W_t are quoted from its revision note and line 254–256 only; I did not re-read the whole lemma for this revision.
- (i) §2.2–2.3, §4–§7, §10 were re-read for conflicts with G_t / F_t^syn / d_label and edited only where listed above; their content was not re-verified.

**Monitoring half-width (§9.4): unchanged.** T1–T3 do not change d (= H + 1), M (= K = 30) or the assumed N (fill rate 1). The formulas were re-evaluated in a throwaway script (not in the repository) and reproduce all twelve cells of the table and the two side values (n_t = 15: 0.219 / 0.173; δ = 0.05: 0.228 / 0.180). The only edit is the deletion of the "d = H = 5" information row. Realised widths may differ through the capacity cap and the fill rate, which are unmeasured.

**§17:** U21, U25, U26, U33 reworded; new U35 (auction data; default not obtained), U36 (sensitivity thresholds), U37 (cut-off and submission time), U38 (order types and limit prices), U39 (remainders, partial fills, lots), U40 (capacity cap), U41 (withholding rate), U42 (same-security lots), U43 (label fallback conventions), U44 (A12 failure).

---

## Revision log (v0.2 → v0.3, 2026-11-15, researcher)

Only this file was changed. Nothing was run on data, fitted, downloaded or installed. The numbers in §9.4, §10.1 and §10.2 come from evaluating formulas in a throwaway script (assumed sample sizes, binomial and normal arithmetic; no data). "As requested" = done as `reviews/plan_review_1.md` / the lead's task asked. Deviations and reservations are in the last column and collected at the end.

**A. Review items P1–P12**

| # | Where | What was done | Deviation / reservation |
|---|---|---|---|
| P1 | §8.1–8.4, §6.1 (RND row), §10 | Three estimands separated (deployed outcome; additive attribution; within-batch selection). Q-select is now the per-order statistic θ_sel against the exact stratified-random expectation from the same nominated list ("matched order opportunities"; the phrase "matched exposure" is dropped). One card per confirmatory test (C1–C4) with formula, comparator, weighting, null, test statistic, labels. Aggregate composition demoted to a descriptive term named as such | The lead asked for the standardised fixed-yuan cohort comparison "in addition"; I made it **the** confirmatory statistic, because the aggregate composition term is exactly what the reviewer showed not to be Q-select. Consequence: the H-A bound is now per order (U3). θ_sel still contains tilts within strata (stated, §15.1) |
| P2 | §3.9, §8.2, A20 | Overnight / intraday intervals with auction trades between them; Lemma 3 applied per interval and summed; independent share ledger; acceptance criteria R1–R4 with tolerances; stress cases incl. same-stock entry / exit across strategies, dividends, splits, delisting, terminal holdings. PERF's "cohort composition = 0" now asserted only under stated proportionality conditions | Applying Lemma 3 to wealth-normalised holdings on 2T intervals is my reading (valid for arbitrary vectors by the lemma's own statement); unreviewed, flagged §16.2 item 1. Tolerances and the delisting value are placeholders |
| P3 | §8.1–8.3, §9.1, §10.1 | Terminal wealth / CAGR (descriptive, not decomposed); additive statistic AR = annualised arithmetic mean of daily returns (attributed; scale does not drift with compounding); θ_sel for tests. Bootstrap, bound and power calculation all use the test's own statistic | "P1 = annualised net return" of v0.2 is replaced by AR with CAGR beside it |
| P4 | §6.1, §7 | NET-K added (same nominations, population, coverage denominator, pool as LOSS). NET-U kept as an end-to-end benchmark with its own pool and denominator, reported separately | — |
| P5 | §6.1 | Added to round 1: SCORE (top-⌈cK⌉), VOL, LIQ, TREND, VT (feasible, capped at 1), LOSS-LR. E-const split into E-const-dev (implementable, capped at 1) and E-const-expost (reference only) | VT's and TREND's exact rules are my specification; they are simple on purpose |
| P6 | §4.3, §4.4, §6.3 | One frozen deployment algorithm; hyper-parameters chosen once on tuning years and never again; fit / calibration / threshold / online-state updates separated, using matured past labels only; no early stopping at deployment. Search spaces, distinct configurations and CPU time reported; budget sensitivity on development years; log-loss removed as a common criterion | To remove the contradiction I chose "tune once, freeze" rather than yearly re-tuning. Costs: tuning rests on two validation years; the development evaluation window shrinks from 2016–2021 to 2017–2021; gate models are one year stale. All stated in §4.3 |
| P7 | §3.2, §3.7, §11 | Close-based fill exclusion relabelled "hindsight diagnostic", not a strategy, no theorem quantity. VWAP given its own timeline and filtration. Orders are pre-determined limit orders; **H + 1 pre-funded sleeves** so that no buy is funded by a same-auction sale | Larger change than the review literally asked: the sleeve count changed and about a quarter of capital is idle in the ungated strategy (arithmetic estimate). I saw no other way to make order quantities G_t-measurable without assuming same-auction funding, which is unverified. User question §16.1 item 4 |
| P8 | §5.4, §5.5, §7.3, §7.4 | Interpretation narrowed to "pipeline feature intervention, incremental to controls R". Added matched-window history control R_H-hist, event-trigger control R_O, fixed-nomination placement experiment, permuted-Z capacity control, training-only residualisation — for both groups. Confirmatory contrasts use a fixed base(−Z), so nominations are identical | R_H-hist is binned (10 bins), not the full daily history: still a summary |
| P9 | §12.1 | Executable protocol: six environments with analytic μ_t, six adaptive policies incl. variable n_t, zero-entry stretches and stopping, three revelation patterns, any-time failure indicator, fixed horizons and replications, exact binomial intervals, flag rule, comparators | The lead's "partly accepted" is respected: `theory/checks/` is not modified here (out of scope; §16.2 item 4). The time-uniform comparator Cmp-V2 is only a **candidate** until the theory task confirms it; the comparator I can vouch for (Cmp-V1) is valid at a fixed time only |
| P10 | §9.3, §10, §15.2 | p_eq = max of the two one-sided p-values, entered into Holm with the difference p-values. "Economically negligible" reserved for demonstrated equivalence; otherwise "no detectable difference; inconclusive". Block length 4(H+1) with sensitivity 2(H+1), 8(H+1) | — |
| P11 | §9.1, §9.2, §9.5 | Unresolved trades: "marked hybrid" column beside resolved-only; capital-weighted versions; pooled tail statistics recomputed on resampled date blocks of trade records; ICC on raw labels with unequal group sizes; ratio variance for loss fractions; N and N/(Md) called reference scenarios | — |
| P12 | §2.1, §2.2, §2.4 (A14–A20), §5.2a | Adversarial accounting cases (delisting, long suspension, corporate actions); upstream-independence item; turnover > 1 rule; chip initialisation; warm-up of the 500-day and 260-week variants | The cap rule for V > 1 and the initial chip mass are placeholders pending a reading of the reference implementation |
| "Minimum additional experiments" | §3.9 / §12.1 (accounting stress tests); §12.1 (known-truth coverage); §6.1 (matched-opportunity NET, SCORE, cheap controls); §7.3 (fixed-nomination, matched-history Z ablations); **§10.2 (`null_pipeline`, mandatory before the hold-out, with a numerical pass criterion)**; §4.4, §12 (hold-out preconditions) | As requested | The null simulation holds the base stage fixed and its pass criterion has limited power (0.79 against a true rate of 8% at B = 400); both stated |

**B. Synchronisation with the revised theory (S1–S4)**

| # | Where | What was done | Note |
|---|---|---|---|
| S1 | §3.8 (iii), §3.3, §11 | O1 marked at the scheduled exit (opening auction of t+H); O1-close is a robustness variant; O1′ of v0.2 no longer exists | — |
| S2 | §3.3, §9.4, §11, U25 | d = H + 1 fixed in advance, with the reason (valid under both operational assumptions) and audit item A18 for OA-next; d is no longer a robustness dimension | **Recomputation result:** v0.2 already used d = H + 1, so the hold-out half-widths are numerically unchanged (primary: 0.221 form (a) / 0.175 form (b)); I re-ran the formulas to confirm. The other columns changed only because of the new development window. The d = H row is shown for information only |
| S3 | §3.6 (addition), §8.2, §9.1 (P4) | Costs on traded amount = share change × execution price (post-trade minus pre-trade marked holdings); unit test | — |
| S4 | Header, §3.8, §12, §15 | Statuses quoted from the theorems.md table; Cor. 1.3 and Remark 4 "conditional on the result surviving review" wherever used; the revised Cor. 1.3 wording (no identification-limit claim; completion convention; A4-D) and A5 for P_T ≤ dM adopted | — |

**C. Other-participant-action variables (Z1–Z5)**

| # | Where | What was done | Deviation / reservation |
|---|---|---|---|
| Z1 | §1, §5, §5.6 | Z split into Z_H (unchanged) and Z_O (LHB summary and institutional seats; block trades; executed share changes dated by announcement). Trigger conditions of the Dragon–Tiger list enter the control set R_O | Marked "pending user confirmation at Gate 2" |
| Z2 | §5.6.4 | Northbound, margin, shareholder counts excluded with reasons | Margin as a negative control: **judged not worth running in round 1** (not a known null; costly; §10.2 tests false positives directly). Left as an optional item U31 |
| Z3 | §1, §5.6.4 | Unlock schedules and pre-disclosed plans not in any experiment | Superseded by Z3-user |
| **Z3-user** | §1, §5.6.4, §16.1, §17 | **User decision relayed by the lead (2026-11-15): Z_O uses free data only. Unlock schedules and pre-disclosure are written as "out of scope for this paper; possible future extension if licensed data become available"; the planned "conditional on licensed data" extension experiment and the §17 item on university data for them were removed** | The separate question of licensed *base price* data if the audit fails (F3) is unchanged and still open (§16.1 item 5) |
| Z4 | §5.6.2–5.6.5, §2.4 (OA1–OA9) | Encoding (indicator, days since event, intensity; zero with indicator when no event); availability rule; full sample versus event sub-sample; effect on power; OA1–OA9 merged into the audit, incl. rule originals and the absence of a second free source | (1) The lead asked for "has-value" indicators in the base set; for event classes the event indicator *is* the Z_O signal, so only the "data exist on this date" indicator and the trigger proxies go into controls. (2) OA1's "disclosure date + 1 trading day" is implemented as s+1 only when the rule original is archived, else s+2. (3) OA3's cut-off for the confirmatory group moved from 2018-01 to 2013-01 (gate fits start in 2013) |
| Z5 | §7, §8.4, §10 | Confirmatory: gate with versus without each group at fixed nominations (C3, C4); all other cells exploratory. **Holm family m = 4** (C1, C2, C3, C4); m = 3 if no Z_O class passes the audit. P8 controls applied to both groups. Wording "observable actions of other identifiable participants"; no game-theoretic claim | v0.2's Ungated(±Z), base-placement and D1-versus-D0 contrasts left the family (6 → 4 tests) |

**D. Other**

| # | Where | What was done |
|---|---|---|
| D1 Tushare | §2.1, §2.4 note, §14.2, U32 | `joshuaxql/qlib_data` and the `chenditc/investment_data` release asset (recorded in `DOWNLOAD_LIST.md` as Tushare-derived, the latter partly) removed from hard and fallback dependencies; optional only on separate user confirmation; cross-checking without them described. `ellendan/a-share-prices` kept as soft, provenance UNVERIFIED |
| D2 Fetch budget | §2.5, §14.3, U24 | Request counts and rate-limit rules per data class, from the feasibility file's measurements; all ESTIMATES |
| D3 §17 | §17 | Updated: U3 / U4 redefined, U7, U9, U10, U13 changed, U17 withdrawn, U22–U34 added (Z_O, lag rule, fetch budget, d = H + 1, O1 definition, sleeves, null simulation, synthetic protocol, margin control, Tushare-derived files, tolerances, budget sensitivity). University data for unlock / pre-disclosure removed per Z3-user |
| D4 Wording | whole file | No statement of expected direction or size of any result; numerical proposals marked PLACEHOLDER, formula evaluations marked ESTIMATE; CGO and abnormal-turnover formulas still "NOT CHECKED AGAINST THE ORIGINAL" with implementation blocked (§5.1, §5.3, §5.2a); literature cited with its abstract-level reading depth |

**E. Items not done as asked, in one place**
1. P1: the fixed-yuan cohort statistic replaces, rather than supplements, the aggregate composition term in the tests.
2. P7: sleeve count changed to H + 1 (beyond the literal request).
3. P9: `theory/checks/` untouched; Cmp-V2 only a candidate.
4. S2: nothing to recompute for the hold-out column (d was already H + 1); stated rather than presented as a change.
5. Z2: margin negative control not scheduled.
6. Z4: coverage indicators handled as described above; OA1 and OA3 thresholds adapted.

**F. Things I am not sure about**
- Whether θ_sel with liquidity × volatility strata is the right "selection" estimand; sector tilts remain in it. A reviewer may prefer more strata, at the cost of thinner cells within 30 names.
- Whether tuning on two validation years is adequate; the alternative (yearly re-tuning as a declared part of the algorithm) is also defensible.
- The normal-approximation p-values with a bootstrap standard error for a ratio statistic; this is what §10.2 is meant to test, and the procedure may have to change.
- W-swap's handling of names with non-overlapping histories; W-perm's weakened temporal dependence.
- Trading-day counts (242 per year; 1,090 / 1,215 / 2,305), the fill rate of 1 in §9.4, the invested-fraction arithmetic of §3.7 and all run-time estimates are unmeasured.
- All trading and disclosure rules remain unverified against exchange originals.
- Sections kept verbatim from v0.2 (§2.2–2.3, the A1–A13 table and fallbacks, §3.4–3.6, §4.1–4.2, §5.1–5.3, Appendix) were re-read for consistency but not re-verified.

---

## Revision log (v0.1 → v0.2, 2026-11-15, researcher, Task B second half)

Only this file was changed. Nothing was run on data, downloaded or installed. The half-width numbers in §9.4 come from evaluating the formulas of `theory/theorems.md` in a throwaway script (assumed sample sizes, no data); they are estimates.

**A. Alignment with `theory/setup.md` / `theory/theorems.md`**
1. **Selected entry = fill, not submission** (§3.1, §3.4, §3.7, §3.8 (i)). v0.1 defined A_{ti} as "order submitted" with label L = 0 for non-fills. setup.md §3.1 defines a selected entry as an executed fill with F_t at the fill point. Changed accordingly: τ_t = opening-auction match; unfilled orders have no label and are excluded from n_t, N_T, K_T, P_T; a separate order ledger records submissions and non-fills. *Why:* setup.md governs; otherwise Theorem 1's target in the experiments would differ from the one in the theory.
2. **Selection by tradability made explicit** (§3.8 (ii), §15.1). Added: what the fill filter does to the executed set (endogenous truncation at limit-up), what μ_t therefore means, and five reports (fill rates, filled-versus-unfilled characteristics, paper outcome of unfilled orders, loose-tradability variant, submission-based alternative in a separate table). RND is matched on submitted counts and passes through the same fill rule; fill-matched version as sensitivity. *Why:* requested; without it, differences between gates' executed trades could be misread as signal differences.
3. **d from H per setup §3.3** (§3.3, §3.8 (iv)). d = H + 1 because τ_t precedes the close and O1 is determined at the close of t+H. v0.1 reached the same number by a different argument (mark at the open of t+H); that argument is removed.
4. **Label O1 redefined as in setup §3.2**: marked at the *close* of t+H (v0.1: at the open). The v0.1 mark is kept as the variant O1'. **Unresolved and flagged** (§16.2 item 1): the exit is at the open of t+H, half a day before the O1 mark. Not decided here because it requires a change to setup.md or to the exit rule.
5. **Label O2**: restated per setup §3.2 (A3 fails; no non-informative-censoring assumption; no resolved-only estimator). Added the deadline labels L^lo, L^hi and the Cor. 1.3 interval, **marked conditional on the result surviving review** wherever used (§3.8 (v), §9.2, §11, §12).
6. **Table "which label enters which quantity"** added (§3.8 (vi)); A4 accounting restated on executed entries (§3.8 (vii)); the matured-only rate labelled as not covered (Cor. 1.2).
7. **Lemma 3 conventions fixed** (§8.3): e_t = 1'h_t, w_t = h_t/e_t; reference h^E = e^G w^B, i.e. interaction booked under composition (eq. (2)), alternative ordering as sensitivity; when e_t^B = 0, w_t^B = equal weight on the base strategy's nominated lists of the last H decision days (v0.1's "set the term to zero" becomes the sensitivity). *Why:* Lemma 3 qualifications 1 and 5 require the conventions to be fixed in advance. *Caveat:* the zero-exposure convention is the plan's choice (setup.md does not fix one) — flagged to the lead.
8. **Metrics** (§9.1–9.2): P2 over executed (not submitted) trades; secondary metrics list the interval in form (b) as primary, with (a), (c), Cor. 1.2 and Cor. 1.3 (conditional).

**B. Experiment-to-claim map** (§12)
9. Table rewritten: every row now names a v3 hypothesis and the specific items of theorems.md (Theorem 1(a)/(b)/(c), Cor. 1.1–1.3, Prop. 2, Lemma 3, Remark 4) or states "empirical only". References to `design_notes.md` numbering removed. Header states that no item has been externally reviewed and that Cor. 1.3 is a draft.
10. Two experiments added: `dependence_diag` (§9.5) and `power_precheck` (§10.1). `synth_validation` extended to Theorem 1(b)/(c), Cor. 1.1–1.3 and to reproducing the §9.4 table.

**C. What the theory is actually good for**
11. **New §9.4**: assumed N, d, M under our conventions (M = K = 30, d = 6, about 1,090 hold-out days, N about 32,700 ungated / 16,350 at c = 0.5), the formula, a worked case, and a table of estimated half-widths. Primary setting: about 0.22 (form (a)) / 0.18 (form (b)) at the end of the hold-out, 0.13 / 0.12 if monitored continuously from 2016; [0,1] for about the first 130 days. Stated consequence: the interval is not used to compare methods or in any confirmatory test; its role is limited to (a) limits of evidence, (b) validity contrast with the matured-only rate, (c) bookkeeping. *Why:* `theory/checks/README.md` shows the interval is very conservative; the plan must not imply otherwise. Observation recorded: with constant n_t the half-width depends on the number of days and d, not on K.
12. **New §9.5 / experiment `dependence_diag`**: same-day intraclass correlation, cross-day autocorrelation, block-bootstrap and long-run-variance effective sample size, placed between the reference points N and N/(Md) of Prop. 2, with explicit limits (cannot certify a restricted class; does not license narrower intervals; confounded by time-varying μ_t).
13. §1 item 3, §15.1, §15.2 updated to state the width limitation as known in advance rather than as a possible finding.

**D. Items v0.1 left open**
14. **PERF** (§6.1, §8.2, §9.3, §10): enters only Q-total and the exposure-schedule attribution; removed from Q-select and from the confirmatory family. **Confirmatory family reduced from 7 to 6 tests; Holm over m = 6.** *Why:* its within-day selection contrast is zero by construction.
15. **Cohort-level decomposition** (§8.2): defined as Lemma 3 applied per entry cohort and summed; stated as our reading (exact by additivity), enforced by a unit test; not a statement of theorems.md (§16.2 item 3).
16. **Exposure level / timing sub-split** (§8.3): kept, now with an explicit definition (λ = Σe^G/Σe^B; level = (λ−1)Σ e^B r; timing = Σ(e^G − λe^B) r) and caveats (ex post, descriptive, exploratory, not in any confirmatory test).
17. **CGO and abnormal turnover** (§5.1, §5.3): relabelled "NOT CHECKED AGAINST THE ORIGINAL"; implementation is blocked until the formulas are checked against Grinblatt & Han (2005) and Liu, Stambaugh & Yuan (2019) and the check is recorded. I did not check them.
18. **Placeholders** collected in the new §17 with how each is to be set and its sensitivity range; values unchanged from v0.1 (commission 2.5 bps, slippage 5 bps, bound ±1%/year, and the others). New placeholders: δ (U15), deadline D (U16), minimum prior power (U18), exploratory alternative bounds (U3, U4).
19. **Prior power** (new §10.1, experiment `power_precheck`): block-bootstrap long-run variance of the daily difference series on development data → predicted hold-out standard error → normal-approximation power for the equivalence and difference tests, with Holm; pre-declared consequences; "inconclusive" stated as a possible, reported outcome. Arithmetic illustration only (no data): for ±1%/year, 80% equivalence power needs an annualised long-run volatility of the difference series of at most about 0.72% (0.58% at the strictest Holm step).

**E. Data sources and approvals**
20. **AKShare is now the primary source; BaoStock the cross-check** (§2.1, §2.4 A1 / F1, §14.2). v0.1 had "BaoStock + AKShare" with BaoStock supplying the bars. *Why:* user decision of 2026-11-15. *Open:* whether AKShare supplies every required field is UNVERIFIED; using BaoStock for a missing field is F1 and needs confirmation (§16.1 item 3).
21. **Tushare**: no experiment depends on it; removed from the dependency table; remaining mentions only state that it is not used. Added a provenance note that two approved cross-check datasets are partly Tushare-derived (§2.1, §16.1 item 2) — a question for the user, not a dependency.
22. **Approval status** updated throughout (header, §2.1, §14.1, §14.2, §16.1): the download list was approved on 2026-11-15; a separate Python 3.12 and the download method for `qlib_bin.tar.gz` are outside that approval.

**F. Mechanism side-track**
23. `mechanism_sidetrack` and H-M marked **ON HOLD — pending lead / user decision** (§1, §12, §13, §15.2, §16.1 item 7). Row kept; scope neither extended nor deleted.

**G. Things I am not sure about (not resolved by this revision)**
- The trading-day counts (about 242 per year; 1,090 / 1,460 / 2,550) are approximations, and the fill rate was set to 1 in §9.4; realised N and widths will differ.
- Whether a mark at the open of t+H would allow d = H is not covered by setup.md; I claim only d = H + 1.
- The cohort-level decomposition and the level / timing split are my own algebra, checked by hand only, not reviewed.
- That PERF's cohort-level composition term is exactly zero under the cash rule assumes equal slots within a cohort and no interaction with blocked exits; to be confirmed by the unit test.
- Same-auction use of sale proceeds (§16.2 item 5) and all trading-rule details remain UNVERIFIED against exchange originals.
- The power formulas are normal approximations; the block-bootstrap long-run variance on about six development years is itself imprecise.
- Sections of v0.1 not mentioned above (§4, §5.2, §5.4–5.5, §6.2–6.3, §7, most of §11, §14.3) were left as written and were not re-verified.


## Part C. Abstract theoretical setup the plan relies on (theory/setup.md)

# Problem setup — abstract part (Stage 2, Task A)

> Researcher (sub-agent), 2026-11-15. **Restructured after review round 3** (`reviews/proof_check_3.md` §4): this file now contains **only the abstract setting on which the statements in `theorems.md` depend**. Everything about A-share trading (execution model, valuation rules, operational lag, dividends, partial fills, the experiments' checklist) was moved to `theory/instantiation_ashare.md`, which is a set of modelling assumptions and conventions and is **not part of any statement**. Revision logs: top of `theory/proofs.md` (the round-3 log maps the old section numbers of this file to the new ones).
> Review state: three review rounds (GPT + Gemini Flash); round-3 revisions applied and NOT re-reviewed.

## 1. Objects and information times

Time is indexed by integers t = 1, 2, … ("days"). All random objects live on one probability space (Ω, 𝒜, ℙ). Each day has **two** information times:

```
 day t:   G_t  ──(orders are submitted)──▶  fills are determined  ──▶  F_t        day t+1:  G_{t+1} …
          pre-submission information                                   post-fill information
```

- **G_t (pre-submission information):** what is known when the orders of day t are submitted, before their fills are known.
- **F_t (post-fill information):** G_t together with the outcome of the day-t fills (and whatever else is declared to be known at that instant). G_t ⊆ F_t ⊆ F_{t+1}.

Orders are chosen with G_t; which of them become **executed entries** is known with F_t; the conditional target (§5) is defined with F_t. The loss count of day t becomes known at the latest with F_{t+d}; in between, anything may be observed and used. Nothing in this file says what a "day", an "order" or a "fill" is in a market; that is the instantiation's job.

## 2. Notation

| Symbol | Meaning |
|---|---|
| t, T | day index; monitoring time |
| (F_t), (G_t) | post-fill filtration (increasing); pre-submission σ-fields, G_t ⊆ F_t |
| C_t | candidate set of day t (finite, random) |
| O_{ti} ∈ {0,1} | an order for candidate i is submitted on day t (A1-G) |
| A_{ti} ∈ {0,1} | candidate i is an **executed entry** of day t |
| n_t = Σ_{i∈C_t} A_{ti}, M | number of entries of day t; known cap, n_t ≤ M |
| L_{ti} ∈ {0,1} | loss label of entry (t,i) (A2) |
| d_label ≥ 1 | label-finalisation lag: deterministic integer, part of the label convention (A2(b)) |
| d ≥ 1 | monitoring (revelation) lag: deterministic integer, fixed before any data are examined (A3) |
| X_t = Σ_{i∈C_t} A_{ti} L_{ti} | number of losing entries of day t; 0 ≤ X_t ≤ n_t |
| μ_t = E[X_t ∣ F_t] | entry-time conditional expected number of losses |
| N_T = Σ_{t≤T} n_t | number of executed entries through T (the denominator of every rate) |
| r_T^entry = Σ_{t≤T} μ_t / N_T | **target** (N_T > 0), §5 |
| R_T = Σ_{t≤T} X_t / N_T | realised loss fraction (not fully observed at T) |
| K_T, P_T | revealed labels equal to 1; unrevealed labels, among entries through T (A4) |
| Q_{j,T} = Σ_{t≤T, t≡j (mod d)} n_t² | predictable range clock of lane j ∈ {0,…,d−1} |
| c_0, L_k, b, b*, B_T, B*_T | constants and radii of Theorem 1 (`theorems.md`) |
| J_T, K^lo_T, K^hi_T, P_T^D = N_T − \|J_T\| | common revealed set and counts for bracket labels (A4-D; Corollary 1.3). P_T^D is **not** P_T |

## 3. Assumptions

Each assumption is followed by what it needs in an application. None of them is "true by construction" or "mere bookkeeping": each has to be supported by a data audit or a written convention, and `instantiation_ashare.md` says what that support would be for A-shares and where it is currently missing.

**A1 (decision information).** (F_t)_{t≥1} is an increasing family of σ-fields. For every t the finite random set C_t, the indicators A_{ti} ∈ {0,1} (i ∈ C_t) and n_t = Σ_{i∈C_t} A_{ti} are F_t-measurable, and n_t ≤ M for a known integer M ≥ 1. Any randomisation used is F_t-measurable.

*Role of M.* M does not appear in the radii of Theorem 1. It makes X_t ≤ n_t ≤ M bounded, hence integrable, so that μ_t is an ordinary conditional expectation and E[μ_t − X_t ∣ F_t] = 0; and it enters the rate of Corollary 1.1.
*Needs in an application.* A declared F_t and evidence that candidate sets and the entry indicator use nothing later than it. Where the entry indicator is simulated from data that were not available at the declared instant, A1 can only be claimed for a filtration that contains those data, and the target changes with it (instantiation §2, "synthetic fills").

**A1-G (pre-submission measurability) — used in no proof; required to read the results as statements about an implementable strategy.** There are σ-fields G_t ⊆ F_t and G_t-measurable order indicators O_{ti} ∈ {0,1}, i ∈ C_t, with Σ_i O_{ti} ≤ M, such that the complete specification of every submitted order (name, quantity, order type, limit price) is G_t-measurable, and A_{ti} ≤ O_{ti} (an executed entry arises only from a submitted order).

*Why it is stated.* A1 alone lets A_{ti} depend on everything in F_t, including the outcome of the very fills it describes; a rule that decides "which orders participated" after seeing their prices satisfies A1 but cannot be traded (round-3 item X2). The concentration argument does not need A1-G; any sentence of the form "the monitored strategy is executable" does.
*Needs in an application.* The order-generation code may read only data stamped before submission (instantiation §2.1).

**A2 (fixed, frozen label).**
(a) Every executed entry (t,i) has a label L_{ti} ∈ {0,1}, a random variable defined on all of Ω by a convention (execution, valuation, exit and missing-data rules) fixed before any data are examined. X_t = Σ_{i∈C_t} A_{ti} L_{ti}, μ_t = E[X_t ∣ F_t].
(b) *Freezing.* Wherever the convention refers to what data are available (for instance a rule for missing or late inputs), it does so at a **deterministic label-finalisation lag d_label ≥ 1 that is part of the convention**, i.e. at day t + d_label, and the value so obtained is final. In particular L_{ti} is **not a function of the monitoring lag d** of A3 and is never revised. (A label whose convention contains no data-availability rule, such as the target label of Corollary 1.3, satisfies (b) vacuously.)
(c) **Nothing** is assumed about the joint law of labels: no independence or conditional independence within a day, no stationarity, no mixing, no restriction on how μ_t evolves.

*Why (b).* If a missing-data rule were evaluated at day t + d, changing d would change L_{ti}, X_t, μ_t and the target, not only the radius (round-3 item X3). With (b) the same random variables are monitored whatever valid d is used.
*Needs in an application.* A written rule that assigns a value in {0,1} to **every** entry in every state of the world and terminates; point-in-time data as of day t + d_label; a count of the entries whose label is set by a fallback rule (instantiation §3). A2 does not hold for a rule set that leaves some case undefined or lets a later data revision change a label.

**A3 (bounded revelation lag).** There is a known **deterministic** integer d ≥ 1, **fixed before any data are examined**, with X_t F_{t+d}-measurable for all t ≥ 1.

*Remarks.* A3 concerns the day's loss **count**, not individual labels (that is A5), and restricts nothing about what is known earlier. A sufficient condition: every L_{ti} is F_{t+d_label}-measurable and d ≥ d_label. The converse is false (if all labels are deterministically 0, A3 holds with d = 1 whenever the inputs arrive). No minimality of d is claimed anywhere.
*Needs in an application.* An audit of when every input of every label reaches the declared information set, for all days. This is a substantive assumption about the data pipeline (instantiation §4), not a consequence of a holding horizon. For a label whose resolution time is unbounded (instantiation §6, executable liquidation) nothing guarantees A3 for any fixed d, and Theorem 1 is not applied to it.

**A4 (observable accounting).** At monitoring time T the monitor knows, for every executed entry (t,i) with t ≤ T, whether its label has been revealed, and the value of every revealed label. "Revealed" means that the **final value of the label itself** is known, not a proxy. K_T counts revealed labels equal to 1; P_T = N_T − (number of revealed labels).

*Remarks.* A4 puts no condition on the revelation mechanism: which labels are revealed early may depend on the labels. Theorem 1 uses A4 for computability; validity uses the pathwise fact K_T ≤ Σ_{t≤T} X_t ≤ K_T + P_T.
*Needs in an application.* A ledger in which an entry is marked "revealed" only when its frozen value (A2(b)) is recorded, and which is never corrected afterwards. A ledger fed by provisional marks does not satisfy A4.

**A5 (individual revelation by the lag) — optional; used only in Corollary 1.1(b) and Proposition 2's construction.** Every label of every entry of day t is revealed (in the sense of A4) at all monitoring times T ≥ t + d. *Consequence:* P_T ≤ Σ_{T−d<t≤T} n_t ≤ dM. *Needs:* the ledger is updated from the same data that support A3. A3 does not imply A5.

**A4-D (accounting through a common revealed set) — used only in Corollary 1.3.** For the two bracket labels L^lo ≤ L^hi of Corollary 1.3 there is, at each monitoring time T, a set J_T of executed entries (t,i), t ≤ T, known to the monitor, such that for every entry in J_T **both** values are known; the interval is computed from K^lo_T = Σ_{(t,i)∈J_T} L^lo_{ti}, K^hi_T = Σ_{(t,i)∈J_T} L^hi_{ti} and P_T^D := N_T − |J_T|.

*Remarks (reworded in round 3, item X10).* A4-D restricts **the interval calculation**, which uses label information only through the common set; it does not restrict the underlying ledger, which may record the two components at different times (an entry with only one component recorded is simply not in J_T and is counted in P_T^D). What fails without a common set is the reading of K^hi_T − K^lo_T as a count of entries (proofs §1.8, Step 5).

## 4. Two lags, both fixed in advance

- **d_label** belongs to the label (A2(b)); **d** belongs to the monitoring procedure (A3). They may be equal.
- **A larger monitoring lag, same labels.** If A3 holds with d it holds with every d′ > d (F is increasing), for the **same** X_t, μ_t and target because of A2(b). Coverage of Theorem 1 is therefore preserved. This is a statement about one frozen family of labels; it says nothing about labels recomputed with a later data deadline, which are different random variables.
- **The radius is not monotone in d.** Changing d changes the partition of days into lanes. `checks/check_lag_monotonicity.py`: T = 4, one entry on day 1 and one on day 4, δ = 0.05 gives B_T = 4.418 for d = 2 and 3.653 for d = 3 (both clipped intervals are [0,1] there); entries only on days t ≡ 1 (mod 3), 10 per day, T = 3000: B*_T/N_T = 0.103 for d = 2 and 0.075 for d = 3; with 10 entries every day the radius increases with d. So a larger valid lag worsens the worst-case bound of Corollary 1.1 but the computed intervals for two lags are not nested.
- **Consequence.** d must be fixed before the data are seen. A lag chosen after looking at the widths is not covered by Theorem 1.
- Lanes are residue classes of the day index used in §1.

## 5. The target, and what it is not

r_T^entry = (Σ_{t≤T} μ_t) / N_T, defined when N_T > 0 (when N_T = 0 the target is undefined and every interval in `theorems.md` is [0,1] by convention). It is a **random**, generally unobservable quantity: the average, over executed entries through T, of the loss probability each day's batch had given F_t.

It is **not**:
1. the realised loss fraction R_T (bracketed deterministically by [K_T/N_T, (K_T+P_T)/N_T], Corollary 1.2);
2. E[R_T ∣ information at T] (that conditions old entries on new information);
3. a statement about the next entry or batch: μ_{T+1} can be anything given the past;
4. a population parameter: there is no stationary "true loss probability" in the model;
5. filtration-free: it depends on (F_t). A different declared F_t that still satisfies A1–A3 gives a different, also validly monitored, target. In particular the loss probability "given post-fill information" already reflects whatever the fill mechanism reveals, and is not the probability assessed with G_t when the order was chosen. Any paper statement must name F_t explicitly;
6. a measure of economic performance: a low loss probability is compatible with rare large losses.

Monitoring r_T^entry is **inference about the past entry stream**, not control of future risk.

## 6. What this file deliberately does not contain

No market rule, execution model, price or valuation rule, corporate-action treatment, data source or numerical lag appears above. The statements in `theorems.md` use only §1–§5. Whether A1–A5 hold for a concrete trading system is a separate question, addressed for A-shares in `theory/instantiation_ashare.md`; **the conclusions of the theorems apply to that system only to the extent that those modelling assumptions hold**, and several of them are unverified.
