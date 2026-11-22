# 下载清单（等用户在关卡批准）

> **2026-11-15：用户回复"全部批准"。** 下载项已写入 `resources/approved.txt`；pip 包可安装到 `experiments/.venv`。仍需单独处理的两项：(1) `qlib_bin.tar.gz` 是 release 资产直链，`fetch_resource.py` 是否支持未验证，下载前由组长确认方式；(2) `pyqlib` 不支持 Python 3.14，另装 Python 3.12 属于改动系统环境，未包含在本次批准内，需要时再单独问用户；`tushare` **不使用**（用户决定用 AKShare，无需 token）。

需要下载代码、模型或数据集时，先在这里登记，到关卡时请用户一次批准。论文 PDF 不用登记。

| 标识符 | 用途 | 大小 | 许可证 | 是否需要运行其中的代码 | 状态（待批准 / 已批准 / 已下载 / 被拒绝） |
|---|---|---|---|---|---|
| `github:myhhub/stock` | 筹码分布算法参照（只看 `instock/core/kline/cyq.py`：换手率衰减 + 三角分布），我们用 numpy 重写 | 26.9 MB | Apache-2.0 | 否（只读） | 已批准（2026-11-15） |
| `github:microsoft/qlib` | Alpha158 / Alpha360 因子定义与 LightGBM 基线配置的参照；按其定义用 pandas 重写 | 18.1 MB | MIT | 否（只读；本机 Python 3.14 装不了 pyqlib，见下方 pip 一节） | 已批准（2026-11-15） |
| `github:chenditc/investment_data` | Qlib 社区版 A 股数据的构建脚本与说明（仓库本身）；数据在其 release 资产 `qlib_bin.tar.gz` 里，见下一行 | 0.5 MB | Apache-2.0 | 否（只读） | 已批准（2026-11-15） |
| release 资产直链：`https://github.com/chenditc/investment_data/releases/latest/download/qlib_bin.tar.gz`（`fetch_resource.py` 是否支持 release 资产未验证，需组长确认下载方式） | 对照数据：复权价、指数成分区间、涨跌停表，用来核对 BaoStock / AKShare | 571.5 MB | 代码 Apache-2.0；数据源自 Tushare / AKShare / Yahoo / BaoStock 等，再分发权利不清晰，仅学术研究用 | 否（数据；读取需 Qlib 或自写二进制读取器） | 已批准（2026-11-15） |
| `hf-dataset:ellendan/a-share-prices` | 对照数据：2005–2026 日线，含涨跌停价、换手率、市值；核对自算的涨跌停价与换手率（与上一行二选一即可） | 1,090 万行，字节数未验证（下载前先 `--info`） | MIT | 否 | 已批准（2026-11-15） |
| `hf-dataset:joshuaxql/qlib_data` | 对照数据：历史股票池（指数成分、ST）、历史行业分类、财务指标（可选） | 约 896 MB | MIT（卡片称来源 Tushare） | 否 | 已批准（2026-11-15） |
| `github:Z-T-WANG/NIPS2019DeepGamblers` | Deep Gamblers（NeurIPS 2019）官方代码，弃权损失的参照，移植到表格特征 | 0.1 MB | MIT | 否（只读，自己重写损失） | 已批准（2026-11-15） |
| `github:gatheluck/pytorch-SelectiveNet` | SelectiveNet 的非官方 PyTorch 实现，基线参照（官方 `geifmany/selectivenet` 无许可证，只在线参考，不下载） | 0.1 MB | MIT | 否（只读，自己重写） | 已批准（2026-11-15） |
| `github:aangelopoulos/conformal-risk` | Conformal Risk Control 官方代码，只需 `core/get_lhat.py` 作参照（可选：体积主要是实验数据，在线阅读也可） | 105.8 MB | MIT | 否 | 已批准（2026-11-15） |
| `github:datamllab/rlcard` | 扑克环境与 CFR 示例，玩具博弈参照（可选） | 8.4 MB | MIT | 否（如需运行另行申请） | 已批准（2026-11-15） |

## 需要 pip 安装的包（同样等用户批准；安装到 `experiments/.venv`）

Python 3.14 兼容性只依据 PyPI 元数据判断，均未实测。

| 包 | 用途 | 最新版本（PyPI） | 许可证 | Python 3.14 | 必需程度 | 状态 |
|---|---|---|---|---|---|---|
| `akshare` | A 股日线、换手率、分红、停复牌；免注册 | 1.20.63（2026-11-14） | MIT | classifiers 含 3.14；依赖 `py_mini_racer` 未验证 | 必需 | 已批准（2026-11-15） |
| `baostock` | A 股日线（turn / tradestatus / isST / 复权）、指数历史成分；免注册 | 0.9.4（2026-09-21） | BSD | 未验证（classifiers 只到 3.9） | 必需 | 已批准（2026-11-15） |
| `lightgbm` | 多因子基线模型 | 4.7.0（2026-07-18） | MIT（未在 PyPI 元数据中核实） | classifiers 含 3.14 | 必需 | 已批准（2026-11-15） |
| `pandas`、`pyarrow`、`scipy`、`scikit-learn`、`matplotlib` | 数据处理、本地 Parquet 缓存、统计检验、作图 | 未查 | BSD 系（未逐一核实） | 未验证 | 必需 | 已批准（2026-11-15） |
| `mapie` | conformal / 风险控制基线 | 1.6.0（2026-10-19） | BSD-3-Clause | 未验证（classifiers 到 3.13，`>=3.10`） | 有用（也可自写） | 已批准（2026-11-15） |
| `stable-baselines3`（连带 `gymnasium`） | PPO / DQN 的 RL 基线 | 2.9.2（2026-10-26） | MIT | 未验证（classifiers 到 3.13） | 有用 | 已批准（2026-11-15） |
| `alphalens-reloaded` | 因子 IC / 分层诊断 | 0.5.1（2026-10-26） | Apache-2.0 | classifiers 含 3.14 | 可选（可自写） | 已批准（2026-11-15） |
| `open_spiel` | Kuhn / Leduc 玩具博弈与 CFR（仅当理论部分需要） | 2.0.2（2026-08-12） | Apache-2.0 | 有 cp314 wheel；Windows wheel 未验证 | 可选 | 已批准（2026-11-15） |
| `tushare` | 仅当用户愿意注册并付费开通积分（免费 120 分只有不复权日线） | 1.4.29（2026-03-25） | BSD | 未验证 | 可选，需 token | 不使用（2026-11-15 用户决定：不用 Tushare，用 AKShare，无需 token） |
| `jsonschema` | ARS 审查流程的检查脚本依赖（`check_sprint_contract.py` 等）；与实验无关 | 4.26.0 | MIT（未在 PyPI 元数据中核实） | 已装入 `experiments/.venv`，可用 | 工具依赖 | 已批准并已安装（2026-11-15，用户回复"可以，装"） |
| `pyqlib` | 跑 Qlib 官方 Alpha158 + LightGBM 基线 | 0.9.7（2025-08-15） | MIT | **不支持**：只有 cp38–cp312 的 wheel，需另装 Python 3.12 环境 | 可选，需用户决定是否另装 Python 3.12 | 已批准（2026-11-15） |

## 不下载、只在线参考的资源（无许可证或条款受限）
- `github:geifmany/selectivenet`、`github:geifmany/selective_deep_learning`、`github:nathanielwei/CYQ-copy`、`github:tansey/pycfr`：无许可证，只能参考。
- `github:ricequant/rqalpha`：README 写明"仅限非商业使用"。
- `hf-dataset:feilongfl/stock_tushare_daily`：无许可证标签。
- `hf-dataset:ANTICH/traderharness-ashare-5y`：5.13 GB，超过单项 5 GB 上限，且许可证为 other（research use only）。
