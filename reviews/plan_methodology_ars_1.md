> **Provenance note (lead, 2026-11-15).** ARS `academic-paper-reviewer` · `methodology-focus`, two-seat panel (Journal-Fit Reviewer `eic` + Methodology `methodology`), run under the v3.6.2 two-phase sprint contract. Reviewed object: `reviews/ars_work/manuscript.md` = research question v3 + `experiments/PLAN.md` v0.4 + `theory/setup.md` (a pre-experiment design; no results exist). Machine checks: contract valid (Schema 13.2; SC-12 warning: single-judge mandatory dimension); Phase 1 conformance PASS ×2; Phase 2 conformance PASS ×2; panel synthesis PASS. Both seats and the synthesizer are Claude subagents (same model family as the lead), in fresh contexts without access to each other's output — **role-separated, not independent, and not a cross-model review**. Reviewer cards accepted by the user before Phase 1. Raw cards: `reviews/ars_work/*_phase1_output.md`, `*_phase2_output.md`. Calibration: NOT_CALIBRATED.

# Editorial Decision Package

## Calibration Resolution

`calibration_status: NOT_CALIBRATED`

No closed calibration profile or replay validator is bound to this panel. Seat-level confidence numbers are self-reported scope disclosures and carry no weight in the decision.

## Panel Composition and Scope

- **Mode**: `reviewer_methodology_focus`, contract `reviewer/reviewer_methodology_focus/v2`, `panel_size` 2.
- **Seats**: `eic` (scores D2 writing_and_structure only) and `methodology` (scores D1 methodology_rigor only). No Devil's Advocate, Reviewer 2 or Reviewer 3 seat exists in this mode.
- **Execution provenance**: both seats ran on the same model family, in fresh contexts, with no access to each other's output. They are role-separated; they are not independent reviewers, and correlated errors between them cannot be excluded. No cross-model check was run on this synthesis.
- **Criteria binding**: `criteria_binding_unavailable` (unbound review). Both cards state that they make no venue-alignment claim; this letter makes none.
- **Reviewed object**: a pre-experiment research design (research question, experiment plan v0.4, abstract theoretical setup). No results exist; neither seat penalised their absence. Neither seat reviewed the mathematical proofs.
- **Integrity**: both seats report finding no text in the submission addressed to reviewers.
- **Citation convention**: seat findings are cited as `EIC-W<n>` (eic card) and `R1-W<n>` (methodology card), always with the `-W` suffix. Bare `R<n>` and `S<n>` are roadmap transport references, not seat names and not a work rank.

## Sprint Contract Audit (mechanical)

Step 1, role-scoped matrix. D1 (eligible: methodology): methodology = block, block_class repairable; eic = not_assessed (ineligible, excluded). D2 (eligible: eic): eic = warn; methodology = not_assessed (ineligible, excluded).

Step 2, failure conditions.

| Condition | Expression | Quantifier | Fired |
|---|---|---|---|
| F1 | D1 has a fatal block | any | false (block is repairable) |
| F2 | D1 scores 'block' | any | true |
| F3 | D1 scores 'warn' | any | false (score is block, not warn) |
| F4 | D2 scores 'warn' or worse | any | true |
| F0 | every dimension scores 'pass' | all | false |

Step 3, precedence. Fired: F2 (severity 90) and F4 (severity 40). F2 has the highest severity; its action governs.

dimension_verdicts: [D1=block, D2=warn]
fired_conditions: [F2, F4]
da_critical_adjudications: []
editorial_decision=major_revision

---

## Part 1: Editorial Decision Letter

Dear Authors,

Thank you for submitting your pre-experiment research design (research question v3, experiment plan v0.4, abstract theoretical setup). It was reviewed through 2 role-separated review seats: an editor seat for exposition and structure, and a methodology seat for design rigor. Their execution provenance is stated above and is not reduced to an independence claim.

### Decision: Major Revision

The decision is the mechanical outcome of the sprint contract (condition F2: the methodology dimension scored a repairable block). Because nothing has been run, every required item below is a change to the plan text or a pre-freeze check; none requires redesign of the study architecture.

### Consensus Analysis

With two seats and disjoint scoring dimensions, the 4-reviewer consensus labels (CONSENSUS-4, CONSENSUS-3) cannot be assigned and are not used. Findings are classified as corroborated (both seats) or single-seat.

#### Points of Agreement

- **Corroborated theme, Part A is not aligned with Part B.** EIC-W2 (Major): the governing Part A lacks the second feature group and its test C4, lists different primary indicators, and carries stale wording for H-T and H-M. R1-W12 (Minor): Part A still describes the selection comparator as matched entries and invested capital, which Part B does not equalise. The two seats cite different instances of the same defect; each instance is single-seat, the theme is raised by both. The severities attach to different sub-claims and do not conflict.
- **Corroborated premise, an inconclusive outcome for C1 and C2 is a live possibility.** R1-W3 argues from an indicative variance calculation (the seat labels it its own assumption, not a result); EIC-W3 notes the unverified 1.7 bps standard-error requirement. The seats draw different, compatible consequences: a design-stage power statement (R1-W3) and a statement of what the paper contributes under each outcome (EIC-W3).
- **Adjacent findings, H-A is worded about existing abstention methods while the tested gates are two in-house implementations.** EIC-W5 treats this as a hypothesis-wording issue (Minor); R1-W4 raises it as one of three reasons the equivalence verdict may lack assay sensitivity (Major parent). Remedies are compatible (reword H-A; report attainable-range benchmarks).
- **Shared strengths.** Both seats credit the separation of three estimands with one card per confirmatory test (EIC-S4, R1-S1) and the pre-fixed outcome wording that reserves "negligible" for a rejected equivalence null (EIC-S1, R1-S3).

#### Points of Disagreement

None. No finding of one seat is disputed by the other, in existence, remedy or severity of the same sub-claim. All remaining findings are single-seat findings on which the other seat is silent; silence is not counted as agreement or opposition.

### Decision Rationale

The methodology seat scored D1 as a repairable block resting on the joint impact of five Major findings on the four primary tests C1 to C4; it states that none is rejection-level alone. First, the dependence-preserving null world retains the base score, so the values it declares true are not true by construction (R1-W1), and no simulated world represents the realistic null of C3 and C4, in which both gates are informative and only the added feature group is not (R1-W2). The advertised false-positive protection therefore rests on the world the plan itself calls possibly favourable. Second, the two equivalence tests that carry H-A have no demonstrated attainable power (R1-W3) and a margin not anchored to the attainable scale of the statistic (R1-W4). Third, the announcement dates behind C4 are validated only by an unsigned match rate, which cannot detect the early-dating error that would bias C4 toward a positive finding (R1-W5).

The editor seat scored D2 as warn on three Major framing findings: the question promises a four-way attribution while one component is confirmatory (EIC-W1), the governing Part A is out of step with Part B (EIC-W2), and no contribution is stated per outcome (EIC-W3). This fires F4, which is outranked by F2.

A stricter decision is not available: the block is declared repairable, so F1 does not fire. A milder one is not available either: the contract permits no qualitative override of a fired condition. The seats do not conflict, so no arbitration was needed. The methodology seat also records that the three earlier critical points are resolved at design level, with residues captured in R1-W6, R1-W9 and R1-W12.

### Blocking Issues (0-3, immutable source order)

| Transport ref | Blocking issue | Source reviewer(s) | Evidence anchor | Resolving roadmap item |
|---|---|---|---|---|
| R4, R5 | The mandatory null simulation does not instantiate the nulls of C2 to C4: one world keeps the base score, and no world has informative gates with only the Z group nulled | methodology (R1-W1, R1-W2) | text: §10.2 W-swap "all −Z, Z_H and Z_O features except the base score"; absence: §10.2 Null worlds | R4, R5 |
| R6, R7 | The equivalence tests carrying H-A have no shown attainable power and a margin not anchored to the attainable scale of the statistic | methodology (R1-W3, R1-W4) | text: §10.1 "The actual standard error is UNVERIFIED."; text: §8.3 "such days carry no selection information and are counted" | R6, R7 |
| R8 | Point-in-time validity of the Z_O announcement dates is checked only by an unsigned match rate on a small sample | methodology (R1-W5) | text: §2.4 OA6 "back-filling before it ... cannot be detected from free data" | R8 |

---

## Part 2: Revision Roadmap

Items are in immutable source order: seat order eic, then methodology; within a seat, the card's weakness order. Order carries no priority. Severity, evidence anchor and confidence are transported from the cards unchanged. Exact `proposed_targets[]` block ids are not given: no block manifest was bound to this run.

### Step 1b Sub-Claim Inventory

| sub_claim_id | parent_weakness | eic position | methodology position | Classification |
|---|---|---|---|---|
| SC-1 | EIC-W1 question vs confirmatory coverage | raised | not-mentioned | single-seat |
| SC-2a | EIC-W2 Part A lacks second feature group, C4, four-test family | raised | not-mentioned | single-seat |
| SC-2b | EIC-W2 Part A primary indicators differ from Part B statistic | raised | not-mentioned | single-seat |
| SC-2c | EIC-W2 stale status of H-T and H-M in Part A | raised | not-mentioned | single-seat |
| SC-3 | EIC-W3 no contribution statement per outcome | raised | not-mentioned (premise corroborated by R1-W3) | single-seat |
| SC-4 | EIC-W4 label "identifiable participants" | raised | not-mentioned | single-seat |
| SC-5 | EIC-W5 H-A names untested method families | raised | not-mentioned (adjacent: SC-15c) | single-seat |
| SC-6 | EIC-W6 scope qualifier missing from binding wording | raised | not-mentioned | single-seat |
| SC-7 | EIC-W7 definitions governed by files not submitted | raised | not-mentioned | single-seat |
| SC-8 | EIC-W8 stacked revision logs with superseded statements | raised | not-mentioned | single-seat |
| SC-9 | EIC-W9 overloaded symbols and codes | raised | not-mentioned | single-seat |
| SC-10 | EIC-W10 no positioning text | raised | not-mentioned | single-seat |
| SC-11 | EIC-W11 ordering and reference problems | raised | not-mentioned | single-seat |
| SC-12 | R1-W1 W-swap keeps base score | not-mentioned | raised | single-seat |
| SC-13 | R1-W2 no world with informative reference gate | not-mentioned | raised | single-seat |
| SC-14a | R1-W3 attainable equivalence power not shown | not-mentioned (unverified SE noted in EIC-W3) | raised | single-seat |
| SC-14b | R1-W3 confirmatory-vs-estimation choice made after seeing development estimates; vague threshold | not-mentioned | raised | single-seat |
| SC-15a | R1-W4 zero-choice orders dilute the statistic | not-mentioned | raised | single-seat |
| SC-15b | R1-W4 cost-anchored margin rationale does not fit a difference statistic | not-mentioned | raised | single-seat |
| SC-15c | R1-W4 weakly tuned in-house gates make equivalence easier | not-mentioned (adjacent: SC-5) | raised | single-seat |
| SC-16a | R1-W5 unsigned match rate for announcement dates | not-mentioned | raised | single-seat |
| SC-16b | R1-W5 single-snapshot limits on index membership and ST status | not-mentioned | raised | single-seat |
| SC-17 | R1-W6 simulation uses one seed, test uses five-seed average | not-mentioned | raised | single-seat |
| SC-18 | R1-W7 no stopping rule for revise-and-repeat | not-mentioned | raised | single-seat |
| SC-19 | R1-W8 hyper-parameters frozen on one or two years of data | not-mentioned | raised | single-seat |
| SC-20 | R1-W9 uncontrolled fourth verdict in §15.2 | not-mentioned | raised | single-seat |
| SC-21 | R1-W10 training label of unfilled orders undefined | not-mentioned | raised | single-seat |
| SC-22 | R1-W11 truncated outcomes at end of hold-out | not-mentioned | raised | single-seat |
| SC-23 | R1-W12 Part A comparator wording | not-mentioned (same theme as SC-2a to SC-2c) | raised | single-seat; theme corroborated |
| SC-24a | R1-W13 planning script outside repository | not-mentioned | raised | single-seat |
| SC-24b | R1-W13 freeze attested only in an editable internal file | not-mentioned | raised | single-seat |

### Required Revisions (Must Fix)

| Transport ref | Revision Item | Sub-Claim(s) | Severity | Evidence Anchor | Confidence | Source | Obligation class | Cost scope | Bounded consequence |
|---|---|---|---|---|---|---|---|---|---|
| R1 | Restate H-A as the within-batch-selection claim it is tested as; state that the other three sources are descriptive; add a table mapping each clause of the question to its estimand and evidential status | SC-1 | major | text: §8.4 "Nothing else is confirmatory: not Q-total, not the aggregate composition term" | 4 — backtest methodology; claims against tests | EIC-W1 | must_fix | section: Part A question and H-A; Part B §8.4 | claim_scope_unsupported; claim: H-A |
| R2 | Issue a revised Part A matching Part B (hypotheses, confirmatory family, primary statistic, role of H-T, status of H-M), or remove C4 from the confirmatory family until Part A includes it | SC-2a, SC-2b, SC-2c | major | text: §1 "pending user confirmation at Gate 2; free data only, per the user's decision relayed by the lead on 2026-11-15" | 5 — direct comparison of the two parts | EIC-W2 | must_fix | section: Part A v3 | editorial_conformance_unmet; section: Part A |
| R3 | Add a contributions paragraph and an outcome-by-contribution table separating contributions that survive any outcome from those that need informative tests | SC-3 | major | absence: Part A v3 section and Part B §1 and §15.2, statement of contribution under each outcome class | 4 — programme-committee experience with protocol papers | EIC-W3 | must_fix | section: Part A; Part B §1, §15.2 | interpretive_ambiguity_remains; manuscript: contribution statement |
| R4 | In W-swap, swap the base score as seen by the gate together with the other features (real score kept only for nominations and strata), or restate that world's true values and remove it from the pass criterion for the affected cards | SC-12 | major | text: §10.2 W-swap "all −Z, Z_H and Z_O features except the base score" | 4 — calibration simulations for selection statistics | R1-W1 | must_fix | section: Part B §10.2 | evidence_gap_remains; claim: size control of C2 to C4 |
| R5 | Add a mandatory null world with the −Z panel real and the Z columns permuted within day (within day and class for Z_O), re-drawn per replication, and include it in the pass criterion for C3 and C4 | SC-13 | major | absence: §10.2 Null worlds, a world nulling only the Z_H or Z_O columns | 4 — size calibration of paired difference tests | R1-W2 | must_fix | section: Part B §10.2, §12 | evidence_gap_remains; claim: size control of C3 and C4 |
| R6 | Put a design-stage variance calculation into the plan, state the smallest bound at which 80% power is plausible, and decide before any development outcome whether C1 and C2 are confirmatory tests or pre-declared estimation targets | SC-14a, SC-14b | major | text: §10.1 "The actual standard error is UNVERIFIED." | 3 — order-of-magnitude reasoning under the seat's own assumptions, no data | R1-W3 | must_fix | re_analysis: Part B §10.1 | acceptance_criterion_unmet; claim: H-A via C1 and C2 |
| R7 | Pre-specify and report beside C1 and C2 the share of orders with a real within-stratum choice and the statistic for a perfect-foresight gate and for SCORE under the same strata and coverage; justify the bound against that range or by the investor-anchored rule alone | SC-15a, SC-15b, SC-15c | major | text: §8.3 "such days carry no selection information and are counted" | 4 — equivalence and non-inferiority test design | R1-W4 | must_fix | section: Part B §8.3, §9.3 | interpretive_ambiguity_remains; claim: negligible-effect verdict |
| R8 | Make the date audit signed (share of sampled records dated before the original announcement, with an upper confidence limit, checked against the announcement document), set a pass limit, and pre-specify that a failing class leaves the confirmatory feature group | SC-16a, SC-16b | major | text: §2.4 OA6 "back-filling before it (the share-change table carries entry timestamps of 2019 for records of the 1990s) cannot be detected from free data" | 4 — point-in-time data and disclosure-timing leakage | R1-W5 | must_fix | new_data: Part B §2.4 OA5, OA6 | evidence_gap_remains; dataset: Z_O announcement dates |

### Required Item Details

**R1: Align the stated question with what is confirmed**
- **Problem**: Part A promises a four-way attribution and H-A speaks of "most of" the gain; only within-batch selection is confirmatory.
- **Source**: EIC-W1.
- **Requirement**: Minimum remedy as in the table. The seat names a costlier option that is the authors' choice: a pre-specified interval statement for the exposure-schedule share.
- **Acceptance criteria**: H-A reads as a within-batch-selection claim and a clause-to-estimand table with evidential status is present.

**R2: Synchronise Part A with Part B**
- **Problem**: The governing document and the analysis plan disagree on the number of hypotheses, the confirmatory family and the primary metric.
- **Source**: EIC-W2; same theme in R1-W12 (see S16).
- **Requirement**: Revise Part A, or withdraw C4 from the confirmatory family.
- **Acceptance criteria**: Part A and Part B state the same hypotheses, confirmatory family and primary statistic.

**R3: State the contribution under each outcome**
- **Problem**: Outcome wording is fixed, but what the reader learns under an inconclusive or estimation-only outcome is not stated.
- **Source**: EIC-W3; premise corroborated by R1-W3.
- **Requirement**: Contributions paragraph plus outcome-by-contribution table; no result values needed.
- **Acceptance criteria**: every outcome class (equivalence shown, hypothesis contradicted, inconclusive, estimation only) has a stated contribution.

**R4: Repair the dependence-preserving null world**
- **Problem**: The gate can still learn from the retained base score, so the declared zero values are not true by construction, and the boundary version does not sit on the boundary for C2.
- **Source**: R1-W1.
- **Requirement**: Minimum remedy as in the table. Stronger option named by the seat: estimate that world's true values by a large independent run and centre the tests on them.
- **Acceptance criteria**: every world in the pass criterion has true values that hold by construction or are estimated and stated.

**R5: Add the realistic null for C3 and C4**
- **Problem**: In both simulated worlds neither gate is informative, so the paired-difference inference is checked on a configuration other than the one tested.
- **Source**: R1-W2.
- **Requirement**: As in the table.
- **Acceptance criteria**: the mandatory simulation and its pass rule include a world with real −Z features and permuted Z columns.

**R6: Show attainable power before the freeze**
- **Problem**: The required standard error is unverified; the seat's indicative arithmetic (its own assumption) suggests equivalence at the proposed bound may be out of reach; the fallback decision is made after development estimates are seen under a vague threshold.
- **Source**: R1-W3 (confidence 3).
- **Requirement**: As in the table. Stronger option named by the seat, with a scope cost: a longer confirmatory window or a larger nominated list.
- **Acceptance criteria**: the plan contains a design-stage variance calculation and a status for C1 and C2 fixed before any development outcome.

**R7: Anchor the equivalence margin and show assay sensitivity**
- **Problem**: Zero-choice orders dilute the statistic, the cost-based rationale does not define a tolerance for a difference statistic, and thinly tuned gates make equivalence easier.
- **Source**: R1-W4; adjacent wording point in EIC-W5 (see S2).
- **Requirement**: As in the table. Stronger option named by the seat: define the confirmatory statistic on informative orders only.
- **Acceptance criteria**: the informative-order share and the perfect-foresight and SCORE benchmarks are pre-specified reporting items and the bound is justified against them.

**R8: Signed audit of announcement dates**
- **Problem**: A match rate cannot separate late dating from early dating; early dating biases C4 toward a detected difference.
- **Source**: R1-W5.
- **Requirement**: As in the table. Stronger option named by the seat: a confirmatory-grade sensitivity of C4 without the share-change class or with a longer lag.
- **Acceptance criteria**: a signed audit criterion with a pass limit and a pre-specified exclusion rule is in the plan.

### Suggested Revisions (Should Fix)

| Transport ref | Revision Item | Sub-Claim(s) | Severity | Evidence Anchor | Confidence | Source | Obligation class | Cost scope | Bounded consequence |
|---|---|---|---|---|---|---|---|---|---|
| S1 | Rename the second feature group (for example "public disclosure-event variables"), remove "opponent action" residue, mention the listing-trigger control set beside the name | SC-4 | minor | text: §5.6 "observable actions of other identifiable participants (new; pending user confirmation at Gate 2)" | 4 — A-share disclosure data | EIC-W4 | should_fix | sentence: Part B §5.6 and item codes | claim_scope_unsupported; section: §5.6 |
| S2 | Reword H-A to "the two gates as implemented here"; describe the performance gate as descriptive only | SC-5 | minor | text: §9.3 "PERF and TREND (no within-batch selection by construction): Q-total and exposure-schedule terms only." | 4 — hypothesis wording against test cards | EIC-W5 | should_fix | sentence: Part A H-A | claim_scope_unsupported; claim: H-A |
| S3 | Add market, period and signal-family scope to the pre-fixed verdict sentences | SC-6 | minor | text: §15.1 "One market, one frequency, long-only, one family of base signals." | 4 — emerging-market backtest reviewing | EIC-W6 | should_fix | sentence: Part B §9.3, §15.2 | claim_scope_unsupported; section: §9.3 |
| S4 | Reproduce in the paper the definitions and statements now cited by pointer | SC-7 | minor | text: §3.8 "The text of I-§3 governs; the summary below is for orientation." | 4 — reading for self-containedness | EIC-W7 | should_fix | section: appendix | reader_traceability_reduced; manuscript: definitions |
| S5 | Move the revision logs to a separate change record; define or drop earlier-round item codes | SC-8 | minor | text: Revision log v0.4 "old revision logs below were left as historical record and still contain superseded statements" | 5 — direct observation | EIC-W8 | should_fix | section: Part B revision logs | reader_traceability_reduced; section: revision logs |
| S6 | Add a symbol and code table with unique prefixes | SC-9 | minor | text: §2.4 A24 "If U + M are not rare the label is driven by a convention" | 4 — notation only | EIC-W9 | should_fix | section: notation table | reader_traceability_reduced; manuscript: notation |
| S7 | Supply a positioning passage naming the closest prior work before the framing is frozen | SC-10 | minor | absence: Parts A, B and C, positioning passage | 3 — passage missing; external file not seen | EIC-W10 | should_fix | section: Part A or Part B §1 | reporting_requirement_unmet; manuscript: positioning |
| S8 | Fix subsection order, the dangling "above" reference, the language mix and the forward reference of §9.4 | SC-11 | minor | text: §5 "5.2a Implementation details of §5.1–5.2 that must be fixed before coding (P12)" | 5 — direct observation | EIC-W11 | consider | sentence: Part A opening; Part B §5, §9.4 | editorial_conformance_unmet; manuscript: ordering |
| S9 | Run the null simulation on the five-seed average, or state that the pass applies to the one-seed procedure and add a small five-seed cross-check | SC-17 | minor | text: §10.2 Cost "plus 15 deployment refits; one seed" | 4 — simulation-based size checks | R1-W6 | should_fix | section: Part B §10.2 | evidence_gap_remains; claim: size check of the tested statistic |
| S10 | Fix in advance an ordered list of candidate inference procedures and a maximum number of attempts; report every attempt | SC-18 | minor | text: §10.2 If it fails "every change is logged, and the simulation is repeated with fresh seeds" | 4 — sequential selection of inference procedures | R1-W7 | should_fix | section: Part B §10.2 | method_reproducibility_unresolved; section: §10.2 |
| S11 | State the rule mapping frozen settings to larger training sets, or add a development-only sensitivity | SC-19 | minor | text: §4.3 Schedule item 2 "validation years v in {2015, 2016} (fit 2013..v−2, calibrate v−1, evaluate v)" | 3 — tuning practice for boosted models | R1-W8 | should_fix | section: Part B §4.3 | interpretive_ambiguity_remains; claim: equivalence reading of C2 |
| S12 | Define the §15.2 contradiction verdict as a pre-specified test in the family, or label it descriptive | SC-20 | minor | text: §15.2 "If the adjusted interval lies entirely outside the bound, H-A is contradicted for that gate" | 4 — multiple-testing procedure design | R1-W9 | should_fix | sentence: Part B §15.2, §3.2 | acceptance_criterion_unmet; section: §15.2 |
| S13 | State how unfilled standard counterfactual orders are labelled for gate training, identically across feature sets | SC-21 | minor | text: §4.3 Training population of gates "with labels / returns from standard counterfactual orders" | 4 — label construction for selective-prediction training | R1-W10 | should_fix | sentence: Part B §4.3, §3.8 | method_reproducibility_unresolved; section: §4.3 |
| S14 | State whether later prices value exits of in-window entries, or end confirmatory decision days one holding period plus a buffer before the data end | SC-22 | minor | text: §8.3 "Orders unresolved at the end of the data are valued at the last mark and flagged." | 4 — horizon truncation in overlapping-return backtests | R1-W11 | should_fix | sentence: Part B §8.3 | method_reproducibility_unresolved; section: §8.3 |
| S15 | Bring Part A's comparator wording into line with Part B (order counts and yuan per order; invested exposure not equalised) | SC-23 | minor | text: Part A, Q-选股 "对照是日内匹配入场数、投入资金、预设风险特征的选择" | 4 — consistency of registered estimands | R1-W12 | should_fix | sentence: Part A Q-选股 | editorial_conformance_unmet; section: Part A |
| S16 | Commit the planning script; give the freeze an independent time stamp before the hold-out is opened | SC-24a, SC-24b | minor | text: §9.4 "Evaluated with a throwaway script (not in the repository; this revision may change only this file)" | 3 — reproducibility and pre-registration practice | R1-W13 | should_fix | other: repository and external registry | method_reproducibility_unresolved; table: §9.4 |

Note: S15 (R1-W12) belongs to the same theme as R2 (EIC-W2) and can be closed by the same revision of Part A; it is kept separate because its transported severity is Minor.

### Source-Traceability Checklist

- [ ] R1 — obligation `must_fix`: align H-A and the question with the confirmatory coverage (EIC-W1)
- [ ] R2 — obligation `must_fix`: synchronise Part A with Part B (EIC-W2)
- [ ] R3 — obligation `must_fix`: state the contribution under each outcome (EIC-W3)
- [ ] R4 — obligation `must_fix`: repair the W-swap null world (R1-W1)
- [ ] R5 — obligation `must_fix`: add the informative-reference-gate null world (R1-W2)
- [ ] R6 — obligation `must_fix`: design-stage power statement and fixed status of C1, C2 (R1-W3)
- [ ] R7 — obligation `must_fix`: anchor the equivalence margin, show assay sensitivity (R1-W4)
- [ ] R8 — obligation `must_fix`: signed audit of announcement dates (R1-W5)
- [ ] S1 — obligation `should_fix`: rename the second feature group (EIC-W4)
- [ ] S2 — obligation `should_fix`: reword H-A to the two gates as implemented (EIC-W5)
- [ ] S3 — obligation `should_fix`: scope qualifier in binding wording (EIC-W6)
- [ ] S4 — obligation `should_fix`: reproduce externally governed definitions (EIC-W7)
- [ ] S5 — obligation `should_fix`: move revision logs out of the plan (EIC-W8)
- [ ] S6 — obligation `should_fix`: symbol and code table (EIC-W9)
- [ ] S7 — obligation `should_fix`: positioning passage (EIC-W10)
- [ ] S8 — obligation `consider`: ordering and reference edits (EIC-W11)
- [ ] S9 — obligation `should_fix`: five-seed null simulation or cross-check (R1-W6)
- [ ] S10 — obligation `should_fix`: stopping rule for revise-and-repeat (R1-W7)
- [ ] S11 — obligation `should_fix`: rule for frozen hyper-parameters on larger windows (R1-W8)
- [ ] S12 — obligation `should_fix`: status of the §15.2 contradiction verdict (R1-W9)
- [ ] S13 — obligation `should_fix`: training label of unfilled orders (R1-W10)
- [ ] S14 — obligation `should_fix`: end-of-sample truncation (R1-W11)
- [ ] S15 — obligation `should_fix`: Part A comparator wording (R1-W12)
- [ ] S16 — obligation `should_fix`: commit planning script, external freeze time stamp (R1-W13)

### Response Letter Template

Respond to every item R1 to R8 and S1 to S16 using `templates/revision_response_template.md`. A declined item stays visible with its reason. The revised design requires re-review.

---

## Part 3: Reviewer Report Summary (Appendix)

### Journal-Fit Review (eic seat) Summary
- Recommendation: none stated on the card; dimension score D2 = warn (D1 not_assessed) | Confidence: per-finding only, 3 to 5
- Key Point: the plan is disciplined about what it will claim, but the framing layer (question and hypotheses in Part A, contribution per outcome) promises more than the confirmatory design delivers and is out of step with Part B; 3 Major and 8 Minor findings, 6 strengths.

### Reviewer 1 (Methodology) Summary
- Recommendation: none stated on the card; dimension score D1 = block, repairable (D2 not_assessed) | Confidence: per-finding only, 3 to 4
- Key Point: the architecture is sound and the three earlier critical points are resolved at design level, but the four primary tests lack valid null calibration, demonstrated power, an anchored margin and signed date validation; 5 Major and 8 Minor findings, 8 strengths. Arithmetic receipts: no recomputable statistics; the half-width table of §9.4 was not re-evaluated.

### Reviewer 2 (Domain) Summary
- not run in methodology-focus mode

### Reviewer 3 (Perspective) Summary
- not run in methodology-focus mode

### Devil's Advocate Summary
- not run in methodology-focus mode

### Limits of This Synthesis
- Two seats, same model family, fresh contexts, no access to each other's output: role-separated, not independent.
- Unbound review: no venue-alignment claim.
- Mathematical proofs were not reviewed by either seat.
- The synthesizer read only the contract and the two Phase 2 cards; it did not read the submission and raises no finding of its own.
- No block manifest was bound, so the roadmap carries locators but no exact `proposed_targets[]` block ids; no machine-readable `revision-roadmap/1.0` JSON was emitted.


## Attachment: Suggested-Reference Check (advisory, #1001)

The suggested-reference check did not run: methodology-focus mode has no Reviewer 2 or Reviewer 3 seat.

## Attachment: Reviewer Claim Check (advisory, #1002)

The reviewer claim check did not run: the judge subagent must receive the full manuscript inline with no tools, and the 233 KB manuscript could not be passed that way in this session.

## Attachment: Acronym Check (advisory, #849)

### Acronym check (advisory; no reply needed)
Coverage: body (partial)
Not in this input: English abstract, Chinese abstract.
Not checked:
- Body, line 76: MIT (the initials before its parentheses do not spell it)
- Body, line 270: EX (the initials before its parentheses do not spell it)
- Body, line 366: ROC (the initials before its parentheses do not spell it)
- Body, line 366: STD (the initials before its parentheses do not spell it)
- Body, line 434: CGO (the initials before its parentheses do not spell it)
- Body, line 459: OA6 (the initials before its parentheses do not spell it)
- Body, line 469: OA3 (the initials before its parentheses do not spell it)
- Body, line 533: LOSS (the initials before its parentheses do not spell it)
- Body, line 950: OA1 (the initials before its parentheses do not spell it)
- Body, line 1053: RV9 (the initials before its parentheses do not spell it)

| Scope | Line | Rule | Acronym | Uses |
|---|---|---|---|---|
| Body | 9 | Not defined | RQ | 1 |
| Body | 18 | Not defined | CSA | 2 |
| Body | 18 | Not defined | RCPS | 2 |
| Body | 27 | Not defined | ACM | 1 |
| Body | 27 | Not defined | ICAIF | 1 |
| Body | 36 | Not defined | OA9 | 1 |
| Body | 38 | Not defined | GPT | 6 |
| Body | 39 | Not defined | CERT | 3 |
| Body | 42 | Not defined | RV1 | 6 |
| Body | 42 | Not defined | RV13 | 6 |
| Body | 43 | Not defined | SF | 29 |
| Body | 56 | Not defined | HOLD | 2 |
| Body | 56 | Not defined | ON | 2 |
| Body | 62 | Not defined | CVaR | 3 |
| Body | 74 | Not defined | ST | 8 |
| Body | 78 | Not defined | CSDC | 2 |
| Body | 79 | Not defined | OA5 | 3 |
| Body | 79 | Not defined | SSE | 2 |
| Body | 80 | Not defined | JSON | 1 |
| Body | 88 | Not defined | CSI | 4 |
| Body | 89 | Not defined | IPO | 1 |
| Body | 92 | Not defined | NaN | 4 |
| Body | 115 | Not defined | CSMAR | 1 |
| Body | 115 | Not defined | RESSET | 1 |
| Body | 192 | Not defined | RND | 3 |
| Body | 198 | Not defined | CONF | 12 |
| Body | 198 | Not defined | LIQ | 3 |
| Body | 198 | Not defined | LR | 3 |
| Body | 198 | Not defined | NET | 10 |
| Body | 198 | Not defined | PERF | 10 |
| Body | 198 | Not defined | SCORE | 6 |
| Body | 198 | Not defined | TREND | 4 |
| Body | 198 | Not defined | VOL | 3 |
| Body | 198 | Not defined | VT | 6 |
| Body | 221 | Not defined | AR | 10 |
| Body | 223 | Not defined | VWAP | 6 |
| Body | 227 | Not defined | RV6 | 1 |
| Body | 228 | Not defined | LP | 7 |
| Body | 230 | Not defined | OA | 5 |
| Body | 235 | Not defined | RV4 | 1 |
| Body | 248 | Not defined | RV2 | 1 |
| Body | 251 | Not defined | RV7 | 1 |
| Body | 311 | Not defined | RV11 | 1 |
| Body | 312 | Not defined | RV3 | 1 |
| Body | 347 | Not defined | RV8 | 1 |
| Body | 366 | Not defined | BETA | 1 |
| Body | 366 | Not defined | CNTP | 1 |
| Body | 366 | Not defined | CORD | 1 |
| Body | 366 | Not defined | CORR | 1 |
| Body | 366 | Not defined | KLEN | 1 |
| Body | 366 | Not defined | KLOW | 1 |
| Body | 366 | Not defined | KMID | 1 |
| Body | 366 | Not defined | KUP | 1 |
| Body | 366 | Not defined | RESI | 1 |
| Body | 366 | Not defined | RSQR | 1 |
| Body | 366 | Not defined | RSV | 1 |
| Body | 366 | Not defined | SUMP | 1 |
| Body | 366 | Not defined | VMA | 1 |
| Body | 366 | Not defined | VSTD | 1 |
| Body | 366 | Not defined | VSUMP | 1 |
| Body | 366 | Not defined | WVMA | 1 |
| Body | 369 | Not defined | PB | 1 |
| Body | 369 | Not defined | PE | 1 |
| Body | 373 | Not defined | CPU | 5 |
| Body | 390 | Not defined | RankIC | 2 |
| Body | 412 | Not defined | RP | 3 |
| Body | 414 | Not defined | NOT | 5 |
| Body | 414 | Not defined | THE | 4 |
| Body | 421 | Not defined | PR | 1 |
| Body | 426 | Not defined | ATO | 1 |
| Body | 459 | Not defined | INS | 3 |
| Body | 468 | Not defined | BLK | 1 |
| Body | 468 | Not defined | LHB | 1 |
| Body | 516 | Not defined | ACI | 1 |
| Body | 516 | Not defined | CRC | 1 |
| Body | 516 | Not defined | DEUP | 1 |
| Body | 516 | Not defined | DQN | 1 |
| Body | 516 | Not defined | ISA | 1 |
| Body | 516 | Not defined | PPO | 1 |
| Body | 516 | Not defined | RL | 1 |
| Body | 516 | Not defined | SGR | 1 |
| Body | 576 | Not defined | CAGR | 2 |
| Body | 576 | Not defined | TW | 2 |
| Body | 643 | Not defined | TOST | 2 |
| Body | 684 | Not defined | ANOVA | 1 |
| Body | 702 | Not defined | SPA | 1 |
| Body | 725 | Not defined | README | 1 |
| Body | 859 | Not defined | GPU | 2 |
| Body | 949 | Not defined | PLAN | 1 |
| Body | 952 | Not defined | ARS | 1 |
| Body | 1015 | Not defined | MoF | 1 |
| Body | 1015 | Not defined | SZSE | 1 |
