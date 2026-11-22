> REVIEW NOTE: this is part 5 of 5 of one document (PLAN amendment v0.9.3: part 1 = header, A0, A1; part 2 = A2, A3, A4.1, A4.2; part 3 = A4.3, A5; part 4 = A6, A7; part 5 = A8-A11). Review this part on its own; material in other parts cannot be checked here, so say "not visible in this part" rather than "missing" where a cross-reference points elsewhere.

## A8. Population, parameters, freeze

- **Population (user decision of 2026-11-17, O4): the pilot list and the pilot screen.** The
  confirmatory population is the list `experiments/data/universe_pilot_v1.csv` (1,000 names; SHA-256
  in §13A) with the screen U-LIQ-P of §13A: each month the 300 most traded eligible names of the
  list. K = 30, H = 5, c = 0.5 unchanged (15 submissions per day). No further data are downloaded.
  Candidates (A) and (B) of v0.8 §2.3 are not used. What this implies, to be stated in the paper:
  1. **Scope.** The list is a convenience sample: 889 names fetched in code order (almost all SSE
     main board) plus 111 names from the random sample; SSE main board 898, ChiNext 45, SZSE main
     board 38, STAR 19; 109 delisted. It was assembled from stock codes and a seeded random draw, not
     from any price or outcome. Results are results for "the 300 most traded names of this list",
     **not for the A-share market**, and the scope clause of §9.3 says so. Cross-sectional ranks are
     relative to a list dominated by SSE main-board names (KL-23, KL-24).
  2. **Development data already seen.** The development years of the confirmatory population are
     exactly the data of the three exploratory rounds. Base re-tuning (§A7), gate tuning and
     `precision_v9` run on data whose gate outcomes have been looked at; development results are not
     new evidence. The protection of the primary family is the unopened hold-out and nothing else.
  3. **Hold-out data on disk (checked 2026-11-17 from file footers only, no row read):** of the 1,000
     raw bar files, 897 end in 2026-06, 46 end before 2022 and the rest in between (delistings); the
     Z_O raw files run to 2026-06. Whether every hold-out input is complete is established by the
     formal audit, which reads hold-out rows only for completeness checks defined in advance and
     computes no return, label or feature–outcome relation.
  4. **Precision.** The pilot standard errors apply to this population directly; the hold-out has
     about 1,075 decision days against 1,202 in the pilot evaluation period.
  5. The formal data audit (§2.4), the event table and the Z_O date audit are run on this list.
     The third event source (EV3) and the unaudited INS dates remain limitations (KL-25, OA10).
- **Freeze checklist additions (to §18), in order:** (1) this amendment approved and logged, with
  the three exploratory rounds and the claim mapping of §A4.2; (2) `research_question.md` v5;
  (3) chronology audit of §A7 and the Z_O window definition (window counted from availability:
  event days t − lag − W + 1 … t − lag, lag 2) confirmed in code; the gate training window of
  §A2.1 and the Z_O* feature set implemented and covered by the look-ahead test; (4) formal data
  audit for the population (no new pull), including the date audit of LHB and BLK; (5) base
  re-tuning, gate tuning with criterion §A2.2; the tuning matrix (method × feature set × search
  space × validation years × budget) printed; (6) `precision_v9` with its pass criteria and
  `null_pipeline` (extended to the simultaneous-interval rule and to fixed-count policies);
  (7) inference settings, interval rule, annual diagnostics and secondary analyses frozen;
  this file, the code and the configuration archived with their SHA-256 hashes recorded in
  `STATUS.md`, after which none of them is edited; (8) only then the hold-out is opened, once.
- **Point-in-time audit: scope and tests (v0.9.2; GPT). Until it passes, neither baseline fairness
  nor causal ordering is established, and the hold-out stays closed.** Items (3) and (4) cover:
  (a) the monthly liquidity screen uses only data before the selection date; (b) eligibility,
  listing and delisting status as of each date, and the construction date of the code list (a
  list drawn in 2026 that includes delisted names is still not a point-in-time universe; stated as
  a limitation); (c) availability dates and later revisions of **Z_H as well as Z_O\*** fields;
  (d) price adjustment, suspensions, limit-up/limit-down fills and the terminal return of delisted
  names; (e) nested chronology — base tuning, base out-of-sample scores, gate labels, gate fitting
  (the new Y−1 window) and annual refits. **Tests:** the look-ahead test and the cut-off-invariance
  test of v0.8 (`cutoff_invariance.py`: data after a cut-off are altered and every feature,
  nomination and decision before it must be unchanged; run and passed on the 100-name smoke
  pipeline of the pilot code, `results/pilot/PILOT_SMOKE_REPORT.md`) are re-run on the frozen code, extended to the Y−1 gate window, the Z_O* features,
  the Z_H features, the monthly screen and the chosen tuning configurations. Passing the pilot-code
  version is not carried over.
- **Further freeze checks (v0.9.3; GPT's review of v0.9.2).** (a) *Selection chronology:* for every
  historical out-of-sample base score fed to a gate, whether the hyperparameters that produced it
  were selected using outcomes of that same period; if so this is stated and its effect on gate
  training assessed (it does not touch the hold-out). (b) *Source-level availability:* cut-off
  invariance cannot detect a historical value that was revised later; a sample of Z_H and Z_O*
  records is checked against the original disclosures for the date on which they became public;
  fields whose historical vintage cannot be established are excluded or moved to a labelled
  sensitivity, and where neither is possible the limitation is stated. (c) *Estimand-defining
  implementation choices, each fixed in writing:* seed averaging = daily numerators and counts
  averaged over the five seeds before the ratio (equal to the mean of five ratios only if counts
  agree across seeds); the P3 window; whether a change of K or c in a sensitivity refits and
  retunes the gates (it does: refit with the chosen configuration, no retuning; PLACEHOLDER); the
  worst-5% convention of §A4.3 item 0 (⌊0.05·n⌋ lowest ρ, ties by order id); **if only one of LHB
  and BLK passes the date audit, Z_O\* is that class alone and P3 is so labelled.** (d) Execution:
  the fill and cost sensitivities include a conservative case (participation cap, one-day delayed
  exit on limit-down); without it the estimates concern the specified simulator only.

---

## A9. Sections of PLAN v0.8 replaced or changed

| v0.8 section | Change |
|---|---|
| §2.3 | population = pilot list with screen U-LIQ-P (§A8; user decision O4) |
| §4.3 | threshold step replaced by the fixed-count rule for LOSS, LOSS-LR, NET-K, VOL, LIQ; fixed-count gates fitted through Y−1 (§A2.1) |
| §5.6 | primary Z_O feature set = LHB and BLK classes (Z_O*); INS in a sensitivity only (§A4.1) |
| §6.1 | VOL, LIQ, LOSS, LOSS-LR, NET-K rows: fixed count; "-thr" secondary policies added |
| §6.3 item 3 | tuning criterion V for fixed-count methods (§A2.2) |
| §7.2, §7.3 (c) | confirmatory Z contrasts are P2, P3; 20 permutation draws per seed and a noise control (§A4.3 item 6) |
| §8.3 | kept as the definition of θ_sel; §A3 adds V, δ, θ_uns and the identity |
| §8.4 | family replaced by P1–P6 per base (§A4.1); C1–C4 secondary (§A4.2) |
| §9.1, §9.2 | loss-frequency and tail contrasts become a named key secondary (§A4.3 item 0) |
| §9.3 | bound unchanged in value, extended to P1–P4 (§A5); wording rules replaced for the primary family |
| §12 | experiment-to-claim map: P1–P4 use no theory result (§A11) |
| §10 (multiple comparisons) | Holm family replaced by simultaneous intervals over the primary family |
| §10.1, §10.1b | withdrawn; replaced by `precision_v9` (§A6) |
| §10.2 | `null_pipeline` extended as in §A8 item (6) |
| §13A | closed: three exploratory rounds done; results in `PILOT_RESULTS_SUMMARY.md` |
| §15.2, §15.3 | outcome wording by the classes of §A4.1 (to be rewritten when this is merged) |
| §18 | additions of §A8 |

Unchanged: execution and accounting conventions (§3), features and controls (§4.1, §5), the hold-out
window, the cost model, the bootstrap unit and block length, the standing qualifier on synthetic
fills, the known-limitations register (§19).

---

## A10. Decisions of the user (2026-11-17)

First round, on the v0.9 draft ("O4 changed, the others as proposed"):

| ID | Decision |
|---|---|
| O1 | The primary contrasts of §A4.1 replace C1–C4 as the confirmatory claims (`research_question.md` v5 to be written) |
| O2 | One bound for every primary contrast: 4.96 bp per order, from Δ_cap = 1% per year |
| O3 | No TOST in the family; classification by simultaneous intervals |
| O4 | Population: the pilot list of 1,000 names, monthly top 300 by liquidity; no further download (§A8) |
| O5 | Unstratified random abstention takes precedence over the nine-cell version among the secondary selection statistics |
| O6 | Permutation follow-up: 20 draws per seed, fixed configuration |
| O7 | Z_O event analysis with a 5-day availability window (its form was changed by the review, §A4.3 item 7; the minimum-support rule is dropped) |
| O8 | No validity gate on hold-out base performance; unconditional reporting with annual diagnostics |

Second round, after the reviews of v0.9 (`reviews/plan_review_2.md`; "all as the lead proposed"):

| ID | Decision | Where |
|---|---|---|
| D1 | δ(NET-K(−Z), SCORE) enters the primary family as P4 (eight contrasts) | §A4.1 |
| D2 | Fixed-count gates are fitted through Y−1; the Y−2 window is a sensitivity | §A2.1 |
| D3 | The INS class is excluded from the primary Z_O specification; with INS as a sensitivity | §A4.1, §A4.3 item 2 |
| D4 | It is accepted that "negligible" is out of reach at the pilot precision; an unadjusted TOST is printed as a secondary report; Δ is not re-anchored | §A4.1 |
| D5 | Loss-frequency and tail differences are a named key secondary, outside the family | §A4.3 item 0 |
| D6 | Positioning: an empirical study; Theorem 1 is a monitoring tool and no primary contrast depends on a theory result. The lead noted that this is the item the user may most want to revisit; it can be reopened at Gate 3 | §A11 |

Third round, after the re-review of v0.9.1 (`reviews/plan_review_3.md`), told that the most likely
outcome is eight inconclusive contrasts ("continue, as an estimation study"):

| ID | Decision | Where |
|---|---|---|
| D7 | The study continues with this design and is framed as an estimation study; no class label is a success criterion; Δ unchanged | §A0 |

Fourth round, after the reviews of v0.9.2 (`reviews/plan_review_4.md`; "all as the lead proposed"):

| ID | Decision | Where |
|---|---|---|
| D8 | A base predictor whose hyperparameters are selected on V (BASE-V) is added as a comparator, and the gates are compared with it in the primary family (P5, P6; twelve contrasts) | §A4.1, §A7 |
| D9 | The paper's subject is stated as fixed-coverage re-ranking; variable-count threshold policies stay secondary | §A0 |
| D10 | The four class labels are removed; primary contrasts are reported as estimates with simultaneous intervals and the Δ reference line; Δ unchanged. This supersedes the classification part of O3 and the unadjusted-TOST display of D4 | §A0, §A4.1 |

Decided by the lead after the discussion `inference-target` (technical; reported to the user): the
inferential target and assumptions of §A0; the simulation suite and pass rule of §A6; the
descriptive fallback (Route B), which would need the user's decision if triggered.

Superseded statements of earlier versions, kept above for the record: "eight contrasts" (now
twelve); every mention of classes "negligible / beneficial / harmful / inconclusive".

Still PLACEHOLDER and to be confirmed at the freeze (v0.9.3 list replaces the one below): the event
window (5 days), K ∈ {20, 50} and c ∈ {0.1, 0.3, 0.7, 0.9} of the sensitivity, the simulation sizes,
p_max = 6% and the 0.1 bp truth-error limit of §A6, the pooled averaging of §A2.2, the refit rule
for sensitivities (§A8).

Earlier list: the event window (5 days), K ∈ {20, 50} of the
sensitivity, the simulation sizes and the pass criteria of §A6 (94.0% / 5% / 1% / 2.5%), the pooled
averaging of the tuning criterion (§A2.2).

Not adopted, with reasons (v0.9.3): a matched-budget base(+Z) primary experiment (both reviewers;
it would let Z change nominations and is a different study — it stays the exploratory unit of v0.8
§7.1 and the Z claims are narrowed, §A0, §A4.3 item 6); loss frequency or a tail measure as a
co-primary quantity, and a redesign in which Theorem 1 is tested by the market experiment (Gemini,
rated critical in two successive reviews; the user's decisions D5 and D6 stand, and the paper says
that the primary quantity is mean net return and that the theory is supporting); restoring a
variable-count gate as primary (Gemini; the threshold gates degenerated in the pilot — they stay
secondary and the subject is narrowed, D9); an ensemble of the five seeds as the policy (Gemini;
between-seed averaging lowers the SE by about a tenth at most on the pilot decisions, §A0; the
ensemble policy itself is unverified and may be added as a secondary). **Withdrawn:** v0.9.2
refused a base tuned on the endpoint as "a new design element after outcomes were seen"; GPT
pointed out that the whole amendment is pilot-informed and a comparator declared before the
hold-out is opened can be disclosed in the same way. The lead agrees; see D8.

Reviewer suggestions not adopted, with reasons: re-anchoring Δ to the achievable power (Gemini;
contrary to v0.8 §9.3); loss frequency as a co-primary contrast (Gemini; adopted as key secondary
instead, to keep the family at eight); re-tuning for every permutation draw (GPT; cost — the
fixed-configuration scope is stated); conditional permutation (both; no defensible model of Z given
the other features is available, and no conditional-information claim is made).

Disagreement recorded from the discussion: the lead read the pilot contrast real Z_H minus permuted
Z_H (+2.82 bp on the LightGBM base) as "permuted columns hurt the gate"; GPT pointed out that the
permuted-minus-no-Z interval includes zero, so neither that reading nor an information reading is
established. The lead withdraws the reading; item 6 of §A4.3 describes the contrast and does not
claim to settle it.

---

## A11. Relation to the theory files (v0.9.1; both reviewers; unchanged in v0.9.2)

**No primary contrast, key secondary or classification of this amendment uses a result of
`theory/theorems.md`.** P1–P4 are comparisons of fitted selection policies by mean net return with
bootstrap inference; they neither test nor rely on Theorem 1, its corollaries, Proposition 2 or
Lemma 3. The paper is positioned accordingly (D6): an empirical study of abstention gates, with the
theory results in a supporting role. What each result is used for, and what checks it:

| Result (label of `theorems.md`; none is a theorem in the sense of rule 3 yet) | Role in the paper | Checked by |
|---|---|---|
| Theorem 1, Corollaries 1.1–1.2 (time-uniform interval for the entry loss rate under delayed labels) | monitoring tool reported for the deployed strategies; shows how wide an honest interval is (about ±0.17 in the pilot) | synthetic validation protocol of v0.8 §12.1 (coverage under optional stopping, delays, dependence); unchanged |
| Proposition 2 (lower bound) | context for the width of the Theorem 1 interval | no market experiment; stated as theory only |
| Lemma 3 (additive attribution) | descriptive split of paired ΔAR into exposure, composition and cost (§A3.3) | ledger reconciliation R2–R4 and known-answer cases of v0.8 §12.1 |
| Identity θ_uns = θ_sel + A (§A3.2; `草稿`) | decomposition shown beside the secondary selection statistics | algebraic proof to be written into `theory/` and reviewed; unit tests with empty cells, zero submissions, singleton cells and days with fewer than K nominations; an identity, not an empirical claim |

If the user later decides that Theorem 1 is to be a core contribution, the experiments for it are
those of v0.8 §12.1 and need their own review; nothing in P1–P4 would change.
