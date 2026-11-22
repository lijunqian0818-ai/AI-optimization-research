contract_role: eic

## Dimension Scores

### D1: methodology_rigor

score: not_assessed

### D2: writing_and_structure

score: warn
trigger: "correctable expository problems such as redundant or excessive length, sections out of logical order, inconsistent terminology or notation, missing signposting, departures from expected conventions for method-focused papers, or isolated phrases whose strength exceeds the stated scope and can be fixed by rewording"

## Review Body

I read the whole submission (Part A, Part B v0.4 including all three revision logs, Part C) as a pre-experiment, registered-report-style protocol and did not penalise the absence of results, abstract or conclusions. I score only D2. Nothing below softens or substitutes for the methodology seat's judgment on D1. This is an unbound call, so I make no venue-alignment claim beyond the general perspective of an applied AI-in-finance readership. I found no text in the manuscript that addresses reviewers or attempts to alter the review.

Overall view. The plan is unusually disciplined about what it will and will not say: non-goals, binding wording per outcome, a standing synthetic-execution qualifier and an explicit confirmatory family are all present, and a qualified reader can determine what is claimed and what would count as support or refutation. That is why D2 is not a block. The warn rests on three things a reader of this readership would stumble on. First, the stated question and hypotheses in Part A promise a four-way attribution of selective-trading gains across named families of existing methods, while Part B confirms only one component (within-batch selection) for two in-house gates and leaves the rest descriptive. Second, Part A, which is declared to govern, has not been brought into line with Part B: it does not contain the second feature group or its confirmatory test. Third, the document never says what the paper contributes under each outcome, although it repeatedly concedes that every confirmatory test may end inconclusive. All three are repairable by rewriting the framing layer, not by redesign. The remaining findings concern length, self-containedness, notation and scope qualifiers.

On the three questions in my card. (1) Novelty and usefulness of the question: the attribution question is a sensible one for this readership given that an abstention layer is prior art, and the plan correctly refuses a "first abstention approach" claim, but the submission contains no positioning text, so newness cannot be judged from it (W10). (2) Publishable finding under every outcome: the wording rules cover every outcome, the contribution statement does not (W3). (3) Proportionality to a single-market, free-data study: mostly well handled inside Part B, with gaps at the level of the hypothesis wording (W1, W5), the feature-group label (W4) and the scope qualifier (W6).

### S1: Outcome wording is fixed in advance, including the outcome against the authors' own hypothesis

**Evidence Anchor**: text: §15.2 "this is reported as a finding against our own hypothesis"

The three-way wording rule (negligible only after a rejected equivalence null, detected only after a rejected difference null, otherwise inconclusive) and the ban on "adds nothing" after a failure to reject are exactly what a reader needs to trust the eventual prose.

### S2: Explicit non-goals bound the framing

**Evidence Anchor**: text: §1 "Poker is motivation only."

The plan disclaims private-information, game-theoretic, first-of-kind and not-losing claims in its scope section, and repeats the interpretation limits where the contrasts are defined.

### S3: The execution-realism qualifier is stated once and enforced everywhere

**Evidence Anchor**: text: §1 "Consequently no claim is made that any backtested order would have filled in the market."

The synthetic-fill wording, the list of phrases that may not be used, and the admission that the fill sensitivity does not measure the gap to real fills keep the backtest claims proportionate to daily-bar data.

### S4: Estimands are separated and the confirmatory family is closed

**Evidence Anchor**: text: §8 "Three different quantities are defined and never interchanged."

One card per test with estimand, comparator, null, statistic and labels is the right convention for a method-focused protocol and is easy to follow.

### S5: The status and novelty of the theory are reported candidly

**Evidence Anchor**: text: §15.1 "Theorem 1 is, per the internal audit, essentially a corollary of known results"

The header and threats section state review status per result, refuse the word "theorem", and assign the monitoring result an appendix-level role.

### S6: Experiment-to-claim map

**Evidence Anchor**: table: §12 experiment-to-claim map

Each experiment is tied to a hypothesis, to the theory item it uses or to "empirical only", and to its dependencies, which lets a reader trace any planned claim to its source.

### W1: The stated question promises a four-way attribution, the confirmatory design answers one component

**Severity**: Major

**Evidence Anchor**: text: §8.4 "Nothing else is confirmatory: not Q-total, not the aggregate composition term" and §8.3 "by construction this statistic gives no credit for avoiding whole days"

**Confidence**: 4 — backtest-methodology and empirical asset-pricing background; reading of claims against tests, not of estimator validity

Part A asks where the apparent improvement comes from (selection, timing, exposure, cost) and H-A asserts that most of it is reproduced by exposure- and cost-aware comparators. Part B's confirmatory cards C1 and C2 test only whether within-batch selection is within a per-order bound. The existence of an apparent improvement (Q-total), the exposure-schedule, timing and cost terms, and any statement about "most of" the improvement are all descriptive, with unadjusted intervals and convention-dependent splits. A rejected equivalence null in C1 or C2 therefore supports "within-batch selection is negligible for this gate", not "the gain is mostly exposure and cost". The plan nowhere states this mapping in one place, so a reader of Part A will expect a stronger result than the design can deliver. Minimum remedy: restate H-A as the within-batch-selection claim it is tested as, state that the remaining three sources are estimated descriptively, and add a short table mapping each clause of the research question to its estimand and its evidential status. A stronger, costlier option that is the authors' choice: pre-specify an interval statement for at least the exposure-schedule share so the "where from" question has more than one inferential leg.

### W2: Part A, declared governing, is not synchronised with Part B

**Severity**: Major

**Evidence Anchor**: text: §1 "pending user confirmation at Gate 2; free data only, per the user's decision relayed by the lead on 2026-11-15"

**Confidence**: 5 — direct comparison of the two parts of the submission

Part A states that its v3 section governs. Its research question and H-Z name one group, holder-state variables, and its wording constraint fixes how that group is to be called. Part B adds a second group (other participants' disclosed actions), gives it its own confirmatory test C4 and enlarges the Holm family to four, on a "pending confirmation" basis. Part A also still lists as primary indicators net portfolio performance, loss magnitude, turnover and the return of abstained trades, while Part B's confirmatory statistic is the per-order selection statistic and those indicators are descriptive. H-T is still worded in Part A as a candidate theorem while Part B gives it a limits-of-evidence appendix role, and H-M is on hold. A protocol in which the hypothesis document and the analysis plan disagree on the number of hypotheses, the confirmatory family and the primary metric is not ready to be frozen or cited. Remedy: issue a revised Part A (question, hypotheses H-A, H-Z for each group, the role of H-T, the status of H-M, primary statistic) that matches Part B, or remove C4 from the confirmatory family until the governing document includes it.

### W3: No statement of what the paper contributes under each outcome

**Severity**: Major

**Evidence Anchor**: absence: Part A v3 section and Part B §1 and §15.2 — expected a statement of the paper's contribution under each outcome class (equivalence shown, hypothesis contradicted, inconclusive, tests replaced by estimation); checked Part A v3 section, Part B §1, §9.3, §10.1, §10.2, §15.2, §16.1 item 10

**Confidence**: 4 — programme-committee experience with negative-result and protocol papers

The plan fixes how each outcome will be worded but not what the reader learns in each case. It concedes that every test may end inconclusive, that the power pre-check may show this before the hold-out is opened, that the hold-out may then be reported as estimation without verdicts, that the monitoring interval is too wide to compare methods, and that the theory is close to known results. With the illustrative requirement of a standard error near 1.7 bps per order for an informative equivalence test left unverified, the inconclusive branch is a live possibility, and under it the document does not say what remains: the attribution protocol itself, the complete-null check of a selective-trading pipeline, the accounting and reconciliation machinery, or the descriptive decomposition. Readers of this type of venue will ask this first. Remedy: add a contributions paragraph and a short outcome-by-contribution table, stating plainly which contributions are methodological and survive any empirical outcome and which depend on the tests being informative. No result values are needed for this.

### W4: The label "identifiable participants" is stronger than the features

**Severity**: Minor

**Evidence Anchor**: text: §5.6 "observable actions of other identifiable participants (new; pending user confirmation at Gate 2)" and §5.6.1 "seat-level detail (not fetched)"

**Confidence**: 4 — familiarity with A-share disclosure data at the level of what such tables contain

The group is built from stock-day aggregates of disclosed events: indicators, days since the last event, and scaled net amounts. Names are excluded from features by design, seat-level detail is not fetched, and the plan itself notes that block-trade counterparties are mostly an anonymous institutional label. The features therefore record that a disclosure-triggering event occurred and its aggregate size, not who acted. The interpretation rules already disclaim private-information and game readings, so the problem is the name and the residue of "opponent action" in file names and item codes, which a reader will take as a promise of participant-level behaviour. A plainer name such as "public disclosure-event variables" would match what the tests can show. The control set for listing triggers should be mentioned next to the name wherever the group is introduced.

### W5: H-A names method families that the confirmatory tests do not cover

**Severity**: Minor

**Evidence Anchor**: text: §9.3 "PERF and TREND (no within-batch selection by construction): Q-total and exposure-schedule terms only."

**Confidence**: 4 — reading of hypothesis wording against the test cards

H-A in Part A speaks of existing abstention methods and lists confidence filtering, matured-performance gating and generic loss prediction. The matured-performance gate has no within-batch statistic and receives no confirmatory verdict; the two gates that do are the authors' own implementations in one pipeline; published selective-prediction methods are postponed to an optional second round. The hypothesis should be reworded to "the two gates as implemented here", with the performance gate described as assessed descriptively only.

### W6: Binding wording lacks a market, period and signal-family qualifier

**Severity**: Minor

**Evidence Anchor**: text: §15.1 "One market, one frequency, long-only, one family of base signals."

**Confidence**: 4 — emerging-market backtest reviewing experience

The generalisation limit is listed as a threat, and the single realised history is acknowledged, but the binding sentences of §9.3 and §15.2 require only the synthetic-execution qualifier. A verdict from one hold-out of about four and a half years on CSI 300 and CSI 500 members with one price-volume base signal should carry that scope in the verdict sentence itself. Add the qualifier to the pre-fixed wording.

### W7: Key definitions are governed by documents not included in the submission

**Severity**: Minor

**Evidence Anchor**: text: §3.8 "The text of I-§3 governs; the summary below is for orientation."

**Confidence**: 4 — reading for self-containedness

The label tree, the synthetic fill rule, the order-policy checklist and the statements and constants of Theorem 1, its corollaries and Lemma 3 are cited by pointer to an instantiation file and a theorems file that are not part of what was submitted. The summaries are adequate for following the experiments, and the confirmatory cards use no theory result, so the core is not affected, but a method-focused paper must state its own definitions. The paper version needs the statements it relies on reproduced in an appendix.

### W8: Length is inflated by three stacked revision logs that contain superseded statements

**Severity**: Minor

**Evidence Anchor**: text: Revision log v0.4 "old revision logs below were left as historical record and still contain superseded statements"

**Confidence**: 5 — direct observation

Roughly a quarter of Part B is revision history, and the two older logs describe conventions that the current text has withdrawn (a close-marked label, a different sleeve count, a six-test family). Reviewer-item codes from earlier rounds are used as signposts in section headings without being defined in this document. Move the logs to a separate change record and keep one current plan.

### W9: Symbols and codes are overloaded

**Severity**: Minor

**Evidence Anchor**: text: §2.4 A24 "If U + M are not rare the label is driven by a convention"

**Confidence**: 4 — direct observation; notation only, not the mathematics

U denotes both a label outcome class and the numbered user parameters; P1 to P5 are metrics, P1 to P4 are price branches and P1 to P12 are review items; R is a control set and R1 to R4 are reconciliation tests; OA prefixes both the disclosure-data audit items and an availability assumption; d is a monitoring lag and also the purge gap. A one-page symbol and code table with unique prefixes would remove the back-tracking this causes.

### W10: No positioning against prior work in the submission

**Severity**: Minor

**Evidence Anchor**: absence: Parts A, B and C — expected a short positioning passage naming the closest prior work and how the attribution question differs from it; checked Part A v3 section, Part B header, §1, §6.2, §15.1, §16.2 item 6

**Confidence**: 3 — I can judge that the passage is missing, not what the external positioning file contains

Positioning is delegated to an external file, citations appear as keys only, and the evidence base for the second feature group is stated to be abstract-level reading. Whether the question is new to this readership cannot be assessed from the submission. This is expected of a plan at this stage but must be supplied before the framing is frozen.

### W11: Minor ordering and reference problems

**Severity**: Minor

**Evidence Anchor**: text: §5 "5.2a Implementation details of §5.1–5.2 that must be fixed before coding (P12)"

**Confidence**: 5 — direct observation

Subsection 5.2a follows 5.3; Part A opens by voiding conflicting text "above" that is not in the submission; Part A is in Chinese while Parts B and C are in English; the half-width table of §9.4 precedes the definition of its comparators in §12.1. These are editing matters.
