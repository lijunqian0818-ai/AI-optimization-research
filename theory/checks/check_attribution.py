"""Lemma 3 (additive P&L attribution identity): exactness and where the gain is booked.

Run:  python theory/checks/check_attribution.py > theory/checks/results_check_attribution.txt

Construction. n_assets assets, T days. Excess returns x_t = m_t * 1 + eps_t, where the market
component m_t has a two-state regime (good / bad day). The baseline B holds an equal-weight
portfolio of k assets with full exposure every day (optionally zero exposure on some days, to
exercise the zero-baseline-exposure convention). The gated strategy G
  * times EXPOSURE with a noisy signal of the regime (high exposure on predicted good days),
  * picks its k assets UNIFORMLY AT RANDOM, independently of returns (no selection advantage).
Costs: proportional to dollar turnover. h_t is the dollar holding carried through period t
(after the trades at the start of period t). The dollar trade at the start of period t is
    trade_t = h_t - h_{t-1} * (1 + x_{t-1})      (h_0 := 0),
i.e. the new holding minus the PRE-TRADE MARKED holding (the old share position at the new price);
this equals (change in number of shares) x (execution price). C = kappa * sum_t |trade_t|_1.
The cash return is zero in this toy, so the total return equals the excess return x.
No terminal liquidation is charged.
(Round-1 review item D7: the first version used |h_t - h_{t-1}|_1, which books price drift of an
unchanged share position as trading. That formula is kept only as `turnover_cost_naive` for the
side-by-side comparison printed at the end.)
(Round-2 review items G3, G4: the return-based formula above is a SHORTCUT. The definition is
share-based, trade_t = (s_t - s_{t-}) * p_t with s_{t-} the pre-trade shares AFTER corporate
actions. The shortcut agrees with it only if the return used is the ex-distribution,
split-adjusted price return; in this toy there are no corporate actions and the cash return is
zero, so x is that return and the simulation is unaffected. `adversarial_cases()` at the end of
the output tests the definition on a cash dividend and on a split with no trade (dollar traded
must be 0), and tests that slippage is counted once under either accounting convention.)

Checked:
  (a) identity  Pi^G - Pi^B = exposure term + composition term - (C^G - C^B)  to rounding error;
  (b) exposure term significantly positive, composition term ~ 0 (within a few standard errors);
  (c) gross (G vs exposure-matched reference E) equals the composition term exactly; the net
      difference adds -(C^G - C^E);
  (d) the split is convention dependent: alternative ordering (reference e^B w^G) moves the
      interaction term; a different fallback w^B on zero-baseline-exposure days moves mass
      between the two terms; the SUM is unchanged in both cases.
"""
import sys

import numpy as np

SEEDS = [7, 8, 9]


def turnover_cost(h, x, kappa):
    """Cost of the trades h_t - h_{t-1} * (1 + x_{t-1}) (pre-trade marked holdings subtracted)."""
    pre = np.vstack([np.zeros((1, h.shape[1])), h[:-1] * (1.0 + x[:-1])])
    return kappa * np.abs(h - pre).sum()


def turnover_cost_naive(h, kappa):
    """WRONG for dollar holdings (review item D7); kept for comparison only."""
    prev = np.vstack([np.zeros((1, h.shape[1])), h[:-1]])
    return kappa * np.abs(h - prev).sum()


def one_path(rng, T=500, n_assets=50, k=10, kappa=0.001, p_zero_base=0.0, fallback="equal_all"):
    good = rng.random(T) < 0.5
    m = np.where(good, 0.004, -0.004)
    x = m[:, None] + 0.02 * rng.standard_normal((T, n_assets))
    signal = np.where(rng.random(T) < 0.75, good, ~good)       # 75% accurate regime signal
    # baseline: equal weight in k assets chosen by a return-independent base score
    wB = np.zeros((T, n_assets))
    wG = np.zeros((T, n_assets))
    for t in range(T):
        wB[t, rng.choice(n_assets, k, replace=False)] = 1.0 / k
        wG[t, rng.choice(n_assets, k, replace=False)] = 1.0 / k   # random, no skill
    eB = np.ones(T)
    zero_days = rng.random(T) < p_zero_base
    eB[zero_days] = 0.0
    if fallback == "equal_all":      # convention when e^B_t = 0: equal weight in all assets
        wB[zero_days] = 1.0 / n_assets
    elif fallback == "keep":         # convention: the weights the baseline would have had
        pass
    eG = np.where(signal, 1.0, 0.2)
    hB, hG, hE = eB[:, None] * wB, eG[:, None] * wG, eG[:, None] * wB
    CB, CG, CE = (turnover_cost(h, x, kappa) for h in (hB, hG, hE))
    CBn, CGn, CEn = (turnover_cost_naive(h, kappa) for h in (hB, hG, hE))
    PiB, PiG, PiE = (hB * x).sum() - CB, (hG * x).sum() - CG, (hE * x).sum() - CE
    port_B = (wB * x).sum(1)
    expo = ((eG - eB) * port_B).sum()
    comp = (eG * ((wG - wB) * x).sum(1)).sum()
    # alternative ordering: reference e^B w^G
    expo_alt = ((eG - eB) * (wG * x).sum(1)).sum()
    comp_alt = (eB * ((wG - wB) * x).sum(1)).sum()
    inter = ((eG - eB) * ((wG - wB) * x).sum(1)).sum()
    return dict(
        lhs=PiG - PiB, expo=expo, comp=comp, dcost=CG - CB,
        resid=(PiG - PiB) - (expo + comp - (CG - CB)),
        resid_alt=(PiG - PiB) - (expo_alt + comp_alt - (CG - CB)),
        gross_GE_minus_comp=((hG * x).sum() - (hE * x).sum()) - comp,
        net_GE_minus_comp_plus_cost=(PiG - PiE) - (comp - (CG - CE)),
        EB_resid=(PiE - PiB) - (expo - (CE - CB)),
        expo_alt=expo_alt, comp_alt=comp_alt, inter=inter,
        inter_check=(expo_alt - expo) - inter,
        CB=CB, CG=CG, CE=CE, CBn=CBn, CGn=CGn, CEn=CEn,
    )


def summarise(rows, key):
    v = np.array([r[key] for r in rows])
    return v.mean(), v.std(ddof=1) / np.sqrt(len(v))


def main():
    reps = 300
    print(f"paths per seed = {reps}, seeds = {SEEDS}; T=500 days, 50 assets, k=10, kappa=0.001")
    print("unit: P&L in units of one day's full exposure (exposure 1 = 1 dollar)")
    for p_zero, fallback in ((0.0, "equal_all"), (0.2, "equal_all"), (0.2, "keep")):
        print()
        print(f"--- baseline zero-exposure days: {p_zero:.0%}; fallback w^B on those days: {fallback} ---")
        print("seed  Pi^G-Pi^B        exposure term     composition term   -(C^G-C^B)       "
              "max|identity resid|  max|gross G-E - comp|  max|net G-E resid|  max|E-B resid|")
        for seed in SEEDS:
            rng = np.random.default_rng(seed)
            rows = [one_path(rng, p_zero_base=p_zero, fallback=fallback) for _ in range(reps)]
            f = lambda k: "%+.4f(se %.4f)" % summarise(rows, k)
            mx = lambda k: max(abs(r[k]) for r in rows)
            dc = summarise([dict(v=-r["dcost"]) for r in rows], "v")
            print(f"{seed:<5d} {f('lhs')}  {f('expo')}  {f('comp')}  {'%+.4f(se %.4f)' % dc}  "
                  f"{mx('resid'):.2e}             {mx('gross_GE_minus_comp'):.2e}               "
                  f"{mx('net_GE_minus_comp_plus_cost'):.2e}            {mx('EB_resid'):.2e}")
        # convention dependence, last seed's rows
        print("alternative ordering (reference e^B w^G), last seed:")
        print("   exposure_alt %s  composition_alt %s  interaction %s" % (
            "%+.4f(se %.4f)" % summarise(rows, "expo_alt"),
            "%+.4f(se %.4f)" % summarise(rows, "comp_alt"),
            "%+.4f(se %.4f)" % summarise(rows, "inter")))
        print("   max|identity resid (alt)| = %.2e ; max|(expo_alt - expo) - interaction| = %.2e" % (
            max(abs(r["resid_alt"]) for r in rows), max(abs(r["inter_check"]) for r in rows)))
    # same random stream, two fallback conventions: sum invariant, split changes
    print()
    print("--- same paths (seed 7), 20% zero-exposure baseline days, two fallback conventions ---")
    for fallback in ("equal_all", "keep"):
        rng = np.random.default_rng(7)
        rows = [one_path(rng, p_zero_base=0.2, fallback=fallback) for _ in range(reps)]
        print(f"fallback={fallback:<10s} expo={np.mean([r['expo'] for r in rows]):+.6f} "
              f"comp={np.mean([r['comp'] for r in rows]):+.6f} "
              f"expo+comp={np.mean([r['expo'] + r['comp'] for r in rows]):+.6f} "
              f"lhs+dcost={np.mean([r['lhs'] + r['dcost'] for r in rows]):+.6f}")

    # D7: corrected trade formula versus the naive holdings difference
    print()
    print("--- cost formula (review item D7) ---")
    print("unit test: 1 share bought at 100 on day 1 and held; price 100 -> 110 -> 121 (x = 0.10, 0.10)")
    h = np.array([[100.0], [110.0], [121.0]])
    x = np.array([[0.10], [0.10], [0.0]])
    print(f"  dollar traded, corrected formula: {turnover_cost(h, x, 1.0):.6f}  (true value: 100, the initial purchase)")
    print(f"  dollar traded, naive |h_t - h_(t-1)|: {turnover_cost_naive(h, 1.0):.6f}")
    print("simulation (seed 7, baseline never at zero exposure): mean total cost per path")
    rng = np.random.default_rng(7)
    rows = [one_path(rng) for _ in range(reps)]
    for a in ("B", "G", "E"):
        c, cn = np.mean([r["C" + a] for r in rows]), np.mean([r["C" + a + "n"] for r in rows])
        print(f"  C^{a}: corrected {c:.6f}   naive {cn:.6f}   relative difference {(cn - c) / c:+.4%}")

    ok = adversarial_cases()
    if not ok:
        sys.exit(1)


# ----------------------------------------------------------------------------------------------
# Round-2 review items G3 (corporate actions) and G4 (slippage counted once).
# Deterministic single-asset cases; no random numbers.
# Round-3 review item K1: case (v), wealth identity with a non-zero cash return. Its second part
# uses its own generator with the fixed seed 2026 (it does not touch the simulation's streams).
# ----------------------------------------------------------------------------------------------

def trade_dollars_shares(s, p, phi):
    """Share-based dollar trade vector (the definition adopted in round 2, item G3):
           s_{t-} = s_{t-1} * phi_t      (pre-trade shares AFTER corporate actions; s_0 := 0)
           trade_t = (s_t - s_{t-}) * p_t
    s[t]   shares carried through period t (after the trade at the start of period t)
    p[t]   raw (unadjusted) price per share at the start of period t, in the share units of s[t]
    phi[t] share multiplier of the corporate actions that take effect between the trade of
           period t-1 and the trade of period t (1 = none, 2 = 2-for-1 split); phi[0] is unused.
    Cash distributions do not appear here: they are credited to the cash ledger."""
    s, p, phi = (np.asarray(a, dtype=float) for a in (s, p, phi))
    s_pre = np.concatenate([[0.0], s[:-1] * phi[1:]])
    return (s - s_pre) * p


def trade_dollars_shares_no_ca(s, p):
    """WRONG when a split occurs: share difference without the corporate-action update."""
    s, p = np.asarray(s, dtype=float), np.asarray(p, dtype=float)
    return (s - np.concatenate([[0.0], s[:-1]])) * p


def trade_dollars_return_shortcut(h, r):
    """Return-based shortcut  trade_t = h_t - h_{t-1} * (1 + r_{t-1}),  r[t] = return used for period t."""
    h, r = np.asarray(h, dtype=float), np.asarray(r, dtype=float)
    return h - np.concatenate([[0.0], h[:-1] * (1.0 + r[:-1])])


def adversarial_cases(tol=1e-12):
    print()
    print("--- adversarial accounting cases (round-2 review items G3, G4; round-3 item K1) ---")
    results = []

    def check(name, value, expected, tol=tol):
        good = abs(value - expected) <= tol
        results.append(good)
        print(f"  [{'PASS' if good else 'FAIL'}] {name}: value {value:+.6f}, required {expected:+.6f}")

    def show(name, value):
        print(f"  [info] {name}: {value:+.6f}")

    # (i) cash dividend, no trade: 1 share, price 100 -> 99 after a cash dividend of 1 per share
    print("(i) cash dividend: 1 share bought at 100; dividend 1 per share; ex-dividend price 99; NO trade")
    s, p, phi, div = [1.0, 1.0], [100.0, 99.0], [1.0, 1.0], 1.0
    h = np.array(s) * np.array(p)
    r_total = (phi[1] * p[1] + div) / p[0] - 1.0          # dividend-inclusive total return = 0
    r_exdist = phi[1] * p[1] / p[0] - 1.0                 # ex-distribution, split-adjusted price return = -1%
    tr = trade_dollars_shares(s, p, phi)
    check("period-1 trade (initial purchase), share-based", tr[0], 100.0)
    check("period-2 trade, share-based formula (s_t - s_{t-}) * p_t", tr[1], 0.0)
    check("period-2 trade, return shortcut with ex-distribution price return", trade_dollars_return_shortcut(h, [r_exdist, 0.0])[1], 0.0)
    show(f"period-2 trade, return shortcut with TOTAL return ({r_total:+.4f}) -- wrong, reports a sale",
         trade_dollars_return_shortcut(h, [r_total, 0.0])[1])
    cash_dist = s[0] * div                                # credited to the cash ledger, not a trade
    wealth_change = (h[1] + cash_dist) - h[0]             # cash after purchase is 0 in this example
    check("cash distribution credited to the cash ledger", cash_dist, 1.0)
    check("wealth change equals h_1 * total return (P&L uses total return)", wealth_change - h[0] * r_total, 0.0)

    # (ii) 2-for-1 split (share multiplier 2; round-3 item K2: earlier mislabelled "1-for-2"), no trade: 1 share at 100 becomes 2 shares at 50
    print("(ii) split: 1 share bought at 100; 2-for-1 split; post-split price 50; NO trade")
    s, p, phi = [1.0, 2.0], [100.0, 50.0], [1.0, 2.0]
    h = np.array(s) * np.array(p)
    r_adj = phi[1] * p[1] / p[0] - 1.0                    # split-adjusted price return = 0
    r_raw = p[1] / p[0] - 1.0                             # raw price ratio = -50%
    tr = trade_dollars_shares(s, p, phi)
    check("period-1 trade (initial purchase), share-based", tr[0], 100.0)
    check("period-2 trade, share-based formula with s_{t-} = s_{t-1} * phi_t", tr[1], 0.0)
    check("period-2 trade, return shortcut with split-adjusted price return", trade_dollars_return_shortcut(h, [r_adj, 0.0])[1], 0.0)
    show("period-2 trade, share difference WITHOUT the corporate-action update -- wrong, reports a purchase",
         trade_dollars_shares_no_ca(s, p)[1])
    show(f"period-2 trade, return shortcut with RAW price ratio ({r_raw:+.4f}) -- wrong, reports a purchase",
         trade_dollars_return_shortcut(h, [r_raw, 0.0])[1])

    # (iii) controls: the corrected formula must still see genuine trades next to a corporate action
    print("(iii) controls: a genuine trade on the corporate-action date must still be reported")
    check("dividend 1 + purchase of 1 more share at 99", trade_dollars_shares([1.0, 2.0], [100.0, 99.0], [1.0, 1.0])[1], 99.0)
    check("2-for-1 split + sale of 1 of the 2 post-split shares at 50", trade_dollars_shares([1.0, 1.0], [100.0, 50.0], [1.0, 2.0])[1], -50.0)

    # (iv) G4: slippage must be counted exactly once
    print("(iv) slippage counted once: buy 1 share, benchmark price 100, actual execution price 101, "
          "end price 110, explicit fee 0.10")
    bench, execp, endp, fee = 100.0, 101.0, 110.0, 0.10
    true_wealth_change = endp - execp - fee
    pi_exec = execp * (endp / execp - 1.0) - fee                         # convention A
    pi_bench = bench * (endp / bench - 1.0) - (fee + (execp - bench))    # convention B
    pi_double = execp * (endp / execp - 1.0) - (fee + (execp - bench))   # inconsistent mixture
    show("true wealth change", true_wealth_change)
    check("convention A (execution-price accounting, C = explicit fees only) minus true wealth change", pi_exec - true_wealth_change, 0.0)
    check("convention B (benchmark-price accounting, C = fees + shortfall) minus true wealth change", pi_bench - true_wealth_change, 0.0)
    show("inconsistent mixture (execution-price holdings AND slippage in C) minus true wealth change -- wrong",
         pi_double - true_wealth_change)

    # (v) K1 (round 3): wealth change versus Pi when the cash return is NOT zero.
    #     Claim tested: with costs debited at the trade (start of the period),
    #         W_{T+1} - W_1 = Pi + sum_t rho_t (W_t - c_t),      c_t = fee_t + shortfall_t,
    #     and with costs debited at the END of the period,
    #         W_{T+1} - W_1 = Pi + sum_t rho_t W_t.
    #     Wealth is produced by an explicit cash-and-shares ledger, not by either formula.
    print("(v) non-zero cash return (round-3 item K1): wealth from an explicit cash/share ledger "
          "versus Pi + cash-benchmark term")

    def ledger(W1, s, p, pexec, fee, rho, timing):
        """s[t] shares carried through period t (t = 0..T-1), p[t] benchmark prices at the start of
        period t (t = 0..T; p[T] marks the terminal holdings), pexec[t] execution prices of the
        trade at the start of period t, fee[t] explicit charge of period t, rho[t] cash return.
        timing = 'start': fee debited at the trade; 'end': fee debited after cash has earned rho.
        Returns W_{T+1} - W_1, Pi, sum rho_t W_t, sum rho_t c_t."""
        T = len(rho)
        cash, s_prev = float(W1), np.zeros_like(s[0])
        Pi = sum_rho_W = sum_rho_c = 0.0
        for t in range(T):
            W_t = cash + float(s_prev @ p[t])                 # wealth marked at benchmark, pre-trade
            sf = float((s[t] - s_prev) @ (pexec[t] - p[t]))   # execution shortfall
            cash -= float((s[t] - s_prev) @ pexec[t])         # pay for / receive from the trade
            if timing == "start":
                cash -= fee[t]
            cash *= 1.0 + rho[t]                              # cash (possibly negative) earns rho
            if timing == "end":
                cash -= fee[t]
            x = p[t + 1] / p[t] - 1.0 - rho[t]                # excess return (no distributions here)
            c_t = fee[t] + sf
            Pi += float((s[t] * p[t]) @ x) - c_t
            sum_rho_W += rho[t] * W_t
            sum_rho_c += rho[t] * c_t
            s_prev = s[t]
        W_end = cash + float(s_prev @ p[T])
        return W_end - W1, Pi, sum_rho_W, sum_rho_c

    # reviewer's counterexample: cash 100, start-of-period charge 1, cash return 10%, no risky holdings
    z = np.zeros(1)
    one = [np.ones(1), np.ones(1)]
    dW, Pi, rW, rc = ledger(100.0, [z], one, [np.ones(1)], [1.0], [0.10], "start")
    check("reviewer's example, start-of-period charge: terminal wealth from the ledger", 100.0 + dW, 108.9, tol=1e-9)
    check("  wealth change", dW, 8.9, tol=1e-9)
    check("  Pi (= -cost; no risky holdings)", Pi, -1.0)
    check("  wealth change minus [Pi + sum rho_t (W_t - c_t)]  (corrected formula)", dW - (Pi + rW - rc), 0.0, tol=1e-9)
    show("  Pi + sum rho_t W_t  (round-2 formula; gives 9, not 8.9)", Pi + rW)
    show("  wealth change minus [Pi + sum rho_t W_t]  -- wrong for start-of-period charges", dW - (Pi + rW))
    dW, Pi, rW, rc = ledger(100.0, [z], one, [np.ones(1)], [1.0], [0.10], "end")
    check("same example, charge debited at the END of the period: wealth change", dW, 9.0, tol=1e-9)
    check("  wealth change minus [Pi + sum rho_t W_t]  (end-of-period formula)", dW - (Pi + rW), 0.0, tol=1e-9)

    # multi-period, 3 assets, risky holdings, fees and execution shortfall, time-varying cash return
    rng = np.random.default_rng(2026)
    T, m = 8, 3
    p = 50.0 * np.exp(np.cumsum(0.03 * rng.standard_normal((T + 1, m)), axis=0))
    s = np.round(rng.uniform(0.0, 2.0, size=(T, m)), 2)
    pexec = p[:T] * (1.0 + 0.002 * rng.uniform(-1.0, 1.0, size=(T, m)))
    fee = rng.uniform(0.0, 0.5, size=T)
    rho = rng.uniform(0.0, 0.02, size=T)
    print(f"    multi-period case: T={T}, {m} assets, seed 2026, initial cash 300, fees in [0,0.5], "
          "execution prices within 0.2% of benchmark, rho_t in [0,2%]")
    dW, Pi, rW, rc = ledger(300.0, s, p, pexec, fee, rho, "start")
    show("  multi-period: wealth change (ledger)", dW)
    show("  multi-period: Pi", Pi)
    show("  multi-period: sum rho_t W_t", rW)
    show("  multi-period: sum rho_t c_t", rc)
    check("  multi-period, costs at the trade: wealth change minus [Pi + sum rho_t (W_t - c_t)]", dW - (Pi + rW - rc), 0.0, tol=1e-9)
    show("  multi-period, costs at the trade: wealth change minus [Pi + sum rho_t W_t]  -- wrong (= -sum rho_t c_t)", dW - (Pi + rW))
    dW, Pi, rW, rc = ledger(300.0, s, p, p[:T], fee, rho, "end")
    check("  multi-period, no shortfall, fees at period END: wealth change minus [Pi + sum rho_t W_t]", dW - (Pi + rW), 0.0, tol=1e-9)
    dW, Pi, rW, rc = ledger(300.0, s, p, pexec, fee, np.zeros(T), "start")
    check("  multi-period, rho = 0 (W4): wealth change minus Pi", dW - Pi, 0.0, tol=1e-9)

    ok = all(results)
    print(f"adversarial cases: {sum(results)} of {len(results)} required equalities hold -> {'ALL PASS' if ok else 'FAILURE'}")
    return ok


if __name__ == "__main__":
    main()
