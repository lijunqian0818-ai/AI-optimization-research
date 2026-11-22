# 代码、数据与基线资源清单

> 检索日期：2026-11-15。检索人：literature-scout（实例 2）。
> 核实方式：星数 / 许可证 / 大小来自 `tools/search_resources.py` 与 `tools/fetch_resource.py --info`（GitHub API）；最后推送时间来自 GitHub API `pushed_at`；包版本与 Python 支持来自 PyPI 元数据；内容描述来自实际打开的仓库 / 文档 / 数据集页面。
> 没能核实的项一律写"未验证"。**本清单没有下载或安装任何东西。**
> "Py3.14"一栏只依据 PyPI 元数据（classifiers / requires-python / wheel 标签）判断，**都没有在本机实测安装**。

推荐程度：**必需** = 没有它实验做不了或基线不完整；**有用** = 明显省事或可作对照；**可选** = 只作参照。

---

## A. A 股日频数据源（免费）

### A1. AKShare —— 推荐程度：必需（主数据源之一）
- 链接：https://github.com/akfamily/akshare ；文档 https://akshare.akfamily.xyz
- 星数 23,341；许可证 MIT；仓库 12.8 MB；最后更新 2026-11-14；PyPI `akshare` 1.20.63（2026-11-14）。
- 获取方式：`pip install akshare`，调用时实时抓取东方财富 / 新浪 / 腾讯等公开网页接口。**不需要注册或 token。**
- 字段（已核对文档 stock_quote 页）：
  - 东财日线历史（文档中名称为 `stock_zh_a_hist_em`，旧名 `stock_zh_a_hist`，以安装版本为准）：开高低收、成交量、成交额、振幅、涨跌幅、**换手率（%）**；`adjust` 可选不复权 / `qfq` / `hfq`。
  - 新浪日线 `stock_zh_a_daily_sina`：可取 `qfq-factor` / `hfq-factor` 复权因子，含 turnover；文档明确警告"多次调用有封 IP 风险"。
  - 腾讯日线 `stock_zh_a_hist_tx`：备用源。
  - 筹码分布 `stock_cyq_em`：获利比例、平均成本、90/70 成本区间与集中度。**文档原文："单次返回指定 symbol 和 adjust 的近 90 个交易日数据"**——不能用来取长历史，必须自己算（见 F 节）。
  - 两网及退市 `stock_zh_a_stop_em`：只返回当日行情，不是退市股历史。
  - 文档目录里还有：停复牌信息、涨停板行情（涨停股池）、分红派息 / 分红配送。涨停股池的可回溯日期范围**未验证**（文档页过长未读到该段）。
- 覆盖范围：年份与股票数文档未统一说明，取决于上游网站；**未验证**。
- 幸存者偏差：**有风险**。已退市股票的历史日线能否取到、历史指数成分是否提供，均**未验证**；需要实测。
- 使用条款：代码 MIT；数据版权归上游网站，属爬取性质，仅适合学术研究，论文中需说明来源。上游接口可能随时变更或限流（稳定性风险）。
- Py3.14：PyPI `requires-python >=3.11.5`，classifiers 含 3.14 —— 元数据层面兼容，未实测。依赖 `py_mini_racer`（筹码接口用），其 3.14 的 Windows wheel **未验证**。
- 用途：数据。备注：批量拉全市场长历史较慢，需做本地缓存和限速。

### A2. BaoStock（证券宝）—— 推荐程度：必需（主数据源之一）
- 链接：http://www.baostock.com ；PyPI https://pypi.org/project/baostock/
- 星数：不适用（非 GitHub 项目）；许可证 PyPI 标注 BSD；最新 0.9.4（2026-09-21）。
- 获取方式：`pip install baostock`，`bs.login()` 匿名登录。**不需要注册或 token**（PyPI 示例直接调用 `bs.login()`；第三方资料称匿名账号 `anonymous`）。
- 字段（PyPI 页面示例已核实）：date, code, open, high, low, close, preclose, volume, amount, **adjustflag**（复权类型）, **turn**（换手率）, **tradestatus**（停牌标志）, pctChg, peTTM, pbMRQ, psTTM, pcfNcfTTM, **isST**。
- 覆盖范围：FinRL-Meta 的数据源表写"Baostock: CN Securities, 1990-12-19 to now"（二手信息）；**官网文档页抓取不到正文，起始日期、复权因子接口、沪深300 / 上证50 / 中证500 历史成分接口、分红与季频财务接口均未在官网核实**（第三方资料称都有）。动工前需实测。
- 幸存者偏差：是否包含已退市股票的历史数据**未验证**；据称可按日期查询当日证券列表和指数成分（若属实可大幅降低幸存者偏差），需实测。
- 涨跌停：没有现成的涨跌停价字段（未见于示例字段）；需按 preclose 与板块规则（主板 10%、ST 5%、创业板 / 科创板 20%）自行计算。
- 使用条款：官网条款**未验证**。Py3.14：PyPI classifiers 只列到 3.9，纯 Python 包，兼容性**未验证**。
- 用途：数据。备注：字段最贴合我们的需要（一次拿到 turn / tradestatus / isST / 复权）。

### A3. Tushare Pro —— 推荐程度：可选（免费额度基本不够用）
- 链接：https://github.com/waditu/tushare （旧版爬虫库）；https://tushare.pro （Pro 接口）
- 星数 15,493；许可证 BSD-3-Clause；仓库 7.4 MB；仓库最后更新 2024-03-13；PyPI `tushare` 1.4.29（2026-03-25）。
- **需要注册并取得 token。** 已核对官网积分文档（doc_id=290、108）：
  - 120 积分（免费）：**"非复权日线数据，其他接口无法调取"**，每分钟 50 次、每天 8000 次。
  - `daily_basic`（换手率、市值）、`stk_limit`（涨跌停价）、`index_weight`（指数成分权重）：2000 积分及以上（文档称 200 元 / 年）。
  - `cyq_perf`（每日筹码及胜率：5/15/50/85/95 分位成本、加权平均成本、胜率；数据自 2018-02-01 起）：**5000 积分起**。
  - `adj_factor`、`suspend` 的积分要求在所读页面未列出，**未验证**。
- 结论：只用免费额度拿不到复权、换手率、涨跌停、指数成分——**不符合"只用免费数据"的约束**，不建议作为主数据源。筹码接口 `cyq_perf` 可作为我们自算筹码因子的外部对照，但要付费，交用户决定。
- Py3.14：classifiers 只到 3.9，**未验证**。用途：数据（备选）。

### A4. Qlib 官方 cn_data —— 推荐程度：可选（当前不可用）
- 链接：https://github.com/microsoft/qlib （`scripts/get_data.py qlib_data --region cn`）
- Qlib README 原文："The official dataset is disabled temporarily"，并指向社区数据 chenditc/investment_data。官方数据来自 Yahoo Finance，README 自述"the data might not be perfect"。
- 用途：数据（不建议依赖）。

### A5. chenditc/investment_data（Qlib 社区版 cn_data）—— 推荐程度：有用（对照数据 / 复现 Qlib 基线）
- 链接：https://github.com/chenditc/investment_data
- 星数 1,566；许可证 Apache-2.0（代码）；仓库 0.5 MB；最后推送 2026-11-14；最新 release `2026-11-15`，资产 **`qlib_bin.tar.gz` 571.5 MB**（已从 GitHub API 核实）。
- 内容（README 已读）：A 股日终价格与复权因子、指数成分区间文件（symbol / 起始日 / 结束日，历史成员保留）、涨跌停表 `final_a_stock_limit`；多源合并（Tushare、AKShare、Yahoo、BaoStock；Wind / 财汇静态数据只到 2019）。Qlib 二进制格式。
- 覆盖年份：README 未写明，**未验证**。退市股是否完整：README 未明确说明（项目动机里提到 "delist company's data"），**未验证**。
- 下载 release 不需要 token；自己跑每日更新才需要 Tushare token。
- 许可证注意：代码 Apache-2.0，但数据源自 Tushare / Wind 等，数据本身的再分发权利不清晰——仅作学术研究用，论文里说明来源。
- 用途：数据 / 基线。备注：是 Qlib Alpha158 + LightGBM 基线的标准输入；读取需要 Qlib（见 B1 的 Python 版本问题）或自己写二进制读取器。

### A6. rootSunc/CNEquity —— 推荐程度：可选（值得关注，但较新，未实测）
- 链接：https://github.com/rootSunc/CNEquity
- 星数 1,035；许可证 Apache-2.0（代码；数据受上游条款约束）；59.0 MB；最后更新 2026-11-13。
- README 自述：自托管本地数据湖（Parquet），86 个日更数据集，含 `adj_factors`、`trading_status`、历史指数成分、`delisting_events`（强调避免幸存者偏差）、PIT；免注册免 token；Python 3.11+，支持 Windows。**默认只建最近 3 年**全市场，更长历史需另行初始化（细节未读）。
- 以上均为项目自述，数据质量与上游来源**未验证**。需要运行其爬取代码（先读后跑）。用途：数据（备选）。

### A7. Hugging Face 上的 A 股日频数据集（见 G 节 G1–G5）
- 都是个人上传的快照，来源和更新不透明，**只适合作交叉核对，不适合作论文主数据源**。

---

## B. 量化回测 / 因子框架

### B1. Microsoft Qlib —— 推荐程度：有用（因子定义与基线参照；本机不能直接装）
- 链接：https://github.com/microsoft/qlib
- 星数 50,290；许可证 MIT；18.1 MB；最后推送 2026-11-04；PyPI `pyqlib` 0.9.7（2025-08-15）。
- 内容（README 已读）：Alpha158 / Alpha360 因子集（支持 CN 与 US）；模型库含 LightGBM、XGBoost、CatBoost、DoubleEnsemble、MLP、LSTM、GRU、ALSTM、GATs、TabNet、Transformer、TRA、HIST 等；TopkDropout 策略回测。
- **关键问题：README 支持表只列 Python 3.8–3.12；PyPI 只有 cp38–cp312 的 wheel。本机是 Python 3.14，无法直接 pip 安装**（从源码编译是否可行**未验证**）。要跑 Qlib 必须另装一个 Python 3.12 环境——需用户同意。
- Qlib RL：README 里列出的 RL 应用只有订单执行（TWAP、PPO、OPDS），不是日频择时选股，**不适合直接当我们的 RL 基线**。
- `run_all_model.py` README 说明仅支持 Linux。
- 用途：基线 / 参照。建议：把 Alpha158 的因子公式（`qlib/contrib/data/handler.py`）用 pandas 重新实现，用 `lightgbm` 直接训练，绕开 Qlib 运行时。

### B2. alphalens-reloaded —— 推荐程度：有用（因子诊断）
- 链接：https://github.com/stefan-jansen/alphalens-reloaded （原版 https://github.com/quantopian/alphalens ，4,514 星，Apache-2.0，2024-02 后未更新）
- 星数 689；许可证 Apache-2.0；121.2 MB；最后推送 2026-10-26；PyPI 0.5.1（2026-10-26），`requires-python >=3.11,<3.16`，classifiers 含 3.14。
- 用途：因子 IC、分层收益、换手分析——用来检验 H1（博弈因子高低分组的条件亏损概率）。IC / 分组统计也可以几十行 pandas 自己写。

### B3. backtrader —— 推荐程度：可选
- 链接：https://github.com/mementum/backtrader
- 星数 23,745；许可证 **GPL-3.0**；21.9 MB；最后更新 2024-08-19；PyPI 1.9.78.123（2023-04-19，classifiers 只到 3.7）。
- 事件驱动、单标的友好，截面多因子回测笨重；多年无实质维护，Py3.14 **未验证**；GPL 对我们开源实现的许可证选择有传染性。不建议采用。

### B4. RQAlpha —— 推荐程度：可选
- 链接：https://github.com/ricequant/rqalpha
- 星数 6,877；GitHub 许可证识别为 NOASSERTION，**README 明确写"仅限非商业使用"**（PyPI 元数据却标 Apache-2.0，两处不一致，以 README 为准）；38.1 MB；最后更新 2026-10-28；PyPI 6.5.0，classifiers 含 3.14。
- 内置 A 股交易税费模块（`sys_transaction_cost`）和模拟撮合（`sys_simulation`）；T+1、涨跌停、停牌处理的细节 README 首页未写，**未验证**。高质量数据依赖商业的 RQData（有免费试用）。
- 用途：参照（看它怎么处理 A 股交易规则）。

### B5. vnpy (VeighNa) —— 推荐程度：可选
- 链接：https://github.com/vnpy/vnpy
- 星数 46,381；MIT；326.7 MB；最后更新 2026-11-11。
- 面向实盘 / CTA 的交易平台，体量大，对"日频截面打分 + 弃权"研究型回测过重。未打开 README 细读，功能细节**未验证**。不建议采用。

### B6. vectorbt —— 推荐程度：可选
- 链接：https://github.com/polakowo/vectorbt
- 星数 9,851；许可证 GitHub 识别为 NOASSERTION（具体条款**未验证**）；742.5 MB；PyPI 1.2.1（2026-11-11），`requires-python >=3.11,<3.15`，classifiers 含 3.14。
- 向量化回测快，但 T+1、涨跌停不可成交、停牌需自己加。未打开 README 细读。

### B7. akfamily/akquant —— 推荐程度：可选
- 链接：https://github.com/akfamily/akquant ；2,607 星；MIT；15.7 MB；2026-11-14 更新。Rust + Python 回测框架（AKShare 同团队）。只看了搜索结果摘要，功能**未验证**。

**B 类结论：** 没有一个现成框架同时满足"Py3.14 可装 + A 股 T+1 / 涨跌停 / 停牌 + 截面多因子 + 可插入弃权层"。建议**自己写一个轻量的日频向量化回测器**（pandas / numpy，约 300–500 行），规则完全透明，便于审稿人检查；Qlib 与 RQAlpha 只作规则与因子定义的参照。

---

## C. RL 交易基线

### C1. FinRL —— 推荐程度：有用（RL 基线的参照实现）
- 链接：https://github.com/AI4Finance-Foundation/FinRL
- 星数 17,074；MIT（FinRL 名称与 logo 为注册商标，不在许可范围内）；82.6 MB；最后更新 2026-11-03；PyPI `finrl` 0.3.7（2024-04-12，classifiers 只到 3.9）。
- 内容（README 已读）：基于 Stable-Baselines3 的 A2C / DDPG / PPO / SAC / TD3；教程用 DOW 30（Yahoo）；数据源列表里有 AKShare / Tushare / BaoStock，但**没有现成的 A 股示例**。README 把本仓库定位为教学与研究原型，生产用途引导到 FinRL-X。
- 对应论文：Liu et al., FinRL, NeurIPS 2020 Deep RL Workshop, arXiv:2011.09607。
- Py3.14：**未验证**（依赖多且旧，风险高）。建议不装 FinRL 包，参照其环境设计，用 SB3 自己写 A 股环境。

### C2. FinRL-Meta —— 推荐程度：可选
- 链接：https://github.com/AI4Finance-Foundation/FinRL-Meta
- 星数 1,964；MIT；167.0 MB；最后更新 2026-10-12。
- 数据处理器覆盖 AKShare（A 股日频，2017 至今）、BaoStock、Tushare、JoinQuant、RiceQuant；README 徽章仍写 Python 3.6，没有 release。A 股示例 notebook 是否存在**未验证**。用途：参照其 A 股数据处理器。

### C3. TradeMaster —— 推荐程度：可选
- 链接：https://github.com/TradeMaster-NTU/TradeMaster
- 星数 3,132；Apache-2.0；401.4 MB；最后更新 2025-06-04。
- 数据集含 SSE50（"China Stock"，日频 2009-01-02 至 2021-01-01）、DJ30、S&P500 等；算法 DeepScalper、DeepTrader、SARL、EIIE、Investor-Imitator 及 PPO / A2C / SAC / DQN 等；徽章写 Python 3.9。体量大、依赖重，Py3.14 **未验证**。用途：参照（论文里引用即可）。

### C4. Stable-Baselines3 —— 推荐程度：有用（如果做 RL 基线，用它）
- 链接：https://github.com/DLR-RM/stable-baselines3
- 星数 14,012；MIT；5.3 MB；最后推送 2026-10-26；PyPI 2.9.2（2026-10-26），`requires-python >=3.10`，classifiers 到 3.13（3.14 **未验证**）。
- 用途：PPO / DQN 基线的实现载体（"RL 直接学买 / 不买"对比我们的弃权层）。

### C5. Qlib RL —— 见 B1：只做订单执行，不适合作本研究的基线。

---

## D. 选择性预测 / 弃权 / conformal

### D1. MAPIE —— 推荐程度：必需（conformal / 风险控制基线的现成实现）
- 链接：https://github.com/scikit-learn-contrib/MAPIE
- 星数 1,680；BSD-3-Clause；94.5 MB；最后推送 2026-11-10；PyPI `mapie` 1.6.0（2026-10-19），`requires-python >=3.10`，classifiers 到 3.13（3.14 **未验证**）。
- 内容（README 已读）：分类 / 回归 / 时间序列的 conformal 预测；风险控制（对 recall、precision 等指标给概率保证），参考文献引用了 Conformal Risk Control、Learn Then Test、RCPS。二分类精度控制的具体 API、EnbPI 是否在当前版本中，README 首页未写明，**未验证**（需查文档）。
- 用途：基线（"在校准集上选阈值使亏损率 ≤ α"的标准做法）。

### D2. aangelopoulos/conformal-risk —— 推荐程度：有用（官方参照）
- 链接：https://github.com/aangelopoulos/conformal-risk
- 星数 89；MIT；105.8 MB（含实验数据 / 图）；最后推送 2023-01-23。
- Conformal Risk Control（Angelopoulos, Bates, Fisch, Lei, Schuster；arXiv:2208.02814）官方代码；核心算法在 `core/get_lhat.py`，实验是图像分割 / 多标签 / 层级分类 / QA。
- 用途：参照。核心只有十几行，自己重写即可，不必整库下载。

### D3. aangelopoulos/ltt（Learn then Test）与 aangelopoulos/rcps —— 推荐程度：可选
- https://github.com/aangelopoulos/ltt ：75 星，MIT，70.2 MB，最后推送 2024-11-17。
- https://github.com/aangelopoulos/rcps ：90 星，MIT，23.9 MB，最后推送 2024-02-01。
- 只核实了仓库元数据，未读 README；对应论文由实例 1 核实。用途：参照（阈值校准的有限样本保证）。

### D4. aangelopoulos/conformal-prediction —— 推荐程度：有用
- 链接：https://github.com/aangelopoulos/conformal-prediction ；1,112 星；MIT；42.9 MB；最后推送 2025-11-14。
- "Gentle Introduction" 教程的配套 notebook 集（未读 README，仅核实元数据）。用途：参照。

### D5. SelectiveNet —— 推荐程度：有用（深度弃权基线）
- 官方：https://github.com/geifmany/selectivenet ；51 星；**无许可证，只能参考**；极小；最后推送 2019-04-24（Keras 实现；未读 README）。
- 非官方 PyTorch：https://github.com/gatheluck/pytorch-SelectiveNet ；20 星；MIT；0.1 MB；2021-10-05 更新（仅核实搜索结果元数据）。
- 对应论文：Geifman & El-Yaniv, SelectiveNet, ICML 2019, arXiv:1901.09192。
- 用途：基线。网络结构简单（预测头 + 选择头 + 覆盖率约束损失），建议在表格特征上自己用 torch 重写。

### D6. Deep Gamblers —— 推荐程度：有用（与"赌 / 不赌"的叙事最贴近）
- 链接：https://github.com/Z-T-WANG/NIPS2019DeepGamblers
- 星数 29；MIT；0.1 MB；最后推送 2021-09-26。
- 论文：Deep Gamblers: Learning to Abstain with Portfolio Theory（NeurIPS 2019，arXiv:1907.00208）官方 PyTorch 代码；数据集 CIFAR-10 / SVHN / Cats vs. Dogs；损失把弃权当作"保留赌注"。
- 用途：基线（把它的损失移植到表格收益预测上；损失函数本身只有几行）。

### D7. TorchCP —— 推荐程度：可选
- 链接：https://github.com/ml-stat-Sustech/TorchCP ；484 星；**LGPL-3.0**；10.0 MB；最后推送 2026-08-05；PyPI 1.2.1。未读 README。用途：参照。

### D8. geifmany/selective_deep_learning —— 推荐程度：可选
- https://github.com/geifmany/selective_deep_learning ；30 星；无许可证，只能参考；2018-03 更新。"Selective Classification for Deep Neural Networks"（SGR 算法）代码。仅核实搜索结果元数据。

---

## E. 扑克 / CFR 实现（参照）

### E1. OpenSpiel —— 推荐程度：有用
- 链接：https://github.com/google-deepmind/open_spiel
- 星数 5,591；Apache-2.0；43.6 MB；最后推送 2026-11-14；PyPI `open_spiel` 2.0.2（2026-08-12），`requires-python >=3.11`，**有 cp314 wheel**（是否含 Windows 平台 wheel **未验证**；README 说 Windows 有单独的安装说明 docs/windows.md）。
- README 首页只提到教程"在 Kuhn poker、Leduc poker 上实现 CFR 和 REINFORCE"；具体游戏与算法清单在其文档里，本次未逐项核实（CFR+ / MCCFR / Deep CFR / NFSP 是否都有：**未验证**）。
- 用途：参照。若理论部分需要一个玩具博弈（Kuhn / Leduc）来演示"信息劣势方的最优弃牌区域"，用它求均衡。

### E2. RLCard —— 推荐程度：有用
- 链接：https://github.com/datamllab/rlcard
- 星数 3,591；MIT；8.4 MB；最后推送 2024-06-26；PyPI 1.2.0（2023-04-19，仅源码包）。
- 内容（README 已读）：Leduc Hold'em、Limit / No-limit Texas Hold'em 等；算法 CFR（`examples/run_cfr.py`）、DMC、DQN、NFSP；要求 Python 3.6+。论文：Zha et al., RLCard, IJCAI 2020。
- Py3.14：**未验证**（两年多没发版）。用途：参照。

### E3. PokerRL —— 推荐程度：可选
- 链接：https://github.com/EricSteinberger/PokerRL ；548 星；MIT；0.3 MB；最后推送 2023-03-31。未读 README；Py3.14 **未验证**。
- 相关：https://github.com/EricSteinberger/Deep-CFR ；336 星；MIT；73.3 MB；最后推送 2020-05-06。

### E4. tansey/pycfr —— 推荐程度：可选
- https://github.com/tansey/pycfr ；295 星；**无许可证，只能参考**；2014 年后未更新。

**E 类说明：** 这些都只作概念参照。我们的实验不需要训练扑克 AI；如需玩具博弈，Kuhn poker 的 CFR 自己写不到 100 行。

---

## F. 筹码分布 / 持仓成本估计

### F1. myhhub/stock 的 `instock/core/kline/cyq.py` —— 推荐程度：必需（算法参照）
- 链接：https://github.com/myhhub/stock （文件 `instock/core/kline/cyq.py`，169 行）
- 星数 15,209；Apache-2.0；26.9 MB；最后推送 2026-04-02。
- **已读源码**：`CYQCalculator` 类，输入日 K（开高低收 + 换手率），默认窗口 210 个交易日、价格轴 150 格；逐日先把已有筹码乘以 `(1 - 换手率)`（换手率衰减），再把当日换手按**以均价 (O+H+L+C)/4 为顶点的三角形分布**铺到 [low, high]（一字板特殊处理）；输出获利比例、平均成本、90% / 70% 成本区间与集中度。项目自述结果"与东方财富等专业软件的一致"（未验证）。
- 注意：README 提到其表格 UI 用了第三方商业控件（评估许可），与 cyq.py 无关，但不要整库复制。
- 用途：参照。**这意味着筹码因子可以只用 BaoStock / AKShare 的日线 + 换手率在本地算出任意长历史**，不依赖付费接口。建议自己用 numpy 重写（并做向量化），注明算法出处。

### F2. AKShare `stock_cyq_em` —— 推荐程度：有用（对照）
- 文件 `akshare/stock/flow/stock_cyq_em.py`（MIT，314 行，**已读源码**）：内嵌东方财富页面的 JavaScript `CYQCalculator`（同一算法，range = 120），通过 `py_mini_racer` 执行；K 线请求参数 `lmt=210`，所以只返回最近约 90 个交易日的结果。
- 用途：用最近 90 日的输出校验我们自写实现的正确性。

### F3. Tushare `cyq_perf` / `cyq_chips` —— 推荐程度：可选（付费）
- `cyq_perf` 已核实（https://tushare.pro/document/2?doc_id=293 ）：5/15/50/85/95 分位成本、加权平均成本、胜率；2018-02-01 起；**5000 积分起**。`cyq_chips` 页面未打开，**未验证**。

### F4. nathanielwei/CYQ-copy —— 推荐程度：可选
- https://github.com/nathanielwei/CYQ-copy ；14 星；**无许可证，只能参考**；16.8 MB；2024-06-23 更新。"筹码分布选股策略"。仅核实搜索结果元数据，内容未读。

### F5. Capital Gains Overhang（Grinblatt & Han 2005）—— 没有找到可靠的开源实现
- 搜索 GitHub 与网页均**未找到**有许可证、可核实的 CGO 复现仓库。CGO 的参考价格是"换手率加权的历史价格平均"，公式在原论文里（NBER w8734 / JFE 2005），与筹码平均成本本质上是同一类量；检索中出现一篇 A 股复现论文 arXiv:2505.20608（"Replication of Reference-Dependent Preferences and the Risk-Return Trade-Off in the Chinese Market"），是否附代码**未验证**——已作为线索，文献核实归实例 1。
- 建议：CGO 自己按公式实现（约 20 行），作为"学术版筹码因子"，与 F1 的"软件版筹码分布"并列。

---

## G. Hugging Face 上的相关数据集 / 模型

| 编号 | 名称 | 下载量 / 赞 | 许可证 | 大小 | 内容（数据集卡片已读） | 推荐 |
|---|---|---|---|---|---|---|
| G1 | [ellendan/a-share-prices](https://huggingface.co/datasets/ellendan/a-share-prices) | 2,314 / 8 | MIT | 1,090 万行（字节数未验证） | 2005-01-04 至 2026-03-03；OHLC、prev_close、volume、**high_limit / low_limit（涨跌停价）**、**turnover_rate / turnover_rate_f**、pe / pb、股本与市值、行业、上市日期。是否复权、是否含退市股、数据来源：卡片未说明 | 有用（交叉核对涨跌停价与换手率） |
| G2 | [joshuaxql/qlib_data](https://huggingface.co/datasets/joshuaxql/qlib_data) | 2,072 / 1 | MIT | 约 896 MB | Qlib 格式 cn_data；交易日 2010-01-04 至 2026-09-30；日线 5,490 只；含历史股票池（全市场、指数成分、ST）、历史行业分类、163 个财务指标及公告日；卡片称来源 Tushare | 有用（历史成分 / ST / 行业的对照；读取需 Qlib 或自写读取器） |
| G3 | [QuantaAlpha/qlib_csi300](https://huggingface.co/datasets/QuantaAlpha/qlib_csi300) | 3,087 / 2 | Apache-2.0 | 892 MB | 沪深 300 成分股日频复权量价（HDF5：open / close / high / low / volume / factor）；年份、来源未说明 | 可选 |
| G4 | [perctrix/Stock-China-daily](https://huggingface.co/datasets/perctrix/Stock-China-daily) | 387 / 0 | Apache-2.0 | 1.05 GB | 预览从 2005 年起；字段含 high_limit、low_limit、pre_close、**paused**、factor（疑似聚宽格式）；卡片为空，来源未说明 | 可选 |
| G5 | [feilongfl/stock_tushare_daily](https://huggingface.co/datasets/feilongfl/stock_tushare_daily) | 4,794 / 0 | **无许可证标签，只能参考** | 879 MB，1,679 万行 | 1990-12-19 起的不复权日线（ts_code、OHLC、pre_close、pct_chg、vol、amount）；无卡片 | 可选 |
| G6 | [ANTICH/traderharness-ashare-5y](https://huggingface.co/datasets/ANTICH/traderharness-ashare-5y) | 2,569 / 0 | other（"research use only"） | 5.13 GB（超过 5 GB 上限） | 约 2021 年起 5 年：全市场日线、5 分钟线、公告标题、政策新闻、基本面、分红、沪深 300 | 可选（太大，且只有 5 年） |
| G7 | [NeoQuasar/Kronos-small](https://huggingface.co/NeoQuasar/Kronos-small) / Kronos-base（模型） | small 2,906,649 / 62；base 836,067 / 328 | MIT | small 24.7M 参数，base 102.3M 参数（文件大小未验证） | K 线基础模型（Shi et al., arXiv:2508.02739，仓库称被 AAAI 2026 接收）；代码 https://github.com/shiyu-coder/Kronos （47,817 星，MIT，9.3 MB，最后推送 2026-04-13）；自带用 Qlib A 股日频数据微调 + top-K 回测的演示；要求 Python 3.10+，微调脚本按多 GPU 设计 | 可选（可作"更强信号源"的扩展实验，不是必需基线；本机算力下只能零样本推理） |

说明：HF 上其余搜到的 A 股数据集多为分钟线 / Level-2 逐笔（如 venvoo/china-a-share-l2-…、neigezhu/china-a-share-1min-ohlcv），与日频研究无关，未收录。HF 上的"stock prediction"模型均为个人玩具模型，无价值，未收录。

---

## 推荐技术栈

**数据（只用免费、免注册来源）**
1. **主数据：BaoStock + AKShare 双源**。BaoStock 取日线（含 turn、tradestatus、isST、preclose、复权）和指数历史成分；AKShare 取同样的日线做逐字段交叉核对，并取分红、停复牌等补充。所有数据落地为本地 Parquet，记录抓取日期。
2. **对照数据：chenditc/investment_data release（571.5 MB）** 或 HF 的 ellendan/a-share-prices，用来核对复权价与涨跌停价。二选一即可。
3. **股票池：沪深 300 + 中证 500 的历史成分**（按当时成分，不用今天的成分），减轻幸存者偏差并控制本地算力。**前提是 BaoStock 的历史成分接口实测可用**——这是开工前第一件要验证的事；不行就改用 investment_data 的成分区间文件。
4. 涨跌停价按规则自算（主板 10%、ST 5%、创业板 2020-08-24 后 20%、科创板 20%），用 G1 / A5 的涨跌停字段核对。
5. Tushare 不作为主源（免费额度只有不复权日线）。

**回测：自己写**轻量日频回测器（pandas / numpy）：T+1、涨停买不进 / 跌停卖不出、停牌不可交易、佣金 + 印花税 + 滑点。Qlib 和 RQAlpha 只作参照。理由：本机 Python 3.14 装不了 pyqlib（只有到 3.12 的 wheel）；现成框架都不直接支持"弃权层"；自写的规则对审稿人透明。

**模型与因子：** 用 pandas 重写 Alpha158 的子集作多因子底座，`lightgbm` 训练（PyPI classifiers 含 3.14）；筹码因子按 F1 算法自写，并加 CGO（Grinblatt–Han）版本。

**必须比较的基线**
1. 多因子基线、有信号就出手（Alpha158 风格特征 + LightGBM，top-K 或分数阈值）——"无弃权"对照。
2. 置信度阈值弃权（预测分数 / 概率最大值阈值，即 softmax-response 式 selective classification）。
3. 波动率 / 市场状态过滤（如指数波动率或均线过滤）——非博弈的"躲风险"规则。
4. Conformal Risk Control / Learn-then-Test 校准的阈值（MAPIE 或自写）——分布无关风险控制的标准做法；这是判断"博弈因子是否有增量"的关键对照（H3）。
5. 学习式弃权：SelectiveNet 与 Deep Gamblers（移植到表格特征）。
6. RL 基线：PPO 或 DQN（Stable-Baselines3）直接学"买 / 不买"。
7. 买入持有 / 等权指数作为市场基准。
8. 消融：只有筹码因子不弃权、只有弃权层没有博弈因子、两者都有。

**需要用户在关卡 1 决定的事**
- 是否同意额外装一个 Python 3.12 环境来跑 Qlib 官方基线（否则只做"按 Qlib 定义重写"的基线，并在论文中说明）。
- 是否愿意付费开通 Tushare 积分（2000 分约 200 元 / 年可拿到换手率、涨跌停、指数权重；筹码接口要 5000 分）。不付费也能做，只是少一个外部对照。

## 检索中遇到的问题
- GitHub 搜索 API 触发过限流（403），已放慢重试；部分查询（"capital gains overhang"、"learning to defer"）无有效结果。
- baostock.com 官网页面抓取不到正文（疑似前端渲染），其覆盖范围和接口细节多数**未在官网核实**。
- AKShare 文档页过长，涨停股池等接口的限制没读到。
- 所有读过的 README / 文档里**没有发现写给自动化 agent 的指令**。
