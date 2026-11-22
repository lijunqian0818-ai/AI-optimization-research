# ARS Literature Review (narrative / integrative) — Poker-style abstention for equity trading

> Produced by the lead with ARS `deep-research` · `lit-review` (bibliography + source verification + synthesis roles run inline). Date: 2026-11-15. Review form chosen by the user: narrative / integrative.
> **Read level: abstracts and bibliographic metadata only** unless stated. No full texts were read for this file. Method-level weaknesses are therefore *not assessed (read scope: abstract_only)*.
> AI disclosure: compiled with AI assistance (Claude); every entry below was checked against OpenAlex, Crossref or the arXiv API on 2026-11-15.

## 1. Search strategy

- **Sources:** OpenAlex (`tools/search_resources.py papers`), arXiv API (`tools/search_resources.py arxiv`, plus direct `export.arxiv.org` ID lookups), Crossref DOI lookups for classics.
- **Query families (≈27 queries):** poker / imperfect-information game + trading; CFR + financial market; selective classification / abstention / reject option + stock or trading; conformal (risk control) + trading; meta-labeling; Kyle / Glosten–Milgrom / no-trade; PIN; capital gains overhang / disposition effect + A-share; factor timing + China; Kelly + parameter uncertainty; risk-sensitive / CVaR RL + portfolio; multi-agent RL market simulation.
- **Inclusion / exclusion:** `literature/screening_criteria.md` (draft v0).
- **Flow:** ≈150 records returned → 30 retained below after relevance screening and existence verification. Records whose identifier could not be confirmed were dropped.
- **Search limitations:** the arXiv keyword endpoint returned empty results for several queries (tool issue, not evidence of absence); Semantic Scholar, SSRN full-text, CNKI and Google Scholar were not searched; Chinese-language literature is not covered. This review therefore **cannot support any "nobody has done X" claim** — that is the job of `novelty_report.md` and its three-way check.

## 2. Annotated bibliography

Verification: **V** = identifier resolved and title/authors matched on 2026-11-15. Evidence tier: T1 peer-reviewed, T2 preprint, T3 other.

### Theme A — Abstention / selective prediction as a trading decision (closest to our architecture)

1. **Chalkidis, N., & Savani, R. (2021). Trading via selective classification. ICAIF '21.** doi:10.1145/3490354.3494379; arXiv:2110.14914. [V, T1] — Applies binary and ternary selective classification to trading-strategy design: the strategy takes no position when the classifier abstains. Walk-forward evaluation with logistic regression, random forests, feed-forward and recurrent nets; backtests on commodity futures. *Relevance: high — this is the "abstain = no trade" idea already published; purely empirical per the abstract, no game-theoretic component, not equities / A-shares.*
2. **Zhang, Y., Zheng, S., Dalirrooyfard, M., Wu, P., Schneider, A., Raj, A., Nevmyvaka, Y., & Chen, C. (2023). Learning to abstain from uninformative data.** arXiv:2309.14240. [V, T2] — Studies learning under a generative process where a large share of samples is uninformative (high label noise), motivated explicitly by finance; proposes a selective-learning-inspired loss with a near-optimality guarantee and an algorithm that jointly trains predictor and selector. *Relevance: high — a theory-backed abstention method motivated by finance; the selector is statistical, not derived from a market mechanism.*
3. **Ziyin, L., Wang, Z., Liang, P. P., Salakhutdinov, R., Morency, L.-P., & Ueda, M. (2019). Deep Gamblers: Learning to abstain with portfolio theory.** arXiv:1907.00208 (NeurIPS 2019 per OpenAlex listing as arXiv; venue not re-verified). [V, T2] — Recasts m-class selective classification as an (m+1)-class problem whose loss is the doubling rate of a horse-race gamble; abstaining = reserving one's stake. Experiments on SVHN / CIFAR-10. *Relevance: medium-high — already links abstention to betting (Kelly-style) theory, though for image classification.*
4. **Hao, Z., Chen, H., & Qi, R. (2026). Coverage-constrained selective prediction for short-horizon cryptocurrency event contracts via adaptive quantile thresholds. Algorithms.** doi:10.3390/a19080704. [V, T1] — Formulates fixed-odds price-direction contracts as selective prediction with a coverage constraint; trade only when win probability exceeds the break-even rate. *Relevance: medium-high — same decision structure (win-probability threshold + coverage) in crypto.*
5. **Torres, D., Cheng, W., & Huang, H. (2026). FinAbstain: Uncertainty-calibrated multimodal RAG for selective financial forecasting.** arXiv:2607.24875. [V, T2] — LLM/RAG forecasting pipeline whose controller abstains above an uncertainty threshold; compares temperature scaling, isotonic regression, conformal prediction. **The abstract states that reported results are explicitly labeled simulated, not empirical.** *Relevance: medium — shows the abstention framing is active in 2026; provides no empirical evidence.*
6. **Geifman, Y., & El-Yaniv, R. (2017). Selective classification for deep neural networks.** arXiv:1705.08500. [V, T2 as listed] — Foundational risk–coverage framework with a guaranteed-risk selection procedure. *Background.*
7. **Chow, C. K. (1970). On optimum recognition error and reject tradeoff. IEEE Trans. Inf. Theory.** doi:10.1109/TIT.1970.1054406. [V, T1] — Classical optimal reject rule. *Background.*
8. **Angelopoulos, A. N., Bates, S., Fisch, A., Lei, L., & Schuster, T. (2022). Conformal risk control.** arXiv:2208.02814. [V, T2 as listed] — Extends conformal prediction to control the expectation of any monotone loss; includes extensions to distribution shift. *Relevance: candidate tool for H2b; exchangeability-based.*
9. **Xu, Y., Guo, W., & Wei, Z. (2025). Selective conformal risk control.** arXiv:2512.12844. [V, title/metadata only] — *Lead for H2b; content not read.*

### Theme B — Imperfect-information games and strategic trading

10. **Chriss, N. A. (2025). Position building in competition is a game with incomplete information.** arXiv:2501.01241. [V, T2] — Bayesian-game extension of competitive trading equilibria where firms are uncertain about competitors' target sizes and impact models; includes non-strategic traders. *Relevance: medium — a genuine incomplete-information trading game, but about institutional execution, not a retail entry / abstain decision.*
11. **Kyle, A. S. (1985). Continuous auctions and insider trading. Econometrica.** doi:10.2307/1913210. [V, T1] — Canonical informed-trader / noise-trader / market-maker model.
12. **Glosten, L. R., & Milgrom, P. R. (1985). Bid, ask and transaction prices in a specialist market with heterogeneously informed traders. J. Financial Economics.** doi:10.1016/0304-405X(85)90044-3. [V, T1] — Adverse selection as the source of the spread.
13. **Milgrom, P., & Stokey, N. (1982). Information, trade and common knowledge. J. Economic Theory.** doi:10.1016/0022-0531(82)90046-1. [V, T1] — No-trade theorem: purely informational trade cannot occur among rational agents with common priors. *The classical formal statement of "if you might be the uninformed one, don't trade".*
14. **Easley, D., Kiefer, N. M., O'Hara, M., & Paperman, J. B. (1996). Liquidity, information, and infrequently traded stocks. J. Finance.** doi:10.1111/j.1540-6261.1996.tb04074.x. [V, T1] — Origin of the PIN (probability of informed trading) measure; an existing empirical proxy for information disadvantage (requires order-flow data).
15. **Paseda, O. A. (2025). Game theory applications in finance: a review of literature. J. Capital Markets Studies.** doi:10.1108/JCMS-04-2025-0044. [V, T1] — Recent survey. *Venue quality not assessed.*
16. **Zinkevich, M., Johanson, M., Bowling, M., & Piccione, C. (2007). Regret minimization in games with incomplete information.** doi:10.7939/R3Q23R282 (University of Alberta technical-report record; NeurIPS version not re-verified). [V] — CFR.
17. **Brown, N., & Sandholm, T. (2018). Superhuman AI for heads-up no-limit poker: Libratus beats top professionals. Science.** doi:10.1126/science.aao1733. [V, T1]
18. **Moravčík, M., et al. (2017). DeepStack: Expert-level artificial intelligence in heads-up no-limit poker. Science.** doi:10.1126/science.aam6960. [V (title), T1]
19. **Brown, N., & Sandholm, T. (2019). Superhuman AI for multiplayer poker. Science.** doi:10.1126/science.aay2400. [V, T1]
20. **Vadori, N., Ardon, L., Ganesh, S., Spooner, T., et al. (2023). Towards multi-agent reinforcement learning-driven over-the-counter market simulations. Mathematical Finance.** doi:10.1111/mafi.12416; arXiv:2210.07184. [V, T1]
21. **Mascioli, C., Gu, A., Wang, Y., Chakraborty, M., et al. (2024). A financial market simulation environment for trading agents using deep reinforcement learning. ICAIF '24.** doi:10.1145/3677052.3698639. [V, T1] — *20–21: simulators in which an informed-trader mechanism could be tested.*

### Theme C — "Other holders' cost" factors and factor timing (candidate Z variables, A-share evidence)

22. **Grinblatt, M., & Han, B. (2005). Prospect theory, mental accounting, and momentum. J. Financial Economics.** doi:10.1016/j.jfineco.2004.10.006. [V, T1] — Capital gains overhang (aggregate holders' cost basis from turnover-weighted past prices) — the academic counterpart of the "chip / holding-cost" factor in `idea.md`.
23. **Shefrin, H., & Statman, M. (1985). The disposition to sell winners too early and ride losers too long. J. Finance.** doi:10.1111/j.1540-6261.1985.tb05002.x. [V, T1]
24. **Pan, Y., Fan, R., & Zhang, G. (2025). Overreaction, investor anxiety, and anomalies in the A-share disposition effect. J. Economics, Business and Management.** doi:10.18178/joebm.2025.13.3.877. [V, T1; venue quality not assessed] — A-share data 2010–2022; reports that capital gains relate *negatively* to cross-sectional returns, contrary to earlier studies.
25. **Ma, T., Liao, C., & Jiang, F. (2022/2023). Timing the factor zoo via deep learning: Evidence from China. Accounting & Finance.** doi:10.1111/acfi.13033. [V, T1; abstract not available]
26. **Gu, S., Kelly, B., & Xiu, D. (2020). Empirical asset pricing via machine learning. Review of Financial Studies.** doi:10.1093/rfs/hhaa009. [V, T1] — Standard ML multi-factor baseline reference.

### Theme D — Bet sizing and risk-sensitive RL

27. **Kelly, J. L. (1956). A new interpretation of information rate. Bell System Technical Journal.** doi:10.1002/j.1538-7305.1956.tb03809.x. [V, T1]
28. **Yang, H., Liu, X.-Y., Zhong, S., & Walid, A. (2020). Deep reinforcement learning for automated stock trading: An ensemble strategy. ICAIF '20.** doi:10.1145/3383455.3422540. [V, T1] — Widely used RL trading baseline (FinRL lineage).
29. **Alameer, A., & Alshehri, K. (2022). On CVaR-based reinforcement learning in quantitative investment.** doi:10.36227/techrxiv.19961525. [V, T2]
30. **Choudhary, H., Orra, A., Thakur, M., Gao, X.-Z., et al. (2026). A CVaR-constrained safe reinforcement learning framework with action repair for practical portfolio optimization. IEEE Trans. Artificial Intelligence.** doi:10.1109/TAI.2026.3686783. [V, T1]

**Unverified leads (not citable until checked by `literature-scout`):** López de Prado's *meta-labeling* (Advances in Financial Machine Learning, 2018) — the practitioner name for "a second model decides whether to act on the primary signal"; fractional-Kelly-under-estimation-error literature (two 2026 SSRN preprints surfaced, titles only: doi:10.2139/ssrn.7549165, doi:10.2139/ssrn.6195358); no-trade regions under transaction costs.

## 3. Synthesis

### 3.1 Literature matrix

| Theme | Abstain / no-trade decision | Explicit game or informed opponent | Formal guarantee | Equities / A-share evidence |
|---|---|---|---|---|
| A. Selective prediction for trading (1–5) | Yes | No | (2) yes, statistical; (1),(4),(5) not stated in abstracts | (1) commodity futures; (4) crypto; (5) simulated only |
| A. Selective / conformal theory (6–9) | Yes | No | Yes (i.i.d. / exchangeable settings) | No (vision / NLP) |
| B. Microstructure & no-trade theory (11–14) | Yes, as an equilibrium outcome | Yes | Yes (equilibrium theorems) | Not a daily retail decision rule |
| B. Poker AI (16–19) | Fold is an action | Yes | Yes (regret / equilibrium) | No finance |
| C. Cost-basis & factor timing (22–26) | No | No (behavioural) | No | Yes, incl. A-shares |
| D. Kelly / risk-sensitive RL (27–30) | Sizing rather than abstain | No | (27) yes | Mixed |

### 3.2 Themes

**Theme 1 — "Abstain when unsure" is already a published trading design.** Chalkidis & Savani (2021) state the idea directly; Hao et al. (2026) and Torres et al. (2026) show it is being re-used in crypto and LLM settings; Zhang et al. (2023) supply a finance-motivated learning theory. *Implication: an abstention layer on top of signals is, by itself, not novel.*

**Theme 2 — The betting analogy has also been drawn, on the ML side.** Deep Gamblers (2019) derives an abstention loss from horse-race gambling / doubling rate. So "poker or gambling thinking → abstention" as a *metaphor* has precedent; what has precedent is statistical, not strategic (no opponent, no information sets).

**Theme 3 — The strategic foundations exist, but in a different layer of finance.** Milgrom–Stokey, Kyle and Glosten–Milgrom formalise why an uninformed party should fear trading; PIN is an empirical proxy. In the sources retrieved here, none of these is used to derive a *learned, daily, per-trade abstention rule on top of factor signals*. This is an observation about this search only (bounded: 27 queries, OpenAlex + arXiv, English), **not** a verified gap.

**Theme 4 — Candidate "game factors" already have academic names.** The user's chip / holding-cost idea corresponds to capital gains overhang (Grinblatt & Han, 2005) and the disposition effect. In the literature these are behavioural return predictors, not measures of adversaries' information.

**Theme 5 — Guarantees available off the shelf assume exchangeability.** Selective-classification and conformal risk control results (6, 8) are i.i.d./exchangeable; Angelopoulos et al. mention distribution-shift extensions (not read). Whether any retrieved finance paper proves selected-risk control under temporal dependence could not be determined from abstracts.

### 3.3 Contradictions / tensions

- **Sign of the cost-basis effect in A-shares.** Grinblatt & Han (2005) associate capital gains overhang with momentum-type predictability (US); Pan et al. (2025) report a *negative* cross-sectional relation in A-shares, "contrary to existing studies" (their abstract). Unresolved here; it means the direction in which a "chip" factor should trigger abstention cannot be assumed.
- **Informed trading: threat or signal?** Microstructure theory (12, 14) treats informed flow as a cost to the uninformed counterparty, while a directional follower may benefit from trading *with* informed flow. The retrieved sources do not settle which applies to a daily long-only entry decision (this tension was also raised in the GPT discussion, thread `research-question`).

### 3.4 Knowledge gaps (candidate, all bounded by the search limitations in §1)

1. A mechanism-derived (rather than purely statistical) abstention rule for equity entry decisions, with a testable restriction that a generic loss predictor would not produce.
2. Selected-trade risk guarantees valid under temporal dependence / drift for trading streams.
3. Evidence on whether cost-basis / turnover-abnormality variables add *incremental* value to an abstention layer beyond calibrated confidence, volatility and liquidity filters — in A-shares, out of sample, at matched coverage.
4. A-share-specific constraints (T+1, price limits, long-only) in selective trading: not addressed in any abstract retrieved.

### 3.5 Synthesis limitations

Abstract-level reading only; one tool (arXiv keyword search) partially failed; no Chinese-language databases; venue quality for (15) and (24) not assessed; several classics verified by DOI/title only. Gap statements are hypotheses for the novelty check, not findings.
