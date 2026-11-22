"""Feature catalogue: one FeatureSpec per column a feature function returns.

`tests/test_registry.py` asserts that the columns produced by the code and
the names in the catalogue coincide, so the catalogue cannot drift.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import pandas as pd


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    group: str        # B0 | Z_H | Z_O | R_H-sum | R_H-hist | R_O | DIAG (diagnostics; never a model feature)
    role: str         # primary | variant (pre-declared, robustness runs only) | control | diagnostic
    formula: str
    window: str       # look-back in trading days
    fields: str       # raw fields needed
    warmup: int       # rows of the name's history needed before the first non-NaN value
    timing: str       # why the value is in G_t
    source: str       # where the definition comes from and whether it was checked


BAR_TIMING = "bar rows dated <= t-1 (G_t, PLAN 3.1); adjusted by own preclose-chain factor through t-1"


FEATURE_GROUPS = ("B0", "Z_H", "R_H-sum", "R_H-hist", "Z_O", "R_O")     # model features; DIAG is not one


def diag_specs() -> list[FeatureSpec]:
    from .config import DIAG_XSRC_WINDOW
    return [FeatureSpec(
        "diag_filled_xsrc_in_window", "DIAG", "diagnostic",
        f"1 if a bar row inserted from the cross-check source (flag filled_from_xsrc) lies in the last "
        f"{DIAG_XSRC_WINDOW} rows ending t-1, else 0", str(DIAG_XSRC_WINDOW), "filled_from_xsrc", 0, BAR_TIMING,
        "PLAN v0.7 section 3.11 rule 12, rulings F-18 / E-16; NOT a model feature; the window length is the "
        "implementer's choice (longest primary window)")]


def catalogue(include_diag: bool = True) -> pd.DataFrame:
    """All columns the panel produces. Model features have a group in
    FEATURE_GROUPS; `role` tells primary definitions from pre-declared
    variants (Z_H) and controls. Group DIAG holds diagnostics only."""
    from . import base_b0, zh, controls, zo
    specs = base_b0.specs() + zh.specs() + controls.rh_sum_specs() + controls.rh_hist_specs() \
        + zo.specs() + controls.ro_specs() + (diag_specs() if include_diag else [])
    df = pd.DataFrame([asdict(s) for s in specs])
    if df["name"].duplicated().any():
        raise ValueError("duplicate feature names: " + str(df.loc[df["name"].duplicated(), "name"].tolist()))
    return df


def feature_sets() -> dict:
    """Column lists by group and role, for the strategy layer: a variant
    never enters a primary feature set (PLAN v0.7 section 5.3)."""
    cat = catalogue(include_diag=False)
    out = {g: cat.loc[cat["group"] == g, "name"].tolist() for g in FEATURE_GROUPS}
    out["Z_H_primary"] = cat.loc[(cat["group"] == "Z_H") & (cat["role"] == "primary"), "name"].tolist()
    out["Z_H_variants"] = cat.loc[(cat["group"] == "Z_H") & (cat["role"] == "variant"), "name"].tolist()
    return out
