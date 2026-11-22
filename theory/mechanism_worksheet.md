# Worksheet 5 — mean-reverting price-pressure toy model

> Researcher (sub-agent), 2026-11-15. Side-track H-M of `00_idea/research_question.md` (v3).
> **This is NOT a theorem. It is NOT a game** (no players, information sets, strategies or equilibrium). **It is NOT an identification of the disposition effect or of any holder behaviour.** It is a three-line conditional-expectation calculation under assumed reduced-form dynamics. Not reviewed by anyone.

## Assumptions (all imposed, none derived)

- P_t = V_t − λ S_t: observed price = "pressure-free value" V_t minus an impact λ > 0 (constant) times a selling-pressure state S_t (S_t > 0: price temporarily depressed).
- W1. E[V_{t+h} − V_t ∣ F_t] = a_t h (a_t is F_t-measurable drift per day).
- W2. E[S_{t+h} ∣ F_t] = ρ^h S_t, 0 ≤ ρ < 1 (pressure decays geometrically in expectation).
- W3. Expected round-trip cost in price units c_{t,h} (F_t-measurable). T+1 ⇒ h ≥ 1.

## Derivation

P_{t+h} − P_t = (V_{t+h} − V_t) − λ(S_{t+h} − S_t). Take E[· ∣ F_t] and use W1, W2:

  E[P_{t+h} − P_t ∣ F_t] − c_{t,h} = a_t h + λ(1 − ρ^h) S_t − c_{t,h}.   (W)

For S_t > 0 (λ(1−ρ^h) > 0 since ρ < 1, h ≥ 1): (W) > 0 ⇔ S_t > S*_{t,h} := (c_{t,h} − a_t h) / (λ(1 − ρ^h)).

Comparative statics of the threshold when c_{t,h} − a_t h > 0: S* decreases in h (through 1 − ρ^h; for fixed c), increases in ρ, decreases in λ. With a_t = 0 and c constant, an entry is profitable in expectation only if λS_t > c, and then only for horizons h > log(1 − c/(λS_t)) / log ρ. The pressure term λ(1−ρ^h)S_t is increasing and concave in h and saturates at λS_t; its half-life is log(1/2)/log ρ.

## What the worksheet does and does not deliver

- It predicts **expected price changes**, not loss probabilities: the sign of (W) says nothing about ℙ(P_{t+h} − P_t − cost < 0) without distributional assumptions. It therefore does not connect to the loss label L of `setup.md` or to r_T^entry.
- Sign is conditional: for S_t < 0 (buying pressure) the same formula predicts a negative expected change. The model has no unconditional sign for any observable proxy, consistent with `positioning.md` §2 item 5.
- Illiquidity cuts both ways: if costs scale with impact, c_{t,h} = κλ, the threshold becomes S* = κ/(1−ρ^h) − a_t h/(λ(1−ρ^h)), and for a_t = 0 it **does not depend on λ**. So "more illiquid ⇒ lower entry threshold" is not a prediction once costs are tied to the same illiquidity.

## Candidate joint restrictions that could separate this from ordinary transient liquidity pressure

**From the worksheet model as stated: none.** (W) is the generic transient-price-pressure / liquidity-provision equation: every implication above (reversal increasing and concave in h, saturating; slower with higher ρ; larger with higher λ) holds for any mean-reverting pressure state, whatever causes it. Nothing in W1–W3 refers to holders, reference prices or gains.

Candidates that would require **additional structural assumptions not in the worksheet** (all unverified, none derived, listed only so they can be accepted or rejected explicitly):

1. *Source restriction.* S_t = g(holder state), e.g. increasing in the fraction of holders with unrealised gains, with a kink at the reference price. Prediction: conditional on realised order-flow imbalance, volume and volatility (the generic liquidity-pressure proxies), the holder-state variable still predicts the reversal, and asymmetrically around zero unrealised gain. Weakness: this is an assumption about the *measurement* of S_t, not a consequence of the dynamics; a generic liquidity story with correlated proxies mimics it.
2. *Persistence tied to holder turnover.* ρ = 1 − (rate at which the holder base turns over and reference prices reset). Prediction: reversal half-life decreasing in turnover, jointly with (1): horizon × turnover × holder-state interaction of a specific sign. Weakness: turnover also proxies liquidity, which shortens reversals in generic models too; the sign is the same, so it does not discriminate without a magnitude restriction.
3. *Horizon restriction from T+1.* No discriminating content found: h ≥ 1 applies to every explanation.

Assessment against the stop rule (design notes §2, Worksheet 5; research question H-M): the worksheet itself yields **no** joint restriction (horizon × persistence × liquidity) that distinguishes it from ordinary transient liquidity pressure. Candidates 1–2 need an explicit behavioural model of S_t and ρ that I have not built; whether one can be built with a restriction that a generic model cannot mimic is open, and I do not currently see how. On the present evidence the stop rule points to **drop**, unless the lead wants the two candidates developed within the two-week limit.
