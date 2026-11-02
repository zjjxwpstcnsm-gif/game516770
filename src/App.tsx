import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Database,
  ExternalLink,
  FileText,
  Gamepad2,
  LayoutDashboard,
  LoaderCircle,
  Menu,
  RefreshCw,
  Search,
  ShieldCheck,
  Signal as SignalIcon,
  TriangleAlert,
  X,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Data, ETF, Event, Game, Signal } from "./types";
import {
  describe,
  formatTime,
  number,
  percent,
  safeURL,
  shanghaiDate,
  stale,
  statusLabel,
  upcoming,
} from "./utils";
const nav = [
  ["dashboard", "今日总览", LayoutDashboard],
  ["calendar", "大事件日历", CalendarDays],
  ["games", "游戏情报库", Gamepad2],
  ["etf", "ETF 行情研究", BarChart3],
  ["signals", "投资信号", SignalIcon],
  ["backtest", "历史回测", Activity],
  ["news", "行业情报", FileText],
  ["system", "系统状态", Database],
] as const;
const titles: Record<string, [string, string]> = {
  dashboard: ["今日投资驾驶舱", "从游戏产业事件，到可验证的投资研究。"],
  calendar: ["大事件日历", "区分消息首次公开时间与事件实际发生时间。"],
  games: ["游戏情报库", "游戏热度与投资价值，是两个独立维度。"],
  etf: ["ETF 行情研究", "场内交易价格 · 历史价格不代表未来收益"],
  signals: ["投资信号档案", "规则先行，证据可追溯，不确定性明确可见。"],
  backtest: ["历史事件研究", "买预期，卖事实？让真实交易数据回答。"],
  news: ["行业情报", "原始来源、公开时间与核验状态，一目了然。"],
  system: ["系统状态", "透明呈现采集、分析与发布链路的健康状态。"],
};
function Link({ url, children }: { url?: string; children?: ReactNode }) {
  return safeURL(url) ? (
    <a
      className="source-link"
      href={safeURL(url)}
      target="_blank"
      rel="noreferrer"
    >
      {children || "原始来源"}
      <ExternalLink size={12} />
    </a>
  ) : null;
}
function Empty({
  text = "暂无可用数据",
  detail = "系统将在获得可核实的数据后自动更新。",
}: {
  text?: string;
  detail?: string;
}) {
  return (
    <div className="empty">
      <Database size={25} />
      <strong>{text}</strong>
      <span>{detail}</span>
    </div>
  );
}
function Badge({
  children,
  tone = "muted",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
function Panel({
  title,
  eyebrow,
  action,
  children,
  className = "",
}: {
  title: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-head">
        <div>
          {eyebrow && <span className="eyebrow">{eyebrow}</span>}
          <h2>{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
function BulletList({
  items,
  empty = "暂无充分证据",
}: {
  items?: string[];
  empty?: string;
}) {
  return items?.length ? (
    <ul className="bullet-list">
      {items.map((x, i) => (
        <li key={i}>{x}</li>
      ))}
    </ul>
  ) : (
    <p className="muted small">{empty}</p>
  );
}
function PriceChart({
  etf,
  compact = false,
}: {
  etf?: ETF;
  compact?: boolean;
}) {
  if (!etf?.prices?.length)
    return (
      <Empty
        text="行情数据尚不可用"
        detail="不使用估值或演示价格替代交易所收盘价。"
      />
    );
  const prices = etf.prices.slice(compact ? -60 : -250);
  return (
    <>
      <div className="chart" style={{ height: compact ? 235 : 340 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={prices}
            margin={{ top: 12, right: 12, bottom: 0, left: -20 }}
          >
            <defs>
              <linearGradient
                id={`fill-${etf.code}`}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="0%" stopColor="#44c7ae" stopOpacity={0.22} />
                <stop offset="100%" stopColor="#44c7ae" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#242b34" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: "#83909f", fontSize: 11 }}
              tickFormatter={(x) => x.slice(5)}
              minTickGap={44}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={["auto", "auto"]}
              tick={{ fill: "#83909f", fontSize: 11 }}
              tickFormatter={(x) => number(x, 2)}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: "#171e27",
                border: "1px solid #354151",
                borderRadius: 8,
                color: "#edf2f8",
              }}
              formatter={(v) => [number(v, 3), "收盘价"]}
            />
            <Area
              type="monotone"
              dataKey="close"
              stroke="#44c7ae"
              strokeWidth={2}
              fill={`url(#fill-${etf.code})`}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="chart-caption">
        <span>
          {prices[0]?.date} — {prices.at(-1)?.date} ·{" "}
          {etf.adjustment || "复权方式待核实"}
        </span>
        <Link url={etf.source_url}>行情来源</Link>
      </div>
    </>
  );
}
function EventList({
  events,
  games,
  limit,
}: {
  events: Event[];
  games: Game[];
  limit?: number;
}) {
  return events.length ? (
    <div className="event-list">
      {events.slice(0, limit).map((e) => (
        <a
          className="event-item"
          href={`#/games/${encodeURIComponent(e.game_id)}`}
          key={e.id}
        >
          <div className="event-date">
            <strong>{e.event_date?.slice(8, 10) || "—"}</strong>
            <span>{e.event_date?.slice(0, 7) || "日期未知"}</span>
          </div>
          <div className="event-content">
            <div className="row wrap">
              <Badge
                tone={["SSS", "SS"].includes(e.importance) ? "gold" : "muted"}
              >
                {e.importance}
              </Badge>
              <span className="small muted">
                {games.find((g) => g.id === e.game_id)?.name || e.game_id}
              </span>
            </div>
            <h3>{e.title}</h3>
            <span className="small muted">
              {statusLabel(e.status)} · 首次公开{" "}
              {e.announced_at?.slice(0, 10) || "未知"}
            </span>
          </div>
          <ArrowRight size={16} />
        </a>
      ))}
    </div>
  ) : (
    <Empty
      text="暂无已确认的重大事件"
      detail="不根据传闻或模型推测编造未来日程。"
    />
  );
}
function EtfCards({ data }: { data: Data }) {
  return (
    <div className="etf-cards">
      {data.etfs.length ? (
        data.etfs.map((e) => (
          <a href={`#/etf/${e.code}`} className="etf-card" key={e.code}>
            <div className="row between">
              <span className="ticker">{e.code}</span>
              {e.code === "516770" && <Badge tone="teal">主标的</Badge>}
            </div>
            <h3>{e.name}</h3>
            <div className="row between">
              <strong className="price">{number(e.latest?.close, 3)}</strong>
              <span
                className={
                  typeof e.latest?.change_pct === "number" &&
                  e.latest.change_pct >= 0
                    ? "up"
                    : "down"
                }
              >
                {typeof e.latest?.change_pct === "number" &&
                  (e.latest.change_pct >= 0 ? (
                    <ArrowUpRight size={16} />
                  ) : (
                    <ArrowDownRight size={16} />
                  ))}
                {percent(e.latest?.change_pct)}
              </span>
            </div>
            <div className="small muted">
              场内收盘价 · {e.as_of || "尚无有效行情"}
            </div>
          </a>
        ))
      ) : (
        <Empty text="ETF 行情尚未采集" />
      )}
    </div>
  );
}
function SignalDetail({
  signal,
  aged = false,
}: {
  signal?: Signal;
  aged?: boolean;
}) {
  return (
    <>
      <div className="signal-title">
        <span className="signal-symbol">
          <ShieldCheck size={25} />
        </span>
        <div>
          <span className="eyebrow">
            {aged ? "历史研究快照" : "规则引擎研究结论"}
          </span>
          <h2>
            {aged
              ? "数据已过期，暂停判断"
              : signal?.signal || "数据不足，暂停判断"}
          </h2>
        </div>
      </div>
      <div className="signal-columns">
        <div>
          <h4>主要依据</h4>
          <BulletList items={signal?.reasons} />
        </div>
        <div>
          <h4>风险与失效条件</h4>
          <BulletList
            items={[
              ...(signal?.risks || []),
              ...(signal?.invalidating_conditions || []),
            ]}
          />
        </div>
      </div>
      <div className="signal-bottom">
        <span>
          规则 {signal?.strategy_version || "—"} · 数据截止{" "}
          {formatTime(signal?.data_cutoff_time)}
        </span>
        <Badge tone="muted">启发式评分，非预测概率</Badge>
      </div>
    </>
  );
}
function Dashboard({ data, aged }: { data: Data; aged: boolean }) {
  const primary = data.etfs.find((e) => e.code === "516770");
  const signal = data.signals.find((s) => s.etf_code === "516770");
  const future = upcoming(data.events, 7);
  return (
    <>
      <EtfCards data={data} />
      <div className="dashboard-grid">
        <section className="panel signal-panel">
          <div className="panel-head">
            <span className="eyebrow">TODAY'S RESEARCH · 516770</span>
            <Badge tone={aged ? "amber" : "teal"}>
              {aged ? "历史快照" : statusLabel(data.system.status)}
            </Badge>
          </div>
          <SignalDetail
            signal={signal}
            aged={aged || (!!signal && signal.signal_date !== shanghaiDate())}
          />
        </section>
        <Panel
          title="未来 7 天催化剂"
          eyebrow="UPCOMING CATALYSTS"
          action={
            <a
              href="#/calendar"
              className="icon-link"
              aria-label="查看全部事件"
            >
              <ArrowRight size={18} />
            </a>
          }
        >
          <EventList events={future} games={data.games} limit={3} />
        </Panel>
        <Panel
          title="主标的走势"
          eyebrow="MARKET PULSE"
          action={
            <a href="#/etf" className="subtle-link">
              深入研究 <ArrowRight size={14} />
            </a>
          }
        >
          <PriceChart etf={primary} compact />
        </Panel>
        <Panel title="重点游戏追踪" eyebrow="HIGH-IMPACT GAMES">
          <div className="watch-games">
            {data.games
              .filter((g) => ["SSS", "SS"].includes(g.heat_grade))
              .slice(0, 3)
              .map((g) => (
                <a key={g.id} href={`#/games/${g.id}`}>
                  <div className="game-avatar">
                    <Gamepad2 size={23} />
                  </div>
                  <div>
                    <h3>{g.name}</h3>
                    <span className="small muted">
                      {g.developer || "开发商待核验"}
                    </span>
                  </div>
                  <Badge tone="gold">{g.heat_grade}</Badge>
                </a>
              ))}
          </div>
          {!data.games.some((g) => ["SSS", "SS"].includes(g.heat_grade)) && (
            <Empty text="暂无证据充分的 SSS / SS 游戏" />
          )}
          <p className="note">
            <TriangleAlert size={14} />{" "}
            高热度不等于直接盈利受益，更不等于买入机会。
          </p>
        </Panel>
      </div>
      <div className="two-column">
        <Panel
          title="行业最新情报"
          action={
            <a className="subtle-link" href="#/news">
              全部情报 <ArrowRight size={14} />
            </a>
          }
        >
          {data.news.length ? (
            <div className="news-list">
              {data.news.slice(0, 5).map((n) => (
                <article key={n.id}>
                  <div className="row wrap">
                    <span className="small teal">{n.source}</span>
                    <span className="small muted">
                      {formatTime(n.published_at)}
                    </span>
                    <Badge>{statusLabel(n.verification_status)}</Badge>
                  </div>
                  <h3>
                    <Link url={n.url}>{n.title}</Link>
                  </h3>
                  <p>{n.summary || "暂无中文摘要，请阅读原始来源。"}</p>
                </article>
              ))}
            </div>
          ) : (
            <Empty text="暂无通过校验的资讯" />
          )}
        </Panel>
        <Panel title="未来 30 天时间轴">
          <EventList
            events={upcoming(data.events, 30)}
            games={data.games}
            limit={5}
          />
        </Panel>
      </div>
      <Panel
        title="历史类比，不是必然规律"
        action={
          <a className="subtle-link" href="#/backtest">
            打开事件研究 <ArrowRight size={14} />
          </a>
        }
      >
        <div className="research-callout">
          <Activity size={24} />
          <div>
            <h3>《黑神话：悟空》与《影之刃零》事件窗口</h3>
            <p>
              对照 T−20 至 T+20
              交易日的真实价格路径，区分情绪影响与成分股的盈利关联。两个样本不足以证明可靠交易规律。
            </p>
          </div>
        </div>
      </Panel>
    </>
  );
}
function Calendar({ data }: { data: Data }) {
  const [days, setDays] = useState(30);
  const [grade, setGrade] = useState("all");
  const [mode, setMode] = useState("timeline");
  const [offset, setOffset] = useState(0);
  const events = upcoming(data.events, days).filter(
    (e) => grade === "all" || e.importance === grade,
  );
  const today = new Date(`${shanghaiDate()}T12:00:00+08:00`);
  const month = new Date(today.getFullYear(), today.getMonth() + offset, 1);
  const prefix = `${month.getFullYear()}-${String(month.getMonth() + 1).padStart(2, "0")}`;
  const count = new Date(
    month.getFullYear(),
    month.getMonth() + 1,
    0,
  ).getDate();
  const padding = (month.getDay() + 6) % 7;
  return (
    <>
      <div className="toolbar">
        <div className="tabs">
          {[7, 30, 90].map((d) => (
            <button
              className={days === d ? "selected" : ""}
              onClick={() => setDays(d)}
              key={d}
            >
              未来 {d} 天
            </button>
          ))}
        </div>
        <div className="row">
          <select
            aria-label="事件重要级别"
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
          >
            <option value="all">全部级别</option>
            {["SSS", "SS", "S", "A", "B"].map((g) => (
              <option key={g}>{g}</option>
            ))}
          </select>
          <div className="tabs">
            <button
              onClick={() => setMode("timeline")}
              className={mode === "timeline" ? "selected" : ""}
            >
              时间轴
            </button>
            <button
              onClick={() => setMode("month")}
              className={mode === "month" ? "selected" : ""}
            >
              月历
            </button>
          </div>
        </div>
      </div>
      {mode === "timeline" ? (
        <Panel title={`已公布 / 已确认事件 · ${events.length}`}>
          <EventList events={events} games={data.games} />
        </Panel>
      ) : (
        <Panel
          title={`${prefix.replace("-", " 年 ")} 月`}
          action={
            <div className="row">
              <button
                className="icon-button"
                aria-label="上个月"
                onClick={() => setOffset(offset - 1)}
              >
                <ChevronLeft size={18} />
              </button>
              <button
                className="icon-button"
                aria-label="下个月"
                onClick={() => setOffset(offset + 1)}
              >
                <ChevronRight size={18} />
              </button>
            </div>
          }
        >
          <div className="calendar-grid">
            {["一", "二", "三", "四", "五", "六", "日"].map((d) => (
              <div className="weekday" key={d}>
                {d}
              </div>
            ))}
            {Array.from({ length: padding }, (_, i) => (
              <div key={`p${i}`} className="calendar-cell pad" />
            ))}
            {Array.from({ length: count }, (_, i) => {
              const date = `${prefix}-${String(i + 1).padStart(2, "0")}`;
              return (
                <div
                  className={`calendar-cell ${date === shanghaiDate() ? "today" : ""}`}
                  key={date}
                >
                  <span>{i + 1}</span>
                  {events
                    .filter((e) => e.event_date?.slice(0, 10) === date)
                    .map((e) => (
                      <a
                        key={e.id}
                        href={`#/games/${e.game_id}`}
                        title={e.title}
                      >
                        {e.importance} · {e.title}
                      </a>
                    ))}
                </div>
              );
            })}
          </div>
        </Panel>
      )}
      <p className="note">
        仅展示已公布或已确认且未取消/延期的未来节点；筛选范围按北京时间计算。
      </p>
    </>
  );
}
function Games({ data, id }: { data: Data; id?: string }) {
  const [query, setQuery] = useState("");
  const selected = data.games.find((g) => g.id === id);
  if (selected) {
    const events = data.events
      .filter((e) => e.game_id === selected.id)
      .sort((a, b) => (a.event_date || "").localeCompare(b.event_date || ""));
    return (
      <>
        <a className="subtle-link" href="#/games">
          <ChevronLeft size={16} /> 返回游戏情报库
        </a>
        <Panel
          title={selected.name}
          action={<Badge tone="gold">{selected.heat_grade}</Badge>}
        >
          <div className="detail-grid">
            <div>
              <label>开发商</label>
              <p>{selected.developer || "未核验"}</p>
            </div>
            <div>
              <label>发行商</label>
              <p>{selected.publisher || "未核验"}</p>
            </div>
            <div>
              <label>热度评分</label>
              <p>{number(selected.heat_score, 0)} / 100</p>
            </div>
            <div>
              <label>官方来源</label>
              <p>
                <Link url={selected.official_url}>游戏官网</Link>
              </p>
            </div>
          </div>
          <h4>热度证据</h4>
          <p className="body-copy">{describe(selected.heat_basis)}</p>
          <h4>投资关联：独立于游戏热度</h4>
          <p className="body-copy">{describe(selected.investment_relation)}</p>
        </Panel>
        <Panel title="完整事件里程碑">
          {events.length ? (
            events.map((e) => (
              <div className="milestone" key={e.id}>
                <div className="row between wrap">
                  <h3>{e.title}</h3>
                  <Badge tone={e.status === "confirmed" ? "teal" : "muted"}>
                    {statusLabel(e.status)}
                  </Badge>
                </div>
                <div className="detail-grid">
                  <div>
                    <label>事件发生 / 预计日期</label>
                    <p>{e.event_date || "未确认"}</p>
                  </div>
                  <div>
                    <label>消息首次公开</label>
                    <p>{e.announced_at || "未知"}</p>
                  </div>
                  <div>
                    <label>系统首次发现</label>
                    <p>{formatTime(e.first_seen_at)}</p>
                  </div>
                </div>
                <div className="row wrap">
                  {e.source_urls.map((u, i) => (
                    <Link key={u} url={u}>
                      证据 {i + 1}
                    </Link>
                  ))}
                </div>
                <details>
                  <summary>
                    关系证据与历史修订（{e.history?.length || 0}）
                  </summary>
                  <p>{describe(e.company_links)}</p>
                  <pre>{JSON.stringify(e.history || [], null, 2)}</pre>
                </details>
              </div>
            ))
          ) : (
            <Empty text="暂无已核实的里程碑" />
          )}
        </Panel>
      </>
    );
  }
  return (
    <>
      <div className="search-box">
        <Search size={18} />
        <input
          aria-label="搜索游戏"
          placeholder="搜索游戏名称、别名或开发商…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      <div className="game-grid">
        {data.games
          .filter((g) =>
            [g.name, ...(g.aliases || []), g.developer]
              .join(" ")
              .toLowerCase()
              .includes(query.toLowerCase()),
          )
          .map((g) => (
            <a className="panel game-card" href={`#/games/${g.id}`} key={g.id}>
              <div className="row between">
                <Gamepad2 size={27} />
                <Badge
                  tone={["SSS", "SS"].includes(g.heat_grade) ? "gold" : "muted"}
                >
                  {g.heat_grade}
                </Badge>
              </div>
              <h2>{g.name}</h2>
              <span className="small muted">
                {g.developer || "开发商待核验"}
              </span>
              <p>{describe(g.investment_relation)}</p>
              <div className="row between small">
                <span>
                  {data.events.filter((e) => e.game_id === g.id).length}{" "}
                  个里程碑
                </span>
                <ArrowRight size={16} />
              </div>
            </a>
          ))}
      </div>
      {!data.games.length && <Empty text="游戏实体库尚未建立" />}
    </>
  );
}
function EtfPage({ data, id }: { data: Data; id?: string }) {
  const [code, setCode] = useState(id || "516770");
  const e = data.etfs.find((e) => e.code === code);
  return (
    <>
      <div className="tabs etf-tabs">
        {data.etfs.map((e) => (
          <button
            key={e.code}
            className={code === e.code ? "selected" : ""}
            onClick={() => setCode(e.code)}
          >
            {e.code} · {e.name}
          </button>
        ))}
      </div>
      {e ? (
        <>
          <Panel title={e.name} action={<Badge tone="teal">场内收盘价</Badge>}>
            <div className="market-summary">
              <strong className="price">{number(e.latest?.close, 3)}</strong>
              <span
                className={(e.latest?.change_pct || 0) >= 0 ? "up" : "down"}
              >
                {percent(e.latest?.change_pct)}
              </span>
              <span className="muted small">
                {e.as_of || "行情日期缺失"} · {e.index_name || "跟踪指数待核实"}
              </span>
            </div>
            <PriceChart etf={e} />
          </Panel>
          <Panel title="技术指标与趋势">
            <div className="indicator-grid">
              {[
                ["ma5", "5 日均线"],
                ["ma10", "10 日均线"],
                ["ma20", "20 日均线"],
                ["ma60", "60 日均线"],
                ["rsi14", "RSI 14"],
                ["volatility20", "20 日波动率"],
                ["return5", "5 日收益"],
                ["return20", "20 日收益"],
                ["return60", "60 日收益"],
              ].map(([k, label]) => (
                <div key={k}>
                  <label>{label}</label>
                  <strong>
                    {k.startsWith("return") || k === "volatility20"
                      ? percent(e.indicators?.[k])
                      : number(e.indicators?.[k], k.startsWith("ma") ? 3 : 2)}
                  </strong>
                </div>
              ))}
            </div>
          </Panel>
          <Panel
            title="持仓与受益映射"
            action={
              <span className="small muted">
                持仓日期 {e.holdings_as_of || "未知"}
              </span>
            }
          >
            {e.holdings?.some((h) => !h.published_at) && (
              <p className="notice warning">
                部分持仓缺少首次公开时间，不作为历史回测当时已知权重。期末持仓也不代表当前实时权重。
              </p>
            )}
            {e.holdings?.length ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>成分股</th>
                      <th>代码</th>
                      <th>披露权重</th>
                      <th>持仓期末</th>
                      <th>证据</th>
                    </tr>
                  </thead>
                  <tbody>
                    {e.holdings.map((h, i) => (
                      <tr key={i}>
                        <td>{String(h.name || "未提供")}</td>
                        <td className="ticker">{String(h.code || "—")}</td>
                        <td>{percent(h.weight)}</td>
                        <td>{String(h.as_of || e.holdings_as_of || "未知")}</td>
                        <td>
                          <Link
                            url={
                              typeof h.source_url === "string"
                                ? h.source_url
                                : undefined
                            }
                          >
                            原始披露
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <Empty
                text="尚无可验证的持仓权重"
                detail="缺失权重不会填零或推断直接受益；未核实关系只作行业情绪研究。"
              />
            )}
          </Panel>
        </>
      ) : (
        <Empty text="该 ETF 暂无有效数据" />
      )}
    </>
  );
}
function Signals({ data, aged }: { data: Data; aged: boolean }) {
  const [archive, setArchive] = useState<Signal[]>(data.signals);
  const [selectedDate, setSelectedDate] = useState("latest");
  const [archiveError, setArchiveError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${import.meta.env.BASE_URL}data/signals.json`, {
      signal: controller.signal,
    })
      .then((r) => {
        if (!r.ok) throw Error("archive");
        return r.json();
      })
      .then((value) => {
        if (Array.isArray(value)) setArchive(value);
        else throw Error("schema");
      })
      .catch((e) => {
        if (e.name !== "AbortError") setArchiveError(true);
      });
    return () => controller.abort();
  }, [data]);
  const displayed =
    selectedDate === "latest"
      ? data.signals
      : archive.filter((s) => s.signal_date === selectedDate);
  return (
    <>
      <div className="notice">
        <TriangleAlert size={18} />
        <span>
          本页是研究参考，不保证收益，不执行真实证券交易。评分是透明的启发式规则，不是上涨概率。
        </span>
      </div>
      <div className="toolbar">
        <span className="small muted">
          保留首次生成的历史信号，不用后续信息改写
        </span>
        <select
          aria-label="历史信号日期"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
        >
          <option value="latest">最新研究</option>
          {[...new Set(archive.map((s) => s.signal_date))]
            .sort()
            .reverse()
            .map((date) => (
              <option key={date} value={date}>
                {date} · 历史快照
              </option>
            ))}
        </select>
      </div>
      {archiveError && (
        <p className="note">历史信号档案暂不可用，当前快照仍可查看。</p>
      )}
      {displayed.length ? (
        displayed.map((s, i) => (
          <Panel
            key={`${s.etf_code}-${s.signal_date}-${i}`}
            title={`${s.etf_code} · ${s.signal_date}`}
          >
            <SignalDetail
              signal={s}
              aged={aged || s.signal_date !== shanghaiDate()}
            />
            {selectedDate !== "latest" && (
              <p className="note">
                当时归档结论：{s.signal}。仅供回看，不是今日建议。
              </p>
            )}
            <details>
              <summary>评分依据与可追溯来源</summary>
              <p>{describe(s.confidence_basis)}</p>
              <div className="score-breakdown">
                {s.score_breakdown?.map((b) => (
                  <section className="score-event" key={b.event_id}>
                    <div className="row between wrap">
                      <h4>
                        {data.events.find((e) => e.id === b.event_id)?.title ||
                          b.event_id}
                      </h4>
                      <Badge tone="teal">
                        启发式评分 {number(b.score, 1)} / 100
                      </Badge>
                    </div>
                    <div className="indicator-grid">
                      {Object.entries(b.components).map(([key, value]) => (
                        <div key={key}>
                          <label>
                            {{
                              event_importance: "事件重要性",
                              credibility: "证据可信度",
                              heat: "游戏热度",
                              timing: "时间窗口",
                              etf_relation: "ETF 受益关联",
                              trend: "市场趋势确认",
                            }[key] || key}
                          </label>
                          <strong>{number(value, 0)}</strong>
                        </div>
                      ))}
                    </div>
                    {b.exposure && (
                      <>
                        <p>
                          影响渠道：
                          {{
                            direct: "直接盈利关联",
                            indirect: "间接经济关联",
                            sentiment: "行业情绪，未核实直接收益",
                          }[b.exposure.relation] || "无明确关联"}{" "}
                          · 已核实关联持仓：
                          {percent(b.exposure.verified_holding_weight)}
                        </p>
                        <p className="note">{b.exposure.limitation}</p>
                        {b.exposure.evidence?.map((e, i) => (
                          <div className="row wrap small" key={i}>
                            <span>
                              {String(e.stock_code || "")} · 权重{" "}
                              {percent(e.holding_weight)} · 截止{" "}
                              {String(e.holdings_as_of || "未知")}
                            </span>
                            <Link
                              url={
                                typeof e.source_url === "string"
                                  ? e.source_url
                                  : undefined
                              }
                            >
                              关系证据
                            </Link>
                            <Link
                              url={
                                typeof e.holdings_source === "string"
                                  ? e.holdings_source
                                  : undefined
                              }
                            >
                              权重来源
                            </Link>
                          </div>
                        ))}
                      </>
                    )}
                  </section>
                ))}
              </div>
              <div className="row wrap">
                {s.source_ids.map((id) => {
                  const n = data.news.find((n) => n.id === id);
                  const e = data.events.find((e) => e.id === id);
                  return n ? (
                    <Link key={id} url={n.url}>
                      {n.title}
                    </Link>
                  ) : e ? (
                    <a
                      className="source-link"
                      key={id}
                      href={`#/games/${e.game_id}`}
                    >
                      {e.title}
                    </a>
                  ) : safeURL(id) ? (
                    <Link key={id} url={id}>
                      原始证据
                    </Link>
                  ) : (
                    <code key={id}>{id}</code>
                  );
                })}
              </div>
            </details>
          </Panel>
        ))
      ) : (
        <Empty text="数据不足，暂停判断" />
      )}
      <Panel title="历史信号与每日研究档案">
        <p className="body-copy">
          每日信号按研究日期保存至公开报告档案，保留当时的数据截止时间、策略版本和证据。请勿将当前事件库回填为历史已知信息。
        </p>
        <Link url="https://github.com/zjjxwpstcnsm-gif/game516770/tree/main/public/data/reports">
          查看按日期保存的历史报告
        </Link>
      </Panel>
    </>
  );
}
function Backtest({ data }: { data: Data }) {
  const [code, setCode] = useState("516770");
  const studies = data.event_studies.filter((s) => s.etf_code === code);
  const offsets = [-20, -10, -5, -1, 0, 1, 3, 5, 10, 20];
  const comparison = offsets.map((offset) => {
    const row: Record<string, unknown> = { offset };
    studies.forEach((study, i) => {
      const point = ((study.points as Record<string, unknown>[]) || []).find(
        (p) => p.offset === offset,
      );
      row[`s${i}`] =
        typeof point?.return === "number" ? point.return * 100 : null;
    });
    return row;
  });
  return (
    <>
      <div className="notice">
        <TriangleAlert size={18} />
        <span>
          小样本事件研究不代表因果关系。需控制同期市场表现、交易成本和首次已知时间；缺失窗口不会用预测补齐。
        </span>
      </div>
      <Panel
        title="同基准事件窗口对比"
        eyebrow="EVENT STUDY · T−20 → T+20"
        action={
          <select
            value={code}
            aria-label="事件研究 ETF"
            onChange={(e) => setCode(e.target.value)}
          >
            {data.etfs.map((e) => (
              <option key={e.code} value={e.code}>
                {e.code}
              </option>
            ))}
          </select>
        }
      >
        {studies.length ? (
          <>
            <div className="row wrap" style={{ marginBottom: 18 }}>
              {studies.map((s, i) => (
                <span
                  className="small"
                  style={{ color: ["#55c9b1", "#d9b876", "#90aaf4"][i % 3] }}
                  key={i}
                >
                  {String(s.title)}
                  {s.complete_window ? "" : " · 窗口未完整"}
                </span>
              ))}
            </div>
            <div className="chart" style={{ height: 300 }}>
              <ResponsiveContainer>
                <LineChart data={comparison}>
                  <CartesianGrid stroke="#242b34" />
                  <XAxis
                    dataKey="offset"
                    tick={{ fill: "#83909f", fontSize: 11 }}
                    tickFormatter={(v) => `T${v >= 0 ? "+" : ""}${v}`}
                  />
                  <YAxis
                    tick={{ fill: "#83909f", fontSize: 11 }}
                    tickFormatter={(v) => `${v}%`}
                  />
                  <Tooltip
                    formatter={(v) => `${number(v)}%`}
                    contentStyle={{
                      background: "#171e27",
                      border: "1px solid #354151",
                    }}
                  />
                  <ReferenceLine x={0} stroke="#d9b876" strokeDasharray="4 4" />
                  <ReferenceLine y={0} stroke="#657484" />
                  {studies.map((s, i) => (
                    <Line
                      key={i}
                      dataKey={`s${i}`}
                      name={String(s.title)}
                      stroke={["#55c9b1", "#d9b876", "#90aaf4"][i % 3]}
                      dot={false}
                      connectNulls={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="note">
              统一以 T−1 收盘价为
              0%。不连结缺失数据点，发售前后尚未完整的区间保持空缺。
            </p>
          </>
        ) : (
          <Empty text="暂无可比较的真实事件窗口" />
        )}
      </Panel>
      <Panel title="各事件数据与口径">
        {data.event_studies.length ? (
          data.event_studies.map((s, i) => {
            const points = (
              (s.points || s.window || s.series || []) as Record<
                string,
                unknown
              >[]
            ).map((p) => ({
              ...p,
              cumulative_return:
                typeof p.return === "number" ? p.return * 100 : null,
            }));
            return (
              <div className="study" key={i}>
                <h3>
                  {String(s.title || s.event_title || s.event_id || "历史事件")}{" "}
                  <span className="muted small">
                    {String(s.etf_code || "516770")}
                  </span>
                </h3>
                {points.length ? (
                  <div className="chart" style={{ height: 270 }}>
                    <ResponsiveContainer>
                      <LineChart data={points}>
                        <CartesianGrid stroke="#242b34" />
                        <XAxis
                          dataKey="offset"
                          tick={{ fill: "#83909f", fontSize: 11 }}
                        />
                        <YAxis tick={{ fill: "#83909f", fontSize: 11 }} />
                        <Tooltip
                          contentStyle={{
                            background: "#171e27",
                            border: "1px solid #354151",
                          }}
                        />
                        <ReferenceLine
                          x={0}
                          stroke="#d9b876"
                          strokeDasharray="4 4"
                        />
                        <Line
                          dataKey="cumulative_return"
                          name="累计收益 %"
                          stroke="#44c7ae"
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <Empty
                    text="事件窗口尚不完整"
                    detail={String(
                      s.reason ||
                        s.message ||
                        "需要真实、完整的事件日前后交易价格。",
                    )}
                  />
                )}
                <details>
                  <summary>事件研究结果与数据口径</summary>
                  <pre>{JSON.stringify(s, null, 2)}</pre>
                </details>
              </div>
            );
          })
        ) : (
          <Empty
            text="尚无完整的事件窗口"
            detail="仅在官方事件日期和真实历史价格均可验证时生成研究结果。"
          />
        )}
      </Panel>
      <Panel title="策略回测与验证集">
        <p className="body-copy">
          使用当时已知事件回放，信号后下一交易日执行；同时报告费用、滑点、样本量和买入持有基准。未完成验证时不展示收益承诺。
        </p>
        <div className="indicator-grid" style={{ marginTop: 24 }}>
          {[
            ["sample_size", "已平仓样本"],
            ["win_rate", "胜率"],
            ["cumulative_return", "策略累计收益"],
            ["max_drawdown", "最大回撤"],
            ["buy_hold_return", "买入持有收益"],
          ].map(([key, label]) => (
            <div key={key}>
              <label>{label}</label>
              <strong>
                {key === "sample_size"
                  ? number(data.backtest[key], 0)
                  : Number(data.backtest.sample_size) > 0
                    ? percent(data.backtest[key])
                    : "—"}
              </strong>
            </div>
          ))}
        </div>
        <p className="note">
          {statusLabel(String(data.backtest.status))} · 费用{" "}
          {String(data.backtest.transaction_cost_bps ?? "未知")} bps + 滑点{" "}
          {String(data.backtest.slippage_bps ?? "未知")}{" "}
          bps。零交易样本不展示虚假的有效绩效。
        </p>
        <details>
          <summary>回测状态与指标</summary>
          <pre>
            {JSON.stringify(
              data.backtest || { status: "unavailable" },
              null,
              2,
            )}
          </pre>
        </details>
      </Panel>
    </>
  );
}
function NewsPage({ data }: { data: Data }) {
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("all");
  const [category, setCategory] = useState("all");
  const filtered = data.news
    .filter(
      (n) =>
        (source === "all" || n.source === source) &&
        (category === "all" || n.category === category) &&
        `${n.title} ${n.summary}`.toLowerCase().includes(query.toLowerCase()),
    )
    .sort((a, b) => (b.published_at || "").localeCompare(a.published_at || ""));
  return (
    <>
      <div className="toolbar">
        <div className="search-box">
          <Search size={18} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索行业资讯…"
            aria-label="搜索资讯"
          />
        </div>
        <div className="row">
          <select
            aria-label="筛选资讯来源"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          >
            <option value="all">全部来源</option>
            {[...new Set(data.news.map((n) => n.source))].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
          <select
            aria-label="筛选资讯主题"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="all">全部主题</option>
            {[...new Set(data.news.map((n) => n.category))].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>
      <Panel title={`行业情报 · ${filtered.length} 条`}>
        <div className="news-list full">
          {filtered.map((n) => (
            <article key={n.id}>
              <div className="row between wrap">
                <div className="row wrap">
                  <Badge tone="teal">{n.source}</Badge>
                  <Badge>{statusLabel(n.verification_status)}</Badge>
                  <span className="small muted">
                    可信度 {n.credibility_score} / 100
                  </span>
                </div>
                <span className="small muted">
                  发布时间 {formatTime(n.published_at)}
                </span>
              </div>
              <h3>
                <Link url={n.url}>{n.title}</Link>
              </h3>
              <p>{n.summary || "AI 分析暂不可用，请查看原始来源。"}</p>
              <div className="row between wrap">
                <span className="small muted">
                  采集于 {formatTime(n.collected_at)}
                </span>
                {n.game_ids.map((id) => (
                  <a
                    key={id}
                    className="subtle-link small"
                    href={`#/games/${id}`}
                  >
                    {data.games.find((g) => g.id === id)?.name || id}
                  </a>
                ))}
              </div>
              {!!n.limitations && (
                <p className="note">数据限制：{describe(n.limitations)}</p>
              )}
            </article>
          ))}
        </div>
        {!filtered.length && <Empty text="没有符合筛选条件的资讯" />}
      </Panel>
    </>
  );
}
function System({ data, aged }: { data: Data; aged: boolean }) {
  return (
    <>
      <div className="system-cards">
        <div className="panel">
          <span className="eyebrow">DATA FRESHNESS</span>
          <h2>{aged ? "数据已过期" : "快照更新时间有效"}</h2>
          <span className="small muted">{formatTime(data.generated_at)}</span>
        </div>
        <div className="panel">
          <span className="eyebrow">AI ANALYSIS</span>
          <h2>
            {statusLabel(
              data.system.ai_status || data.report.ai_status || "unavailable",
            )}
          </h2>
          <span className="small muted">
            最近成功 {formatTime(data.system.last_ai_success_at)}
          </span>
          <p className="note">AI 失败不阻断事实数据和规则引擎</p>
        </div>
        <div className="panel">
          <span className="eyebrow">STRATEGY VERSION</span>
          <h2>{data.system.strategy_version || "—"}</h2>
          <span className="small muted">规则版本可追溯</span>
        </div>
      </div>
      <Panel title="数据源健康状态">
        {data.system.source_status?.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>数据源</th>
                  <th>状态</th>
                  <th>采集结果</th>
                  <th>说明</th>
                </tr>
              </thead>
              <tbody>
                {data.system.source_status.map((s, i) => (
                  <tr key={i}>
                    <td>{s.name || s.source || String(s.id || i + 1)}</td>
                    <td>
                      <Badge
                        tone={
                          ["ok", "success"].includes(s.status)
                            ? "teal"
                            : "amber"
                        }
                      >
                        {statusLabel(s.status)}
                      </Badge>
                    </td>
                    <td>{s.count ?? String(s.records ?? "—")}</td>
                    <td className="wrap-cell">{s.error || s.message || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty text="尚无采集运行记录" />
        )}
      </Panel>
      <Panel title="运行和发布信息">
        <div className="detail-grid">
          <div>
            <label>最近采集成功</label>
            <p>{formatTime(data.system.last_success_at)}</p>
          </div>
          <div>
            <label>数据截止</label>
            <p>{formatTime(data.data_cutoff_time)}</p>
          </div>
          <div>
            <label>时区</label>
            <p>Asia/Shanghai</p>
          </div>
          <div>
            <label>Schema 版本</label>
            <p>{data.schema_version}</p>
          </div>
          <div>
            <label>生产构建状态</label>
            <p>{statusLabel(data.system.build_status || "unavailable")}</p>
          </div>
          <div>
            <label>构建版本</label>
            <p>
              {data.system.build_commit?.slice(0, 12) || "尚无 CI 版本记录"}
            </p>
          </div>
        </div>
        <div className="row wrap">
          <Link url={data.system.build_run_url || undefined}>
            本次构建运行记录
          </Link>
          <Link url="https://github.com/zjjxwpstcnsm-gif/game516770/actions">
            查看真实 Actions 运行与构建状态
          </Link>
          <Link url="https://github.com/zjjxwpstcnsm-gif/game516770">
            查看源码与配置
          </Link>
        </div>
        <p className="note">
          北京时间每日 08:20、工作日 17:25、周日 20:30 定时运行；GitHub
          调度可能延迟，实际结果以运行记录为准。
        </p>
        <details>
          <summary>完整运行诊断</summary>
          <pre>{JSON.stringify(data.system, null, 2)}</pre>
        </details>
      </Panel>
    </>
  );
}
export default function App() {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [route, setRoute] = useState(location.hash.slice(2) || "dashboard");
  const [menu, setMenu] = useState(false);
  const [retry, setRetry] = useState(0);
  const [clock, setClock] = useState(Date.now());
  useEffect(() => {
    const timer = setInterval(() => setClock(Date.now()), 60000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    const listener = () => {
      setRoute(location.hash.slice(2) || "dashboard");
      setMenu(false);
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", listener);
    return () => window.removeEventListener("hashchange", listener);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    fetch(`${import.meta.env.BASE_URL}data/latest.json`, {
      signal: controller.signal,
      cache: "no-cache",
    })
      .then(async (r) => {
        if (!r.ok) throw Error(`HTTP ${r.status}`);
        const value = await r.json();
        if (
          !value.generated_at ||
          !Array.isArray(value.etfs) ||
          !Array.isArray(value.events) ||
          !value.system
        )
          throw Error("数据格式不符合约定");
        setData(value);
      })
      .catch((e) => {
        if (e.name !== "AbortError")
          setError(`无法读取有效的数据快照（${e.message}）。`);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [retry]);
  const [page, id] = route.split("/");
  const validPage = nav.some((n) => n[0] === page) ? page : "dashboard";
  const title = titles[validPage];
  const aged = useMemo(
    () => (data ? stale(data.generated_at, clock) : true),
    [data, clock],
  );
  return (
    <div className="app-shell">
      <aside className={`sidebar ${menu ? "open" : ""}`}>
        <a href="#/dashboard" className="brand">
          <span className="brand-mark">
            G<span>α</span>
          </span>
          <div>
            GAME ALPHA<small>游戏行业投资情报中心</small>
          </div>
        </a>
        <span className="nav-label">研究工作台</span>
        <nav>
          {nav.map(([key, label, Icon]) => (
            <a
              href={`#/${key}`}
              key={key}
              className={validPage === key ? "active" : ""}
            >
              <Icon size={18} />
              <span>{label}</span>
              {key === "dashboard" && <span className="nav-dot" />}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="row">
            <span className={`status-dot ${aged ? "warn" : ""}`} />
            <span>
              {data ? (aged ? "历史快照模式" : "数据快照已载入") : "等待数据"}
            </span>
          </div>
          <p>
            事实优先 · 证据驱动
            <br />
            独立判断，不追逐噪音。
          </p>
          <Link url="https://github.com/zjjxwpstcnsm-gif/game516770">
            GitHub 开源项目
          </Link>
        </div>
      </aside>
      {menu && (
        <button
          className="overlay"
          onClick={() => setMenu(false)}
          aria-label="关闭导航"
        />
      )}
      <div className="main-shell">
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            aria-label={menu ? "关闭菜单" : "打开菜单"}
            onClick={() => setMenu(!menu)}
          >
            {menu ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="breadcrumb">
            研究工作台 <ChevronRight size={13} /> <span>{title[0]}</span>
          </div>
          <div className="row topbar-right">
            <span className="live-chip">
              <span className="status-dot" /> 研究终端
            </span>
            <span className="small muted">
              <Clock3 size={13} /> 北京时间
            </span>
            <button
              className="icon-button"
              aria-label="重新加载数据"
              onClick={() => setRetry(retry + 1)}
            >
              <RefreshCw size={16} className={loading ? "spin" : ""} />
            </button>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <span className="eyebrow">GAME INDUSTRY INTELLIGENCE</span>
              <h1>{title[0]}</h1>
              <p>{title[1]}</p>
            </div>
            <div className="date-box">
              <strong>{data?.report?.date || shanghaiDate()}</strong>
              <span>快照更新 {formatTime(data?.generated_at)}</span>
            </div>
          </div>
          {data && aged && (
            <div className="notice warning" role="status">
              <TriangleAlert size={18} />
              <span>
                当前为过期历史快照，不代表今日建议。最近更新：
                {formatTime(data.generated_at)}。实时研究判断已暂停。
              </span>
            </div>
          )}
          {loading && !data ? (
            <div className="loading" role="status">
              <LoaderCircle className="spin" size={28} />
              <h2>正在读取研究数据</h2>
              <p>核对行情、事件与数据来源…</p>
            </div>
          ) : error ? (
            <div className="panel error-panel" role="alert">
              <TriangleAlert size={30} />
              <h2>研究数据暂不可用</h2>
              <p>{error}</p>
              <p className="muted">
                首次部署需要运行数据流水线。我们不会用演示数据替代真实市场信息。
              </p>
              <button
                className="primary-button"
                onClick={() => setRetry(retry + 1)}
              >
                重新加载
              </button>
              <Link url="https://github.com/zjjxwpstcnsm-gif/game516770/actions">
                查看流水线状态
              </Link>
            </div>
          ) : data ? (
            <>
              {validPage === "dashboard" && (
                <Dashboard data={data} aged={aged} />
              )}{" "}
              {validPage === "calendar" && <Calendar data={data} />}{" "}
              {validPage === "games" && <Games data={data} id={id} />}{" "}
              {validPage === "etf" && <EtfPage data={data} id={id} />}{" "}
              {validPage === "signals" && <Signals data={data} aged={aged} />}{" "}
              {validPage === "backtest" && <Backtest data={data} />}{" "}
              {validPage === "news" && <NewsPage data={data} />}{" "}
              {validPage === "system" && <System data={data} aged={aged} />}
            </>
          ) : null}
          <footer>
            <span>
              GAME ALPHA <span className="muted">/ 证据驱动的游戏行业研究</span>
            </span>
            <p>
              仅供研究参考，不构成个性化投资建议。不保证收益，不执行证券交易。所有日期均按北京时间展示。
            </p>
          </footer>
        </main>
      </div>
    </div>
  );
}
