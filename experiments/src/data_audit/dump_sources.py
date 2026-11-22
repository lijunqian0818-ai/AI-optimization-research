"""Dump signatures / upstream URLs of the AKShare and BaoStock functions used by the audit (no network)."""
import inspect, re, sys
import akshare as ak, baostock as bs
FUNCS = ["stock_zh_a_hist_em","stock_zh_a_daily_sina","stock_zh_a_hist_tx","stock_info_sh_delist","stock_info_sz_delist",
 "stock_zh_a_stop_em","stock_zh_a_st_em","stock_tfp_em","index_stock_cons","index_stock_cons_csindex","index_stock_cons_sina",
 "index_stock_cons_weight_csindex","index_stock_info","index_detail_hist_cni","index_detail_cni","stock_fhps_detail_em","stock_fhps_em","stock_history_dividend_detail",
 "stock_history_dividend","stock_dividend_cninfo","stock_info_change_name","stock_info_sz_change_name","stock_individual_info_em",
 "stock_zh_a_gbjg_em","stock_share_change_cninfo","stock_info_a_code_name","stock_info_sh_name_code","stock_info_sz_name_code",
 "stock_lhb_detail_em","stock_lhb_jgmmtj_em","stock_dzjy_mrmx","stock_dzjy_mrtj","stock_ggcg_em","stock_notice_report",
 "stock_share_hold_change_sse","stock_share_hold_change_szse","stock_shareholder_change_ths","stock_lhb_detail_daily_sina","stock_zh_index_daily","tool_trade_date_hist_sina","stock_zh_a_hist"]
out = open(sys.argv[1], "w", encoding="utf-8")
for f in FUNCS:
    fn = getattr(ak, f, None)
    if fn is None:
        out.write(f"### {f}: NOT PRESENT\n\n"); continue
    fn = inspect.unwrap(fn); src = inspect.getsource(fn)
    urls = sorted(set(re.findall(r"https?://[^\s\"']+", src)))
    out.write(f"### {f}{inspect.signature(fn)}\nfile: {inspect.getsourcefile(fn)}\nurls: {urls}\n")
    out.write(src + "\n\n")
out.write("\n\n##### BAOSTOCK\n")
for n in dir(bs):
    if n.startswith("query"):
        fn = getattr(bs, n)
        out.write(f"### {n}{inspect.signature(fn)}\n")
import baostock.common.contants as c
out.write(inspect.getsource(c))
out.close()
for f in FUNCS:
    fn = getattr(ak, f, None)
    if fn is None: print(f, "NOT PRESENT"); continue
    fn = inspect.unwrap(fn); src = inspect.getsource(fn)
    print(f, inspect.signature(fn), sorted(set(re.findall(r"https?://[^/\s\"']+", src))))
