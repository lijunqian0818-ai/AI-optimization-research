"""Dump source of candidate AKShare functions (no network calls) for field / pagination inspection."""
import inspect, re, sys
import akshare as ak
names = [n for n in dir(ak) if not n.startswith("_") and callable(getattr(ak, n))]
extra = [n for n in names if re.search(r"gdfx|hold_control|hold_change|notice|zjc|jzc|plan|circulate|share_change|stock_hsgt|fund_hold|institute_hold|stock_report_disclosure|sy_|zh_a_stop|delist|info_sh_delist|info_sz_delist", n)]
print("EXTRA NAME MATCHES:")
for n in extra:
    f = getattr(ak, n)
    try: sig = str(inspect.signature(f))
    except Exception: sig = "?"
    d = (inspect.getdoc(f) or "").strip().splitlines()
    print("-", n + sig, "|", " / ".join(d[:2]))
targets = sys.argv[1:]
for n in targets:
    print("\n" + "#" * 30, n)
    try:
        print(inspect.getsource(getattr(ak, n)))
    except Exception as e:
        print("ERR", e)
