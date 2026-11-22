"""Run every engine test module and the dry run; write summary.json.

    experiments/.venv/Scripts/python.exe experiments/src/engine/tests/run_all.py

Outputs under experiments/results/engine_tests/: one JSON per module, dryrun_real_data.json,
summary.json.  Every file carries the conventions hash (SHA-256 of engine/config.py and
engine/rule_calendar.py; PLAN v0.7, E-20).  Exit code 0 only if every test passed and the dry
run raised no error.

The dry run only READS files under experiments/data/raw (see dryrun_real_data.py).
"""
from __future__ import annotations

import json
import platform
import sys
from datetime import datetime

from common import OUT, run_tests

import dryrun_real_data
import test_fills
import test_ledger_r4
import test_reconcile_random
import test_rule_calendar
import test_v07_components
import test_v07_rules
import test_v08_changes
from engine.config import conventions_hash

MODULES = [("rule_calendar", test_rule_calendar, "rule_calendar.json"),
           ("fills", test_fills, "fills.json"),
           ("ledger_r4", test_ledger_r4, "ledger_r4.json"),
           ("v07_rules", test_v07_rules, "v07_rules.json"),
           ("v07_components", test_v07_components, "v07_components.json"),
           ("reconcile_random", test_reconcile_random, "reconcile_random.json"),
           ("v08_changes", test_v08_changes, "v08_changes.json")]

RESIDUAL_KEYS = ["naive_vs_ledger_rel", "naive_variants_max_rel", "R2_daily_rel", "R2_cum_rel", "R1_residual_rel",
                 "R1_residual_alt_rel", "terms_vs_wealth_diff_rel", "R1_normalised_residual_abs",
                 "normalised_terms_vs_return_diff_abs", "trade_vector_vs_records_rel", "cash_return_recursion_rel",
                 "turnover_identity_rel", "cost_total_vs_lot_costs_rel"]
DRY_KEYS = ("naive_vs_ledger_rel", "R2_daily_rel", "R2_cum_rel", "trade_vector_vs_records_rel",
            "turnover_identity_rel", "cost_total_vs_lot_costs_rel", "fill_decision_mismatches", "buy_orders_rechecked",
            "R2_pass", "R3_pass", "v07_counts")


def main() -> int:
    summary = {"run_at": datetime.now().isoformat(timespec="seconds"), "python": platform.python_version(),
               "data_cutoff_of_dry_run": dryrun_real_data.DATA_CUTOFF.isoformat(),
               "conventions_hash": conventions_hash(), "modules": {}, "failed_tests": []}
    for name, mod, out in MODULES:
        s = run_tests(name, mod.TESTS, out)
        summary["modules"][name] = {"n": s["n"], "passed": s["passed"], "failed": s["failed"]}
        summary["failed_tests"] += [f"{name}.{r['test']}" for r in s["results"] if r["status"] != "pass"]
        if name == "reconcile_random":
            infos = [r["info"] for r in s["results"] if "info" in r and "seed" in r["info"]]
            summary["max_residuals_random"] = {k: max(i[k] for i in infos) for k in RESIDUAL_KEYS} if infos else {}
            summary["seeds"] = [(i["seed"], i["start"]) for i in infos]
            summary["random_counts"] = {
                "buy_orders_checked": sum(i["buy_orders_checked"] for i in infos),
                "fill_decision_mismatches": sum(i["fill_decision_mismatches"] for i in infos),
                "buy_orders_checked_cap_zero": sum(i["buy_orders_checked_cap_zero"] for i in infos),
                "fill_decision_mismatches_cap_zero": sum(i["fill_decision_mismatches_cap_zero"] for i in infos),
                "lots": sum(i["lots_G"] + i["lots_B"] for i in infos),
                "lots_by_succession_per_seed": {i["seed"]: i["coverage"]["lots_by_succession"] for i in infos},
                "R3_days_over_tolerance": sum(i["R3_days_over_tolerance"] for i in infos),
                "non_netting_days": sum(i["non_netting_days"] for i in infos)}
    d = dryrun_real_data.main()
    summary["dryrun"] = {"load_error": "load_error" in d, "pipeline_error": "pipeline_error" in d,
                         "part_b_error": "part_b_error" in d, "seconds": d["seconds"]}
    for key in ("pipeline", "pipeline_sina_single_source", "pipeline_merged_provisional"):
        if key in d:
            summary["dryrun"][key] = {k: d[key][k] for k in DRY_KEYS}
    if "all_landed_bars" in d:
        b = d["all_landed_bars"]
        summary["dryrun"]["all_landed_bars"] = {"names_loaded": b["load"]["names_loaded"], "rows": b["load"]["rows"],
                                                "n_problems": b["load"]["n_problems"],
                                                "skipped_recently_modified": len(b["files"]["skipped_recently_modified"]),
                                                "truncation_failures": b["universe"]["truncation_failures"]}
    summary["total_tests"] = sum(m["n"] for m in summary["modules"].values())
    summary["total_passed"] = sum(m["passed"] for m in summary["modules"].values())
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"TOTAL {summary['total_passed']}/{summary['total_tests']} tests passed; "
          f"dry run errors: load={summary['dryrun']['load_error']} pipeline={summary['dryrun']['pipeline_error']} "
          f"part_b={summary['dryrun']['part_b_error']}")
    print(json.dumps(summary.get("max_residuals_random", {}), indent=1))
    print(json.dumps(summary.get("random_counts", {}), indent=1))
    print(json.dumps(summary["dryrun"], indent=1, default=str))
    ok = (not summary["failed_tests"] and not summary["dryrun"]["load_error"] and not summary["dryrun"]["pipeline_error"]
          and not summary["dryrun"]["part_b_error"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
