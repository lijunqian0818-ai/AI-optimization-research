# Screening protocol: title/abstract stage
Version 1.0, confirmed by the user on 2026-11-15. Source: `literature/screening_criteria.md` (draft v0) and `00_idea/research_question.md` (v2 section).

Review (narrative / integrative review for a research paper's related-work and novelty check; not a PRISMA systematic review): "Poker-style abstention for equity trading".
Question: Which prior work bears on adding a "trade / abstain" decision layer on top of multi-factor stock signals — motivated by imperfect-information-game (poker) reasoning about being at an information disadvantage — to reduce the loss probability and downside risk of executed trades, with China A-share daily trading as the application?

Note on the records: many records have no abstract. The "abstract" field is a one-line note written by the search agent (often in Chinese), sometimes from bibliographic metadata only. Treat it as a hint about content, not as the paper's abstract. The keyword field holds the search direction (1–8) the record was found under; it is not evidence of eligibility.

## Eligibility
A record is eligible if it meets at least one topic condition AND the general conditions.

Topic conditions:
- T1. Imperfect-information-game models or algorithms (poker, counterfactual regret minimization, Bayesian games, market-microstructure games such as Kyle or Glosten–Milgrom, bluffing / strategic informed trading) applied to financial trading decisions.
- T2. "Selective action" in trading or financial prediction: selective prediction / classification, reject option, abstention, learning to defer, meta-labeling, conformal prediction or conformal risk control, no-trade regions, optimal stopping for trade timing. General (non-financial) theory papers on selective prediction, reject option or conformal risk control are also eligible, because they supply candidate theorems.
- T3. Reinforcement learning for trading or portfolio management that involves risk constraints, downside or tail risk, opponent / multi-agent modelling, or dynamic adjustment of factor weights.
- T4. Dynamic weighting or timing of factors in multi-factor equity models (including machine-learning methods), especially with China A-share evidence.
- T5. Factors describing the state of other market participants: holders' cost basis / capital gains overhang, "chip distribution", disposition effect, crowding, probability of informed trading and similar adverse-selection proxies.
- T6. Bet sizing under uncertainty: Kelly criterion, fractional Kelly, position sizing with estimation error.
- T7. Foundational works for any of the above regardless of year (for example Kyle 1985, Glosten–Milgrom 1985, Milgrom–Stokey 1982, Kelly 1956, Chow 1970, CFR 2007, Libratus, Pluribus, DeepStack).

General conditions:
- Published 2010 or later, unless foundational (T7).
- A scholarly source: peer-reviewed paper, arXiv / SSRN preprint, thesis, or scholarly book.
- English or Chinese.

Full-text-only criteria (quality of the experiments, whether the claimed guarantee actually holds, whether a free full text exists) must NOT be used to exclude at this stage.

## "Decision or risk-control component" (interpret broadly at screening)
Counts: any rule that decides whether, when or how much to trade; abstention or filtering of signals; position sizing; risk constraints; a strategic model of other traders.
Does not count on its own: a model that only forecasts prices or returns and reports forecast accuracy.
Exception, treat as unclear: a forecasting paper whose title suggests uncertainty, confidence or calibration is used to decide when to act.

## Decisions
- "include" (code INC): at least one topic condition T1–T7 is clearly met on the title and note, and no exclusion code clearly applies.
- "unclear" (code UNC): a topic condition is plausibly met but the title and note are insufficient, for example: (a) a title-only record whose title suggests trading with abstention, game-theoretic trading, or a cost-basis factor; (b) a reinforcement-learning trading paper where it is not stated whether risk or other agents are modelled; (c) a forecasting paper that may use uncertainty to gate trades.
- "exclude": give ONE code, the first criterion that clearly fails, checked in this order:
  - E1 source type: blog post, marketing material, strategy "sharing" without a method, or opinion piece with neither experiments nor theory.
  - E2 off topic: clearly meets none of T1–T7.
  - E3 prediction only: forecasts prices or returns with no decision or risk-control component, and is not presented as a standard baseline for multi-factor equity prediction.
  - E4 poker engineering: poker or game-AI engineering with no link to finance or to general decision theory, and not foundational.
  - E5 high-frequency engineering: order-book or market-making implementation work whose content is specific to high-frequency execution and gives no model of informed trading or adverse selection.
  - E6 crypto only: cryptocurrency-specific work whose method clearly cannot transfer to equities.
  - E7 date: published before 2010 and not foundational.
  - E9 other reason (explain).

## Principles
- Sensitive: missing a closely related paper is worse than an extra full-text check; when in doubt, "unclear".
- Decisive: "unclear" only when a topic condition T1–T7 is plausibly met.
- Judge content, not language, venue prestige, or citation count.
- Judge only the text of the record. Do not use recalled knowledge of the paper.

## Boundary cases (synthetic)
1. TI: "Selective classification for commodity futures trading". Note: classifier abstains, strategy holds no position. Expected: include (INC), T2.
2. TI: "Deep reinforcement learning for stock trading". Note: none. Expected: unclear (UNC); RL trading, risk or multi-agent content not stated.
3. TI: "LSTM stock price forecasting with attention". Note: reports RMSE only. Expected: exclude E3.
4. TI: "A faster abstraction algorithm for no-limit hold'em solvers". Note: poker solver speed-up. Expected: exclude E4.
5. TI: "On optimum recognition error and reject tradeoff" (1970). Expected: include (INC), T7 foundational for T2.
6. TI: "Capital gains overhang and momentum in Chinese stocks". Note: title only. Expected: include (INC), T5.

## Amendment log
| Date | Change | Reason | Records to re-screen |
|------|--------|--------|----------------------|
