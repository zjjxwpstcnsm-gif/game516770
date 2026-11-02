# Agnes 客户端

`AgnesClient().analyze(records)` 是同步批次接口。所有新闻、日报等 AI 调用都应复用它，不在前端调用 API。

- 环境变量：`AGNES_API_KEY`、`AGNES_BASE_URL`、`AGNES_MODEL`。
- 预算变量：`AGNES_DAILY_CALL_LIMIT=50`、`AGNES_DAILY_TOKEN_LIMIT=100000`、`AGNES_DAILY_BUDGET_USD=0.5`、`AGNES_COST_PER_MILLION_TOKENS=5`。
- 最后一个价格是保守预算估值，不是 Agnes 官方报价。账户限额和实际资费仍以提供方为准，运营者应按账户配置。
- 每个 HTTP 请求在发出前持久化调用次数和最大估算 token 预留；异常/用量缺失时不退还预留，避免失败重试无账可查。
- `public/data/system/ai_cache` 只包含公开证据的结构化摘要、哈希键及聚合预算账本。不得放密钥、原始提示词或私有持仓。CI 必须保留并提交此目录；否则跨工作流缓存和每日预算不能保证。
- 同一输入成功后不重复计费。文件锁抑制同进程/同工作目录并发重复；GitHub Actions 工作流仍需全局 `concurrency`，跨独立副本不共享锁。
- 整体 HTTP 请求采用 `asyncio.wait_for` 限制墙钟时间；单分析最多 5 次请求，包含格式修复。格式不合格最多一次修复，不盲目重试 400/401/403。
- 校验 Schema、引用 ID 和数字词元必须来自引用证据，但不宣称这能证明自然语言因果判断正确。AI 结果只能解释事实，规则信号不得被其改写。
- 无 key 返回 `unavailable`，不影响有效采集数据或规则引擎。此接口供同步 Python 流水线调用，不直接在正在运行的异步事件循环中调用。
