"""Engine configuration: every tunable number of the backtest core in one place.

Source of every value: experiments/PLAN.md v0.7 (section and U-code given per field).
`PARAM_STATUS` states, for each field, whether it is a PLACEHOLDER of the plan, a
default adopted at Gate 2, a lead decision, a ruling of PLAN v0.7 (E-n / G-n), or a
point on which the plan is silent (those are listed in ENGINE_TEST_REPORT.md).

Nothing here is estimated from data. Rule-type numbers (stamp duty, transfer fee,
price bands, dividend tax, disclosure regimes) are NOT here: they live in
rule_calendar.py.

Conventions hash (PLAN 3 intro, v0.7 E-20): `conventions_hash()` returns the SHA-256 of
the bytes of this file and of rule_calendar.py; it is written into every result file.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
from pathlib import Path


@dataclass(frozen=True)
class EngineConfig:
    # --- horizon / slots (PLAN 3.3, 3.7) ---
    H: int = 5                       # holding period in market trading days
    K: int = 30                      # slots per day (= M)
    W0: float = 1.0e7                # notional capital, yuan

    # --- cost model (PLAN 3.6) ---
    commission_rate: float = 0.00025     # per side
    min_commission: float = 0.0          # 5.0 only in the lot-rounding robustness run
    slippage_rate: float = 0.0005        # modelled execution shortfall per side
    cash_return: float = 0.0             # W4; annual simple rate, non-zero only in the robustness run
    cash_return_intraday: float = 0.0    # E-19: the intraday interval earns nothing
    cash_return_day_count: float = 365.0  # calendar days per year for the overnight accrual

    # --- fill rule (PLAN 3.2, 3.7) ---
    cap_fraction: float = 0.01           # order value <= 1% of ADV_t
    adv_window: int = 20                 # the 20 most recent TRADED days dated <= t-1 (E-5)
    strict_band_factor: float = 0.8      # SF-strict
    strict_cap_factor: float = 0.1       # SF-strict
    # False = primary definition of PLAN v0.7 (E-5): days without a trade are skipped.
    # True  = sensitivity "cap-zero": the v0.6 wording read literally (the 20 market days
    #         ending t-1, days without a trade counted as zero).
    adv_counts_nontraded_days_as_zero: bool = False
    stale_cap_days: int = 60             # U59: reporting threshold of "stale-cap fills"

    # --- lots (PLAN 3.6, 3.7; RC-11) ---
    lot_rounding: bool = False           # primary run: fractional shares

    # --- conventions (PLAN 3.9, 3.11) ---
    terminal_value_U: float = 0.0        # U33
    dividend_tax_fallback_20_before_2013: bool = False   # PLAN 3.10 list item 4
    transfer_fee_fallback_no_2022_cut: bool = False      # PLAN 3.10 list item 2
    divtax_2015_reading: str = "from"    # E-9: "from" (record date >= 2015-09-08) | "after" (boundary test only)
    cash_exit_explicit_charges: bool = False             # E-13 sensitivity
    rights_missing_R_window: int = 10    # U58 (E-15)
    deadline_extra: int = 10             # U16: deadline D = H + deadline_extra; d_D = D + 1

    # --- universe and candidate set (PLAN 2.3, 3.5) ---
    universe_size: int = 800             # U54 N_U
    universe_window: int = 120           # U54
    universe_min_traded: int = 80        # U54
    universe_min_listed: int = 120       # U54
    candidate_min_listed: int = 60       # U11
    st_lookback: int = 60                # U55

    # --- event table (PLAN 3.11) ---
    ev_tol_cash: float = 0.0001          # U56 two-source agreement, yuan per share
    ev_tol_ratio: float = 1e-6           # share-ratio agreement (plan: "agree"; numerical tolerance)
    ev_tol_flag: float = 0.005           # U56 reference-price consistency: flagged above
    ev_tol_hand: float = 0.02            # U56 reference-price consistency: hand check above
    ev_pair_window: int = 250            # U61 pairing window, market trading days
    # production configuration of the event table (PLAN v0.8 H-2): no resolution input,
    # pending rule "U", undated rights rows excluded.  "provisional" is the pre-declared
    # exploratory sensitivity "provisional booking"; it is never the primary table.
    event_pending: str = "U"
    event_undated_rights: str = "exclude"

    # --- reconciliation tolerances (PLAN 3.9) ---
    tol_R1: float = 1e-10                # x W0
    tol_R2_daily: float = 1e-6           # x W_{t-1}
    tol_R2_cum: float = 1e-4             # x W0

    def kappa_hash(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


PARAM_STATUS = {
    "H": "PLACEHOLDER (PLAN 3.3; robustness H in {1,10,20})",
    "K": "PLACEHOLDER (PLAN 3.7)",
    "W0": "PLACEHOLDER U19 (PLAN 3.7)",
    "commission_rate": "PLACEHOLDER adopted as default at Gate 2 (PLAN 3.6, U1); broker-specific, not a rule",
    "min_commission": "rule value 5 yuan is verified (RC-17); ignored in the primary run, applied in the "
                      "lot-rounding robustness run; PLAN v0.7 ruling E-4 (reserved from the slot cash, once per order)",
    "slippage_rate": "PLACEHOLDER, UNVERIFIED - not estimated from data (PLAN 3.6)",
    "cash_return": "convention W4 (zero) in the primary run; PLAN v0.7 ruling E-19 (overnight interval only). "
                   "The plan gives neither a value nor a day-count convention: annual simple rate, see cash_return_day_count",
    "cash_return_intraday": "PLAN v0.7 ruling E-19: 0",
    "cash_return_day_count": "PLAN SILENT - ACT/365 chosen so that the field has a meaning; listed in the engine report",
    "cap_fraction": "PLACEHOLDER U40 (PLAN 3.7)",
    "adv_window": "PLACEHOLDER U40 (PLAN 3.7); PLAN v0.7 ruling E-5 (traded days only)",
    "strict_band_factor": "PLACEHOLDER U36 adopted at Gate 2; no basis in the rule text (PLAN 3.2); ruling E-6",
    "strict_cap_factor": "PLACEHOLDER U36 adopted at Gate 2 (PLAN 3.2)",
    "adv_counts_nontraded_days_as_zero": "PLAN v0.7 ruling E-5: False = primary; True = pre-declared sensitivity 'cap-zero'",
    "stale_cap_days": "U59 (PLAN v0.7 ruling E-5); reporting only, changes no fill",
    "lot_rounding": "plan: off in the primary run, on in a robustness run (U39)",
    "terminal_value_U": "PLACEHOLDER U33, conservative convention (PLAN 3.9); 1.0 = sensitivity 'last traded price'",
    "dividend_tax_fallback_20_before_2013": "switch for the plan's fallback if RC-14 (pre-2013 10%) stays unverified",
    "transfer_fee_fallback_no_2022_cut": "switch for the plan's fallback if the 2022 notice stays unverified",
    "divtax_2015_reading": "PLAN v0.7 ruling E-9: 'from' is in force; 'after' exists only for the boundary-day test "
                           "(PLAN 3.10 list item 17)",
    "cash_exit_explicit_charges": "PLAN v0.7 ruling E-13: False = primary; True = pre-declared sensitivity "
                                  "(PLAN 3.10 list item 18)",
    "rights_missing_R_window": "PLACEHOLDER U58 (PLAN v0.7 ruling E-15)",
    "deadline_extra": "PLACEHOLDER U16 (PLAN 3.8 (iv)); Cor. 1.3 is a draft",
    "universe_size": "PLACEHOLDER U54 (PLAN 2.3); universe adopted by the lead, not explicitly confirmed by the user",
    "universe_window": "PLACEHOLDER U54 (PLAN 2.3)",
    "universe_min_traded": "PLACEHOLDER U54 (PLAN 2.3)",
    "universe_min_listed": "PLACEHOLDER U54 (PLAN 2.3)",
    "candidate_min_listed": "U11 (PLAN 2.3)",
    "st_lookback": "PLACEHOLDER U55 (PLAN 3.5)",
    "ev_tol_cash": "PLACEHOLDER U56 (PLAN 3.11 rule 2)",
    "ev_tol_ratio": "PLAN SILENT on a tolerance for 'the share ratio agrees' - numerical tolerance only; listed in the engine report",
    "ev_tol_flag": "PLACEHOLDER U56 (PLAN 3.11 rule 6)",
    "ev_tol_hand": "PLACEHOLDER U56 (PLAN 3.11 rule 6); also the tolerance of rule 9 (U61)",
    "ev_pair_window": "U61 (PLAN v0.7 ruling G-1)",
    "event_pending": "PLAN v0.8 ruling H-2 (U65): production 'U' (pending rule); 'provisional' = pre-declared "
                     "exploratory sensitivity; the primary event table takes no resolution input (resolutions=None)",
    "event_undated_rights": "PLAN v0.8 ruling H-2: 'exclude' in production (rights rows without dates are listed only)",
    "tol_R1": "PLACEHOLDER tolerance (PLAN 3.9)",
    "tol_R2_daily": "PLACEHOLDER tolerance (PLAN 3.9)",
    "tol_R2_cum": "PLACEHOLDER tolerance (PLAN 3.9)",
}

DEFAULT = EngineConfig()

_HERE = Path(__file__).resolve().parent
CONVENTION_FILES = ("config.py", "rule_calendar.py")


def conventions_hash() -> dict:
    """SHA-256 of the bytes of the two convention files (PLAN 3 intro; v0.7 E-20) and of
    their concatenation in the order of CONVENTION_FILES.  Written into every result file."""
    out, h_all = {}, hashlib.sha256()
    for name in CONVENTION_FILES:
        b = (_HERE / name).read_bytes()
        out[name] = hashlib.sha256(b).hexdigest()
        h_all.update(b)
    out["combined"] = h_all.hexdigest()
    return out
