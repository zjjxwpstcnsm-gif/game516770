# Game Alpha · 游戏行业投资情报中心

面向 A 股游戏 ETF 的事件驱动研究平台。默认研究 516770，对照 159869、516010。区分游戏热度与可证实的 ETF 经济利益关联；研究提示不是收益承诺，不执行证券交易。

## 架构

- React + TypeScript + Vite + Tailwind CSS + Recharts，默认深色、手机优先。
- Python 3.12 采集、校验、事件版本、技术指标、规则信号、事件研究。
- 静态 JSON 存储在 `public/data`，GitHub Actions 自动更新，GitHub Pages 发布。
- Agnes 只在后台执行结构化解释；前端不访问 AI，也不接触密钥。
- 无 AI 密钥仍可采集、核验和运行规则引擎。缺失数据明确显示，不填充虚构行情。

## 本地运行

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
npm ci
python -m pipeline.run
python -m pipeline.run --validate-only
npm run dev
```

开发地址以 Vite 输出为准，项目路径为 `/game516770/`。路由使用 hash，直接刷新详情页不依赖服务器 rewrite。

```bash
python -m pytest -q
npm test
npm run typecheck
npm run build
npm run preview
```

`package-lock.json` 锁定前端依赖，Python 在 requirements.txt 限定兼容版本范围。

## 自动更新与部署

北京时间（Asia/Shanghai）：

- 每天 08:20：资讯与事件更新。
- 周一至周五 17:25：收盘研究更新。节假日由有效行情日期和交易日判断降级，不伪造交易。
- 周日 20:30：未来事件更新。
- Actions → Research and deploy → Run workflow：手动补跑。

这些定时入口复用同一完整流水线，避免多条数据处理路径漂移。GitHub 定时任务可能延迟、漏执行；公开仓库长期无活动时可能被平台停用。前端展示实际时间和过期警告，不保证精确准点。

首次设置：

1. 仓库 Settings → Pages → Build and deployment → Source 选择 **GitHub Actions**。
2. Settings → Actions → General，允许工作流运行；如组织策略限制写入，允许本仓库工作流保存数据。
3. Actions → Research and deploy → Run workflow。
4. 成功后检查 deploy job 和实际页面，不要只凭构建成功认定上线。

预期地址： https://zjjxwpstcnsm-gif.github.io/game516770/

`concurrency` 串行生产任务；机器人数据提交带 `[skip ci]` 且 push 忽略数据目录，避免递归。测试与数据校验通过后才构建和发布。失败不会覆盖已部署网站；上一次快照仍可查看，但前端必须提示过期。

## Agnes 配置

打开 https://github.com/zjjxwpstcnsm-gif/game516770/settings/secrets/actions

- Secrets → New repository secret → `AGNES_API_KEY`。
- 可选 Variables：`AGNES_BASE_URL=https://apihub.agnes-ai.com/v1`、`AGNES_MODEL=agnes-3.0-flash`。

本地参考 `.env.example`，用 shell 环境变量注入；不要把真实密钥提交到 Git，也不要使用 `VITE_` 前缀。不要在聊天中粘贴密钥。程序不会自动假定历史会话密钥可用。

客户端统一限制尝试次数、退避、Retry-After、总时间、并发、每日调用和 token 预算；永久鉴权错误不盲目重试。Schema 错误仅有限修复，失败时保留事实并标注 AI 暂不可用。持久缓存和预算账本只保存公开事实的分析结果与汇总计数，不保存密钥或原始提示词。

Agnes 实际配额和价格由账户决定，预算不是免费额度承诺。详细环境变量和实现见 `pipeline/ai`。

## 数据与研究规范

- 新闻保留原始链接、采集时间，缺失发布时间为 null。
- 网页是非可信数据，不执行网页指令，不运行采集内容。
- 事件的消息公布、系统首次发现、实际发生时间分别保存；日期变更保留版本。
- 过去事件补录不能冒充当时系统已知。日精度来源不能捏造精确发布时间。
- 场内交易价格、净值、估值分离；价格带来源、日期和复权标记。
- 持仓为披露期快照，不是实时持仓。缺权重或未核实收益权益时不计算伪精确受益。
- 游戏科学、灵游坊的作品热度不自动等于 A 股成分股利润。缺证据时仅讨论行业情绪。
- SSS 是热度等级，不是买入评级。规则评分是启发式，绝不是预测概率。
- 数据不完整或过期时暂停方向性判断，不把昨日信号改日期冒充今天。
- 历史事件窗口以交易日映射，未发生的后续窗口留空。两个案例不构成统计规律。
- 同时展示基准、费用/滑点、样本量和可用性约束；无可靠时点数据不声称完成有效历史策略验证。

## 配置与维护

- `config/watchlist.yaml`：游戏别名、官方来源、Steam 标识、人工核实里程碑。
- `config/sources.yaml`：来源、启用状态、超时与可靠性。
- `config/strategy.yaml`：标的、观察窗口、指标、阈值与策略版本。

增加游戏先补稳定 ID 与别名，再补官方证据；不要仅因媒体夸张标题手动提升为 SSS。新增来源优先 RSS/官方 API，检查 robots、条款、频率和字段单位。修改策略要更新版本，保留历史输出，不使用后验最优参数伪装事前策略。

`public/data/reports/` 保留历史日报；行情、事件、信号与系统状态按流水线持久化。禁止存储大量原始网页全文或图片。个人持仓若启用只能存于浏览器，不公开上传。

## 常见问题

- **AI 不可用**：检查 Secret 名称、额度、鉴权和系统页错误类型；有效采集数据仍保留。
- **行情源故障**：检查来源状态和最后行情日，使用明确标注的历史快照；不要手动填价格。
- **Pages 404**：检查 Source 是否 GitHub Actions、部署 job 是否成功，以及路径 `/game516770/`。
- **工作流不执行**：检查 Actions 权限、默认分支、schedule 状态；使用 Run workflow 补跑。
- **提交被拒绝**：检查分支保护或工作流写入权限；不强推覆盖他人提交。
- **未来无事件**：表示没有满足核实条件的数据，不代表行业一定没有事件。

## 证据与交付记录

官方资料核实清单见 `research.json`；实际测试、运行和部署验收记录见 `docs/DELIVERY.md`。清单里的来源核实与运行时采集是不同证据，不混用。

## 风险声明

本站为公开资料整理和研究工具，不构成个性化投资建议，不保证准确、完整或收益。事件与价格相关不代表因果关系。市场、流动性、政策、数据延迟、模型错误、交易成本和样本偏差均可能造成损失。请自行核实原始来源并承担投资决策责任。
