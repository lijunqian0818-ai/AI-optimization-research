"""List AKShare functions relevant to 'opponent action' variables (no network calls)."""
import inspect, re, sys
import akshare as ak
print("akshare", ak.__version__, "python", sys.version)
pats = {
 "a_restricted_release": r"restricted_release|_xsjj|jiejin",
 "b_insider_holder_trades": r"ggcg|_hold_management|share_hold_change|hold_change|_zjc|inner_trade|management_change|shareholder_change",
 "c_lhb": r"lhb",
 "d_margin": r"margin|rzrq",
 "e_block_trade": r"dzjy",
 "f_holder_number": r"gdhs|holder_number|hold_num",
 "g_northbound": r"hsgt",
 "h_repurchase_pledge_survey": r"repurchase|gpzy|pledge|jgdy|_hg_",
}
names = [n for n in dir(ak) if not n.startswith("_") and callable(getattr(ak, n))]
for k, p in pats.items():
    print("\n==== ", k, p)
    for n in names:
        if re.search(p, n):
            f = getattr(ak, n)
            try:
                sig = str(inspect.signature(f))
            except Exception as e:
                sig = "?"
            doc = (inspect.getdoc(f) or "").strip().splitlines()
            try:
                src = inspect.getsourcefile(f).split("akshare")[-1]
            except Exception:
                src = "?"
            print(f"- {n}{sig}  [{src}]")
            for line in doc[:8]:
                print("     ", line)
