# Fact-check of `literature/novelty_report.md` §8 (N1–N12)

> Lead, ARS `deep-research` · `fact-check` (source-verification role run inline), 2026-11-15. Independent of the scout: I re-ran my own arXiv API field queries and Crossref / arXiv ID lookups; I did not reuse the scout's result lists. Scope limits are the same as the scout's (no CNKI, no broker reports, no Google Scholar, no SSRN full text). AI-assisted. Verdicts: **SUPPORTED** (checked, holds within the stated scope) / **PARTLY** / **NOT VERIFIABLE HERE** / **CORRECTION**.

## A. Existence and content of the key cited sources

| Source as cited | Check | Result |
|---|---|---|
| Khosravi & Huo 2026, *Conformal Selective Acting*, arXiv:2605.20270 | arXiv API by ID | **SUPPORTED.** Exists (2026-05-18). Abstract says: offline conformal-risk methods need exchangeability; online methods bound only long-run averages; A-RCPS controls marginal rather than selective risk; they give an e-process per threshold with anytime-pathwise validity for selective risk. Full title continues "…Anytime-Valid Risk Control for RLVR-Trained LLMs" — the setting is LLM deployment, not finance. |
| Xu, Karampatziakis & Mineiro 2024, A-RCPS | arXiv API (author + title) | **SUPPORTED.** arXiv:2406.10490, "Active, anytime-valid risk controlling prediction sets". NeurIPS venue not re-verified. |
| Benhamou et al. 2026 (PROMOTE) | arXiv API | **SUPPORTED** as to existence: arXiv:2611.03384, "Can We Stop the Backtest Yet? Anytime-Valid Promotion Tests for Adaptive Financial Research Agents". "Accepted at ICAIF 2026" not verified. |
| Choi, Jin & Yan 2013, NBER w18680 | Crossref | **SUPPORTED** as to existence: "Informed Trading and Expected Returns". The 10.8% figure and the direction of the effect were **not** re-verified (no abstract in Crossref). |
| Cherednik 2019 (C012), arXiv:1911.08448 | arXiv API | **SUPPORTED** as to existence. The abstract shown (first ~900 chars) describes a "momentum risk-taking" model and an automated momentum equity trading system; the poker link was not visible in the portion retrieved. Relevance to N2 remains **unverified**; needs a full-text look. |
| Guo 2026, SSRN doi:10.2139/ssrn.7021298 | Crossref (abstract is deposited there) | **NEW INFORMATION — scout could not read this.** Title "When Not to Trade: Leakage-Aware Selective Machine Learning for Factor Rotation". Abstract (first ~1,200 chars): asks "when should a machine-learning strategy refuse to trade?"; a selective deployment framework for **factor and sector rotation**; rolling-origin protocol; the ML signal is deployed only when validation improvement over a fallback benchmark exceeds a calibrated threshold, otherwise the strategy **abstains and falls back to a benchmark portfolio**; formalised as a predictable portfolio rule with a return / mean–variance utility decomposition. The rest of the abstract was cut off. No game or informed-trader mechanism appears in the portion read. → One more precedent for the **abstention layer** (strategy level), consistent with the "high" rating; it does not by itself contradict N1, N3, N4 or N5 on the portion read, but the full paper is unread. |

## B. The "nobody has done X" claims

| ID | Verdict | Basis |
|---|---|---|
| N1 (no mechanism-derived entry-abstention rule for stocks) | **PARTLY / not falsified.** | My queries (`"adverse selection" ∧ abstain ∧ q-fin`; `"informed traders" ∧ retail ∧ "not trade"`; `"no-trade" ∧ "asymmetric information" ∧ learning`) returned nothing on point: results were market-making / execution / price-discovery papers (e.g. arXiv:2607.01198, 2411.05032, 0801.3001). Absence in two narrow arXiv query sets is weak evidence; finance journals and SSRN full text remain unsearched. Keep the scout's "medium" confidence, no higher. |
| N2 (no academic formalisation of poker "fold" as a trade-entry rule) | **PARTLY / not falsified.** | `poker ∧ "stock market"`, `"imperfect information" ∧ "stock trading"`, `fold ∧ poker ∧ trading` returned only game-algorithm papers, Cherednik 2019, and one RL-trading review. Same caveat as N1. Note that Deep Gamblers (abstention from gambling theory) is a partial conceptual precedent and must be cited. |
| N3 (no abstention-for-trading paper uses cost-basis / turnover-abnormality variables) | **SUPPORTED within the listed papers**; Guo 2026 now partially read — no such variables in the portion read. |
| N4 (no incremental-value test of such variables for an abstention layer, A-shares) | **NOT VERIFIABLE HERE.** `"capital gains overhang"` on arXiv returns only arXiv:2505.20608 (a replication study), matching the scout. But the relevant literature is likely Chinese-language (CNKI, broker research), which neither of us searched. This claim must not be written into the paper until the user's Deep Research / CNKI pass is done. |
| N5 (no exchangeability-free selected-trade-risk guarantee on a trading stream) | **PARTLY.** `"selective risk" ∧ trading` returned nothing on point. But the generic tool exists (CSA, confirmed above), so the claim only survives in the narrow form the scout already states. Any theorem we write must be positioned as an adaptation; "first" is not defensible. |
| N6, N7, N8, N9 (properties of specific papers) | **Not independently re-read.** These rest on the scout's full-text reading; my abstract-level three-way scan (`literature/three_way_scan.md`) is consistent with N7 and N8 and with N9's "no trading experiments" only in so far as the abstracts are silent. The external reviewers cannot check these either. Flag for the user's own reading of the top 3 papers. |
| N10 (no A-share daily selective trading with T+1 / price limits) | **NOT VERIFIABLE HERE.** arXiv queries returned noise or nothing. Chinese-language sources unsearched. |
| N11 (conjunction) | Follows from the above; of little evidential value, as the scout notes. |
| N12 (Chalkidis & Savani's own "first" claim vs Pidan & El-Yaniv 2011) | **Not re-verified** (Pidan & El-Yaniv not looked up by me). Harmless to us either way. |

## C. Corrections and additions to the novelty report

1. **Add Guo (2026)** to the abstention-layer precedents (strategy-level abstain-to-benchmark for factor / sector rotation, with a formal decomposition). The report's §9 item 2 ("user must open SSRN manually") is now partly resolved; full text still unread.
2. **CSA is an LLM-deployment paper.** The report describes it accurately but a reader could assume it is finance; say so explicitly when citing it.
3. **Choi, Jin & Yan (2013):** the direction-of-effect statement is the single most consequential empirical claim in the report (it could undercut the whole idea) and it rests on an abstract only. `researcher` or the user should read the paper before Gate 2.
4. No fabricated or non-existent reference was found among the items checked (7 of 7 resolved).

## D. Overall

The scout's two ratings stand after this check: **abstention layer — high; game mechanism + abstention — medium**, with the caveat that every "not found" in N1, N2, N4, N10 is bounded by English-language, arXiv/OpenAlex-level search. The check found one additional precedent (Guo 2026) and no counter-example to the mechanism-level gap.
