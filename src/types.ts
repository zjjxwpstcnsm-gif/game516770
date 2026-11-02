export type Price = {
  date: string;
  close: number;
  open?: number;
  high?: number;
  low?: number;
  volume?: number;
  amount?: number;
};
export type ETF = {
  code: string;
  name: string;
  index_name?: string;
  price_type?: string;
  as_of?: string | null;
  source_url?: string;
  adjustment?: string;
  latest?: {
    close?: number | null;
    change_pct?: number | null;
    volume?: number | null;
    amount?: number | null;
  };
  indicators?: Record<string, number | null>;
  prices: Price[];
  holdings: Record<string, unknown>[];
  holdings_as_of?: string | null;
};
export type Game = {
  id: string;
  name: string;
  aliases?: string[];
  developer?: string;
  publisher?: string;
  heat_grade: string;
  heat_score?: number | null;
  heat_basis?: unknown;
  official_url?: string;
  steam_app_id?: string | number;
  investment_relation?: unknown;
};
export type Event = {
  id: string;
  game_id: string;
  title: string;
  type: string;
  importance: string;
  event_date: string | null;
  announced_at?: string | null;
  first_seen_at?: string | null;
  status: string;
  source_urls: string[];
  company_links?: unknown[];
  history?: unknown[];
};
export type News = {
  id: string;
  title: string;
  url: string;
  source: string;
  published_at: string | null;
  collected_at: string;
  game_ids: string[];
  category: string;
  summary: string;
  verification_status: string;
  credibility_score: number;
  limitations?: unknown;
};
export type Signal = {
  signal_date: string;
  etf_code: string;
  data_cutoff_time?: string | null;
  signal: string;
  signal_score?: number | null;
  confidence_basis?: unknown;
  score_breakdown?: {
    event_id: string;
    score: number;
    components: Record<string, number>;
    exposure?: {
      relation: string;
      verified_holding_weight?: number | null;
      holdings_as_of?: string | null;
      limitation?: string;
      evidence?: Record<string, unknown>[];
    };
  }[];
  reasons: string[];
  risks: string[];
  invalidating_conditions: string[];
  strategy_version: string;
  source_ids: string[];
};
export type SourceStatus = {
  name?: string;
  source?: string;
  status: string;
  error?: string;
  message?: string;
  count?: number;
  last_success_at?: string;
  [key: string]: unknown;
};
export type Data = {
  schema_version: string;
  generated_at: string;
  timezone: string;
  data_cutoff_time?: string | null;
  news: News[];
  games: Game[];
  events: Event[];
  etfs: ETF[];
  signals: Signal[];
  report: {
    date?: string;
    summary?: string;
    reasons?: string[];
    risks?: string[];
    source_ids?: string[];
    ai_status?: string;
  };
  system: {
    status: string;
    generated_at?: string;
    last_success_at?: string | null;
    source_status: SourceStatus[];
    strategy_version: string;
    ai_status?: string;
    last_ai_success_at?: string | null;
    build_status?: string;
    build_run_url?: string | null;
    build_commit?: string | null;
    [key: string]: unknown;
  };
  event_studies: Record<string, unknown>[];
  backtest: Record<string, unknown>;
};
